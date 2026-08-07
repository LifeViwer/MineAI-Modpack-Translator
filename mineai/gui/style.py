"""Shared visual primitives for the MineAI CustomTkinter interface."""

from __future__ import annotations

import customtkinter as ctk


class UI:
    APP_BG = ("#e8edf5", "#070b14")
    SIDEBAR_BG = ("#eef2f7", "#0a0f1b")
    CARD_BG = ("#ffffff", "#0f1626")
    CARD_ALT_BG = ("#f7f9fc", "#111b2e")
    BORDER = ("#d9e0ea", "#223049")
    STRONG_TEXT = ("#111827", "#eef2ff")
    MUTED_TEXT = ("#5b6472", "#93a4bd")
    INFO_BG = ("#e5edff", "#182b47")
    INFO_TEXT = ("#2b5db2", "#7db4ff")
    LOG_BG = "#0b1020"

    SUBTLE = "#233047"
    SUBTLE_HOVER = "#2d3c58"
    PRIMARY = "#2f81f7"
    PRIMARY_HOVER = "#1f6fd4"
    SUCCESS = "#28a745"
    SUCCESS_HOVER = "#218838"
    WARNING = "#ffc107"
    WARNING_HOVER = "#e0a800"
    DANGER = "#dc3545"
    DANGER_HOVER = "#c82333"
    CYAN = "#17a2b8"
    CYAN_HOVER = "#138496"


class ToolTip(ctk.CTkToplevel):
    """Accessible tooltip with keyboard focus support and screen-aware placement."""

    def __init__(self, widget, title: str, text: str, delay_ms: int = 300) -> None:
        self._tip_widget = widget
        self._after_id = None
        self._delay_ms = delay_ms

        parent = getattr(widget, "master", None) or getattr(widget, "_parent", None)
        super().__init__(master=parent)

        self.configure(
            fg_color="#0b1220",
            corner_radius=12,
            border_width=1,
            border_color="#2b3a55",
        )
        try:
            self.overrideredirect(True)
            self.attributes("-topmost", True)
        except Exception:
            pass
        self.withdraw()

        ctk.CTkLabel(
            self,
            text=title,
            anchor="w",
            justify="left",
            font=("Segoe UI", 12, "bold"),
            text_color="#e8efff",
        ).pack(anchor="w", padx=11, pady=(9, 1))
        ctk.CTkLabel(
            self,
            text=text,
            anchor="w",
            justify="left",
            wraplength=300,
            font=("Segoe UI", 11),
            text_color="#b7c6e0",
        ).pack(anchor="w", padx=11, pady=(0, 9))

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<FocusIn>", self._schedule, add="+")
        widget.bind("<FocusOut>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._hide()
        try:
            self._after_id = self._tip_widget.after(self._delay_ms, self._show)
        except Exception:
            self._after_id = None

    def _show(self) -> None:
        try:
            if not self._tip_widget.winfo_exists():
                return

            self.update_idletasks()
            tip_w = max(self.winfo_reqwidth(), 220)
            tip_h = max(self.winfo_reqheight(), 48)
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()

            widget_x = self._tip_widget.winfo_rootx()
            widget_y = self._tip_widget.winfo_rooty()
            widget_w = max(self._tip_widget.winfo_width(), 18)
            widget_h = max(self._tip_widget.winfo_height(), 18)

            x = widget_x + widget_w + 10
            y = widget_y + min(widget_h, 24) + 8

            if x + tip_w + 8 > screen_w:
                x = max(8, widget_x - tip_w - 10)
            if y + tip_h + 8 > screen_h:
                y = max(8, widget_y - tip_h - 8)

            x = max(8, min(x, screen_w - tip_w - 8))
            y = max(8, min(y, screen_h - tip_h - 8))
            self.geometry(f"+{x}+{y}")
            self.deiconify()
        except Exception:
            pass

    def _hide(self, _event=None) -> None:
        if self._after_id:
            try:
                self._tip_widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        try:
            self.withdraw()
        except Exception:
            pass
