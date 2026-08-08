from pathlib import Path

# --- log_model.py -----------------------------------------------------------
path = Path("mineai/gui_qt/log_model.py")
text = path.read_text(encoding="utf-8")

text = text.replace(
    "from dataclasses import dataclass\n",
    "from dataclasses import dataclass\nimport re\n",
    1,
)

anchor = '''@dataclass(frozen=True)\nclass LogEntry:\n    plain_text: str\n    level: str\n    category: str\n    segments: tuple[LogSegment, ...]\n\n\n'''
addition = '''@dataclass(frozen=True)\nclass TranslationParts:\n    left: str\n    separator: str\n    right: str\n    suffix: str = \"\"\n\n\ndef split_translation_message(message: str) -> TranslationParts | None:\n    \"\"\"Split the standard successful translation log without altering raw text.\"\"\"\n    separator = \" -> \" if \" -> \" in message else (\" → \" if \" → \" in message else \"\")\n    if not separator:\n        return None\n    left, _sep, right = message.partition(separator)\n    if not left or not right:\n        return None\n    suffix = \"\"\n    match = re.search(r\"( ×\\d+)$\", right)\n    if match:\n        suffix = match.group(1)\n        right = right[: -len(suffix)]\n    return TranslationParts(left=left, separator=separator, right=right, suffix=suffix)\n\n\n'''
if anchor not in text:
    raise SystemExit("log_model anchor not found")
text = text.replace(anchor, anchor + addition, 1)
path.write_text(text, encoding="utf-8")

# --- i18n.py ---------------------------------------------------------------
path = Path("mineai/gui_qt/i18n.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    '        "log.autoscroll": "Автопрокрутка",\n',
    '        "log.autoscroll": "Автопрокрутка",\n'
    '        "log.full_lines": "Полные строки",\n'
    '        "log.full_lines_tooltip": "Показывать длинные переводы полностью. По умолчанию журнал использует компактный адаптивный preview; файл лога всегда сохраняет полный текст.",\n',
    1,
)
text = text.replace(
    '        "log.autoscroll": "Auto-scroll",\n',
    '        "log.autoscroll": "Auto-scroll",\n'
    '        "log.full_lines": "Full lines",\n'
    '        "log.full_lines_tooltip": "Show long translations in full. By default the journal uses a compact adaptive preview; the log file always keeps the complete text.",\n',
    1,
)
path.write_text(text, encoding="utf-8")

# --- main_window.py ---------------------------------------------------------
path = Path("mineai/gui_qt/main_window.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from mineai.gui_qt.log_model import LogEntry, LogSegment, entry_from_message, matches_entry\n",
    "from mineai.gui_qt.log_model import LogEntry, LogSegment, entry_from_message, matches_entry, split_translation_message\n",
    1,
)

old = '''        self.signals.worker_finished.connect(self._worker_finished)\n        self.signals.worker_failed.connect(self._worker_failed)\n\n        self._build_ui()\n'''
new = '''        self.signals.worker_finished.connect(self._worker_finished)\n        self.signals.worker_failed.connect(self._worker_failed)\n\n        self._log_resize_timer = QTimer(self)\n        self._log_resize_timer.setSingleShot(True)\n        self._log_resize_timer.setInterval(120)\n        self._log_resize_timer.timeout.connect(self._render_log)\n\n        self._build_ui()\n'''
if old not in text:
    raise SystemExit("timer anchor not found")
text = text.replace(old, new, 1)

old = '''        self.log_autoscroll = QCheckBox(t("log.autoscroll"))\n        self.log_autoscroll.setChecked(True)\n\n        open_log = QPushButton(t("button.open_log"))\n'''
new = '''        self.log_autoscroll = QCheckBox(t("log.autoscroll"))\n        self.log_autoscroll.setChecked(True)\n\n        self.log_full_lines = QCheckBox(t("log.full_lines"))\n        self.log_full_lines.setChecked(False)\n        self.log_full_lines.setToolTip(t("log.full_lines_tooltip"))\n        self.log_full_lines.toggled.connect(self._render_log)\n\n        open_log = QPushButton(t("button.open_log"))\n'''
if old not in text:
    raise SystemExit("full lines control anchor not found")
text = text.replace(old, new, 1)

old = '''        log_actions = QHBoxLayout()\n        log_actions.setSpacing(7)\n        log_actions.addStretch(1)\n        log_actions.addWidget(open_log)\n        log_actions.addWidget(clear)\n        log_actions.addWidget(save)\n        toolbar.addLayout(log_actions, 1, 0, 1, 3)\n'''
new = '''        log_actions = QHBoxLayout()\n        log_actions.setSpacing(7)\n        log_actions.addWidget(self.log_full_lines)\n        log_actions.addStretch(1)\n        log_actions.addWidget(open_log)\n        log_actions.addWidget(clear)\n        log_actions.addWidget(save)\n        toolbar.addLayout(log_actions, 1, 0, 1, 3)\n'''
if old not in text:
    raise SystemExit("toolbar anchor not found")
text = text.replace(old, new, 1)

