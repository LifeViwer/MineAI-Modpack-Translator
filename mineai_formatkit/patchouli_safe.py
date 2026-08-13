from __future__ import annotations

from .patchouli import PatchouliBookJsonAdapter as _BasePatchouliBookJsonAdapter


class PatchouliBookJsonAdapter(_BasePatchouliBookJsonAdapter):
    """Patchouli adapter with corpus-proven literal ``link_text`` support."""

    name = "patchouli-book-json"

    def _collect(self, root, path: str, out) -> None:
        super()._collect(root, path, out)
        members = {member.key: member.value for member in root.members}
        pages = members.get("pages")
        if pages is None:
            return
        for index, page in enumerate(pages.items):
            for member in page.members:
                if member.key != "link_text" or member.value.kind != "string":
                    continue
                value = member.value.value
                assert isinstance(value, str)
                if self._is_literal_link_text(value):
                    out.append((f"/pages/{index}/{self._escape('link_text')}", member.value, value))

    @classmethod
    def _is_literal_link_text(cls, value: str) -> bool:
        return any(char.isspace() for char in value) and cls._has_prose(value)
