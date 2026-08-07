"""Settings and prompt editor windows for MineAI Translator."""

from __future__ import annotations

import ctypes
import sys

import customtkinter as ctk
from tkinter import filedialog, messagebox

from mineai.config import ConfigManager
from mineai.constants import DEFAULT_OPENROUTER_MODEL
from mineai.engines.llm_common import get_default_prompts, load_prompts, save_prompts
from mineai.gui.style import ToolTip, UI


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config: ConfigManager, on_saved) -> None:
        super().__init__(parent)
        self.config = config
        self.on_saved = on_saved
        self.title("Настройки · MineAI Translator")
        self.geometry("720x780")
        self.minsize(620, 620)
        self.resizable(True, True)
        self.configure(fg_color=UI.APP_BG)
        self.grab_set()

        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.pack(fill="both", expand=True, padx=14, pady=14)

        header = ctk.CTkFrame(shell, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            header,
            text="Настройки",
            font=("Segoe UI", 22, "bold"),
            text_color=UI.STRONG_TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Подключения, производительность и поведение переводчика",
            font=("Segoe UI", 12),
            text_color=UI.MUTED_TEXT,
        ).pack(anchor="w")

        tabs = ctk.CTkTabview(
            shell,
            corner_radius=14,
            fg_color=UI.CARD_BG,
            border_width=1,
            border_color=UI.BORDER,
        )
        tabs.pack(fill="both", expand=True)
        tab_ai = tabs.add("Локальный ИИ")
        tab_or = tabs.add("OpenRouter")
        tab_gen = tabs.add("Общие и API")

        ai = self._scroll(tab_ai)
        remote = self._scroll(tab_or)
        general = self._scroll(tab_gen)
        self._build_local_ai(ai)
        self._build_openrouter(remote)
        self._build_general(general)

        footer = ctk.CTkFrame(shell, fg_color="transparent")
        footer.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(
            footer,
            text="📝 Редактор промптов",
            height=36,
            corner_radius=10,
            fg_color=UI.CYAN,
            hover_color=UI.CYAN_HOVER,
            command=self._open_prompt_editor,
        ).pack(side="left")
        ctk.CTkButton(
            footer,
            text="Сохранить настройки",
            height=36,
            corner_radius=10,
            fg_color=UI.SUCCESS,
            hover_color=UI.SUCCESS_HOVER,
            command=self._save,
        ).pack(side="right")

    def _scroll(self, tab):
        frame = ctk.CTkScrollableFrame(tab, fg_color="transparent", corner_radius=0)
        frame.pack(fill="both", expand=True, padx=4, pady=4)
        return frame

    def _section(self, parent, title: str, description: str):
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            fg_color=UI.CARD_ALT_BG,
            border_width=1,
            border_color=UI.BORDER,
        )
        card.pack(fill="x", padx=4, pady=6)
        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 13, "bold"),
            text_color=UI.STRONG_TEXT,
        ).pack(anchor="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(
            card,
            text=description,
            font=("Segoe UI", 11),
            text_color=UI.MUTED_TEXT,
            justify="left",
            wraplength=560,
        ).pack(anchor="w", padx=12, pady=(0, 8))
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=(0, 12))
        return body

    def _label(self, parent, text: str):
        ctk.CTkLabel(
            parent,
            text=text,
            font=("Segoe UI", 11, "bold"),
            text_color=UI.MUTED_TEXT,
        ).pack(anchor="w", pady=(8, 2))

    def _browse_row(self, parent, entry, filetypes):
        ctk.CTkButton(
            parent,
            text="Обзор…",
            width=92,
            height=30,
            corner_radius=9,
            fg_color=UI.SUBTLE,
            hover_color=UI.SUBTLE_HOVER,
            command=lambda: self._browse(entry, filetypes),
        ).pack(anchor="e", pady=(2, 0))

    def _build_local_ai(self, parent) -> None:
        body = self._section(parent, "KoboldCPP", "Локальный запуск модели без облачного API.")
        self._label(body, "Исполняемый файл KoboldCPP (.exe)")
        self.ent_ai_exe = ctk.CTkEntry(body, height=32)
        self.ent_ai_exe.insert(0, self.config.get("AI", "exe_path"))
        self.ent_ai_exe.pack(fill="x")
        self._browse_row(body, self.ent_ai_exe, [("Executables", "*.exe")])

        self._label(body, "Модель (.gguf)")
        self.ent_ai_mod = ctk.CTkEntry(body, height=32)
        self.ent_ai_mod.insert(0, self.config.get("AI", "model_path"))
        self.ent_ai_mod.pack(fill="x")
        self._browse_row(body, self.ent_ai_mod, [("GGUF Models", "*.gguf")])

        gpu_val = self.config.getint("AI", "gpu_layers", 99)
        self.lbl_gpu = ctk.CTkLabel(
            body,
            text=f"Слои GPU: {gpu_val}",
            font=("Segoe UI", 11, "bold"),
            text_color=UI.MUTED_TEXT,
        )
        self.lbl_gpu.pack(anchor="w", pady=(12, 2))
        self.slider_gpu = ctk.CTkSlider(
            body,
            from_=0,
            to=99,
            number_of_steps=99,
            command=lambda value: self.lbl_gpu.configure(text=f"Слои GPU: {int(value)}"),
        )
        self.slider_gpu.set(gpu_val)
        self.slider_gpu.pack(fill="x")
        ToolTip(self.slider_gpu, "Слои GPU", "Количество слоёв модели, выгружаемых на GPU. Значение зависит от доступной видеопамяти.")

    def _build_openrouter(self, parent) -> None:
        body = self._section(parent, "OpenRouter / совместимый endpoint", "Облачный OpenRouter или совместимый Chat Completions API.")
        self._label(body, "API URL")
        self.ent_or_url = ctk.CTkEntry(body, height=32)
        self.ent_or_url.insert(0, self.config.get("OPENROUTER", "api_url"))
        self.ent_or_url.pack(fill="x")

        self._label(body, "API ключ OpenRouter")
        self.ent_or_key = ctk.CTkEntry(body, show="*", height=32)
        self.ent_or_key.insert(0, self.config.get("OPENROUTER", "api_key"))
        self.ent_or_key.pack(fill="x")

        self._label(body, "ID модели")
        self.ent_or_model = ctk.CTkEntry(body, height=32)
        self.ent_or_model.insert(0, self.config.get("OPENROUTER", "model") or DEFAULT_OPENROUTER_MODEL)
        self.ent_or_model.pack(fill="x")

        self._label(body, "Site URL · необязательно")
        self.ent_or_site = ctk.CTkEntry(body, height=32)
        self.ent_or_site.insert(0, self.config.get("OPENROUTER", "site_url"))
        self.ent_or_site.pack(fill="x")

        self._label(body, "Название приложения (X-Title)")
        self.ent_or_app = ctk.CTkEntry(body, height=32)
        self.ent_or_app.insert(0, self.config.get("OPENROUTER", "app_name"))
        self.ent_or_app.pack(fill="x")

    def _build_general(self, parent) -> None:
        behavior = self._section(parent, "Поведение", "Настройки обработки текста и повторов запросов.")
        self.var_smart = ctk.BooleanVar(value=self.config.getboolean("GENERAL", "smart_glue"))
        ctk.CTkSwitch(behavior, text="✨ Умный склейщик предложений", variable=self.var_smart).pack(anchor="w", pady=(2, 12))

        try:
            retries_val = self.config.getint("AI", "ai_retries")
        except Exception:
            retries_val = 3
        self.lbl_retries = ctk.CTkLabel(
            behavior,
            text=self._retry_text(retries_val),
            font=("Segoe UI", 11, "bold"),
            text_color=UI.MUTED_TEXT,
        )
        self.lbl_retries.pack(anchor="w")
        self.slider_retries = ctk.CTkSlider(
            behavior,
            from_=0,
            to=5,
            number_of_steps=5,
            command=lambda value: self.lbl_retries.configure(text=self._retry_text(int(value))),
        )
        self.slider_retries.set(retries_val)
        self.slider_retries.pack(fill="x", pady=(4, 10))

        performance = self._section(parent, "Google Translate", "Количество параллельных рабочих потоков.")
        try:
            workers = self.config.getint("GENERAL", "google_workers")
        except Exception:
            workers = 5
        self.lbl_workers = ctk.CTkLabel(
            performance,
            text=f"Потоки Google Translate: {workers}",
            font=("Segoe UI", 11, "bold"),
            text_color=UI.MUTED_TEXT,
        )
        self.lbl_workers.pack(anchor="w")
        self.slider_thr = ctk.CTkSlider(
            performance,
            from_=1,
            to=10,
            number_of_steps=9,
            command=lambda value: self.lbl_workers.configure(text=f"Потоки Google Translate: {int(value)}"),
        )
        self.slider_thr.set(workers)
        self.slider_thr.pack(fill="x", pady=(4, 2))

        deepl = self._section(parent, "DeepL", "API-ключ для движка DeepL.")
        self.ent_deepl = ctk.CTkEntry(deepl, show="*", height=32)
        self.ent_deepl.insert(0, self.config.get("API", "deepl_key"))
        self.ent_deepl.pack(fill="x")

    @staticmethod
    def _retry_text(value: int) -> str:
        return f"Повторы ИИ при ошибке: {value}" if value > 0 else "Повторы ИИ при ошибке: отключены"

    def _open_prompt_editor(self) -> None:
        PromptEditorWindow(self)

    def _browse(self, entry: ctk.CTkEntry, filetypes) -> None:
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _save(self) -> None:
        self.config.set_many("AI", {
            "exe_path": self.ent_ai_exe.get(),
            "model_path": self.ent_ai_mod.get(),
            "gpu_layers": int(self.slider_gpu.get()),
            "ai_retries": int(self.slider_retries.get()),
        })
        self.config.set_many("OPENROUTER", {
            "api_key": self.ent_or_key.get(),
            "api_url": self.ent_or_url.get().strip(),
            "model": self.ent_or_model.get().strip(),
            "site_url": self.ent_or_site.get().strip(),
            "app_name": self.ent_or_app.get().strip(),
        })
        self.config.set_many("GENERAL", {
            "smart_glue": self.var_smart.get(),
            "google_workers": int(self.slider_thr.get()),
        })
        self.config.set_many("API", {"deepl_key": self.ent_deepl.get()})
        self.on_saved()
        self.destroy()


