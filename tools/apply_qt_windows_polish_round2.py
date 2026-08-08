from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# ---- main_window.py -------------------------------------------------------
path = "mineai/gui_qt/main_window.py"
replace_once(
    path,
    'from mineai.gui_qt.view_model import ENGINE_OPTIONS, compact_runtime_status, dashboard_columns, engine_readiness, format_duration, stats_from_snapshot\n',
    'from mineai.gui_qt.view_model import ENGINE_OPTIONS, compact_runtime_status, dashboard_columns, detected_source_roots, engine_readiness, format_duration, stats_from_snapshot\n',
)
replace_once(
    path,
    '        self._runtime_ended_at: float | None = None\n        self._log_entries: list[LogEntry] = []\n',
    '        self._runtime_ended_at: float | None = None\n        self._task_detail = ""\n        self._log_entries: list[LogEntry] = []\n',
)
replace_once(
    path,
    '''        layout.addSpacing(4)\n        self.interface_language = ScrollSafeComboBox()\n        self.interface_language.setObjectName("HeaderLanguageCombo")\n        self.interface_language.addItem("RU", "ru")\n        self.interface_language.addItem("EN", "en")\n        language_index = self.interface_language.findData(self._ui_language)\n        self.interface_language.setCurrentIndex(language_index if language_index >= 0 else 0)\n        self.interface_language.setFixedWidth(58)\n        self.interface_language.setToolTip(t("header.language_tooltip"))\n        self.interface_language.currentIndexChanged.connect(self._change_interface_language)\n        layout.addWidget(self.interface_language)\n''',
    '''        layout.addSpacing(4)\n        self.interface_language = QToolButton()\n        self.interface_language.setObjectName("HeaderLanguageToggle")\n        self.interface_language.setFixedSize(46, 36)\n        self.interface_language.setCursor(Qt.CursorShape.PointingHandCursor)\n        self.interface_language.clicked.connect(self._toggle_interface_language)\n        layout.addWidget(self.interface_language)\n        self._refresh_language_button()\n''',
)
replace_once(
    path,
    '''        host_layout = QVBoxLayout(host)\n        host_layout.setContentsMargins(0, 0, 0, 0)\n        host_layout.setSpacing(0)\n''',
    '''        host_layout = QVBoxLayout(host)\n        host_layout.setContentsMargins(0, 0, 4, 0)\n        host_layout.setSpacing(10)\n''',
)
replace_once(
    path,
    '        layout.setContentsMargins(0, 0, 4, 0)\n',
    '        layout.setContentsMargins(0, 0, 0, 0)\n',
)
replace_once(
    path,
    '''        action_row.addWidget(self.analyze_button)\n        action_row.addWidget(self.start_button, 1)\n''',
    '''        action_row.addWidget(self.analyze_button, 1)\n        action_row.addWidget(self.start_button, 1)\n''',
)
replace_once(
    path,
    '''        open_log = QPushButton(t("button.open_log"))\n        clear = QPushButton(t("button.clear"))\n        save = QPushButton(t("button.save"))\n        open_log.clicked.connect(self._open_log_file)\n        clear.clicked.connect(self._clear_log)\n        save.clicked.connect(self._save_log)\n\n        toolbar.addWidget(self.log_filter, 0, 0)\n        toolbar.addWidget(self.log_search, 0, 1)\n        toolbar.addWidget(self.log_autoscroll, 0, 2)\n        toolbar.setColumnStretch(1, 1)\n\n        log_actions = QHBoxLayout()\n        log_actions.setSpacing(7)\n        log_actions.addWidget(self.log_full_lines)\n        log_actions.addStretch(1)\n        log_actions.addWidget(open_log)\n        log_actions.addWidget(clear)\n        log_actions.addWidget(save)\n        toolbar.addLayout(log_actions, 1, 0, 1, 3)\n''',
    '''        open_log = QToolButton()\n        clear = QToolButton()\n        save = QToolButton()\n        for button in (open_log, clear, save):\n            button.setObjectName("LogToolButton")\n            button.setFixedSize(34, 34)\n            button.setCursor(Qt.CursorShape.PointingHandCursor)\n        open_log.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))\n        clear.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))\n        save.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))\n        open_log.setToolTip(t("button.open_log"))\n        clear.setToolTip(t("button.clear"))\n        save.setToolTip(t("button.save"))\n        open_log.clicked.connect(self._open_log_file)\n        clear.clicked.connect(self._clear_log)\n        save.clicked.connect(self._save_log)\n\n        toolbar.addWidget(self.log_filter, 0, 0)\n        toolbar.addWidget(self.log_search, 0, 1)\n        toolbar.setColumnStretch(1, 1)\n\n        log_actions = QHBoxLayout()\n        log_actions.setSpacing(10)\n        log_actions.addWidget(self.log_autoscroll)\n        log_actions.addWidget(self.log_full_lines)\n        log_actions.addStretch(1)\n        log_actions.addWidget(open_log)\n        log_actions.addWidget(clear)\n        log_actions.addWidget(save)\n        toolbar.addLayout(log_actions, 1, 0, 1, 2)\n''',
)
replace_once(
    path,
    '''                markers = []\n                if (root / "mods").is_dir():\n                    markers.append("mods/ ✓")\n                if (root / "config").is_dir():\n                    markers.append("config/ ✓")\n                suffix = "   " + "   ".join(markers) if markers else ""\n''',
    '''                markers = [f"{name}/ ✓" for name in detected_source_roots(root)]\n                suffix = "   " + "   ".join(markers) if markers else ""\n''',
)
replace_once(
    path,
    '''    def _change_interface_language(self, _index: int) -> None:\n        code = self.interface_language.currentData() or "ru"\n        if code == self._ui_language:\n            return\n        if self._worker and self._worker.is_alive():\n            previous = self.interface_language.findData(self._ui_language)\n            if previous >= 0:\n                self.interface_language.blockSignals(True)\n                self.interface_language.setCurrentIndex(previous)\n                self.interface_language.blockSignals(False)\n            return\n        settings.set("GENERAL", "ui_language", code)\n        translator.set_language(code)\n        self._ui_language = translator.language\n        self.setWindowTitle(f"{t('app.title')} — {__version__}")\n        QTimer.singleShot(0, self._rebuild_ui_for_locale)\n''',
    '''    def _refresh_language_button(self) -> None:\n        if not hasattr(self, "interface_language"):\n            return\n        is_ru = self._ui_language == "ru"\n        self.interface_language.setText("RU" if is_ru else "EN")\n        target = "English" if is_ru else "Русский"\n        self.interface_language.setToolTip(f"{t('header.language_tooltip')} → {target}")\n\n    def _toggle_interface_language(self) -> None:\n        if self._worker and self._worker.is_alive():\n            return\n        code = "en" if self._ui_language == "ru" else "ru"\n        settings.set("GENERAL", "ui_language", code)\n        translator.set_language(code)\n        self._ui_language = translator.language\n        self.setWindowTitle(f"{t('app.title')} — {__version__}")\n        QTimer.singleShot(0, self._rebuild_ui_for_locale)\n''',
)
replace_once(
    path,
    '''    def _set_status(self, text: str, progress) -> None:\n        compact = compact_runtime_status(text)\n        snapshot = self.job_state.snapshot()\n        generated_metrics = "Осталось:" in str(text) and " | " in str(text)\n        if compact:\n            display_text = compact\n        elif generated_metrics:\n            display_text = t("task.running") if snapshot.is_running else self.task_status.fullText()\n        else:\n            display_text = str(text)\n        self.task_status.setText(display_text)\n        self.task_status.setToolTip(str(text) if str(text) != display_text else display_text)\n''',
    '''    def _set_status(self, text: str, progress) -> None:\n        snapshot = self.job_state.snapshot()\n        generated_metrics = "Осталось:" in str(text) and " | " in str(text)\n        if generated_metrics:\n            self._task_detail = compact_runtime_status(text)\n            display_text = ""\n        else:\n            self._task_detail = ""\n            display_text = str(text)\n        self.task_status.setText(display_text)\n        self.task_status.setVisible(bool(display_text))\n        self.task_status.setToolTip(str(text) if str(text) != display_text else display_text)\n''',
)
replace_once(
    path,
    '''        if snapshot.total_files > 0:\n            self.task_title.setText(f"{snapshot.current_file_type} · {snapshot.current_file_done}/{snapshot.total_files}")\n''',
    '''        if snapshot.total_files > 0:\n            title = f"{snapshot.current_file_type} · {snapshot.current_file_done}/{snapshot.total_files}"\n            if self._task_detail:\n                title += f": {self._task_detail}"\n            self.task_title.setText(title)\n''',
)
replace_once(
    path,
    '''        for index in range(self.engine_combo.count()):\n            label = self.engine_combo.itemText(index)\n            if ENGINE_OPTIONS.get(label) == engine_spec:\n                self.engine_combo.setCurrentIndex(index)\n                break\n        google_index = self.google_mode_combo.findData(state["google_mode"])\n''',
    '''        for index in range(self.engine_combo.count()):\n            label = self.engine_combo.itemText(index)\n            if ENGINE_OPTIONS.get(label) == engine_spec:\n                self.engine_combo.setCurrentIndex(index)\n                break\n        # setCurrentIndex() does not emit when the restored index is already 0.\n        # Synchronize dependent option panels explicitly after every locale rebuild.\n        self._engine_changed(self.engine_combo.currentText())\n        google_index = self.google_mode_combo.findData(state["google_mode"])\n''',
)

