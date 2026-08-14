from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Mapping


class ValidationError(ValueError):
    """Raised when translated content violates a format invariant."""


@dataclass(frozen=True)
class ProtectedFragment:
    placeholder: str
    value: str


@dataclass(frozen=True)
class TranslationUnit:
    """One replaceable semantic span inside an immutable source document.

    ``text`` is what the translator receives. Technical fragments may be
    represented by placeholders. ``start``/``end`` address the original source
    text, so serialization never has to reformat the rest of the document.
    """

    id: str
    text: str
    start: int
    end: int
    kind: str
    context: str = ""
    protected: tuple[ProtectedFragment, ...] = ()

    @property
    def source_span_length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class TranslationPlan:
    path: str
    source_text: str
    units: tuple[TranslationUnit, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    @cached_property
    def unit_map(self) -> dict[str, TranslationUnit]:
        return {unit.id: unit for unit in self.units}

    def by_id(self) -> dict[str, TranslationUnit]:
        # Keep the historical public method while avoiding rebuilding the map
        # for every per-unit candidate validation in large locale files.
        return self.unit_map


def validate_translation_candidate(
    adapter,
    plan: TranslationPlan,
    unit_id: str,
    candidate: str,
) -> tuple[bool, str | None]:
    """Validate one candidate before cache/write through the owning adapter.

    Adapters may expose an O(1) ``validate_candidate`` implementation when all
    relevant invariants are local to one TranslationUnit. Otherwise we safely
    fall back to applying that single candidate against the immutable source
    plan and running the adapter's whole-file validator.
    """

    if unit_id not in plan.by_id():
        return False, f"unknown translation unit {unit_id}"
    try:
        local_validator = getattr(adapter, "validate_candidate", None)
        if callable(local_validator):
            local_validator(plan, unit_id, candidate)
        else:
            adapter.apply(plan, {unit_id: candidate})
    except (ValidationError, ValueError) as exc:
        return False, str(exc)
    return True, None
