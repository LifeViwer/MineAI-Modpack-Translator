from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Mapping

from mineai.text_processing import already_translated, is_technical_term, looks_like_source_language
from mineai_formatkit import (
    FORMATKIT_PILOT_HARDENING,
    FORMATKIT_SOURCE_SHA,
    ImmersiveEngineeringManualAdapter,
    ModonomiconBookJsonAdapter,
    PatchouliBookJsonAdapter,
    PatchouliTemplateJsonAdapter,
    TranslationPlan,
    ValidationError,
    validate_translation_candidate,
)


@dataclass(frozen=True)
class FormatKitBookWork:
    adapter_name: str
    adapter: object
    source_plan: TranslationPlan
    pending: Mapping[str, str]
    preserved: Mapping[str, str]
    passthrough: Mapping[str, str]
    total_translatable: int
    target_path: str
    target_parse_error: str | None


_BOOK_ADAPTERS = (
    ModonomiconBookJsonAdapter(),
    PatchouliBookJsonAdapter(),
    PatchouliTemplateJsonAdapter(),
    ImmersiveEngineeringManualAdapter(),
)


def book_adapter_for(path: str):
    normalized = path.replace("\\", "/")
    for adapter in _BOOK_ADAPTERS:
        if adapter.matches(normalized):
            return adapter
    return None


def is_formatkit_book_path(path: str) -> bool:
    return book_adapter_for(path) is not None


def target_path_for_book(path: str, target_code: str) -> str | None:
    adapter = book_adapter_for(path)
    if adapter is None:
        return None
    return adapter.target_path(path.replace("\\", "/"), target_code)


def _raw_source_value(plan: TranslationPlan, unit) -> str:
    originals = plan.metadata.get("originals")
    if isinstance(originals, dict):
        value = originals.get(unit.id)
        if isinstance(value, str):
            return value
    return plan.source_text[unit.start:unit.end]


def _protected_values(unit) -> tuple[str, ...]:
    return tuple(fragment.value for fragment in unit.protected)


def _json_pointer_parts(unit_id: str) -> list[str]:
    if not unit_id.startswith("json:/"):
        raise ValidationError(f"Unexpected Patchouli unit id: {unit_id}")
    pointer = unit_id[len("json:"):]
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]


def _json_pointer_get(root, parts: list[str]):
    current = root
    for part in parts:
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise ValidationError("Patchouli target locator changed type")
    return current


def _json_pointer_set(root, parts: list[str], value) -> None:
    current = root
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    last = parts[-1]
    if isinstance(current, list):
        current[int(last)] = value
    else:
        current[last] = value


def _patchouli_target_candidates(adapter, source_plan: TranslationPlan, target_text: str):
    # Parse through the strict adapter first (duplicates/trailing data fail closed),
    # then compare JSON semantics with only proven translatable fields blanked.
    adapter._parse(target_text)
    source_obj = json.loads(source_plan.source_text)
    target_obj = json.loads(target_text)
    source_shape = copy.deepcopy(source_obj)
    target_shape = copy.deepcopy(target_obj)
    target_values: dict[str, tuple[str, tuple[str, ...]]] = {}
    for source_unit in source_plan.units:
        parts = _json_pointer_parts(source_unit.id)
        target_raw = _json_pointer_get(target_obj, parts)
        if not isinstance(target_raw, str):
            raise ValidationError("Patchouli target translatable field changed type")
        masked, protected = adapter._protect(target_raw)
        target_values[source_unit.id] = (
            masked,
            tuple(fragment.value for fragment in protected),
        )
        _json_pointer_set(source_shape, parts, "<mineai-patchouli-text>")
        _json_pointer_set(target_shape, parts, "<mineai-patchouli-text>")
    if source_shape != target_shape:
        raise ValidationError("Patchouli immutable JSON structure changed")
    for source_unit in source_plan.units:
        candidate = target_values[source_unit.id]
        yield source_unit, candidate[0], candidate[1]


