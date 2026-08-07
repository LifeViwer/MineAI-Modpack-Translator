"""Modern GUI for MineAI Translator."""

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import ctypes
import traceback
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from mineai import __version__
from mineai.cache import load_both_caches
from mineai.config import settings
from mineai.constants import LANGUAGES, MC_VERSIONS
from mineai.gui.settings import SettingsWindow
from mineai.runtime.job import TranslationJob, TranslationOptions
from mineai.runtime.state import JobState
from mineai.gui.migration import MigrationWindow
from mineai.gui.style import ToolTip, UI


def _resolve_icon_path() -> str | None:
    """Ищет icon.ico: в ресурсах PyInstaller, рядом с EXE и в cwd."""
    candidates = []

    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        candidates.append(os.path.join(base, "icon.ico"))
        candidates.append(os.path.join(os.path.dirname(sys.executable), "icon.ico"))

    candidates.append(os.path.join(os.getcwd(), "icon.ico"))

    for path in candidates:
        if os.path.exists(path):
            return path

    return None



from mineai.gui.content_view import ContentViewMixin
from mineai.gui.runtime_view import RuntimeViewMixin
from mineai.gui.sidebar_project import build_sidebar_project
from mineai.gui.sidebar_engine import build_sidebar_engine
from mineai.gui.sidebar_actions import build_sidebar_actions


