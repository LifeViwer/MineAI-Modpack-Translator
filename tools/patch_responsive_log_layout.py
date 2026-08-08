from pathlib import Path

main_path = Path("mineai/gui_qt/main_window.py")
main = main_path.read_text(encoding="utf-8")

main = main.replace(
    "from PyQt6.QtGui import QColor, QDesktopServices, QIcon, QPixmap, QTextCharFormat, QTextCursor\n",
    "from PyQt6.QtGui import QColor, QDesktopServices, QIcon, QPixmap, QTextCharFormat, QTextCursor, QTextOption\n",
    1,
)
main = main.replace(
    "from mineai.gui_qt.view_model import ENGINE_OPTIONS, engine_readiness, format_duration, stats_from_snapshot\n",
    "from mineai.gui_qt.view_model import ENGINE_OPTIONS, dashboard_columns, engine_readiness, format_duration, stats_from_snapshot\n",
    1,
)
main = main.replace(
    "        outer.addWidget(body, 1)\n        outer.addWidget(self._build_footer())\n",
    "        outer.addWidget(body, 1)\n        outer.addWidget(self._build_footer())\n        self._apply_responsive_layout(self.width())\n",
    1,
)

old_status = '''        grid = QGridLayout()\n        grid.setHorizontalSpacing(12)\n        self.kpi_processed = StatCard(t("kpi.processed"), "KpiBlue")\n'''
new_status = '''        self.status_grid = QGridLayout()\n        self.status_grid.setHorizontalSpacing(12)\n        self.status_grid.setVerticalSpacing(12)\n        self.kpi_processed = StatCard(t("kpi.processed"), "KpiBlue")\n'''
if old_status not in main:
    raise SystemExit("status grid anchor not found")
main = main.replace(old_status, new_status, 1)
main = main.replace(
    '''        for col, widget in enumerate((self.kpi_processed, self.kpi_success, self.kpi_errors, self.kpi_eta)):\n            grid.addWidget(widget, 0, col)\n            grid.setColumnStretch(col, 1)\n        card.body.addLayout(grid)\n''',
    '''        self._status_cards = (self.kpi_processed, self.kpi_success, self.kpi_errors, self.kpi_eta)\n        for col, widget in enumerate(self._status_cards):\n            self.status_grid.addWidget(widget, 0, col)\n            self.status_grid.setColumnStretch(col, 1)\n        card.body.addLayout(self.status_grid)\n''',
    1,
)

old_metrics = '''        metrics = QHBoxLayout()\n        metrics.setSpacing(18)\n        self.task_lines = LabeledValue(t("task.line"))\n        self.task_speed = LabeledValue(t("task.speed"))\n        self.task_elapsed = LabeledValue(t("task.elapsed"))\n        self.task_remaining = LabeledValue(t("task.remaining"))\n        for widget in (self.task_lines, self.task_speed, self.task_elapsed, self.task_remaining):\n            metrics.addWidget(widget)\n        metrics.addStretch(1)\n        card.body.addLayout(metrics)\n'''
new_metrics = '''        self.task_metrics_grid = QGridLayout()\n        self.task_metrics_grid.setHorizontalSpacing(18)\n        self.task_metrics_grid.setVerticalSpacing(8)\n        self.task_lines = LabeledValue(t("task.line"))\n        self.task_speed = LabeledValue(t("task.speed"))\n        self.task_elapsed = LabeledValue(t("task.elapsed"))\n        self.task_remaining = LabeledValue(t("task.remaining"))\n        self._task_metrics = (self.task_lines, self.task_speed, self.task_elapsed, self.task_remaining)\n        for col, widget in enumerate(self._task_metrics):\n            self.task_metrics_grid.addWidget(widget, 0, col)\n            self.task_metrics_grid.setColumnStretch(col, 1)\n        card.body.addLayout(self.task_metrics_grid)\n'''
if old_metrics not in main:
    raise SystemExit("task metrics anchor not found")
