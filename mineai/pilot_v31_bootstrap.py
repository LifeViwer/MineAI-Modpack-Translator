from __future__ import annotations


def install_pilot_v31() -> None:
    """Teach the v3 book pilot to materialize immutable Patchouli templates."""
    from mineai import formatkit_books_bridge as _books
    from mineai.processors import formatkit_books_pilot as module

    base = module.FormatKitBooksJarProcessor
    if getattr(base, "_formatkit_v31_template_copy", False):
        return

    class FormatKitBooksJarProcessorV31(base):
        _formatkit_v31_template_copy = True

        def _process_formatkit_book(
            self, zin, zout, item, locale_files, target_lang, mode,
            output_mode, pack_writer, mod_name, written_inplace,
        ) -> bool:
            normalized = item.filename.replace("\\", "/").lower()
            if "/templates/" not in normalized:
                return super()._process_formatkit_book(
                    zin, zout, item, locale_files, target_lang, mode,
                    output_mode, pack_writer, mod_name, written_inplace,
                )

            try:
                raw_source = zin.read(item)
                source_bom = raw_source.startswith(b"\xef\xbb\xbf")
                source_text = raw_source.decode("utf-8-sig")
                target_path = _books.target_path_for_book(
                    item.filename, target_lang["file"]
                )
                assert target_path is not None
                target_text = None
                target_key = target_path.lower()
                if mode != "force" and target_key in locale_files:
                    try:
                        target_text = zin.read(locale_files[target_key]).decode("utf-8-sig")
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
                self.callbacks.on_log(
                    f"⚠ FormatKit шаблон пропущен {item.filename}: {exc}", "yellow"
                )
                return False

            if work.source_plan.metadata.get("patchouli_template_immutable") is not True:
                return super()._process_formatkit_book(
                    zin, zout, item, locale_files, target_lang, mode,
                    output_mode, pack_writer, mod_name, written_inplace,
                )
            if not self.state.should_run():
                return False

            try:
                output_text = _books.build_book_output(work, {})
            except ValueError as exc:
                self.callbacks.on_log(
                    f"❌ FormatKit отклонил шаблон {item.filename}: {exc}", "red"
                )
                return False

            payload = output_text.encode("utf-8")
            if source_bom:
                payload = b"\xef\xbb\xbf" + payload
            self.callbacks.on_log(
                f"🛡 Patchouli/FormatKit шаблон {mod_name} — копия без LLM",
                "cyan",
            )
            if output_mode == "resourcepack" and pack_writer:
                pack_writer.write(work.target_path, payload)
                return True
            if zout:
                zout.writestr(work.target_path, payload)
                written_inplace.add(work.target_path)
                return True
            return False

    module.FormatKitBooksJarProcessor = FormatKitBooksJarProcessorV31
