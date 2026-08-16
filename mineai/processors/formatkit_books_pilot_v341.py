from __future__ import annotations

from mineai import formatkit_books_bridge as _books
from mineai.processors.formatkit_books_pilot import FormatKitBooksJarProcessor as _BaseBooksJarProcessor
from mineai.processors.selection import skip_threshold_reached


class FormatKitBooksJarProcessor(_BaseBooksJarProcessor):
    """v3.4.1 runtime wrapper: resolve semantic children before parent prose.

    The v3.4 processor remains untouched. Only the FormatKit-owned book method is
    overridden so parent candidates can be validated against the already resolved
    semantic child payload without changing unrelated jar/locale/book behavior.
    """

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
            elif work.adapter_name == "modonomicon-book-json":
                label = "Modonomicon/FormatKit"
            else:
                label = "IE Manual/FormatKit"
            self.callbacks.on_log(
                f"⚡ Перевод {mod_name} [{label}] — {len(work.pending)} строк",
                "magenta",
            )

            semantic_children, remaining = _books.split_semantic_book_pending(work)
            if semantic_children:
                translated.update(
                    self.service.translate_dict(
                        semantic_children,
                        target_lang,
                        self.callbacks,
                        context=mod_name,
                        candidate_validator=lambda unit_id, candidate: _books.validate_book_candidate(
                            work, unit_id, candidate
                        ),
                        preserve_source_structure=True,
                    )
                )
            if remaining:
                resolved_semantic = _books.semantic_resolved_values(work, translated)
                translated.update(
                    self.service.translate_dict(
                        remaining,
                        target_lang,
                        self.callbacks,
                        context=mod_name,
                        candidate_validator=lambda unit_id, candidate: _books.validate_book_candidate(
                            work,
                            unit_id,
                            candidate,
                            resolved_semantic=resolved_semantic,
                        ),
                        preserve_source_structure=True,
                    )
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


__all__ = ["FormatKitBooksJarProcessor"]
