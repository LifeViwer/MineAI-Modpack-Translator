from __future__ import annotations

import re

from .core import ValidationError
from .patchouli_safe import PatchouliBookJsonAdapter as _PatchouliBase


_TEMPLATE_PATH_RE = re.compile(
    r"(^|/)patchouli_books/[^/]+/en_us/templates/.+\.json$",
    re.IGNORECASE,
)
_TEMPLATE_VAR_RE = re.compile(r"^#[A-Za-z0-9_.:-]+#?$")
_TRANSLATION_KEY_RE = re.compile(
    r"^(?:[a-z0-9_.-]+:)?[a-z0-9_.-]+(?:[./][a-z0-9_.-]+)+$"
)


class PatchouliTemplateJsonAdapter(_PatchouliBase):
    """Span-preserving adapter for proven Patchouli template JSON.

    Only literal player-visible component ``text`` is exposed. Processor
    substitutions such as ``#tier#``, ``#energy`` and ``#title`` and resource
    translation keys such as ``ars_nouveau.level`` remain immutable.
    """

    name = "patchouli-template-json"

    def matches(self, path: str) -> bool:
        slash = "/" + path.replace("\\", "/").lstrip("/")
        return bool(_TEMPLATE_PATH_RE.search(slash))

    def target_path(self, path: str, target_code: str) -> str:
        slash = path.replace("\\", "/")
        if not self.matches(slash):
            raise ValueError(f"Unsupported Patchouli template source path: {path}")
        marker = "/en_us/"
        index = slash.lower().find(marker)
        if index < 0:
            raise ValueError(f"Unsupported Patchouli template source path: {path}")
        return slash[:index] + f"/{target_code}/" + slash[index + len(marker):]

    def _collect(self, root, path: str, out) -> None:
        if root.kind != "object":
            raise ValidationError("Patchouli template document must be a JSON object")
        members = {member.key: member.value for member in root.members}
        components = members.get("components")
        if components is None:
            return
        if components.kind != "array":
            raise ValidationError("Patchouli template 'components' must be an array")

        for index, component in enumerate(components.items):
            if component.kind != "object":
                raise ValidationError("Patchouli template component must be an object")
            for member in component.members:
                if member.key != "text" or member.value.kind != "string":
                    continue
                value = member.value.value
                assert isinstance(value, str)
                if self._is_literal_template_text(value):
                    out.append(
                        (
                            f"/components/{index}/{self._escape('text')}",
                            member.value,
                            value,
                        )
                    )


    def _collect_fingerprint(self, root, path: str, out) -> None:
        if root.kind != "object":
            raise ValidationError("Patchouli template document must be a JSON object")
        members = {member.key: member.value for member in root.members}
        components = members.get("components")
        if components is None:
            return
        if components.kind != "array":
            raise ValidationError("Patchouli template 'components' must be an array")
        for index, component in enumerate(components.items):
            if component.kind != "object":
                raise ValidationError("Patchouli template component must be an object")
            for member in component.members:
                if member.key != "text" or member.value.kind != "string":
                    continue
                value = member.value.value
                assert isinstance(value, str)
                out.append((f"/components/{index}/{self._escape('text')}", member.value, value))

    @classmethod
    def _is_literal_template_text(cls, value: str) -> bool:
        stripped = value.strip()
        if not stripped or not cls._has_prose(stripped):
            return False
        if _TEMPLATE_VAR_RE.fullmatch(stripped):
            return False
        if _TRANSLATION_KEY_RE.fullmatch(stripped):
            return False
        # The current FTB corpus has no mixed prose+processor-variable template
        # strings. Fail closed rather than guessing how a processor substitutes.
        if "#" in stripped:
            return False
        return True
