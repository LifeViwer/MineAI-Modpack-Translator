"""Main-window sidebar section builder."""

import customtkinter as ctk

from mineai.gui.style import ToolTip


def build_sidebar_actions(self) -> None:
    # Режим обработки
    body = self._make_card(
        self.sidebar,
        "Режим обработки",
        tip_title="Режим обработки",
        tip_text="Append — доперевод, Skip — пропуск почти готового, Force — полный перевод заново.",
    )

    self.var_mode = ctk.StringVar(value=self._pref("process_mode", "append"))

    self._radio_row(
        body,
        "Доперевод (append)",
        self.var_mode,
        "append",
        tip_title="Append",
        tip_text="Переводит только новые или пустые строки. Существующие переводы сохраняются.",
    )

    self._radio_row(
        body,
        "Пропуск от 90% (skip)",
        self.var_mode,
        "skip",
        tip_title="Skip",
        tip_text="Если файл/сущность переведена на 90% и выше, она пропускается. Иначе работает как append.",
    )

    self._radio_row(
        body,
        "С нуля (force)",
        self.var_mode,
        "force",
        tip_title="Force",
        tip_text="Игнорирует существующий перевод и переводит заново. Используй для плохого машинного перевода.",
    )

    # Действия
    body = self._make_card(
        self.sidebar,
        "Действия",
        tip_title="Действия",
        tip_text="Основные команды: миграция готового перевода, анализ сборки, запуск перевода, пауза и остановка.",
    )

    self.btn_migrate = ctk.CTkButton(
        body,
        text="📦 Миграция ресурс-пака",
        height=32,
        corner_radius=10,
        fg_color="#17a2b8",
        hover_color="#138496",
        command=self._open_migration,
    )
    self.btn_migrate.pack(fill="x", pady=2)
    ToolTip(
        self.btn_migrate,
        "Миграция ресурс-пака",
        "Импортирует переводы из готового resource pack в кэш программы, чтобы не переводить эти строки заново.",
    )

    self.btn_analyze = ctk.CTkButton(
        body,
        text="🔍 Анализ сборки",
        height=32,
        corner_radius=10,
        fg_color="#0066cc",
        hover_color="#004c99",
        command=self._start_analysis,
    )
    self.btn_analyze.pack(fill="x", pady=2)
    ToolTip(
        self.btn_analyze,
        "Анализ сборки",
        "Сканирует моды, книги и квесты, показывая, сколько строк уже переведено и сколько осталось.",
    )

    self.btn_start = ctk.CTkButton(
        body,
        text="▶ НАЧАТЬ ПЕРЕВОД",
        height=44,
        corner_radius=12,
        fg_color="#28a745",
        hover_color="#218838",
        font=("Segoe UI", 14, "bold"),
        command=self._start_translation,
    )
    self.btn_start.pack(fill="x", pady=(8, 2))
    ToolTip(
        self.btn_start,
        "Начать перевод",
        "Запускает процесс перевода с выбранными настройками.",
    )

    self.btn_pause = ctk.CTkButton(
        body,
        text="⏸ ПАУЗА",
        height=36,
        corner_radius=12,
        fg_color="#ffc107",
        text_color="black",
        hover_color="#e0a800",
        command=self._toggle_pause,
        state="disabled",
    )
    self.btn_pause.pack(fill="x", pady=2)
    ToolTip(
        self.btn_pause,
        "Пауза",
        "Приостанавливает перевод. Повторное нажатие продолжает работу.",
    )

    self.btn_stop = ctk.CTkButton(
        body,
        text="⏹ ОСТАНОВИТЬ",
        height=36,
        corner_radius=12,
        fg_color="#dc3545",
        hover_color="#c82333",
        command=self._stop,
        state="disabled",
    )
    self.btn_stop.pack(fill="x", pady=2)
    ToolTip(
        self.btn_stop,
        "Остановить",
        "Останавливает текущий перевод или анализ.",
    )

    self.btn_log = ctk.CTkButton(
        body,
        text="📜 Открыть лог",
        height=30,
        corner_radius=10,
        fg_color=self._button_subtle(),
        hover_color=self._button_subtle_hover(),
        text_color="#e8efff",
        command=self._open_log_file,
    )
    self.btn_log.pack(fill="x", pady=(8, 0))
    ToolTip(
        self.btn_log,
        "Открыть лог",
        "Открывает текстовый файл mineai_log.txt с полным журналом действий.",
    )
