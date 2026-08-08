from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match in {path}, got {count}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "mineai/gui_qt/main_window.py",
    "from PyQt6.QtCore import QTimer, Qt, QUrl\n",
    "from PyQt6.QtCore import QTimer, Qt\n",
)
replace_once(
    "mineai/gui_qt/main_window.py",
    "from PyQt6.QtGui import QColor, QDesktopServices, QIcon, QPixmap, QTextCharFormat, QTextCursor, QTextOption\n",
    "from PyQt6.QtGui import QColor, QIcon, QPixmap, QTextCharFormat, QTextCursor, QTextOption\n",
)
replace_once(
    "mineai/gui_qt/main_window.py",
    '''        open_log = QToolButton()\n        clear = QToolButton()\n        save = QToolButton()\n        for button in (open_log, clear, save):\n            button.setObjectName("LogToolButton")\n            button.setFixedSize(34, 34)\n            button.setCursor(Qt.CursorShape.PointingHandCursor)\n        open_log.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))\n        clear.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))\n        save.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))\n        open_log.setToolTip(t("button.open_log"))\n        clear.setToolTip(t("button.clear"))\n        save.setToolTip(t("button.save"))\n        open_log.clicked.connect(self._open_log_file)\n        clear.clicked.connect(self._clear_log)\n        save.clicked.connect(self._save_log)\n''',
    '''        clear = QToolButton()\n        save = QToolButton()\n        for button in (clear, save):\n            button.setObjectName("LogToolButton")\n            button.setFixedSize(34, 34)\n            button.setCursor(Qt.CursorShape.PointingHandCursor)\n        clear.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))\n        save.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))\n        clear.setToolTip(t("button.clear"))\n        save.setToolTip(t("button.export_log"))\n        clear.clicked.connect(self._clear_log)\n        save.clicked.connect(self._save_log)\n''',
)
replace_once(
    "mineai/gui_qt/main_window.py",
    '''        log_actions.addStretch(1)\n        log_actions.addWidget(open_log)\n        log_actions.addWidget(clear)\n        log_actions.addWidget(save)\n''',
    '''        log_actions.addStretch(1)\n        log_actions.addWidget(clear)\n        log_actions.addWidget(save)\n''',
)
replace_once(
    "mineai/gui_qt/main_window.py",
    '''    def _open_log_file(self) -> None:\n        if self._log_file is not None:\n            try:\n                self._log_file.flush()\n            except OSError:\n                pass\n        QDesktopServices.openUrl(QUrl.fromLocalFile(str(LOG_PATH)))\n\n''',
    "",
)
replace_once(
    "mineai/gui_qt/main_window.py",
    '''        path, _ = QFileDialog.getSaveFileName(self, t("button.save"), "mineai_log_export.txt", "Text files (*.txt);;All files (*)")\n''',
    '''        path, _ = QFileDialog.getSaveFileName(self, t("button.export_log"), "mineai_log_export.txt", "Text files (*.txt);;All files (*)")\n''',
)

replace_once(
    "mineai/gui_qt/i18n.py",
    '''        "button.open_log": "Открыть лог",\n        "button.clear": "🗑  Очистить",\n        "button.save": "⇩  Сохранить",\n''',
    '''        "button.open_log": "Открыть лог",\n        "button.clear": "🗑  Очистить",\n        "button.save": "⇩  Сохранить",\n        "button.export_log": "Экспорт лога",\n''',
)
replace_once(
    "mineai/gui_qt/i18n.py",
    '''        "button.open_log": "Open log",\n        "button.clear": "🗑  Clear",\n        "button.save": "⇩  Save",\n''',
    '''        "button.open_log": "Open log",\n        "button.clear": "🗑  Clear",\n        "button.save": "⇩  Save",\n        "button.export_log": "Export log",\n''',
)

replace_once(
    "tests/test_qt_windows_ux.py",
    '''    def test_language_control_is_compact_toggle(self):\n''',
    '''    def test_log_toolbar_has_only_clear_and_export_actions(self):\n        window = TranslatorQtWindow()\n        try:\n            buttons = [\n                button for button in window.findChildren(QToolButton)\n                if button.objectName() == "LogToolButton"\n            ]\n            self.assertEqual(len(buttons), 2)\n            tooltips = {button.toolTip() for button in buttons}\n            self.assertIn("Экспорт лога" if window._ui_language == "ru" else "Export log", tooltips)\n            self.assertNotIn("Открыть лог", tooltips)\n            self.assertNotIn("Open log", tooltips)\n        finally:\n            window.close()\n\n    def test_language_control_is_compact_toggle(self):\n''',
)