# ---- view_model.py --------------------------------------------------------
path = "mineai/gui_qt/view_model.py"
replace_once(
    path,
    '''def dashboard_columns(window_width: int) -> int:\n    """Return a safe dashboard column count for the current top-level width."""\n    return 2 if int(window_width) < COMPACT_DASHBOARD_WIDTH else 4\n\n\nENGINE_OPTIONS = {\n''',
    '''def dashboard_columns(window_width: int) -> int:\n    """Return a safe dashboard column count for the current top-level width."""\n    return 2 if int(window_width) < COMPACT_DASHBOARD_WIDTH else 4\n\n\ndef detected_source_roots(mc_dir: str | Path) -> tuple[str, ...]:\n    """Return supported top-level source folders that actually exist."""\n    root = Path(mc_dir)\n    return tuple(name for name in ("mods", "config", "kubejs", "defaultconfigs") if (root / name).is_dir())\n\n\nENGINE_OPTIONS = {\n''',
)

# ---- theme.py -------------------------------------------------------------
path = "mineai/gui_qt/theme.py"
replace_once(
    path,
    '''QWidget {\n    background-color: #12131C;\n    color: #E2E8F0;\n    font-family: "Segoe UI", "Inter", sans-serif;\n    font-size: 13px;\n}\nQMainWindow, QDialog { background-color: #12131C; }\nQLabel, QCheckBox, QRadioButton { background-color: transparent; border: none; }\nQWidget#AppRoot, QWidget#DashboardBody, QWidget#SidebarHost, QWidget#SidebarContent, QWidget#SidebarViewport { background-color: #12131C; border: none; }\n''',
    '''QWidget {\n    color: #E2E8F0;\n    font-family: "Segoe UI", "Inter", sans-serif;\n    font-size: 13px;\n}\nQMainWindow, QDialog, QWidget#AppRoot, QWidget#DashboardBody, QWidget#SidebarHost, QWidget#SidebarContent, QWidget#SidebarViewport { background-color: #12131C; border: none; }\nQLabel, QCheckBox, QRadioButton { background-color: transparent; border: none; }\n''',
)
replace_once(
    path,
    'QFrame#SidebarActions { background-color: #171824; border: none; border-top: 1px solid #2B2C3D; }\n',
    'QFrame#SidebarActions { background-color: #1E1F2E; border: 1px solid #2B2C3D; border-radius: 10px; }\n',
)
replace_once(
    path,
    '''QComboBox#HeaderLanguageCombo {\n    min-height: 34px; max-height: 34px; background-color: #202231; color: #E2E8F0;\n    border: 1px solid #393B50; border-radius: 8px; padding-left: 9px; padding-right: 22px; font-weight: 700;\n}\nQComboBox#HeaderLanguageCombo:hover { background-color: #2B2D40; border-color: #555872; }\nQComboBox#HeaderLanguageCombo::drop-down { width: 20px; }\n''',
    '''QToolButton#HeaderLanguageToggle {\n    background-color: #202231; color: #E2E8F0; border: 1px solid #393B50;\n    border-radius: 8px; padding: 0; font-weight: 700;\n}\nQToolButton#HeaderLanguageToggle:hover { background-color: #2B2D40; border-color: #8B6BE5; color: #FFFFFF; }\n''',
)
replace_once(
    path,
    'QToolButton#FolderButton:hover { background-color: #33354A; border-color: #4B4E66; }\n',
    '''QToolButton#FolderButton:hover { background-color: #33354A; border-color: #4B4E66; }\nQToolButton#LogToolButton { background-color: #202231; color: #E2E8F0; border: 1px solid #393B50; border-radius: 8px; padding: 0; }\nQToolButton#LogToolButton:hover { background-color: #2B2D40; border-color: #8B6BE5; }\n''',
)
replace_once(
    path,
    '''QLineEdit:hover, QComboBox:hover, QSpinBox:hover { border-color: #4A4D64; }\nQLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #8B6BE5; }\n''',
    '''QLineEdit:hover, QComboBox:hover, QSpinBox:hover { border-color: #4A4D64; }\nQLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #8B6BE5; }\nQSpinBox { padding-right: 34px; }\nQSpinBox::up-button, QSpinBox::down-button { width: 30px; background-color: #202231; border-left: 1px solid #393B50; }\nQSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; border-top-right-radius: 7px; border-bottom: 1px solid #393B50; }\nQSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; border-bottom-right-radius: 7px; }\nQSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #2B2D40; }\n''',
)
replace_once(
    path,
    '''QWidget { background-color: #EEF1F5; color: #283142; }\nQMainWindow, QDialog { background-color: #EEF1F5; }\nQWidget#AppRoot, QWidget#SidebarHost, QWidget#SidebarContent, QWidget#SidebarViewport, QWidget#DashboardBody { background-color: #EEF1F5; }\nQScrollArea#Sidebar { background-color: #EEF1F5; }\nQFrame#SidebarActions { background-color: #F3F5F8; border-color: #D7DBE4; }\n''',
    '''QWidget { color: #2D3442; }\nQMainWindow, QDialog { background-color: #E4E8EE; }\nQWidget#AppRoot, QWidget#SidebarHost, QWidget#SidebarContent, QWidget#SidebarViewport, QWidget#DashboardBody { background-color: #E4E8EE; }\nQScrollArea#Sidebar { background-color: #E4E8EE; }\nQFrame#SidebarActions { background-color: #EFF2F6; border-color: #C9D0DA; }\n''',
)
replace_once(path, 'QFrame#Header, QFrame#Footer { background-color: #F6F7FA; border-color: #D7DBE4; }\n', 'QFrame#Header, QFrame#Footer { background-color: #E9EDF3; border-color: #C9D0DA; }\n')
replace_once(path, 'QFrame#Card { background-color: #F8F9FC; border-color: #D7DBE4; }\n', 'QFrame#Card { background-color: #EFF2F6; border-color: #C9D0DA; }\n')
replace_once(path, 'QFrame#InnerCard { background-color: #F3F5F8; border-color: #D7DBE4; }\n', 'QFrame#InnerCard { background-color: #E9EDF3; border-color: #CDD3DD; }\n')
replace_once(path, 'QLineEdit, QComboBox, QSpinBox { background-color: #F4F6F9; color: #283142; border-color: #C8CED8; selection-background-color: #6B46C1; }\n', 'QLineEdit, QComboBox, QSpinBox { background-color: #E9EDF3; color: #283142; border-color: #BFC7D2; selection-background-color: #6B46C1; }\n')
replace_once(
    path,
    '''QComboBox#HeaderLanguageCombo { background-color: #F1F2F6; color: #272B37; border-color: #CDD2DD; }\nQComboBox#HeaderLanguageCombo:hover { background-color: #E6E8EF; border-color: #B7BECC; }\n''',
    '''QToolButton#HeaderLanguageToggle { background-color: #E5E9F0; color: #272B37; border-color: #BFC7D2; }\nQToolButton#HeaderLanguageToggle:hover { background-color: #DCE1E9; border-color: #7655D0; color: #4D2C9B; }\n''',
)
replace_once(
    path,
    'QToolButton#FolderButton:hover { background-color: #E1E4EC; border-color: #B6BDCB; }\n',
    '''QToolButton#FolderButton:hover { background-color: #DCE1E9; border-color: #AEB7C5; }\nQToolButton#LogToolButton { background-color: #E5E9F0; color: #374151; border-color: #BFC7D2; }\nQToolButton#LogToolButton:hover { background-color: #DCE1E9; border-color: #7655D0; }\nQPushButton#PrimaryButton { background-color: #7652D6; color: #FFFFFF; border-color: #6845C5; }\nQPushButton#PrimaryButton:hover { background-color: #6845C5; border-color: #5B39B5; }\nQPushButton#WarningButton { background-color: #F7EAC7; color: #77520A; border-color: #D8B65B; }\nQPushButton#WarningButton:hover { background-color: #F0DDA8; border-color: #C89D34; }\nQPushButton#DangerButton { background-color: #F6DFE4; color: #A83249; border-color: #D99AA8; }\nQPushButton#DangerButton:hover { background-color: #EFCFD6; border-color: #C97C8E; }\nQSpinBox::up-button, QSpinBox::down-button { background-color: #DDE2E9; border-left-color: #BFC7D2; }\nQSpinBox::up-button { border-bottom-color: #BFC7D2; }\nQSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #D1D7E0; }\n''',
)
replace_once(path, 'QPlainTextEdit#LogView, QPlainTextEdit { background-color: #FAFBFD; color: #263142; border-color: #D9DDE7; }\n', 'QPlainTextEdit#LogView, QPlainTextEdit { background-color: #E9EDF3; color: #263142; border-color: #C9D0DA; }\n')

