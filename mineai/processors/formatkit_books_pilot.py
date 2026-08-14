from __future__ import annotations

import json
import re

from mineai import formatkit_books_bridge as _books
from mineai.constants import BOOK_PATH_MARKERS, MD_PATH_MARKERS, RESEARCH_PATH_MARKERS
from mineai.json_utils import iter_translatable_strings, load_lenient_json
from mineai.processors.analyzer import ModpackAnalyzer as LegacyModpackAnalyzer
from mineai.processors.formatkit_pilot import (
    FormatKitJarProcessor,
    FormatKitStringEstimator,
)
from mineai.processors.selection import skip_threshold_reached
from mineai.text_processing import already_translated, is_technical_term, looks_like_source_language


class FormatKitBooksJarProcessor(FormatKitJarProcessor):
    """Pilot v3: locale pilot plus FormatKit-owned Patchouli and IE manuals."""

    def _process_book_json(
        self, zin, zout, item, locale_files, target_lang, mode,
        output_mode, pack_writer, mod_name, written_inplace,
    ) -> bool:
        if not _books.is_formatkit_book_path(item.filename):
            return super()._process_book_json(
                zin, zout, item, locale_files, target_lang, mode,
                output_mode, pack_writer, mod_name, written_inplace,
            )
        return self._process_formatkit_book(
            zin, zout, item, locale_files, target_lang, mode,
            output_mode, pack_writer, mod_name, written_inplace,
        )

    def _process_book_md(
        self, zin, zout, item, locale_files, target_lang, mode,
        output_mode, pack_writer, mod_name, written_inplace,
    ) -> bool:
        if not _books.is_formatkit_book_path(item.filename):
            return super()._process_book_md(
                zin, zout, item, locale_files, target_lang, mode,
                output_mode, pack_writer, mod_name, written_inplace,
            )
        return self._process_formatkit_book(
            zin, zout, item, locale_files, target_lang, mode,
            output_mode, pack_writer, mod_name, written_inplace,
        )

    def _process_formatkit_book(
        self, zin, zout, item, locale_files, target_lang, mode,
        output_mode, pack_writer, mod_name, written_inplace,
    ) -> bool:
        try:
            raw_source = zin.read(item)
            source_bom = raw_source.startswith(b"\xef\xbb\xbf")
            source_text = raw_source.decode("utf-8-sig")
            tr_path = _books.target_path_for_book(item.filename, target_lang["file"])
            assert tr_path is not None
            tr_key = tr_path.lower()
            target_text = None
            if mode != "force" and tr_key in locale_files:
                try:
                    target_text = zin.read(locale_files[tr_key]).decode("utf-8-sig")
                except (OSError, UnicodeError):
                    target_text = None
            work = _books.plan_book_work(
                item.filename,
                source_text,
                target_lang["file"],
                target_lang["regex"],
                target_text,
                mode,
            )
            assert work is not None
        except (OSError, UnicodeError, ValueError) as exc:
            self.callbacks.on_log(f"⚠ FormatKit книга пропущена {item.filename}: {exc}", "yellow")
            return False

        if work.target_parse_error:
            self.callbacks.on_log(
                "⚠ FormatKit отбросил небезопасную существующую книгу "
                f"{work.target_path}: {work.target_parse_error}",
                "yellow",
            )
        emit_structural_copy = work.adapter_name == "patchouli-template-json"
        if work.total_translatable == 0 and not emit_structural_copy:
            return False

        skip_file = mode == "skip" and work.total_translatable > 0 and skip_threshold_reached(
            work.total_translatable, len(work.pending)
        )
        translated: dict[str, str] = {}
        if work.pending and not skip_file:
            if work.adapter_name == "patchouli-book-json":
                label = "Patchouli/FormatKit"
            elif work.adapter_name == "patchouli-template-json":
                label = "Patchouli Template/FormatKit"
            else:
                label = "IE Manual/FormatKit"
            self.callbacks.on_log(
                f"⚡ Перевод {mod_name} [{label}] — {len(work.pending)} строк",
                "magenta",
            )
            translated = self.service.translate_dict(
                dict(work.pending),
                target_lang,
                self.callbacks,
                context=mod_name,
                candidate_validator=lambda unit_id, candidate: _books.validate_book_candidate(
                    work, unit_id, candidate
                ),
                preserve_source_structure=True,
            )

        if not self.state.should_run():
            return False
        try:
            output_text = _books.build_book_output(work, translated)
        except ValueError as exc:
            self.callbacks.on_log(
                f"❌ FormatKit отклонил реконструкцию книги {item.filename}: {exc}",
                "red",
            )
            return False

        payload = output_text.encode("utf-8")
        if source_bom:
            payload = b"\xef\xbb\xbf" + payload
        if output_mode == "resourcepack" and pack_writer:
            pack_writer.write(work.target_path, payload)
            return True
        if zout:
            zout.writestr(work.target_path, payload)
            written_inplace.add(work.target_path)
            return True
        return False


