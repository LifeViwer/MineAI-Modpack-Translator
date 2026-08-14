from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import Mapping

from .core import ProtectedFragment, TranslationPlan, TranslationUnit, ValidationError
from .locale_safe import MinecraftLangJsonAdapter as _LocaleAdapter
from .minecraft_lang import _PLACEHOLDER_RE
from .patchouli import PatchouliBookJsonAdapter as _SpanJsonAdapter, _Node

_BOOK_PATH_RE = re.compile(
    r"(^|/)data/[^/]+/modonomicon/books/[^/]+/(?:book\.json|categories/.+\.json|entries/.+\.json)$",
    re.IGNORECASE,
)
_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё]{2,}")
_TRANSLATION_KEY_RE = re.compile(r"^book\.[^\s]+$")
_RESOURCE_ID_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$", re.IGNORECASE)
_LITERAL_KEYS = frozenset(
    {
        "name",
        "description",
        "text",
        "title",
        "title1",
        "title2",
        "heading",
        "tooltip",
        "multiblock_name",
    }
)

# Corpus-proven Modonomicon markdown/runtime syntax.
_COLOR_TAG_RE = re.compile(r"\[#\]\((?:[0-9A-Fa-f]{6,8})?\)")
_LINK_RE = re.compile(
    r"\[([^\]\r\n]+)\]\(((?:entry|category|book|https?)://[^)\r\n]+)\)",
    re.IGNORECASE,
)
_MARKDOWN_DELIM_RE = re.compile(r"\*+|_+|`+")
_BACKSLASH_RE = re.compile(r"\\")
_RAW_TAB_RE = re.compile(r"\t")


