from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from mineai.text_processing import is_technical_term, looks_like_source_language
from mineai_formatkit import (
    FORMATKIT_SOURCE_SHA,
    CollapsibleGroupsConfigLangJsonAdapter,
    JaopcaConfigLangJsonAdapter,
    LocaleMergePlan,
    LocaleMergePlanner,
    MinecraftLangJsonAdapter,
    ModonomiconLangJsonAdapter,
    validate_translation_candidate,
)


@dataclass(frozen=True)
class FormatKitLocaleWork:
    """One MineAI locale job planned by the vendored FormatKit snapshot."""

    adapter_name: str
    planner: LocaleMergePlanner
    plan: LocaleMergePlan
    pending: Mapping[str, str]
    passthrough: Mapping[str, str]
    total_translatable: int
    target_path: str
    target_parse_error: str | None


_MODONOMICON_LOCALE_ADAPTER = ModonomiconLangJsonAdapter()

_LOCALE_ADAPTERS = (
    CollapsibleGroupsConfigLangJsonAdapter(),
    JaopcaConfigLangJsonAdapter(),
    MinecraftLangJsonAdapter(),
)


def locale_adapter_for(path: str):
    """Return the first pilot locale adapter that owns ``path``."""

    normalized = path.replace("\\", "/")
    for adapter in _LOCALE_ADAPTERS:
        if adapter.matches(normalized):
            return adapter
    return None


def modonomicon_locale_adapter():
    return _MODONOMICON_LOCALE_ADAPTER


def is_formatkit_locale_path(path: str) -> bool:
    return locale_adapter_for(path) is not None


def target_path_for_locale(path: str, target_code: str) -> str | None:
    adapter = locale_adapter_for(path)
    if adapter is None:
        return None
    return adapter.target_path(path.replace("\\", "/"), target_code)


def plan_locale_work(
    path: str,
    source_text: str,
    target_code: str,
    target_text: str | None,
    mode: str,
    *,
    adapter=None,
    key_filter: Callable[[str], bool] | None = None,
) -> FormatKitLocaleWork | None:
    """Plan one locale while preserving MineAI's product-level string filter.

    FormatKit owns structure, protected fragments and existing-target safety.
    MineAI still decides which visible strings are suitable for translation.

    MineAI's historical ``skip`` mode still treats source-identical target text
    as pending before applying its 90% file threshold. FormatKit's standalone
    ``skip`` mode intentionally differs, so the bridge plans MineAI ``skip`` as
    ``append`` and lets the existing processor/estimator apply that threshold.
    """

    adapter = adapter or locale_adapter_for(path)
    if adapter is None:
        return None

    planner = LocaleMergePlanner(adapter=adapter)
    planner_mode = "append" if mode == "skip" else mode
    merge_plan = planner.plan(
        path.replace("\\", "/"),
        source_text,
        target_code,
        target_text=target_text,
        mode=planner_mode,
    )

    units = merge_plan.source_plan.by_id()
    originals = merge_plan.source_plan.metadata.get("original_values", {})
    eligible_ids: set[str] = set()
    for unit_id, unit in units.items():
        original = originals.get(unit_id, unit.text) if isinstance(originals, dict) else unit.text
        if not isinstance(original, str) or not original.strip():
            continue
        if not looks_like_source_language(original) or is_technical_term(original):
            continue
        if key_filter is not None and not key_filter(unit.context):
            continue
        eligible_ids.add(unit_id)

    pending_ids = set(merge_plan.pending_ids)
    pending = {
        unit_id: units[unit_id].text
        for unit_id in merge_plan.pending_ids
        if unit_id in eligible_ids
    }
    passthrough = {
        unit_id: units[unit_id].text
        for unit_id in merge_plan.pending_ids
        if unit_id not in eligible_ids
    }

    # ``pending_ids`` is intentionally referenced here as an invariant guard:
    # every pending FormatKit unit must be either translated by MineAI or fed
    # back unchanged so reconstruction can never receive an incomplete plan.
    if set(pending) | set(passthrough) != pending_ids:
        raise ValueError("FormatKit locale bridge failed to classify pending units")

    return FormatKitLocaleWork(
        adapter_name=adapter.name,
        planner=planner,
        plan=merge_plan,
        pending=pending,
        passthrough=passthrough,
        total_translatable=len(eligible_ids),
        target_path=merge_plan.target_path,
        target_parse_error=merge_plan.target_parse_error,
    )


def validate_locale_candidate(
    work: FormatKitLocaleWork,
    unit_id: str,
    candidate: str,
) -> tuple[bool, str | None]:
    ok, reason = validate_translation_candidate(
        work.planner.adapter, work.plan.source_plan, unit_id, candidate
    )
    return ok, None if ok else f"FormatKit: {reason}"


def build_locale_output(
    work: FormatKitLocaleWork,
    translated: Mapping[str, str],
) -> str:
    """Build a complete validated locale, retaining source for rejected items."""

    units = work.plan.source_plan.by_id()
    values = dict(work.passthrough)
    for unit_id in work.pending:
        values[unit_id] = translated.get(unit_id, units[unit_id].text)
    return work.planner.build(work.plan, values)


__all__ = [
    "FORMATKIT_SOURCE_SHA",
    "FormatKitLocaleWork",
    "build_locale_output",
    "is_formatkit_locale_path",
    "locale_adapter_for",
    "modonomicon_locale_adapter",
    "plan_locale_work",
    "validate_locale_candidate",
    "target_path_for_locale",
]