old = '''    def resizeEvent(self, event) -> None:\n        super().resizeEvent(event)\n        if hasattr(self, "status_grid") and hasattr(self, "task_metrics_grid"):\n            self._apply_responsive_layout(event.size().width())\n'''
new = '''    def resizeEvent(self, event) -> None:\n        super().resizeEvent(event)\n        if hasattr(self, "status_grid") and hasattr(self, "task_metrics_grid"):\n            self._apply_responsive_layout(event.size().width())\n        if (\n            hasattr(self, "_log_resize_timer")\n            and hasattr(self, "log_view")\n            and hasattr(self, "log_full_lines")\n            and not self.log_full_lines.isChecked()\n        ):\n            self._log_resize_timer.start()\n'''
if old not in text:
    raise SystemExit("resizeEvent anchor not found")
text = text.replace(old, new, 1)

old = '''    def _append_entry_to_view(self, entry: LogEntry, *, allow_scroll: bool = True) -> None:\n        cursor = self.log_view.textCursor()\n        cursor.movePosition(QTextCursor.MoveOperation.End)\n        if not self.log_view.document().isEmpty():\n            cursor.insertBlock()\n        for segment in entry.segments:\n            fmt = QTextCharFormat()\n            fmt.setForeground(QColor(segment.color))\n            fmt.setFontFamily("Cascadia Mono")\n            cursor.insertText(segment.text, fmt)\n        self.log_view.setTextCursor(cursor)\n        if allow_scroll and self.log_autoscroll.isChecked():\n            bar = self.log_view.verticalScrollBar()\n            bar.setValue(bar.maximum())\n'''
new = '''    def _display_segments_for_entry(self, entry: LogEntry) -> tuple[LogSegment, ...]:\n        \"\"\"Return a compact pixel-aware preview without mutating the raw log entry.\"\"\"\n        if (\n            entry.category != "translated"\n            or not hasattr(self, "log_full_lines")\n            or self.log_full_lines.isChecked()\n            or len(entry.segments) != 1\n        ):\n            return entry.segments\n\n        parts = split_translation_message(entry.plain_text)\n        if parts is None:\n            return entry.segments\n\n        metrics = self.log_view.fontMetrics()\n        available = max(320, self.log_view.viewport().width() - 24)\n        if metrics.horizontalAdvance(entry.plain_text) <= available:\n            return entry.segments\n\n        separator_width = metrics.horizontalAdvance(parts.separator + parts.suffix)\n        content_width = max(160, available - separator_width)\n        left_width = max(120, int(content_width * 0.44))\n        right_width = max(120, content_width - left_width)\n        left = metrics.elidedText(parts.left, Qt.TextElideMode.ElideRight, left_width)\n        right = metrics.elidedText(parts.right, Qt.TextElideMode.ElideRight, right_width)\n        preview = f"{left}{parts.separator}{right}{parts.suffix}"\n        return (LogSegment(preview, entry.segments[0].color),)\n\n    def _append_entry_to_view(self, entry: LogEntry, *, allow_scroll: bool = True) -> None:\n        cursor = self.log_view.textCursor()\n        cursor.movePosition(QTextCursor.MoveOperation.End)\n        if not self.log_view.document().isEmpty():\n            cursor.insertBlock()\n        for segment in self._display_segments_for_entry(entry):\n            fmt = QTextCharFormat()\n            fmt.setForeground(QColor(segment.color))\n            fmt.setFontFamily("Cascadia Mono")\n            cursor.insertText(segment.text, fmt)\n        self.log_view.setTextCursor(cursor)\n        if allow_scroll and self.log_autoscroll.isChecked():\n            bar = self.log_view.verticalScrollBar()\n            bar.setValue(bar.maximum())\n'''
if old not in text:
    raise SystemExit("append view anchor not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

# --- tests/test_qt_view_model.py ------------------------------------------
path = Path("tests/test_qt_view_model.py")
text = path.read_text(encoding="utf-8")
# No pure helper is added to view_model; keep this file unchanged.
path.write_text(text, encoding="utf-8")

# --- tests/test_log_model.py ----------------------------------------------
path = Path("tests/test_log_model.py")
if path.exists():
    text = path.read_text(encoding="utf-8")
else:
    text = '''import unittest\n\nfrom mineai.gui_qt.log_model import split_translation_message\n\n\nclass TranslationMessageSplitTests(unittest.TestCase):\n    def test_splits_long_translation_and_duplicate_suffix_without_data_loss(self):\n        source = \" > \" + \"source \" * 80\n        target = \"перевод \" * 90\n        message = f\"{source} -> {target} ×3\"\n        parts = split_translation_message(message)\n        self.assertIsNotNone(parts)\n        assert parts is not None\n        self.assertEqual(parts.left, source)\n        self.assertEqual(parts.separator, \" -> \")\n        self.assertEqual(parts.right, target)\n        self.assertEqual(parts.suffix, \" ×3\")\n        self.assertEqual(parts.left + parts.separator + parts.right + parts.suffix, message)\n\n    def test_non_translation_message_is_untouched(self):\n        self.assertIsNone(split_translation_message(\"Обычная строка журнала\"))\n\n\nif __name__ == \"__main__\":\n    unittest.main()\n'''
path.write_text(text, encoding="utf-8")

print("compact log preview patch applied")