class ModonomiconBookJsonAdapter(_SpanJsonAdapter):
    """Span-preserving adapter for corpus-proven Modonomicon book JSON.

    Modonomicon book structure is language-neutral and lives under ``data/``.
    Most books reference ``book.*`` locale keys; those references are immutable.
    Only literal prose in known display fields becomes a TranslationUnit, so a
    translated overlay can be emitted into MineAI's datapack without touching
    IDs, recipes, anchors, parents, conditions or other runtime structure.

    A small amount of real Modonomicon content uses Gson-style backslash + raw
    newline continuations inside strings. The parser accepts exactly that
    proven extension and preserves its original lexical form on reconstruction.
    """

    name = "modonomicon-book-json"

    def matches(self, path: str) -> bool:
        slash = "/" + path.replace("\\", "/").lstrip("/")
        return bool(_BOOK_PATH_RE.search(slash))

    def target_path(self, path: str, target_code: str) -> str:
        if not self.matches(path):
            raise ValueError(f"Unsupported Modonomicon book path: {path}")
        # Language-neutral book JSON is overlaid at the same data path in the
        # generated datapack. target_code is intentionally irrelevant here.
        return path.replace("\\", "/")

    def prepare(self, path: str, source_text: str) -> TranslationPlan:
        root = self._parse(source_text)
        targets: list[tuple[str, _Node, str]] = []
        self._collect(root, "", targets)
        units: list[TranslationUnit] = []
        originals: dict[str, str] = {}
        original_tokens: dict[str, str] = {}
        for locator, node, value in targets:
            if not self._is_literal_prose(value):
                continue
            masked, protected = self._protect_modonomicon(value)
            unit_id = f"json:{locator}"
            units.append(
                TranslationUnit(
                    id=unit_id,
                    text=masked,
                    start=node.start,
                    end=node.end,
                    kind="modonomicon-literal-text",
                    context=f"{path}:{locator}",
                    protected=protected,
                )
            )
            originals[unit_id] = value
            original_tokens[unit_id] = source_text[node.start : node.end]
        return TranslationPlan(
            path=path,
            source_text=source_text,
            units=tuple(units),
            metadata={
                "fingerprint": self.fingerprint(source_text),
                "originals": originals,
                "original_tokens": original_tokens,
            },
        )

    def apply(self, plan: TranslationPlan, translations: Mapping[str, str]) -> str:
        known = {unit.id for unit in plan.units}
        unknown = set(translations) - known
        if unknown:
            raise ValidationError(f"Unknown translation unit ids: {sorted(unknown)!r}")
        originals = plan.metadata.get("originals")
        tokens = plan.metadata.get("original_tokens")
        if not isinstance(originals, dict) or not isinstance(tokens, dict):
            raise ValidationError("Modonomicon plan is missing original values")

        replacements: list[tuple[int, int, str]] = []
        for unit in plan.units:
            if unit.id not in translations:
                continue
            restored = self._restore(unit, translations[unit.id])
            original = originals.get(unit.id)
            original_token = tokens.get(unit.id)
            if not isinstance(original, str) or not isinstance(original_token, str):
                raise ValidationError(f"Missing original Modonomicon value for {unit.id}")
            self._validate_restored(unit.id, original, restored)
            token = (
                original_token
                if restored == original
                else self._encode_like_source(restored, original_token)
            )
            replacements.append((unit.start, unit.end, token))

        output = plan.source_text
        for start, end, token in sorted(replacements, reverse=True):
            output = output[:start] + token + output[end:]
        self.validate(plan.source_text, output)
        return output

    def validate_candidate(
        self, plan: TranslationPlan, unit_id: str, candidate: str
    ) -> None:
        unit = plan.by_id().get(unit_id)
        originals = plan.metadata.get("originals")
        if unit is None or not isinstance(originals, dict):
            raise ValidationError(f"Unknown Modonomicon translation unit: {unit_id}")
        original = originals.get(unit_id)
        if not isinstance(original, str):
            raise ValidationError(f"Missing original Modonomicon value for {unit_id}")
        restored = self._restore(unit, candidate)
        self._validate_restored(unit_id, original, restored)

    def _collect(self, root: _Node, path: str, out) -> None:
        self._collect_node(root, path, out)

    def _collect_fingerprint(self, root: _Node, path: str, out) -> None:
        # Fingerprinting uses schema locations, not whether target wording still
        # looks like prose. Translation-key fields are immutable and therefore
        # deliberately excluded from both translation and fingerprint spans.
        self._collect_node(root, path, out, include_nonprose_literals=True)

    def _collect_node(
        self,
        node: _Node,
        path: str,
        out: list[tuple[str, _Node, str]],
        *,
        include_nonprose_literals: bool = False,
    ) -> None:
        if node.kind == "object":
            for member in node.members:
                locator = f"{path}/{self._escape(member.key)}"
                value_node = member.value
                if member.key in _LITERAL_KEYS and value_node.kind == "string":
                    value = value_node.value
                    assert isinstance(value, str)
                    # ``book.*`` is a runtime locale reference, never prose.
                    if not self._is_runtime_reference(value):
                        if include_nonprose_literals or self._is_literal_prose(value):
                            out.append((locator, value_node, value))
                    continue
                self._collect_node(
                    value_node,
                    locator,
                    out,
                    include_nonprose_literals=include_nonprose_literals,
                )
        elif node.kind == "array":
            for index, item in enumerate(node.items):
                self._collect_node(
                    item,
                    f"{path}/{index}",
                    out,
                    include_nonprose_literals=include_nonprose_literals,
                )

    def _parse_value(self, text: str, index: int):
        index = self._skip_ws(text, index)
        if index < len(text) and text[index] == '"':
            end = self._scan_string_end(text, index)
            token = text[index:end]
            try:
                value = self._decode_lenient_string(token)
            except json.JSONDecodeError as exc:
                raise ValidationError("Invalid Modonomicon JSON string") from exc
            return _Node("string", index, end, value), end
        return super()._parse_value(text, index)

    @staticmethod
    def _scan_string_end(text: str, start: int) -> int:
        index = start + 1
        escaped = False
        while index < len(text):
            char = text[index]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                return index + 1
            # Gson's lenient reader accepts raw control whitespace in strings;
            # real Pagan's Bless books rely on raw newlines/tabs. We accept
            # those lexically but never generalize invalid structural tokens.
            index += 1
        raise ValidationError("Unterminated Modonomicon JSON string")

    @staticmethod
    def _decode_lenient_string(token: str) -> str:
        body = token[1:-1]
        out: list[str] = []
        i = 0
        while i < len(body):
            char = body[i]
            if char == "\\" and i + 1 < len(body):
                nxt = body[i + 1]
                if nxt == "\n":
                    out.append("\\\\")
                    out.append("\\n")
                    i += 2
                    continue
                if nxt == "\r":
                    if i + 2 < len(body) and body[i + 2] == "\n":
                        out.append("\\\\")
                        out.append("\\r\\n")
                        i += 3
                        continue
                    out.append("\\\\")
                    out.append("\\r")
                    i += 2
                    continue
                out.append(char)
                out.append(nxt)
                i += 2
                continue
            if char == "\n":
                out.append("\\n")
            elif char == "\r":
                out.append("\\r")
            elif char == "\t":
                out.append("\\t")
            elif ord(char) < 0x20:
                out.append(f"\\u{ord(char):04x}")
            else:
                out.append(char)
            i += 1
        return json.loads('"' + "".join(out) + '"')

    @staticmethod
    def _encode_like_source(value: str, original_token: str) -> str:
        encoded = json.dumps(value, ensure_ascii=False)
        if "\\\r\n" in original_token:
            encoded = encoded.replace("\\\\\\r\\n", "\\\r\n")
        if "\\\n" in original_token:
            encoded = encoded.replace("\\\\\\n", "\\\n")
        remainder = original_token.replace("\\\r\n", "").replace("\\\n", "")
        if "\r\n" in remainder:
            encoded = encoded.replace("\\r\\n", "\r\n")
        elif "\n" in remainder:
            encoded = encoded.replace("\\n", "\n")
        if "\t" in original_token:
            encoded = encoded.replace("\\t", "\t")
        return encoded

    def _protect_modonomicon(
        self, text: str
    ) -> tuple[str, tuple[ProtectedFragment, ...]]:
        # Start with the established Patchouli/runtime protection (formatting,
        # literal placeholders, line breaks, etc.), then add Modonomicon
        # markdown links/colour tags/backslashes without hiding link labels.
        masked, protected = super()._protect(text)
        spans: list[tuple[int, int]] = []
        spans.extend((m.start(), m.end()) for m in _COLOR_TAG_RE.finditer(masked))
        for match in _LINK_RE.finditer(masked):
            # [human label](entry://immutable/target)
            spans.append((match.start(), match.start(1)))
            spans.append((match.end(1), match.end()))
        spans.extend((m.start(), m.end()) for m in _MARKDOWN_DELIM_RE.finditer(masked))
        spans.extend((m.start(), m.end()) for m in _BACKSLASH_RE.finditer(masked))
        spans.extend((m.start(), m.end()) for m in _RAW_TAB_RE.finditer(masked))
        for match in _PLACEHOLDER_RE.finditer(masked):
            # Existing placeholders were allocated by the base layer and must
            # not be swallowed by a second protected fragment.
            spans = [span for span in spans if not (span[0] < match.end() and span[1] > match.start())]

        merged = self._merge_spans(spans)
        if not merged:
            return masked, protected
        ids = [int(m.group(1)) for m in _PLACEHOLDER_RE.finditer(masked)]
        next_id = max(ids) + 1 if ids else 0
        out: list[str] = []
        extra: list[ProtectedFragment] = []
        cursor = 0
        for offset, (start, end) in enumerate(merged):
            out.append(masked[cursor:start])
            placeholder = f"[#{next_id + offset}#]"
            out.append(placeholder)
            extra.append(ProtectedFragment(placeholder, masked[start:end]))
            cursor = end
        out.append(masked[cursor:])
        remasked = "".join(out)
        combined = protected + tuple(extra)
        occurrence = {
            match.group(0): index
            for index, match in enumerate(_PLACEHOLDER_RE.finditer(remasked))
        }
        combined = tuple(
            sorted(combined, key=lambda fragment: occurrence.get(fragment.placeholder, 10**9))
        )
        return remasked, combined

    @staticmethod
    def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
        merged: list[list[int]] = []
        for start, end in sorted(spans):
            if start >= end:
                continue
            if not merged or start >= merged[-1][1]:
                merged.append([start, end])
            elif end > merged[-1][1]:
                merged[-1][1] = end
        return [(start, end) for start, end in merged]

    @staticmethod
    def _validate_restored(unit_id: str, original: str, restored: str) -> None:
        if restored.count("\n") != original.count("\n") or restored.count("\r") != original.count("\r"):
            raise ValidationError(f"Modonomicon unit {unit_id} changed line-break structure")
        if restored.count("\\") != original.count("\\"):
            raise ValidationError(f"Modonomicon unit {unit_id} changed literal backslash structure")
        if restored.count("\t") != original.count("\t"):
            raise ValidationError(f"Modonomicon unit {unit_id} changed tab structure")

    @staticmethod
    def _is_runtime_reference(value: str) -> bool:
        stripped = value.strip()
        return bool(
            not stripped
            or _TRANSLATION_KEY_RE.fullmatch(stripped)
            or _RESOURCE_ID_RE.fullmatch(stripped)
        )

    @classmethod
    def _is_literal_prose(cls, value: str) -> bool:
        return not cls._is_runtime_reference(value) and bool(_WORD_RE.search(value))