class FormatKitBooksStringEstimator(FormatKitStringEstimator):
    def _count_book_json(self, archive, item, locale, target_lang, mode) -> int:
        if not _books.is_formatkit_book_path(item.filename):
            return super()._count_book_json(archive, item, locale, target_lang, mode)
        return self._count_formatkit_book(archive, item, locale, target_lang, mode)

    def _count_book_md(self, archive, item, locale, target_lang, mode, smart_glue) -> int:
        if not _books.is_formatkit_book_path(item.filename):
            return super()._count_book_md(archive, item, locale, target_lang, mode, smart_glue)
        return self._count_formatkit_book(archive, item, locale, target_lang, mode)

    def _count_formatkit_book(self, archive, item, locale, target_lang, mode) -> int:
        try:
            source_text = archive.read(item).decode("utf-8-sig")
            tr_path = _books.target_path_for_book(item.filename, target_lang["file"])
            assert tr_path is not None
            target_text = None
            if mode != "force" and tr_path.lower() in locale:
                try:
                    target_text = archive.read(locale[tr_path.lower()]).decode("utf-8-sig")
                except (OSError, UnicodeError):
                    target_text = None
            work = _books.plan_book_work(
                item.filename, source_text, target_lang["file"], target_lang["regex"], target_text, mode
            )
            assert work is not None
        except (OSError, UnicodeError, ValueError):
            return 0
        if mode == "skip" and skip_threshold_reached(work.total_translatable, len(work.pending)):
            return 0
        return len(work.pending)


class FormatKitModpackAnalyzer(LegacyModpackAnalyzer):
    """Analyzer counterpart using the same v3 book plan as processor/estimator."""

    def _analyze_books(self, zin, locale, target_file, target_regex, mod_name, on_row):
        b_en = b_tr = m_en = m_tr = 0
        target_code = target_file[:-5]
        for item in zin.infolist():
            fl = item.filename.lower()
            is_jb = (
                fl.endswith(".json")
                and "/en_us/" in fl
                and (
                    any(x in fl for x in BOOK_PATH_MARKERS)
                    or any(x in fl for x in RESEARCH_PATH_MARKERS)
                )
            )
            is_mb = (
                (fl.endswith(".md") or fl.endswith(".txt"))
                and "/en_us/" in fl
                and any(x in fl for x in MD_PATH_MARKERS)
            )
            if (is_jb or is_mb) and _books.is_formatkit_book_path(item.filename):
                try:
                    source_text = zin.read(item).decode("utf-8-sig")
                    target_path = _books.target_path_for_book(item.filename, target_code)
                    assert target_path is not None
                    target_text = None
                    if target_path.lower() in locale:
                        target_text = zin.read(locale[target_path.lower()]).decode("utf-8-sig")
                    work = _books.plan_book_work(
                        item.filename, source_text, target_code, target_regex, target_text, "append"
                    )
                    assert work is not None
                    translated = work.total_translatable - len(work.pending)
                    if work.adapter_name.startswith("patchouli-"):
                        b_en += work.total_translatable
                        b_tr += translated
                    else:
                        m_en += work.total_translatable
                        m_tr += translated
                    continue
                except (UnicodeError, OSError, ValueError):
                    continue

            if is_jb:
                try:
                    en = load_lenient_json(zin.read(item))
                    tr_path = fl.replace("/en_us/", f"/{target_code}/")
                    tr = load_lenient_json(zin.read(locale[tr_path])) if tr_path in locale else {}
                    en_s = [
                        s for _p, s in iter_translatable_strings(en)
                        if s.strip() and looks_like_source_language(s)
                    ]
                    tr_s = [s for _p, s in iter_translatable_strings(tr)] if tr else []
                    b_en += len(en_s)
                    for idx, s in enumerate(en_s):
                        if idx < len(tr_s) and tr_s[idx] != s and tr_s[idx].strip():
                            b_tr += 1
                except (json.JSONDecodeError, OSError):
                    pass
            elif is_mb:
                try:
                    en_t = zin.read(item).decode("utf-8-sig", errors="ignore")
                    tr_path = fl.replace("/en_us/", f"/{target_code}/") if "/en_us/" in fl else fl
                    tr_t = zin.read(locale[tr_path]).decode("utf-8-sig", errors="ignore") if tr_path in locale else ""
                    tr_lines = tr_t.split("\n")
                    in_yaml = False
                    for idx, line in enumerate(en_t.split("\n")):
                        if line.strip() == "---":
                            in_yaml = not in_yaml
                            continue
                        if in_yaml:
                            match = re.match(r'^(\s*title\s*:\s*[\'"]?)(.*?)([\'"]?)$', line, re.IGNORECASE)
                            if match and looks_like_source_language(match.group(2)):
                                m_en += 1
                                if idx < len(tr_lines) and already_translated(tr_lines[idx], target_regex):
                                    m_tr += 1
                            continue
                        if line.strip().startswith("<") or line.strip().startswith("!["):
                            continue
                        if line.strip() and looks_like_source_language(line) and not is_technical_term(line):
                            m_en += 1
                            if idx < len(tr_lines) and already_translated(tr_lines[idx], target_regex):
                                m_tr += 1
                except OSError:
                    pass

        if b_en:
            on_row("📖", mod_name, "Книга(JSON)", b_tr, b_en, int(b_tr / b_en * 100))
        if m_en:
            on_row("📝", mod_name, "Книга(MD)", m_tr, m_en, int(m_tr / m_en * 100))
        return b_en + m_en, b_tr + m_tr


__all__ = [
    "FormatKitBooksJarProcessor",
    "FormatKitBooksStringEstimator",
    "FormatKitModpackAnalyzer",
]
