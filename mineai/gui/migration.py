"""Resource-pack migration window."""

from __future__ import annotations

import os
import threading
import traceback

import customtkinter as ctk
from tkinter import filedialog, messagebox

from mineai.constants import LANGUAGES
from mineai.gui.style import ToolTip, UI
from mineai.processors.migration import run_migration


class MigrationWindow(ctk.CTkToplevel):
    def __init__(self, parent, mc_dir: str, lang_label: str, cache_std, cache_ai, log_callback):
        super().__init__(parent)
        self.title("Миграция перевода · MineAI Translator")
        self.geometry("620x520")
        self.minsize(520, 430)
        self.resizable(True, True)
        self.configure(fg_color=UI.APP_BG)
        self.grab_set()

        self.mc_dir = mc_dir
        self.lang_api_code = LANGUAGES[lang_label]["api"]
        self.cache_std = cache_std
        self.cache_ai = cache_ai
        self.log_callback = log_callback

        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.pack(fill="both", expand=True, padx=14, pady=14)
        ctk.CTkLabel(
            shell,
            text="Миграция ресурс-пака",
            font=("Segoe UI", 22, "bold"),
            text_color=UI.STRONG_TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            shell,
            text="Импорт готовых переводов в кэш без повторной отправки строк в переводчик.",
            font=("Segoe UI", 12),
            text_color=UI.MUTED_TEXT,
        ).pack(anchor="w", pady=(0, 10))

        card = ctk.CTkFrame(shell, corner_radius=14, fg_color=UI.CARD_BG, border_width=1, border_color=UI.BORDER)
        card.pack(fill="both", expand=True)
        body = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        self._label(body, "Resource Pack (.zip)")
        self.ent_zip = ctk.CTkEntry(body, height=32, placeholder_text="Выберите архив с переводом")
        self.ent_zip.pack(fill="x", pady=(0, 5))
        ctk.CTkButton(
            body,
            text="Обзор…",
            width=92,
            height=30,
            corner_radius=9,
            fg_color=UI.SUBTLE,
            hover_color=UI.SUBTLE_HOVER,
            command=self._browse,
        ).pack(anchor="e")

        self._label(body, "Для какого движка использовать импорт?")
        self.var_cache = ctk.StringVar(value="ai")
        ctk.CTkRadioButton(
            body,
            text="Нейросеть · imported_caches/ai",
            variable=self.var_cache,
            value="ai",
        ).pack(anchor="w", pady=3)
        ctk.CTkRadioButton(
            body,
            text="Google / DeepL · imported_caches/std",
            variable=self.var_cache,
            value="std",
        ).pack(anchor="w", pady=3)

        self.summary = ctk.CTkFrame(body, corner_radius=12, fg_color=UI.CARD_ALT_BG, border_width=1, border_color=UI.BORDER)
        self.summary.pack(fill="x", pady=(14, 2))
        self.lbl_summary_title = ctk.CTkLabel(
            self.summary,
            text="Готово к импорту",
            font=("Segoe UI", 12, "bold"),
            text_color=UI.STRONG_TEXT,
        )
        self.lbl_summary_title.pack(anchor="w", padx=11, pady=(9, 1))
        self.lbl_summary = ctk.CTkLabel(
            self.summary,
            text="После завершения здесь появится количество импортированных строк.",
            font=("Segoe UI", 11),
            text_color=UI.MUTED_TEXT,
            justify="left",
            wraplength=520,
        )
        self.lbl_summary.pack(anchor="w", padx=11, pady=(0, 9))
        ToolTip(
            self.summary,
            "Статистика миграции",
            "Текущий runtime возвращает число импортированных уникальных строк. Отдельные счётчики пропусков и конфликтов пока не экспортируются процессором миграции.",
        )

        self.btn_run = ctk.CTkButton(
            shell,
            text="Начать миграцию",
            height=40,
            corner_radius=11,
            fg_color=UI.SUCCESS,
            hover_color=UI.SUCCESS_HOVER,
            command=self._run,
        )
        self.btn_run.pack(fill="x", pady=(10, 0))

    @staticmethod
    def _label(parent, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=("Segoe UI", 11, "bold"),
            text_color=UI.MUTED_TEXT,
        ).pack(anchor="w", pady=(8, 3))

    def _browse(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("ZIP Archives", "*.zip")])
        if path:
            self.ent_zip.delete(0, "end")
            self.ent_zip.insert(0, path)

    def _run(self) -> None:
        zip_path = self.ent_zip.get().strip()
        if not zip_path or not os.path.exists(zip_path):
            messagebox.showerror("Ошибка", "Выберите существующий ZIP-архив.")
            return

        self.btn_run.configure(state="disabled", text="Миграция выполняется…")
        self.lbl_summary_title.configure(text="Обработка…", text_color="#7db4ff")
        self.lbl_summary.configure(text="Чтение архива и сопоставление строк с оригиналами модов.")
        cache_type = self.var_cache.get()

        def task() -> None:
            try:
                count = run_migration(
                    zip_path,
                    self.mc_dir,
                    cache_type,
                    self.lang_api_code,
                    self.log_callback,
                )
                if count > 0:
                    if cache_type == "ai":
                        self.cache_ai.load_imported_caches()
                    else:
                        self.cache_std.load_imported_caches()
                self.after(0, self._finish, count, cache_type)
            except Exception:
                error = traceback.format_exc()
                self.log_callback(f"❌ Ошибка миграции:\n{error}", "red")
                self.after(0, self._fail, error)

        threading.Thread(target=task, daemon=True).start()

    def _finish(self, count: int, cache_type: str) -> None:
        if count > 0:
            self.lbl_summary_title.configure(text="✓ Миграция завершена", text_color="#79d89a")
            self.lbl_summary.configure(
                text=(
                    f"Импортировано уникальных строк: {count}\n"
                    f"Кэш: {'Нейросеть' if cache_type == 'ai' else 'Google / DeepL'}\n"
                    "Пропуски / конфликты: текущий процессор не экспортирует отдельные счётчики."
                )
            )
            self.btn_run.configure(text="Готово", state="disabled")
        else:
            self.lbl_summary_title.configure(text="⚠ Ничего не импортировано", text_color="#f6c85f")
            self.lbl_summary.configure(text="Совпадающие строки не найдены. Подробности доступны в основном журнале.")
            self.btn_run.configure(text="Повторить", state="normal")

    def _fail(self, _error: str) -> None:
        self.lbl_summary_title.configure(text="✕ Ошибка миграции", text_color="#ff7373")
        self.lbl_summary.configure(text="Операция завершилась ошибкой. Полный traceback записан в основной журнал.")
        self.btn_run.configure(text="Повторить", state="normal")