class TranslatorApp(RuntimeViewMixin, ContentViewMixin, ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title(f"MineAI Translator v{__version__.strip()}")
        self.geometry("1320x860")
        self.minsize(1180, 760)

        icon_path = _resolve_icon_path()
        if icon_path:
            try:
                self.iconbitmap(icon_path)
                self.iconbitmap(default=icon_path)
            except tk.TclError:
                pass

        ctk.set_appearance_mode(settings.get("GENERAL", "theme"))
        ctk.set_default_color_theme(settings.get("GENERAL", "color"))

        self.job_state = JobState()
        self.cache_std, self.cache_ai, polish_total = load_both_caches()

        self._job: TranslationJob | None = None
        self._ui_thread_id = threading.get_ident()
        self._ui_queue: queue.Queue[tuple[object, tuple]] = queue.Queue()
        self.auto_scroll = True

        self.configure(fg_color=self._app_bg())

        self._build_ui()
        self._refresh_folder_label()
        self._refresh_engine_status()
        self._refresh_metrics()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(50, self._drain_ui_queue)

        if polish_total:
            self.log(f"✨ Кэш проверен: исправлено/удалено ошибок: {polish_total}.", "magenta")

    def _build_sidebar(self) -> None:
        build_sidebar_project(self)
        build_sidebar_engine(self)
        build_sidebar_actions(self)

    def _job_instance(self) -> TranslationJob:
        return TranslationJob(
            settings,
            self.cache_std,
            self.cache_ai,
            self.job_state,
            on_log=self.log,
            on_status=self.set_status,
            on_row=self.log_row,
        )

    def _translation_options(self) -> TranslationOptions:
        return TranslationOptions(
            mc_dir=settings.get("GENERAL", "mc_dir"),
            language_label=self.var_lang.get(),
            mc_version=self.var_mc_ver.get(),
            output_mode=self.var_output.get(),
            pack_name=self.entry_rp_name.get().strip(),
            engine=self.var_engine.get(),
            google_mode=self.var_google_mode.get(),
            ai_mode=self.var_ai_mode.get(),
            ai_batch=int(self.slider_ai_batch.get()),
            ai_provider=self.var_ai_provider.get(),
            process_mode=self.var_mode.get(),
            translate_mods=self.var_mods.get(),
            translate_books=self.var_books.get(),
            translate_quests=self.var_quests.get(),
        )

    def _open_settings(self) -> None:
        SettingsWindow(self, settings, self._on_settings_saved)

    def _on_settings_saved(self) -> None:
        self._refresh_folder_label()
        self._refresh_engine_status()

    def _refresh_folder_label(self) -> None:
        path = settings.get("GENERAL", "mc_dir").strip()
        if not path:
            self.lbl_folder.configure(text="Не выбрана", text_color=self._muted_text())
            return
        display = f"...{path[-31:]}" if len(path) > 31 else path
        self.lbl_folder.configure(text=display, text_color=self._strong_text())

    def _select_folder(self) -> None:
        initial = settings.get("GENERAL", "mc_dir").strip()
        path = filedialog.askdirectory(initialdir=initial or None)
        if path:
            settings.set("GENERAL", "mc_dir", path)
            self._refresh_folder_label()

    def _update_output_ui(self) -> None:
        state = "normal" if self.var_output.get() == "resourcepack" else "disabled"
        self.entry_rp_name.configure(state=state)

    def _engine_readiness(self) -> tuple[bool, str, str]:
        engine = self.var_engine.get()
        if engine == "google":
            return True, "✓ Google готов", "Дополнительная настройка не требуется."
        if engine == "deepl":
            key = settings.get("API", "deepl_key").strip()
            if key:
                return True, "✓ DeepL настроен", "API-ключ найден."
            return False, "⚠ DeepL не настроен", "Добавьте API-ключ DeepL в настройках."
        if engine == "ai":
            provider = self.var_ai_provider.get()
            if provider == "openrouter":
                key = settings.get("OPENROUTER", "api_key").strip()
                model = settings.get("OPENROUTER", "model").strip()
                missing = []
                if not key:
                    missing.append("API-ключ")
                if not model:
                    missing.append("ID модели")
                if missing:
                    return False, "⚠ OpenRouter не настроен", "Не задано: " + ", ".join(missing) + "."
                return True, "✓ OpenRouter настроен", f"Модель: {model}"

            model_path = settings.get("AI", "model_path").strip()
            if model_path and model_path.lower().endswith(".gguf") and os.path.isfile(model_path):
                return True, "✓ Локальный ИИ настроен", Path(model_path).name
            if model_path:
                return False, "⚠ Файл модели недоступен", "Проверьте путь к .gguf модели в настройках."
            return False, "⚠ Локальный ИИ не настроен", "Выберите .gguf модель в настройках."
        return False, "⚠ Неизвестный движок", engine

    def _refresh_engine_status(self) -> None:
        if not hasattr(self, "lbl_engine_status"):
            return
        ready, title, detail = self._engine_readiness()
        self.lbl_engine_status.configure(
            text=f"{title}  ·  {detail}",
            text_color="#79d89a" if ready else "#f6c85f",
        )
        if ready:
            self.btn_engine_settings.grid_remove()
        else:
            self.btn_engine_settings.grid()
            self.btn_engine_settings.configure(state="normal")

    def _update_engine_ui(self) -> None:
        self.frame_ai.pack_forget()
        self.frame_google.pack_forget()
        if self.var_engine.get() == "ai":
            self.frame_ai.pack(fill="x", pady=(6, 0))
        elif self.var_engine.get() == "google":
            self.frame_google.pack(fill="x", pady=(6, 0))
        self._refresh_engine_status()

    def _save_ui_preferences(self) -> None:
        values = {
            "language": self.var_lang.get(),
            "mc_version": self.var_mc_ver.get(),
            "output_mode": self.var_output.get(),
            "pack_name": self.entry_rp_name.get().strip() or "MineAI_Pack",
            "engine": self.var_engine.get(),
            "google_mode": self.var_google_mode.get(),
            "ai_mode": self.var_ai_mode.get(),
            "ai_batch": int(self.slider_ai_batch.get()),
            "process_mode": self.var_mode.get(),
            "translate_mods": self.var_mods.get(),
            "translate_books": self.var_books.get(),
            "translate_quests": self.var_quests.get(),
        }
        if hasattr(settings, "set_many"):
            settings.set_many("GUI", values)
        else:
            for key, value in values.items():
                settings.set("GUI", key, value)

    def _on_close(self) -> None:
        try:
            self._save_ui_preferences()
        except Exception:
            pass
        if self._job is not None:
            self._job.stop()
        self.destroy()

    @staticmethod
    def _looks_like_minecraft_dir(path: str) -> bool:
        if not path or not os.path.isdir(path):
            return False
        return any(os.path.isdir(os.path.join(path, marker)) for marker in ("mods", "config"))

    def _validate_minecraft_dir(self) -> bool:
        path = settings.get("GENERAL", "mc_dir").strip()
        if self._looks_like_minecraft_dir(path):
            return True
        messagebox.showerror(
            "Неверная папка Minecraft",
            "Выберите корневую папку сборки Minecraft.\n\n"
            "Ожидается существующая папка, содержащая mods/ или config/.",
        )
        return False

    def _validate_scope(self) -> bool:
        if self.var_mods.get() or self.var_books.get() or self.var_quests.get():
            return True
        messagebox.showwarning("Нечего обрабатывать", "Выберите хотя бы одну область перевода.")
        return False

    def _confirm_inplace(self) -> bool:
        if self.var_output.get() != "inplace":
            return True
        return messagebox.askyesno(
            "Подтвердите перезапись .jar",
            "Режим inplace изменяет оригинальные .jar модов. Это может повредить подписи "
            "или вызвать предупреждения загрузчика.\n\n"
            "Для безопасной работы рекомендуется Resource Pack + Data Pack.\n\n"
            "Продолжить с inplace?",
            icon="warning",
        )


    def _start_analysis(self) -> None:
        if not self._validate_minecraft_dir() or not self._validate_scope():
            return
        self._save_ui_preferences()
        self._reset_run_ui()
        self._lock_ui(True)
        self.job_state.start()
        self._job = self._job_instance()
        options = self._translation_options()
        threading.Thread(target=lambda: self._run_analysis_thread(options), daemon=True).start()

    def _run_analysis_thread(self, options: TranslationOptions) -> None:
        try:
            if self._job is not None:
                self._job.run_analysis(options)
                if not self.job_state.should_run():
                    self.set_status("Остановлено", None)
        except Exception:
            error = traceback.format_exc()
            self.log(f"❌ Ошибка анализа:\n{error}", "red")
            self.set_status("❌ Ошибка анализа", None)
        finally:
            self.job_state.finish()
            self._job = None
            self._lock_ui(False)

    def _start_translation(self) -> None:
        if not self._validate_minecraft_dir() or not self._validate_scope():
            return
        ready, title, detail = self._engine_readiness()
        if not ready:
            self._refresh_engine_status()
            messagebox.showerror("Движок не настроен", f"{title}\n\n{detail}")
            return
        if not self._confirm_inplace():
            return

        self._save_ui_preferences()
        if self.var_engine.get() == "ai":
            settings.set("AI", "ai_provider", self.var_ai_provider.get())
            settings.set("AI", "fallback_google", self.var_ai_fallback.get())

        self._reset_run_ui()
        self._lock_ui(True)
        self.job_state.start()
        self.btn_pause.configure(text="⏸ ПАУЗА", fg_color=UI.WARNING, text_color="black")
        self._job = self._job_instance()
        options = self._translation_options()
        threading.Thread(target=lambda: self._run_translation_thread(options), daemon=True).start()

    def _open_log_file(self) -> None:
        log_path = Path("mineai_log.txt").resolve()
        if not log_path.exists():
            self.log("❌ Лог-файл еще не создан.", "yellow")
            return
        try:
            if sys.platform == "win32":
                os.startfile(str(log_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(log_path)])
            else:
                try:
                    subprocess.Popen(["xdg-open", str(log_path)])
                except OSError:
                    if not webbrowser.open(log_path.as_uri()):
                        raise RuntimeError("не найдено приложение для открытия файла")
        except Exception as exc:
            self.log(f"❌ Не удалось открыть лог: {exc}", "red")

    def _run_translation_thread(self, options: TranslationOptions) -> None:
        try:
            if self._job is not None:
                self._job.run_translation(options)
        except Exception:
            error = traceback.format_exc()
            self.log(f"❌ Ошибка перевода:\n{error}", "red")
            self.set_status("❌ Ошибка перевода", None)
        finally:
            self.job_state.finish()
            self._job = None
            self._lock_ui(False)

    def _open_migration(self) -> None:
        if not self._validate_minecraft_dir():
            return
        self._save_ui_preferences()
        MigrationWindow(
            self,
            settings.get("GENERAL", "mc_dir").strip(),
            self.var_lang.get(),
            self.cache_std,
            self.cache_ai,
            self.log,
        )

def run() -> None:
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MineAI.Translator")
        except Exception:
            pass

    app = TranslatorApp()
    app.mainloop()
