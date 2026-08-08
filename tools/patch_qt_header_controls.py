from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected snippet not found in {path}: {old[:120]!r}")
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one snippet in {path}, found {text.count(old)}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Settings no longer duplicates controls that now live in the top-right header.
replace_once(
    "mineai/gui_qt/dialogs.py",
    "from mineai.gui_qt.i18n import LANGUAGE_LABELS, t",
    "from mineai.gui_qt.i18n import t",
)

replace_once(
    "mineai/gui_qt/dialogs.py",
    '''        self.deepl_key = self._line_row(general_layout, t("settings.deepl"), config.get("API", "deepl_key"), secret=True)\n\n        general_layout.addWidget(self._field_label(t("settings.ui_language")))\n        self.ui_language = QComboBox()\n        for code, label in LANGUAGE_LABELS.items():\n            self.ui_language.addItem(label, code)\n        language_index = self.ui_language.findData(config.get("GENERAL", "ui_language"))\n        self.ui_language.setCurrentIndex(language_index if language_index >= 0 else 0)\n        general_layout.addWidget(self.ui_language)\n\n        general_layout.addWidget(self._field_label(t("settings.theme")))\n        self.theme = QComboBox()\n        self.theme.addItem(t("theme.dark"), "Dark")\n        self.theme.addItem(t("theme.light"), "Light")\n        theme_index = self.theme.findData(config.get("GENERAL", "theme"))\n        self.theme.setCurrentIndex(theme_index if theme_index >= 0 else 0)\n        general_layout.addWidget(self.theme)\n        general_layout.addStretch(1)\n''',
    '''        self.deepl_key = self._line_row(general_layout, t("settings.deepl"), config.get("API", "deepl_key"), secret=True)\n        general_layout.addStretch(1)\n''',
)

replace_once(
    "mineai/gui_qt/dialogs.py",
    '''        self.config.set_many("GENERAL", {\n            "smart_glue": self.smart_glue.isChecked(),\n            "google_workers": self.google_workers.value(),\n            "ui_language": self.ui_language.currentData() or "ru",\n            "theme": self.theme.currentData() or "Dark",\n        })\n''',
    '''        self.config.set_many("GENERAL", {\n            "smart_glue": self.smart_glue.isChecked(),\n            "google_workers": self.google_workers.value(),\n        })\n''',
)

# Localized header-control tooltips.
replace_once(
    "mineai/gui_qt/i18n.py",
    '        "header.migration": "⇄  Миграция",\n',
    '        "header.migration": "⇄  Миграция",\n'
    '        "header.language_tooltip": "Язык интерфейса",\n'
    '        "header.theme_to_light": "Переключить на светлую тему",\n'
    '        "header.theme_to_dark": "Переключить на тёмную тему",\n',
)
replace_once(
    "mineai/gui_qt/i18n.py",
    '        "header.migration": "⇄  Migration",\n',
    '        "header.migration": "⇄  Migration",\n'
    '        "header.language_tooltip": "Interface language",\n'
    '        "header.theme_to_light": "Switch to light theme",\n'
    '        "header.theme_to_dark": "Switch to dark theme",\n',
)

# Main window: compact right-side controls and responsive log toolbar.
replace_once(
    "mineai/gui_qt/main_window.py",
    "    QPushButton,\n    QScrollArea,",
    "    QPushButton,\n    QToolButton,\n    QScrollArea,",
)

replace_once(
    "mineai/gui_qt/main_window.py",
    '''        self.migration_button.clicked.connect(self._open_migration)\n        layout.addWidget(self.migration_button)\n        return header\n''',
    '''        self.migration_button.clicked.connect(self._open_migration)\n        layout.addWidget(self.migration_button)\n\n        layout.addSpacing(4)\n        self.interface_language = QComboBox()\n        self.interface_language.setObjectName("HeaderLanguageCombo")\n        self.interface_language.addItem("RU", "ru")\n        self.interface_language.addItem("EN", "en")\n        language_index = self.interface_language.findData(self._ui_language)\n        self.interface_language.setCurrentIndex(language_index if language_index >= 0 else 0)\n        self.interface_language.setFixedWidth(72)\n        self.interface_language.setToolTip(t("header.language_tooltip"))\n        self.interface_language.currentIndexChanged.connect(self._change_interface_language)\n        layout.addWidget(self.interface_language)\n\n        self.theme_button = QToolButton()\n        self.theme_button.setObjectName("ThemeToggle")\n        self.theme_button.setFixedSize(38, 36)\n        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)\n        self.theme_button.clicked.connect(self._toggle_theme)\n        layout.addWidget(self.theme_button)\n        self._refresh_theme_button()\n        return header\n''',
)

replace_once(
    "mineai/gui_qt/main_window.py",
    '''        toolbar = QHBoxLayout()\n        self.log_filter = QComboBox()\n''',
    '''        toolbar = QGridLayout()\n        toolbar.setHorizontalSpacing(8)\n        toolbar.setVerticalSpacing(7)\n        self.log_filter = QComboBox()\n''',
)

replace_once(
    "mineai/gui_qt/main_window.py",
    '''        toolbar.addWidget(self.log_filter)\n        toolbar.addWidget(self.log_search, 1)\n        toolbar.addWidget(self.log_autoscroll)\n        toolbar.addStretch(1)\n        toolbar.addWidget(open_log)\n        toolbar.addWidget(clear)\n        toolbar.addWidget(save)\n        card.body.addLayout(toolbar)\n''',
    '''        toolbar.addWidget(self.log_filter, 0, 0)\n        toolbar.addWidget(self.log_search, 0, 1)\n        toolbar.addWidget(self.log_autoscroll, 0, 2)\n        toolbar.setColumnStretch(1, 1)\n\n        log_actions = QHBoxLayout()\n        log_actions.setSpacing(7)\n        log_actions.addStretch(1)\n        log_actions.addWidget(open_log)\n        log_actions.addWidget(clear)\n        log_actions.addWidget(save)\n        toolbar.addLayout(log_actions, 1, 0, 1, 3)\n        card.body.addLayout(toolbar)\n''',
)

