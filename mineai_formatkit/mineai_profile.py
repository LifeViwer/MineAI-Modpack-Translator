"""MineAI integration profile built from generic FormatKit adapters.

The profile contains only runtime invariants proven by MineAI's real FTB
Evolution acceptance corpus but not yet suitable for widening every FormatKit
adapter by default.  Keeping them here lets the host vendor one reviewed SDK
implementation instead of maintaining parser forks in the application tree.
"""

from __future__ import annotations

from .core import ProtectedFragment, TranslationPlan, TranslationUnit, ValidationError
from .modonomicon import (
    ModonomiconAwareLocaleMergePlanner,
    ModonomiconAwareMinecraftLangJsonAdapter,
    ModonomiconBookJsonAdapter as _ModonomiconBookJsonAdapter,
)
from .minecraft_lang import _PLACEHOLDER_RE
from .patchouli_base import PatchouliFingerprint
from .patchouli_safe import PatchouliBookJsonAdapter as _PatchouliBookJsonAdapter


class MineAiMinecraftLangJsonAdapter(ModonomiconAwareMinecraftLangJsonAdapter):
    """Current public locale stack plus exact protected-marker ordering.

    MineAI's weak-LLM acceptance runs proved that a candidate can preserve the
    same marker multiset while reordering runtime syntax.  The integration
    profile therefore requires the placeholder sequence to match the canonical
    source order and normalizes layered protection metadata to that same order.
    """

    name = "minecraft-lang-json"

    def _protect(self, text: str) -> tuple[str, tuple[ProtectedFragment, ...]]:
        masked, protected = super()._protect(text)
        occurrence = {
            match.group(0): index
            for index, match in enumerate(_PLACEHOLDER_RE.finditer(masked))
        }
        ordered = tuple(
            sorted(
                protected,
                key=lambda fragment: occurrence.get(fragment.placeholder, 10**9),
            )
        )
        return masked, ordered

    @staticmethod
    def _restore_protected(unit: TranslationUnit, translated: str) -> str:
        expected = [fragment.placeholder for fragment in unit.protected]
        actual = [match.group(0) for match in _PLACEHOLDER_RE.finditer(translated)]
        if actual != expected:
            raise ValidationError(
                f"Unit {unit.id} changed protected placeholder order: "
                f"expected {expected}, got {actual}"
            )
        restored = translated
        for fragment in unit.protected:
            restored = restored.replace(fragment.placeholder, fragment.value)
        return restored

    def validate_candidate(
        self, plan: TranslationPlan, unit_id: str, candidate: str
    ) -> None:
        if unit_id not in plan.by_id():
            raise ValidationError(f"Unknown translation unit id: {unit_id}")
        self.apply(plan, {unit_id: candidate})


class MineAiLocaleMergePlanner(ModonomiconAwareLocaleMergePlanner):
    """Locale merge planner using the MineAI exact-order adapter."""

    def __init__(self, adapter: MineAiMinecraftLangJsonAdapter | None = None) -> None:
        super().__init__(adapter or MineAiMinecraftLangJsonAdapter())


class MineAiModonomiconBookJsonAdapter(_ModonomiconBookJsonAdapter):
    """Official Modonomicon adapter with the same candidate-validation hook."""

    def validate_candidate(
        self, plan: TranslationPlan, unit_id: str, candidate: str
    ) -> None:
        if unit_id not in plan.by_id():
            raise ValidationError(f"Unknown translation unit id: {unit_id}")
        self.apply(plan, {unit_id: candidate})


class MineAiPatchouliBookJsonAdapter(_PatchouliBookJsonAdapter):
    """Current semantic-anchor Patchouli adapter plus corpus-proven guards.

    The current semantic-anchor implementation owns balanced style/link payloads
    correctly.  MineAI's earlier runtime acceptance also proved two additional
    invariants worth retaining during SDK synchronization:

    * structural fingerprints are based on schema locations, not on whether a
      translated value still passes an English/Russian prose heuristic;
    * translators may not add or remove literal backslashes inside visible book
      fields (the real CuBee corruption regression).
    """

    name = "patchouli-book-json"

    def fingerprint(self, text: str) -> PatchouliFingerprint:
        root = self._parse(text)
        targets = []
        self._collect(root, "", targets)
        selected = [(locator, node) for locator, node, _value in targets]
        out: list[str] = []
        cursor = 0
        for locator, node in sorted(selected, key=lambda item: item[1].start):
            out.append(text[cursor:node.start])
            out.append('"<mineai-patchouli-text>"')
            cursor = node.end
        out.append(text[cursor:])
        return PatchouliFingerprint(
            locators=tuple(locator for locator, _node in selected),
            skeleton="".join(out),
        )

    def validate(self, source_text: str, output_text: str) -> None:
        if self.fingerprint(source_text) != self.fingerprint(output_text):
            raise ValidationError("Patchouli JSON structure changed during reconstruction")

        before = self._values_by_locator(source_text)
        after = self._values_by_locator(output_text)
        if before.keys() != after.keys():
            raise ValidationError("Patchouli translatable field locations changed")
        for locator, original in before.items():
            translated = after[locator]
            if translated.count("\\") != original.count("\\"):
                raise ValidationError(
                    f"Patchouli field {locator} changed literal backslash structure"
                )

    def _values_by_locator(self, text: str) -> dict[str, str]:
        root = self._parse(text)
        targets = []
        self._collect(root, "", targets)
        return {locator: value for locator, _node, value in targets}


__all__ = [
    "MineAiLocaleMergePlanner",
    "MineAiModonomiconBookJsonAdapter",
    "MineAiMinecraftLangJsonAdapter",
    "MineAiPatchouliBookJsonAdapter",
]
