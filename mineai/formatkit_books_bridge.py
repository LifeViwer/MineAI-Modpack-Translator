from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from mineai.text_processing import already_translated, is_technical_term, looks_like_source_language
from mineai_formatkit import (
    FORMATKIT_PILOT_HARDENING,
    FORMATKIT_SOURCE_SHA,
    ImmersiveEngineeringManualAdapter,
    ModonomiconBookJsonAdapter,
    PatchouliBookJsonAdapter,
    TranslationPlan,
    TranslationUnit,
    ValidationError,
)


@dataclass(frozen=True)
class FormatKitBookWork:
    adapter_name: str
    adapter: object
    source_plan: TranslationPlan
    units_by_id: Mapping[str, TranslationUnit]
    pending: Mapping[str, str]
    preserved: Mapping[str, str]
    passthrough: Mapping[str, str]
    total_translatable: int
    target_path: str
    target_parse_error: str | None
    emit_structural_copy: bool = False
    target_reuse_disabled: bool = False


# Only formats already exercised by the MineAI pilots are enabled here. The
# current SDK registry supports more formats, but v3.4 is a synchronization and
# cleanup step, not a feature-expansion release.
_BOOK_ADAPTERS = (
    ModonomiconBookJsonAdapter(),
    PatchouliBookJsonAdapter(),
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


def _is_modonomicon_data(adapter) -> bool:
    return getattr(adapter, "name", "") == "modonomicon-book-json"


def target_path_for_book(path: str, target_code: str) -> str | None:
    """Return MineAI's output path for an SDK-owned book source.

    Modonomicon book JSON is locale-neutral datapack data. The SDK deliberately
    refuses to invent a locale target path for it; MineAI, as the output-policy
    owner, overlays the translated document at the same ``data/...`` path.
    """

    adapter = book_adapter_for(path)
    if adapter is None:
        return None
    normalized = path.replace("\\", "/")
    if _is_modonomicon_data(adapter):
        return normalized
    return adapter.target_path(normalized, target_code)


def _raw_source_value(plan: TranslationPlan, unit: TranslationUnit) -> str:
    # Prefer SDK-owned semantic payload metadata where available. This keeps
    # host filtering independent from parser internals while correctly handling
    # semantic child units whose source offsets intentionally cover an outer
    # field/line.
    for key in ("originals", "semantic_payloads", "original_values"):
        values = plan.metadata.get(key)
        if isinstance(values, dict):
            value = values.get(unit.id)
            if isinstance(value, str):
                return value
    return unit.text


def _protected_values(unit: TranslationUnit) -> tuple[str, ...]:
    return tuple(fragment.value for fragment in unit.protected)


def _has_semantic_anchors(plan: TranslationPlan) -> bool:
    anchors = plan.metadata.get("semantic_anchors")
    return isinstance(anchors, dict) and bool(anchors)


def _display_adapter_name(adapter, plan: TranslationPlan) -> str:
    # The current SDK intentionally folds Patchouli templates into the normal
    # Patchouli adapter and exposes zero translation units. Keep the historical
    # MineAI label only for UI/logging and structural-copy policy; there is no
    # second template parser anymore.
    if plan.metadata.get("patchouli_template_immutable") is True:
        return "patchouli-template-json"
    return getattr(adapter, "name", type(adapter).__name__)


def _validate_candidate(
    adapter,
    plan: TranslationPlan,
    units_by_id: Mapping[str, TranslationUnit],
    unit_id: str,
    candidate: str,
) -> tuple[bool, str | None]:
    """Validate one candidate through the unmodified SDK adapter.

    v3.2's per-unit fallback remains a MineAI transport policy. The former
    vendored SDK helper has been removed: reconstructing one candidate against
    the canonical plan invokes the adapter's own local and whole-document
    invariants and is therefore the authoritative fail-closed check.
    """

    if unit_id not in units_by_id:
        return False, f"unknown translation unit {unit_id}"
    try:
        adapter.apply(plan, {unit_id: candidate})
    except (ValidationError, ValueError) as exc:
        return False, str(exc)
    return True, None


def _existing_target_candidates(
    adapter,
    source_plan: TranslationPlan,
    target_text: str,
):
    """Yield public-SDK target candidates in source unit order.

    No private ``_parse``/``_protect``/JSON-pointer access is used. Re-planning
    the target through the same public adapter lets us compare unit topology and
    exact protected runtime fragments before considering reuse.
    """

    target_plan = adapter.prepare(source_plan.path, target_text)
    if len(source_plan.units) != len(target_plan.units):
        raise ValidationError("existing target translation unit topology changed")

    for source_unit, target_unit in zip(source_plan.units, target_plan.units):
        if source_unit.kind != target_unit.kind:
            raise ValidationError("existing target translation unit kind changed")
        if _protected_values(source_unit) != _protected_values(target_unit):
            raise ValidationError("existing target protected runtime fragments changed")
        yield source_unit, target_unit.text


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
    units_by_id = source_plan.by_id()
    display_name = _display_adapter_name(adapter, source_plan)
    emit_structural_copy = source_plan.metadata.get("patchouli_template_immutable") is True
    target_path = target_path_for_book(normalized, target_code)
    assert target_path is not None

    eligible_ids: set[str] = set()
    for unit in source_plan.units:
        original = _raw_source_value(source_plan, unit)
        if not isinstance(original, str) or not original.strip():
            continue
        if not looks_like_source_language(original) or is_technical_term(original):
            continue
        eligible_ids.add(unit.id)

    preserved: dict[str, str] = {}
    target_parse_error: str | None = None

    # A v3.3 target can preserve every flat marker yet attach a style/link to the
    # wrong words. Once the SDK reports semantic anchors, do not mine wording
    # from that old target. Rebuild from canonical English + newly validated
    # semantic units instead. This is intentionally conservative for the first
    # SDK-sync pilot and prevents a previously accepted bad pack from reviving
    # through Append mode.
    target_reuse_disabled = _has_semantic_anchors(source_plan)

    if (
        mode != "force"
        and target_text
        and not emit_structural_copy
        and not _is_modonomicon_data(adapter)
        and not target_reuse_disabled
    ):
        try:
            for source_unit, candidate in _existing_target_candidates(
                adapter, source_plan, target_text
            ):
                if source_unit.id not in eligible_ids:
                    continue
                if candidate == source_unit.text:
                    continue
                if not already_translated(candidate, target_regex):
                    continue
                ok, reason = _validate_candidate(
                    adapter, source_plan, units_by_id, source_unit.id, candidate
                )
                if not ok:
                    raise ValidationError(reason or "existing target candidate rejected")
                preserved[source_unit.id] = candidate
        except (ValidationError, ValueError, KeyError, IndexError, TypeError) as exc:
            target_parse_error = str(exc)
            preserved.clear()

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
        adapter_name=display_name,
        adapter=adapter,
        source_plan=source_plan,
        units_by_id=units_by_id,
        pending=pending,
        preserved=preserved,
        passthrough=passthrough,
        total_translatable=len(eligible_ids),
        target_path=target_path,
        target_parse_error=target_parse_error,
        emit_structural_copy=emit_structural_copy,
        target_reuse_disabled=target_reuse_disabled,
    )


def validate_book_candidate(
    work: FormatKitBookWork,
    unit_id: str,
    candidate: str,
) -> tuple[bool, str | None]:
    ok, reason = _validate_candidate(
        work.adapter,
        work.source_plan,
        work.units_by_id,
        unit_id,
        candidate,
    )
    return ok, None if ok else f"FormatKit: {reason}"


def build_book_output(work: FormatKitBookWork, translated: Mapping[str, str]) -> str:
    values = dict(work.passthrough)
    values.update(work.preserved)
    for unit_id in work.pending:
        values[unit_id] = translated.get(unit_id, work.units_by_id[unit_id].text)
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