def _ie_target_candidates(adapter, source_plan: TranslationPlan, target_text: str):
    adapter.validate(source_plan.source_text, target_text)
    target_plan = adapter.prepare(source_plan.path, target_text)
    if len(source_plan.units) != len(target_plan.units):
        raise ValidationError("IE manual translatable unit count changed")
    for source_unit, target_unit in zip(source_plan.units, target_plan.units):
        if source_unit.kind != target_unit.kind:
            raise ValidationError("IE manual translatable unit kind changed")
        yield source_unit, target_unit.text, _protected_values(target_unit)


def plan_book_work(
    path: str,
    source_text: str,
    target_code: str,
    target_regex: str,
    target_text: str | None,
    mode: str,
) -> FormatKitBookWork | None:
    adapter = book_adapter_for(path)
    if adapter is None:
        return None

    normalized = path.replace("\\", "/")
    source_plan = adapter.prepare(normalized, source_text)
    target_path = adapter.target_path(normalized, target_code)

    eligible_ids: set[str] = set()
    for unit in source_plan.units:
        original = _raw_source_value(source_plan, unit)
        if not original.strip():
            continue
        if not looks_like_source_language(original) or is_technical_term(original):
            continue
        eligible_ids.add(unit.id)

    preserved: dict[str, str] = {}
    target_parse_error: str | None = None
    if mode != "force" and target_text:
        try:
            candidates = (
                _patchouli_target_candidates(adapter, source_plan, target_text)
                if adapter.name.startswith("patchouli-")
                else _ie_target_candidates(adapter, source_plan, target_text)
            )
            for source_unit, candidate, target_protected in candidates:
                if source_unit.id not in eligible_ids:
                    continue
                if _protected_values(source_unit) != target_protected:
                    continue
                if candidate == source_unit.text:
                    continue
                if not already_translated(candidate, target_regex):
                    continue
                preserved[source_unit.id] = candidate
        except (ValidationError, ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            target_parse_error = str(exc)

    pending = {
        unit.id: unit.text
        for unit in source_plan.units
        if unit.id in eligible_ids and unit.id not in preserved
    }
    passthrough = {
        unit.id: unit.text
        for unit in source_plan.units
        if unit.id not in eligible_ids
    }

    return FormatKitBookWork(
        adapter_name=adapter.name,
        adapter=adapter,
        source_plan=source_plan,
        pending=pending,
        preserved=preserved,
        passthrough=passthrough,
        total_translatable=len(eligible_ids),
        target_path=target_path,
        target_parse_error=target_parse_error,
    )



def validate_book_candidate(
    work: FormatKitBookWork,
    unit_id: str,
    candidate: str,
) -> tuple[bool, str | None]:
    """Validate one translated unit before TranslationService caches it.

    Applying a single unit against the immutable source plan exercises the
    adapter's exact marker, newline and technical-token invariants without
    risking the rest of the file. A rejected candidate can therefore fall back
    independently while all other safe units are still reconstructed.
    """
    ok, reason = validate_translation_candidate(
        work.adapter, work.source_plan, unit_id, candidate
    )
    return ok, None if ok else f"FormatKit: {reason}"

def build_book_output(work: FormatKitBookWork, translated: Mapping[str, str]) -> str:
    values = dict(work.passthrough)
    values.update(work.preserved)
    units = work.source_plan.by_id()
    for unit_id in work.pending:
        values[unit_id] = translated.get(unit_id, units[unit_id].text)
    return work.adapter.apply(work.source_plan, values)


__all__ = [
    "FORMATKIT_PILOT_HARDENING",
    "FORMATKIT_SOURCE_SHA",
    "FormatKitBookWork",
    "book_adapter_for",
    "build_book_output",
    "is_formatkit_book_path",
    "plan_book_work",
    "target_path_for_book",
    "validate_book_candidate",
]
