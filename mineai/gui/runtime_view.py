"""Thread-safe status, log and run-control presentation helpers."""

import queue
import threading
import traceback

from mineai.gui.style import UI


class RuntimeViewMixin:
    def _on_scroll_interaction(self) -> None:
        self.auto_scroll = self.textbox.yview()[1] >= 0.99

    def _ensure_ui_thread(self, callback, *args) -> bool:
        """Queue Tk work without calling any Tk API from a worker thread."""
        ui_thread_id = getattr(self, "_ui_thread_id", threading.main_thread().ident)
        if threading.get_ident() != ui_thread_id:
            self._ui_queue.put((callback, args))
            return False
        return True

    def _drain_ui_queue(self) -> None:
        while True:
            try:
                callback, args = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback(*args)
            except Exception:
                error = traceback.format_exc()
                try:
                    self.log(f"❌ Ошибка UI callback:\n{error}", "red")
                except Exception:
                    try:
                        with open("mineai_log.txt", "a", encoding="utf-8") as handle:
                            handle.write(f"❌ Ошибка UI callback:\n{error}\n")
                    except Exception:
                        pass
        self.after(50, self._drain_ui_queue)

    def log(self, message: str, tag: str = "white") -> None:
        if not self._ensure_ui_thread(self.log, message, tag):
            return
        at_bottom = self.textbox.yview()[1] >= 0.99
        self.textbox.insert("end", message + "\n", tag)
        if self.auto_scroll or at_bottom:
            self.textbox.see("end")
        try:
            with open("mineai_log.txt", "a", encoding="utf-8") as handle:
                handle.write(message + "\n")
        except Exception:
            pass

    def log_row(self, icon: str, name: str, kind: str, trans_c: int, en_c: int, pct: int) -> None:
        if not self._ensure_ui_thread(self.log_row, icon, name, kind, trans_c, en_c, pct):
            return
        at_bottom = self.textbox.yview()[1] >= 0.99
        self.textbox.insert("end", f"{icon} {name[:34]:<35}", "cyan")
        self.textbox.insert("end", f"[{kind}]".ljust(15), "magenta")
        self.textbox.insert("end", f"{trans_c}/{en_c}".ljust(12), "white")
        color = "green" if pct >= 90 else ("yellow" if pct >= 50 else "red")
        self.textbox.insert("end", f"{pct}%\n", color)
        if self.auto_scroll or at_bottom:
            self.textbox.see("end")

    def _refresh_metrics(self) -> None:
        if not hasattr(self, "lbl_metric_processed"):
            return
        try:
            snap = self.job_state.snapshot()
        except Exception:
            return
        if snap.total_strings > 0:
            processed = min(snap.translated_strings, snap.total_strings)
            self.lbl_metric_processed.configure(text=f"{processed:,} / {snap.total_strings:,}".replace(",", " "))
            self.lbl_metric_success.configure(text=f"{min(snap.ok_strings, snap.total_strings):,}".replace(",", " "))
            self.lbl_metric_errors.configure(text=f"{min(snap.failed_strings, snap.total_strings):,}".replace(",", " "))
        else:
            self.lbl_metric_processed.configure(text="—")
            self.lbl_metric_success.configure(text="—")
            self.lbl_metric_errors.configure(text="0")
        try:
            eta = self.job_state.eta_text()
        except Exception:
            eta = "—"
        if snap.is_running:
            eta_text = eta
        elif snap.total_strings > 0 and snap.translated_strings >= snap.total_strings:
            eta_text = "готово"
        else:
            eta_text = "—"
        self.lbl_metric_eta.configure(text=eta_text)

    def set_status(self, text: str, progress: float | None) -> None:
        if not self._ensure_ui_thread(self.set_status, text, progress):
            return
        if progress is not None:
            try:
                progress = max(0.0, min(float(progress), 1.0))
            except Exception:
                progress = 0.0
            self.progress.set(progress)
        self.lbl_status.configure(text=text)
        self._refresh_metrics()

    def _lock_ui(self, locked: bool) -> None:
        if not self._ensure_ui_thread(self._lock_ui, locked):
            return
        state = "disabled" if locked else "normal"
        rev = "normal" if locked else "disabled"
        self.btn_analyze.configure(state=state)
        self.btn_start.configure(state=state)
        self.btn_stop.configure(state=rev)
        self.btn_pause.configure(state=rev)
        if hasattr(self, "btn_settings"):
            self.btn_settings.configure(state=state)
        if hasattr(self, "btn_migrate"):
            self.btn_migrate.configure(state=state)
        if hasattr(self, "btn_engine_settings"):
            if locked:
                self.btn_engine_settings.configure(state="disabled")
            else:
                self._refresh_engine_status()
        self._refresh_metrics()

    def _toggle_pause(self) -> None:
        is_paused = self.job_state.toggle_pause()
        if is_paused:
            self.btn_pause.configure(text="▶ ПРОДОЛЖИТЬ", fg_color=UI.CYAN, text_color="white")
            self.log("⏸ Пауза", "yellow")
        else:
            self.btn_pause.configure(text="⏸ ПАУЗА", fg_color=UI.WARNING, text_color="black")
            self.log("▶ Продолжение", "green")

    def _stop(self) -> None:
        active_job = self._job
        if active_job is not None:
            active_job.stop()
        else:
            self.job_state.stop()
        self.btn_stop.configure(state="disabled")
        self.btn_pause.configure(state="disabled")
        # Deliberately keep the current progress instead of presenting Stop as 100% completion.
        self.set_status("🛑 Остановка...", None)

    def _clear_log(self) -> None:
        self.textbox.delete("1.0", "end")

    def _reset_run_ui(self) -> None:
        self._clear_log()
        self.progress.set(0.0)
        self.lbl_status.configure(text="Подготовка...")
        self.lbl_metric_processed.configure(text="—")
        self.lbl_metric_success.configure(text="—")
        self.lbl_metric_errors.configure(text="0")
        self.lbl_metric_eta.configure(text="расчёт...")