# ---- tests ---------------------------------------------------------------
path = "tests/test_qt_view_model.py"
text = Path(path).read_text(encoding="utf-8")
text = text.replace(
    'from mineai.gui_qt.view_model import ',
    'from mineai.gui_qt.view_model import ',
    1,
)
# Add source-root regression test without depending on the exact import layout.
if 'detected_source_roots' not in text:
    text = text.replace('import tempfile\n', 'import tempfile\nfrom pathlib import Path\n')
    text = text.replace('from mineai.gui_qt.view_model import (', 'from mineai.gui_qt.view_model import (\n    detected_source_roots,')
    marker = '\n\nif __name__ == "__main__":\n'
    test = '''\n\nclass SourceRootDetectionTests(unittest.TestCase):\n    def test_detects_all_supported_top_level_sources(self):\n        with tempfile.TemporaryDirectory() as tmp:\n            root = Path(tmp)\n            for name in ("mods", "config", "kubejs", "defaultconfigs"):\n                (root / name).mkdir()\n            self.assertEqual(\n                detected_source_roots(root),\n                ("mods", "config", "kubejs", "defaultconfigs"),\n            )\n'''
    if marker not in text:
        raise RuntimeError('test_qt_view_model.py marker missing')
    text = text.replace(marker, test + marker, 1)
    Path(path).write_text(text, encoding="utf-8")

