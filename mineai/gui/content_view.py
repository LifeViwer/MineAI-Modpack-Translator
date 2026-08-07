"""Reusable main-window chrome and content view for MineAI Translator."""

import ctypes
import sys

import customtkinter as ctk

from mineai.config import settings
from mineai.gui.style import ToolTip, UI


class ContentViewMixin:
    def _app_bg(self):
        return UI.APP_BG

    def _sidebar_bg(self):
        return UI.SIDEBAR_BG

    def _card_bg(self):
        return UI.CARD_BG

    def _border_color(self):
        return UI.BORDER

    def _strong_text(self):
        return UI.STRONG_TEXT

    def _muted_text(self):
        return UI.MUTED_TEXT

    def _info_bg(self):
        return UI.INFO_BG

    def _info_text(self):
        return UI.INFO_TEXT

    def _button_subtle(self) -> str:
        return UI.SUBTLE

    def _button_subtle_hover(self) -> str:
        return UI.SUBTLE_HOVER

    def _log_bg(self) -> str:
        return UI.LOG_BG

    def _pref(self, key: str, fallback: str) -> str:
        try:
            value = settings.get("GUI", key)
        except Exception:
            return fallback
        return value if value != "" else fallback

    def _pref_bool(self, key: str, fallback: bool) -> bool:
        try:
            return settings.getboolean("GUI", key)
        except Exception:
            return fallback

    def _pref_int(self, key: str, fallback: int, minimum: int, maximum: int) -> int:
        try:
            value = settings.getint("GUI", key, fallback)
        except Exception:
            value = fallback
        return max(minimum, min(value, maximum))

    # =========================
    # UI BUILD
    # =========================

    def _build_ui(self) -> None:
        self._font_hero = ctk.CTkFont(size=24, weight="bold")
        self._font_card = ctk.CTkFont(size=13, weight="bold")
        self._font_normal = ctk.CTkFont(size=13)
        self._font_small = ctk.CTkFont(size=12)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkScrollableFrame(
            self,
            width=420,
            corner_radius=18,
            fg_color=self._sidebar_bg(),
            border_width=1,
            border_color=self._border_color(),
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=(12, 8), pady=12)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content()

        self._update_output_ui()
        self._update_engine_ui()
    def _build_content(self) -> None:
        status_card = ctk.CTkFrame(
            self.content,
            corner_radius=16,
            fg_color=self._card_bg(),
            border_width=1,
            border_color=self._border_color(),
        )
        status_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        status_card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(status_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            title_row,
            text="Статус задачи",
            font=self._font_card,
            text_color=self._strong_text(),
        ).pack(side="left")
        self._add_info(
            title_row,
            "Статус задачи",
            "Ключевые показатели текущего анализа или перевода: обработанные и успешные строки, ошибки и ETA.",
        )

        metrics = ctk.CTkFrame(status_card, fg_color="transparent")
        metrics.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 7))
        for column in range(4):
            metrics.grid_columnconfigure(column, weight=1, uniform="metric")

        self.lbl_metric_processed = self._metric_tile(metrics, 0, "ОБРАБОТАНО", "—")
        self.lbl_metric_success = self._metric_tile(metrics, 1, "УСПЕШНО", "—")
        self.lbl_metric_errors = self._metric_tile(metrics, 2, "ОШИБКИ", "0")
        self.lbl_metric_eta = self._metric_tile(metrics, 3, "ОСТАЛОСЬ", "—")

        self.lbl_status = ctk.CTkLabel(
            status_card,
            text="Ожидание...",
            font=self._font_normal,
            text_color=self._muted_text(),
            anchor="w",
            justify="left",
            wraplength=760,
        )
        self.lbl_status.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 7))

        self.progress = ctk.CTkProgressBar(status_card, height=13, corner_radius=8)
        self.progress.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 13))
        self.progress.set(0)
        self.progress.configure(progress_color=UI.PRIMARY, fg_color="#22304a")
        ToolTip(
            self.progress,
            "Прогресс",
            "Общий прогресс по строкам. При больших файлах обновление может приходить пакетами.",
        )

        log_card = ctk.CTkFrame(
            self.content,
            corner_radius=16,
            fg_color=self._card_bg(),
            border_width=1,
            border_color=self._border_color(),
        )
        log_card.grid(row=1, column=0, sticky="nsew")
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(log_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            title_row,
            text="Журнал",
            font=self._font_card,
            text_color=self._strong_text(),
        ).pack(side="left")
        self._add_info(
            title_row,
            "Журнал",
            "Показывает процесс, найденные строки, retry-диагностику, ошибки и служебные сообщения.",
        )
        btn_open = ctk.CTkButton(
            header,
            text="📜 Файл",
            width=90,
            height=26,
            corner_radius=8,
            fg_color=self._button_subtle(),
            hover_color=self._button_subtle_hover(),
            text_color="#e8efff",
            command=self._open_log_file,
        )
        btn_open.grid(row=0, column=1, sticky="e")
        ToolTip(btn_open, "Открыть файл лога", "Открывает mineai_log.txt в системном приложении по умолчанию.")

        self.textbox = ctk.CTkTextbox(
            log_card,
            font=("Consolas", 12),
            wrap="none",
            corner_radius=12,
            fg_color=self._log_bg(),
            text_color="#dbe4f5",
            border_width=1,
            border_color=self._border_color(),
        )
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        for tag, color in [
            ("green", "#2ecc71"),
            ("lime", "#7bed9f"),
            ("yellow", "#f1c40f"),
            ("gold", "#ffd700"),
            ("orange", "#ff9f43"),
            ("red", "#ff4d4d"),
            ("pink", "#ff6b81"),
            ("cyan", "#00e5ff"),
            ("blue", "#54a0ff"),
            ("magenta", "#b000ff"),
            ("dim", "#7f8c8d"),
            ("gray", "#b2bec3"),
            ("white", "#ffffff"),
        ]:
            self.textbox.tag_config(tag, foreground=color)
        self.textbox.bind("<Key>", self._prevent_typing)
        inner = getattr(self.textbox, "_textbox", self.textbox)
        inner.bind("<Key>", self._fix_ctrl_copy, add="+")
        self.textbox.bind("<Button-1>", lambda _e: self._on_scroll_interaction())
        self.textbox.bind("<MouseWheel>", lambda _e: self._on_scroll_interaction())

    # =========================
    # UI HELPERS
    # =========================

    def _metric_tile(self, parent, column: int, title: str, value: str):
        tile = ctk.CTkFrame(
            parent,
            corner_radius=11,
            fg_color=UI.CARD_ALT_BG,
            border_width=1,
            border_color=self._border_color(),
        )
        tile.grid(row=0, column=column, sticky="ew", padx=3)
        ctk.CTkLabel(
            tile,
            text=title,
            font=("Segoe UI", 10, "bold"),
            text_color=self._muted_text(),
        ).pack(anchor="w", padx=10, pady=(7, 0))
        label = ctk.CTkLabel(
            tile,
            text=value,
            font=("Segoe UI", 16, "bold"),
            text_color=self._strong_text(),
        )
        label.pack(anchor="w", padx=10, pady=(0, 7))
        return label

    def _make_card(self, parent, title: str, tip_title: str | None = None, tip_text: str | None = None):
        card = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=self._card_bg(),
            border_width=1,
            border_color=self._border_color(),
        )
        card.pack(fill="x", padx=12, pady=7)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            header,
            text=title,
            font=self._font_card,
            text_color=self._strong_text(),
        ).pack(side="left")

        if tip_text:
            self._add_info(header, tip_title or title, tip_text)

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=14, pady=(6, 12))

        return body

    def _field_label(self, parent, text: str, tip_title: str | None = None, tip_text: str | None = None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(
            row,
            text=text,
            font=self._font_small,
            text_color=self._muted_text(),
        ).pack(side="left")

        if tip_text:
            self._add_info(row, tip_title or text, tip_text)

        return row

    def _add_info(self, parent, title: str, text: str, side: str = "left", padx: tuple[int, int] = (6, 0)):
        mark = ctk.CTkLabel(
            parent,
            text="?",
            width=16,
            height=16,
            fg_color=self._info_bg(),
            text_color=self._info_text(),
            font=("Segoe UI", 10, "bold"),
        )
        mark.pack(side=side, padx=padx)

        try:
            mark.configure(cursor="hand2")
        except Exception:
            pass

        ToolTip(mark, title, text)
        return mark

    def _check_row(self, parent, text: str, variable, tip_title: str, tip_text: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=1)

        cb = ctk.CTkCheckBox(
            row,
            text=text,
            variable=variable,
            font=self._font_normal,
        )
        cb.pack(side="left")

        self._add_info(row, tip_title, tip_text)
        ToolTip(cb, tip_title, tip_text)

        return cb

    def _radio_row(
        self,
        parent,
        text: str,
        variable,
        value: str,
        command=None,
        tip_title: str | None = None,
        tip_text: str | None = None,
    ):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=1)

        rb = ctk.CTkRadioButton(
            row,
            text=text,
            variable=variable,
            value=value,
            command=command,
            font=self._font_normal,
        )
        rb.pack(side="left")

        if tip_text:
            self._add_info(row, tip_title or text, tip_text)
            ToolTip(rb, tip_title or text, tip_text)

        return rb

    def _is_ctrl_pressed(self) -> bool:
        """Надёжная проверка Ctrl на Windows — не зависит от раскладки."""
        if sys.platform == "win32":
            try:
                return bool(ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000)
            except Exception:
                return False
        return False

    def _prevent_typing(self, event):
        if event.state & 4 or self._is_ctrl_pressed():
            return None

        if event.keysym in ["Up", "Down", "Left", "Right", "Prior", "Next", "Home", "End"]:
            return None

        return "break"

    def _fix_ctrl_copy(self, event):
        ctrl = bool(event.state & 4)

        if sys.platform == "win32":
            try:
                ctrl = ctrl or bool(ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000)
            except Exception:
                pass

        if not ctrl:
            return None

        KEY_ACTIONS = {67: "<<Copy>>", 65: "<<SelectAll>>"}

        if event.keycode in KEY_ACTIONS:
            event.widget.event_generate(KEY_ACTIONS[event.keycode])
            return "break"

        return None
