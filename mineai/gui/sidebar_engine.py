"""Main-window sidebar section builder."""

import customtkinter as ctk

from mineai.config import settings
from mineai.gui.style import ToolTip, UI


def build_sidebar_engine(self) -> None:
    # Движок перевода
    body = self._make_card(
        self.sidebar,
        "Движок перевода",
        tip_title="Движок перевода",
        tip_text="Google — быстро, DeepL — качественно при наличии ключа, ИИ — лучший вариант для лора, книг и квестов.",
    )

    self.var_engine = ctk.StringVar(value=self._pref("engine", "google"))

    self._radio_row(
        body,
        "Google Translate",
        self.var_engine,
        "google",
        command=self._update_engine_ui,
        tip_title="Google Translate",
        tip_text="Быстрый машинный перевод. Хорошо подходит для интерфейсов и больших объёмов текста.",
    )

    self._radio_row(
        body,
        "DeepL API",
        self.var_engine,
        "deepl",
        command=self._update_engine_ui,
        tip_title="DeepL API",
        tip_text="Более качественный машинный перевод. Требуется API-ключ DeepL.",
    )

    self._radio_row(
        body,
        "Нейросеть (ИИ)",
        self.var_engine,
        "ai",
        command=self._update_engine_ui,
        tip_title="Нейросеть (ИИ)",
        tip_text="Локальный KoboldCPP или облачный OpenRouter. Лучше всего подходит для книг, квестов и лора.",
    )

    self.frame_google = ctk.CTkFrame(body, fg_color="transparent")
    self.frame_ai = ctk.CTkFrame(body, fg_color="transparent")

    self.engine_status_bar = ctk.CTkFrame(
        body,
        corner_radius=10,
        fg_color=UI.CARD_ALT_BG,
        border_width=1,
        border_color=self._border_color(),
    )
    self.engine_status_bar.pack(fill="x", pady=(8, 2))
    self.engine_status_bar.grid_columnconfigure(0, weight=1)
    self.lbl_engine_status = ctk.CTkLabel(
        self.engine_status_bar,
        text="Проверка конфигурации...",
        anchor="w",
        font=self._font_small,
        text_color=self._muted_text(),
    )
    self.lbl_engine_status.grid(row=0, column=0, sticky="ew", padx=(10, 6), pady=7)
    self.btn_engine_settings = ctk.CTkButton(
        self.engine_status_bar,
        text="Настроить",
        width=88,
        height=25,
        corner_radius=8,
        fg_color=self._button_subtle(),
        hover_color=self._button_subtle_hover(),
        command=self._open_settings,
    )
    self.btn_engine_settings.grid(row=0, column=1, padx=(0, 7), pady=5)

    self.var_google_mode = ctk.StringVar(value=self._pref("google_mode", "single"))
    google_row = ctk.CTkFrame(self.frame_google, fg_color="transparent")
    google_row.pack(fill="x", pady=(6, 0))
    rb_single = ctk.CTkRadioButton(google_row, text="Построчно", variable=self.var_google_mode, value="single", font=self._font_small)
    rb_single.pack(side="left")
    self._add_info(google_row, "Построчно", "Каждая строка переводится отдельным запросом. Надёжнее, но чуть медленнее.")
    ToolTip(rb_single, "Построчно", "Надёжный режим: одна строка — один запрос.")
    rb_batch = ctk.CTkRadioButton(google_row, text="Пачками", variable=self.var_google_mode, value="batch", font=self._font_small)
    rb_batch.pack(side="left", padx=(12, 0))
    self._add_info(google_row, "Пачками", "Несколько строк объединяются в один запрос. Быстрее, но при ошибке пачка может быть повторена построчно.")
    ToolTip(rb_batch, "Пачками", "Быстрый режим: строки отправляются пакетами.")

    self.var_ai_provider = ctk.StringVar(value=settings.get("AI", "ai_provider") or "local")
    provider_row = ctk.CTkFrame(self.frame_ai, fg_color="transparent")
    provider_row.pack(fill="x", pady=(6, 0))
    ctk.CTkLabel(provider_row, text="Провайдер ИИ", font=self._font_small, text_color=self._muted_text()).pack(side="left")
    self._add_info(provider_row, "Провайдер ИИ", "Локальный KoboldCPP использует твою видеокарту/процессор. OpenRouter переводит через облачные модели.")
    self._radio_row(self.frame_ai, "Локально (KoboldCPP)", self.var_ai_provider, "local", command=self._update_engine_ui, tip_title="Локальный ИИ", tip_text="Программа может сама запустить koboldcpp.exe. Нужны exe-файл и модель .gguf. Полный контроль и приватность.")
    self._radio_row(self.frame_ai, "OpenRouter (облако)", self.var_ai_provider, "openrouter", command=self._update_engine_ui, tip_title="OpenRouter", tip_text="Облачные модели через API. Нужны API-ключ и ID модели, например qwen/qwen-2.5-72b-instruct.")

    mode_label_row = ctk.CTkFrame(self.frame_ai, fg_color="transparent")
    mode_label_row.pack(fill="x", pady=(8, 0))
    ctk.CTkLabel(mode_label_row, text="Режим ИИ", font=self._font_small, text_color=self._muted_text()).pack(side="left")
    self._add_info(mode_label_row, "Режим ИИ", "Стандартный — безопаснее. Контекст + лор — более литературный перевод, но требует более сильной модели.")
    self.var_ai_mode = ctk.StringVar(value=self._pref("ai_mode", "safe"))
    mode_row = ctk.CTkFrame(self.frame_ai, fg_color="transparent")
    mode_row.pack(fill="x", pady=(2, 0))
    rb_safe = ctk.CTkRadioButton(mode_row, text="Стандартный", variable=self.var_ai_mode, value="safe", font=self._font_small)
    rb_safe.pack(side="left")
    self._add_info(mode_row, "Стандартный режим", "Аккуратный перевод с жёсткой проверкой JSON, маркеров и плейсхолдеров.")
    ToolTip(rb_safe, "Стандартный режим", "Безопасный режим для большинства задач.")
    rb_context = ctk.CTkRadioButton(mode_row, text="Контекст + лор", variable=self.var_ai_mode, value="context", font=self._font_small)
    rb_context.pack(side="left", padx=(12, 0))
    self._add_info(mode_row, "Контекст + лор", "Более художественный перевод. Хорошо для книг и квестов, но может быть медленнее.")
    ToolTip(rb_context, "Контекст + лор", "Режим для лора, книг и сюжетного текста.")

    batch_label_row = ctk.CTkFrame(self.frame_ai, fg_color="transparent")
    batch_label_row.pack(fill="x", pady=(8, 0))
    self.lbl_batch = ctk.CTkLabel(batch_label_row, text="Размер пачки: 20 строк", font=self._font_small, text_color=self._muted_text())
    self.lbl_batch.pack(side="left")
    self._add_info(batch_label_row, "Размер пачки", "Сколько строк отправлять в один запрос ИИ. Чем больше, тем быстрее, но тем выше шанс ошибки модели.")
    self.slider_ai_batch = ctk.CTkSlider(self.frame_ai, from_=1, to=40, number_of_steps=39, height=16, command=lambda val: self.lbl_batch.configure(text=f"Размер пачки: {int(val)} строк"))
    self.slider_ai_batch.set(self._pref_int("ai_batch", 20, 1, 40))
    self.lbl_batch.configure(text=f"Размер пачки: {int(self.slider_ai_batch.get())} строк")
    self.slider_ai_batch.pack(fill="x", pady=(2, 0))
    ToolTip(self.slider_ai_batch, "Размер пачки ИИ", "Для слабых моделей ставь 5–10. Для сильных моделей можно 20–40.")

    try:
        fallback_val = settings.getboolean("AI", "fallback_google")
    except Exception:
        fallback_val = False
    self.var_ai_fallback = ctk.BooleanVar(value=fallback_val)
    fallback_row = ctk.CTkFrame(self.frame_ai, fg_color="transparent")
    fallback_row.pack(fill="x", pady=(8, 0))
    chk_fallback = ctk.CTkCheckBox(fallback_row, text="Переводить непереведенное через Google", variable=self.var_ai_fallback, font=self._font_small)
    chk_fallback.pack(side="left")
    self._add_info(fallback_row, "Google-подстраховка", "Если ИИ не смог перевести строку, программа попробует Google Translate для этой строки.")
    ToolTip(chk_fallback, "Google-подстраховка", "Полезно, чтобы не оставлять пустые или оригинальные строки после ошибок ИИ.")