class ModonomiconLangJsonAdapter(_LocaleAdapter):
    """Minecraft locale adapter with Modonomicon markdown protection."""

    name = "modonomicon-lang-json"

    def _protect(self, text: str) -> tuple[str, tuple[ProtectedFragment, ...]]:
        masked, protected = super()._protect(text)
        spans: list[tuple[int, int]] = []
        spans.extend((m.start(), m.end()) for m in _COLOR_TAG_RE.finditer(masked))
        for match in _LINK_RE.finditer(masked):
            spans.append((match.start(), match.start(1)))
            spans.append((match.end(1), match.end()))
        spans.extend((m.start(), m.end()) for m in _MARKDOWN_DELIM_RE.finditer(masked))
        spans.extend((m.start(), m.end()) for m in _BACKSLASH_RE.finditer(masked))
        spans.extend((m.start(), m.end()) for m in _RAW_TAB_RE.finditer(masked))

        # Do not let a second protection layer consume placeholders already
        # allocated by locale/runtime protection.
        placeholders = [(m.start(), m.end()) for m in _PLACEHOLDER_RE.finditer(masked)]
        spans = [
            span
            for span in spans
            if not any(span[0] < end and span[1] > start for start, end in placeholders)
        ]
        merged = self._merge_spans(spans)
        if not merged:
            return masked, protected

        ids = [int(m.group(1)) for m in _PLACEHOLDER_RE.finditer(masked)]
        next_id = max(ids) + 1 if ids else 0
        out: list[str] = []
        extra: list[ProtectedFragment] = []
        cursor = 0
        for offset, (start, end) in enumerate(merged):
            out.append(masked[cursor:start])
            placeholder = f"[#{next_id + offset}#]"
            out.append(placeholder)
            extra.append(ProtectedFragment(placeholder, masked[start:end]))
            cursor = end
        out.append(masked[cursor:])
        remasked = "".join(out)
        combined = protected + tuple(extra)
        occurrence = {
            match.group(0): index
            for index, match in enumerate(_PLACEHOLDER_RE.finditer(remasked))
        }
        combined = tuple(
            sorted(combined, key=lambda fragment: occurrence.get(fragment.placeholder, 10**9))
        )
        return remasked, combined


class ModonomiconLocaleMergePlanner:
    """Marker class kept for the integration API; uses the normal safe planner."""

    # Imported lazily to avoid a locale_safe -> modonomicon cycle at module load.
    def __new__(cls, *args, **kwargs):
        from .locale_safe import LocaleMergePlanner

        kwargs.setdefault("adapter", ModonomiconLangJsonAdapter())
        return LocaleMergePlanner(*args, **kwargs)