class PromptEditorWindow(ctk.CTkToplevel):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.title("Редактор промптов ИИ · MineAI Translator")
        self.geometry("860x660")
        self.minsize(700, 520)
        self.resizable(True, True)
        self.configure(fg_color=UI.APP_BG)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._request_close)
        self.prompts = load_prompts()
        self._dirty = False

        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.pack(fill="both", expand=True, padx=14, pady=14)
        header = ctk.CTkFrame(shell, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Редактор промптов", font=("Segoe UI", 22, "bold"), text_color=UI.STRONG_TEXT).pack(side="left")
        self.lbl_dirty = ctk.CTkLabel(header, text="Сохранено", font=("Segoe UI", 11, "bold"), text_color="#79d89a")
        self.lbl_dirty.pack(side="right")

        tabs = ctk.CTkTabview(shell, corner_radius=14, fg_color=UI.CARD_BG, border_width=1, border_color=UI.BORDER)
        tabs.pack(fill="both", expand=True)
        self.txt_mods = self._create_tab(tabs, "mods", "Интерфейс (Моды)")
        self.txt_books = self._create_tab(tabs, "books", "Книги / Справочники")
        self.txt_quests = self._create_tab(tabs, "quests", "Квесты")
        tab_tech = tabs.add("⚙ Тех. правила")
        ctk.CTkLabel(
            tab_tech,
            text="ОПАСНАЯ ЗОНА · изменение правил может сломать JSON/маркеры",
            text_color="#ff7373",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", padx=8, pady=(8, 2))
        ctk.CTkLabel(
            tab_tech,
            text="{markers} — точный список маркеров [#N#] текущего запроса. Если переменная не указана, список добавится автоматически.",
            text_color=UI.MUTED_TEXT,
            font=("Segoe UI", 11),
            justify="left",
            wraplength=720,
        ).pack(anchor="w", padx=8, pady=(0, 6))
        self.txt_tech = ctk.CTkTextbox(tab_tech, wrap="word", font=("Consolas", 13), corner_radius=10)
        self.txt_tech.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.txt_tech.insert("1.0", self.prompts.get("technical", get_default_prompts()["technical"]))

        for widget in (self.txt_mods, self.txt_books, self.txt_quests, self.txt_tech):
            self._fix_ctrl_for_textbox(widget)
            widget.bind("<KeyRelease>", self._mark_dirty, add="+")
            widget.bind("<<Paste>>", self._mark_dirty, add="+")
            widget.bind("<<Cut>>", self._mark_dirty, add="+")

        footer = ctk.CTkFrame(shell, fg_color="transparent")
        footer.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(
            footer,
            text="Сбросить по умолчанию",
            fg_color=UI.DANGER,
            hover_color=UI.DANGER_HOVER,
            command=self._reset,
        ).pack(side="left")
        ctk.CTkButton(
            footer,
            text="Сохранить",
            fg_color=UI.SUCCESS,
            hover_color=UI.SUCCESS_HOVER,
            command=self._save,
        ).pack(side="right")

    def _create_tab(self, tabs, key: str, title: str):
        tab = tabs.add(title)
        ctk.CTkLabel(
            tab,
            text="Переменные: {lang_name} — язык, {context} — название мода/файла",
            text_color=UI.MUTED_TEXT,
            font=("Segoe UI", 11),
        ).pack(anchor="w", padx=8, pady=(8, 5))
        txt = ctk.CTkTextbox(tab, wrap="word", font=("Segoe UI", 13), corner_radius=10)
        txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        txt.insert("1.0", self.prompts.get(key, get_default_prompts()[key]))
        return txt

    def _mark_dirty(self, _event=None) -> None:
        if self._dirty:
            return
        self._dirty = True
        self.lbl_dirty.configure(text="● Есть несохранённые изменения", text_color="#f6c85f")

    def _reset(self) -> None:
        if not messagebox.askyesno(
            "Сбросить промпты?",
            "Все четыре промпта будут заменены значениями по умолчанию. Продолжить?",
            icon="warning",
        ):
            return
        defaults = get_default_prompts()
        for widget, key in (
            (self.txt_mods, "mods"),
            (self.txt_books, "books"),
            (self.txt_quests, "quests"),
            (self.txt_tech, "technical"),
        ):
            widget.delete("1.0", "end")
            widget.insert("1.0", defaults[key])
        self._mark_dirty()

    def _collect(self) -> dict[str, str]:
        return {
            "mods": self.txt_mods.get("1.0", "end").strip(),
            "books": self.txt_books.get("1.0", "end").strip(),
            "quests": self.txt_quests.get("1.0", "end").strip(),
            "technical": self.txt_tech.get("1.0", "end").strip(),
        }

    def _save(self, *, close: bool = True) -> None:
        self.prompts.update(self._collect())
        save_prompts(self.prompts)
        self._dirty = False
        self.lbl_dirty.configure(text="Сохранено", text_color="#79d89a")
        if close:
            self.destroy()

    def _request_close(self) -> None:
        if not self._dirty:
            self.destroy()
            return
        choice = messagebox.askyesnocancel(
            "Несохранённые изменения",
            "Сохранить изменения промптов перед закрытием?",
        )
        if choice is None:
            return
        if choice:
            self._save(close=True)
        else:
            self.destroy()

    @staticmethod
    def _fix_ctrl_for_textbox(widget) -> None:
        def handler(event):
            ctrl = bool(event.state & 4)
            if sys.platform == "win32":
                try:
                    ctrl = ctrl or bool(ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000)
                except Exception:
                    pass
            if not ctrl:
                return None
            actions = {67: "<<Copy>>", 86: "<<Paste>>", 65: "<<SelectAll>>", 88: "<<Cut>>"}
            action = actions.get(event.keycode)
            if action:
                event.widget.event_generate(action)
                return "break"
            return None

        target = getattr(widget, "_textbox", widget)
        target.bind("<Key>", handler, add="+")