replace_once(
    "mineai/gui_qt/main_window.py",
    '''    def _after_settings_saved(self) -> None:\n        new_language = settings.get("GENERAL", "ui_language") or "ru"\n        new_theme = settings.get("GENERAL", "theme") or "Dark"\n        language_changed = new_language != self._ui_language\n        translator.set_language(new_language)\n        self._ui_language = translator.language\n        self._apply_theme(new_theme)\n        if language_changed:\n            QTimer.singleShot(0, self._rebuild_ui_for_locale)\n            return\n        self._refresh_engine_state()\n        self._refresh_system_readiness()\n        self._refresh_footer()\n''',
    '''    def _after_settings_saved(self) -> None:\n        self._refresh_engine_state()\n        self._refresh_system_readiness()\n        self._refresh_footer()\n\n    def _change_interface_language(self, _index: int) -> None:\n        code = self.interface_language.currentData() or "ru"\n        if code == self._ui_language:\n            return\n        if self._worker and self._worker.is_alive():\n            previous = self.interface_language.findData(self._ui_language)\n            if previous >= 0:\n                self.interface_language.blockSignals(True)\n                self.interface_language.setCurrentIndex(previous)\n                self.interface_language.blockSignals(False)\n            return\n        settings.set("GENERAL", "ui_language", code)\n        translator.set_language(code)\n        self._ui_language = translator.language\n        self.setWindowTitle(f"{t('app.title')} — {__version__}")\n        QTimer.singleShot(0, self._rebuild_ui_for_locale)\n\n    def _toggle_theme(self) -> None:\n        new_theme = "Light" if self._theme_name.casefold() == "dark" else "Dark"\n        settings.set("GENERAL", "theme", new_theme)\n        self._apply_theme(new_theme)\n\n    def _refresh_theme_button(self) -> None:\n        if not hasattr(self, "theme_button"):\n            return\n        is_light = self._theme_name.casefold() == "light"\n        self.theme_button.setText("☀" if is_light else "☾")\n        self.theme_button.setToolTip(\n            t("header.theme_to_dark") if is_light else t("header.theme_to_light")\n        )\n''',
)

replace_once(
    "mineai/gui_qt/main_window.py",
    '''            self.migration_button,\n            self.folder_button,\n''',
    '''            self.migration_button,\n            self.interface_language,\n            self.folder_button,\n''',
)

replace_once(
    "mineai/gui_qt/main_window.py",
    '''        if hasattr(self, "segmented_progress"):\n            self.segmented_progress.set_theme(self._theme_name)\n''',
    '''        if hasattr(self, "segmented_progress"):\n            self.segmented_progress.set_theme(self._theme_name)\n        self._refresh_theme_button()\n''',
)

replace_once(
    "mineai/gui_qt/main_window.py",
    '''    def _rebuild_ui_for_locale(self) -> None:\n        if self._worker and self._worker.is_alive():\n            return\n        state = self._capture_ui_state()\n''',
    '''    def _rebuild_ui_for_locale(self) -> None:\n        if self._worker and self._worker.is_alive():\n            return\n        self.setWindowTitle(f"{t('app.title')} — {__version__}")\n        state = self._capture_ui_state()\n''',
)

# Header controls styling for both palettes.
replace_once(
    "mineai/gui_qt/theme.py",
    '''QPushButton#HeaderButton:hover { background-color: #2B2D40; border-color: #555872; }\n''',
    '''QPushButton#HeaderButton:hover { background-color: #2B2D40; border-color: #555872; }\nQComboBox#HeaderLanguageCombo {\n    min-height: 34px; max-height: 34px; background-color: #202231; color: #E2E8F0;\n    border: 1px solid #393B50; border-radius: 8px; padding-left: 9px; padding-right: 22px; font-weight: 700;\n}\nQComboBox#HeaderLanguageCombo:hover { background-color: #2B2D40; border-color: #555872; }\nQComboBox#HeaderLanguageCombo::drop-down { width: 20px; }\nQToolButton#ThemeToggle {\n    background-color: #202231; color: #E2E8F0; border: 1px solid #393B50;\n    border-radius: 8px; padding: 0; font-family: "Segoe UI Symbol", "Segoe UI", sans-serif; font-size: 18px; font-weight: 700;\n}\nQToolButton#ThemeToggle:hover { background-color: #2B2D40; border-color: #8B6BE5; color: #FFFFFF; }\nQToolButton#ThemeToggle:pressed { background-color: #242536; }\n''',
)

replace_once(
    "mineai/gui_qt/theme.py",
    '''QPushButton#HeaderButton:hover { background-color: #E6E8EF; border-color: #B7BECC; }\n''',
    '''QPushButton#HeaderButton:hover { background-color: #E6E8EF; border-color: #B7BECC; }\nQComboBox#HeaderLanguageCombo { background-color: #F1F2F6; color: #272B37; border-color: #CDD2DD; }\nQComboBox#HeaderLanguageCombo:hover { background-color: #E6E8EF; border-color: #B7BECC; }\nQToolButton#ThemeToggle { background-color: #F1F2F6; color: #4B5568; border-color: #CDD2DD; }\nQToolButton#ThemeToggle:hover { background-color: #E6E8EF; border-color: #7655D0; color: #4D2C9B; }\n''',
)

print("Qt header-control review patch applied")
