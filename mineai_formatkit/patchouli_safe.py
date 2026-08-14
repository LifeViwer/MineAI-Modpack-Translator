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


    def _collect_fingerprint(self, root, path: str, out) -> None:
        # Fingerprints include every string-valued link_text location so a
        # translation changing whitespace/prose classification cannot alter
        # the structural field set. Translation-key link_text values remain
        # immutable because prepare() still exposes only proven literals.
        super()._collect_fingerprint(root, path, out)
        members = {member.key: member.value for member in root.members}
        pages = members.get("pages")
        if pages is None:
            return
        existing = {locator for locator, _node, _value in out}
        for index, page in enumerate(pages.items):
            for member in page.members:
                if member.key != "link_text" or member.value.kind != "string":
                    continue
                locator = f"/pages/{index}/{self._escape('link_text')}"
                if locator in existing:
                    continue
                value = member.value.value
                assert isinstance(value, str)
                out.append((locator, member.value, value))
                existing.add(locator)

    @classmethod
    def _is_literal_link_text(cls, value: str) -> bool:
        return any(char.isspace() for char in value) and cls._has_prose(value)