main = main.replace(old_metrics, new_metrics, 1)

old_log = '''        self.log_view.setUndoRedoEnabled(False)\n        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)\n        self.log_view.document().setMaximumBlockCount(MAX_LOG_BLOCKS)\n'''
new_log = '''        self.log_view.setUndoRedoEnabled(False)\n        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)\n        self.log_view.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)\n        self.log_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)\n        self.log_view.document().setMaximumBlockCount(MAX_LOG_BLOCKS)\n'''
if old_log not in main:
    raise SystemExit("log wrap anchor not found")
main = main.replace(old_log, new_log, 1)

insert_anchor = '''    def _build_footer(self) -> QWidget:\n'''
responsive_methods = '''    def resizeEvent(self, event) -> None:\n        super().resizeEvent(event)\n        if hasattr(self, "status_grid") and hasattr(self, "task_metrics_grid"):\n            self._apply_responsive_layout(event.size().width())\n\n    @staticmethod\n    def _place_grid_widgets(grid: QGridLayout, widgets: tuple[QWidget, ...], columns: int) -> None:\n        while grid.count():\n            grid.takeAt(0)\n        for column in range(4):\n            grid.setColumnStretch(column, 0)\n        for index, widget in enumerate(widgets):\n            row, column = divmod(index, columns)\n            grid.addWidget(widget, row, column)\n            grid.setColumnStretch(column, 1)\n\n    def _apply_responsive_layout(self, width: int) -> None:\n        columns = dashboard_columns(width)\n        if getattr(self, "_responsive_columns", None) == columns:\n            return\n        self._place_grid_widgets(self.status_grid, self._status_cards, columns)\n        self._place_grid_widgets(self.task_metrics_grid, self._task_metrics, columns)\n        self._responsive_columns = columns\n\n'''
if insert_anchor not in main:
    raise SystemExit("footer insertion anchor not found")
main = main.replace(insert_anchor, responsive_methods + insert_anchor, 1)
main_path.write_text(main, encoding="utf-8")

view_path = Path("mineai/gui_qt/view_model.py")
view = view_path.read_text(encoding="utf-8")
anchor = '''ENGINE_OPTIONS = {\n'''
addition = '''COMPACT_DASHBOARD_WIDTH = 1420\n\n\ndef dashboard_columns(window_width: int) -> int:\n    """Return a safe dashboard column count for the current top-level width."""\n    return 2 if int(window_width) < COMPACT_DASHBOARD_WIDTH else 4\n\n\n'''
if addition not in view:
    if anchor not in view:
        raise SystemExit("view-model anchor not found")
    view = view.replace(anchor, addition + anchor, 1)
view_path.write_text(view, encoding="utf-8")

test_path = Path("tests/test_qt_view_model.py")
tests = test_path.read_text(encoding="utf-8")
tests = tests.replace(
    "from mineai.gui_qt.view_model import engine_readiness, format_duration, stats_from_snapshot\n",
    "from mineai.gui_qt.view_model import dashboard_columns, engine_readiness, format_duration, stats_from_snapshot\n",
    1,
)
class_anchor = '''class DashboardStatsTests(unittest.TestCase):\n'''
test_block = '''class ResponsiveLayoutTests(unittest.TestCase):\n    def test_dashboard_switches_to_two_columns_on_narrow_windows(self):\n        self.assertEqual(dashboard_columns(1240), 2)\n        self.assertEqual(dashboard_columns(1366), 2)\n        self.assertEqual(dashboard_columns(1419), 2)\n\n    def test_dashboard_keeps_four_columns_when_space_is_available(self):\n        self.assertEqual(dashboard_columns(1420), 4)\n        self.assertEqual(dashboard_columns(1520), 4)\n\n\n'''
if test_block not in tests:
    if class_anchor not in tests:
        raise SystemExit("test class anchor not found")
    tests = tests.replace(class_anchor, test_block + class_anchor, 1)
test_path.write_text(tests, encoding="utf-8")

print("responsive log/layout patch applied")
