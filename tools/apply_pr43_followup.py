from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match in {path}, got {count}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "mineai/gui_qt/dialogs.py",
    "from mineai.gui_qt.widgets import HelpMarker\n",
    "from mineai.gui_qt.widgets import HelpMarker, ScrollSafeSpinBox\n",
)
replace_once(
    "mineai/gui_qt/dialogs.py",
    "        spin = QSpinBox()\n",
    "        spin = ScrollSafeSpinBox()\n",
)

replace_once(
    "mineai/gui_qt/main_window.py",
    '''    def _append_entry_to_view(self, entry: LogEntry, *, allow_scroll: bool = True) -> None:\n        cursor = self.log_view.textCursor()\n        cursor.movePosition(QTextCursor.MoveOperation.End)\n        if not self.log_view.document().isEmpty():\n            cursor.insertBlock()\n        for segment in self._display_segments_for_entry(entry):\n            fmt = QTextCharFormat()\n            fmt.setForeground(QColor(segment.color))\n            fmt.setFontFamily("Cascadia Mono")\n            cursor.insertText(segment.text, fmt)\n        self.log_view.setTextCursor(cursor)\n        if allow_scroll and self.log_autoscroll.isChecked():\n            bar = self.log_view.verticalScrollBar()\n            bar.setValue(bar.maximum())\n''',
    '''    def _append_entry_to_view(self, entry: LogEntry, *, allow_scroll: bool = True) -> None:\n        bar = self.log_view.verticalScrollBar()\n        preserve_scroll = allow_scroll and not self.log_autoscroll.isChecked()\n        previous_scroll = bar.value() if preserve_scroll else None\n\n        # Insert through a document cursor instead of moving the editor's visible\n        # cursor to the end. setTextCursor() scrolls QPlainTextEdit to that cursor\n        # even when the Autoscroll checkbox is disabled.\n        cursor = QTextCursor(self.log_view.document())\n        cursor.movePosition(QTextCursor.MoveOperation.End)\n        if not self.log_view.document().isEmpty():\n            cursor.insertBlock()\n        for segment in self._display_segments_for_entry(entry):\n            fmt = QTextCharFormat()\n            fmt.setForeground(QColor(segment.color))\n            fmt.setFontFamily("Cascadia Mono")\n            cursor.insertText(segment.text, fmt)\n\n        if allow_scroll and self.log_autoscroll.isChecked():\n            bar.setValue(bar.maximum())\n        elif previous_scroll is not None:\n            bar.setValue(min(previous_scroll, bar.maximum()))\n''',
)

replace_once(
    "tests/test_qt_windows_ux.py",
    "    from mineai.gui_qt.main_window import TranslatorQtWindow\n    from mineai.gui_qt.widgets import ScrollSafeComboBox, ScrollSafeSpinBox\n",
    "    from mineai.config import settings\n    from mineai.gui_qt.dialogs import SettingsDialog\n    from mineai.gui_qt.log_model import entry_from_message\n    from mineai.gui_qt.main_window import TranslatorQtWindow\n    from mineai.gui_qt.widgets import ScrollSafeComboBox, ScrollSafeSpinBox\n",
)
replace_once(
    "tests/test_qt_windows_ux.py",
    "    TranslatorQtWindow = None\n    ScrollSafeComboBox = None\n    ScrollSafeSpinBox = None\n",
    "    settings = None\n    SettingsDialog = None\n    entry_from_message = None\n    TranslatorQtWindow = None\n    ScrollSafeComboBox = None\n    ScrollSafeSpinBox = None\n",
)
replace_once(
    "tests/test_qt_windows_ux.py",
    '''    def test_spinbox_ignores_wheel(self):\n        spin = ScrollSafeSpinBox()\n        event = _FakeWheelEvent()\n        spin.wheelEvent(event)\n        self.assertTrue(event.ignored)\n\n''',
    '''    def test_spinbox_ignores_wheel(self):\n        spin = ScrollSafeSpinBox()\n        event = _FakeWheelEvent()\n        spin.wheelEvent(event)\n        self.assertTrue(event.ignored)\n\n    def test_settings_numeric_fields_use_scroll_safe_spinbox(self):\n        dialog = SettingsDialog(settings, lambda: None)\n        try:\n            self.assertIsInstance(dialog.ai_retries, ScrollSafeSpinBox)\n            self.assertIsInstance(dialog.google_workers, ScrollSafeSpinBox)\n        finally:\n            dialog.close()\n\n    def test_log_autoscroll_checkbox_preserves_manual_scroll_position(self):\n        window = TranslatorQtWindow()\n        try:\n            window.resize(1240, 760)\n            window.show()\n            self.app.processEvents()\n            for index in range(250):\n                window.log_view.appendPlainText(f"existing line {index}")\n            self.app.processEvents()\n            bar = window.log_view.verticalScrollBar()\n            self.assertGreater(bar.maximum(), 0)\n\n            window.log_autoscroll.setChecked(False)\n            manual_position = max(0, bar.maximum() // 3)\n            bar.setValue(manual_position)\n            self.app.processEvents()\n            window._append_entry_to_view(\n                entry_from_message("white", "new line while autoscroll is disabled", "#E2E8F0")\n            )\n            self.app.processEvents()\n            self.assertEqual(bar.value(), manual_position)\n\n            window.log_autoscroll.setChecked(True)\n            window._append_entry_to_view(\n                entry_from_message("white", "new line while autoscroll is enabled", "#E2E8F0")\n            )\n            self.app.processEvents()\n            self.assertEqual(bar.value(), bar.maximum())\n        finally:\n            window.close()\n\n''',
)