path = "tests/test_qt_windows_ux.py"
text = Path(path).read_text(encoding="utf-8")
text = text.replace(
    '    from PyQt6.QtWidgets import QApplication\n    from mineai.gui_qt.widgets import ScrollSafeComboBox, ScrollSafeSpinBox\n',
    '    from PyQt6.QtWidgets import QApplication, QToolButton\n    from mineai.gui_qt.main_window import TranslatorQtWindow\n    from mineai.gui_qt.widgets import ScrollSafeComboBox, ScrollSafeSpinBox\n',
)
text = text.replace(
    '    QApplication = None\n    ScrollSafeComboBox = None\n',
    '    QApplication = None\n    QToolButton = None\n    TranslatorQtWindow = None\n    ScrollSafeComboBox = None\n',
)
insert = '''\n    def test_locale_rebuild_keeps_google_and_ai_panels_synchronized(self):\n        window = TranslatorQtWindow()\n        try:\n            window.engine_combo.setCurrentText("Google")\n            window._rebuild_ui_for_locale()\n            self.assertFalse(window.google_options.isHidden())\n            self.assertTrue(window.ai_options.isHidden())\n\n            ai_index = next(\n                i for i in range(window.engine_combo.count())\n                if window.engine_combo.itemText(i) in ("Локальный ИИ", "Local AI")\n            )\n            window.engine_combo.setCurrentIndex(ai_index)\n            window._rebuild_ui_for_locale()\n            self.assertTrue(window.google_options.isHidden())\n            self.assertFalse(window.ai_options.isHidden())\n        finally:\n            window.close()\n\n    def test_language_control_is_compact_toggle(self):\n        window = TranslatorQtWindow()\n        try:\n            self.assertIsInstance(window.interface_language, QToolButton)\n            self.assertIn(window.interface_language.text(), {"RU", "EN"})\n            self.assertEqual(window.interface_language.width(), 46)\n        finally:\n            window.close()\n'''
needle = '    def test_spinbox_ignores_wheel(self):\n        spin = ScrollSafeSpinBox()\n        event = _FakeWheelEvent()\n        spin.wheelEvent(event)\n        self.assertTrue(event.ignored)\n'
if insert.strip() not in text:
    if needle not in text:
        raise RuntimeError('test_qt_windows_ux.py insertion point missing')
    text = text.replace(needle, needle + insert, 1)
Path(path).write_text(text, encoding="utf-8")

print("round2 Qt Windows polish patch applied")
