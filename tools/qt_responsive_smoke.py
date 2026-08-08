import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QPlainTextEdit

from mineai.gui_qt.main_window import TranslatorQtWindow


def grid_positions(grid, widgets):
    positions = []
    for widget in widgets:
        index = grid.indexOf(widget)
        row, column, row_span, column_span = grid.getItemPosition(index)
        positions.append((row, column, row_span, column_span))
    return positions


app = QApplication.instance() or QApplication([])
window = TranslatorQtWindow()
window.show()

long_line = (
    "This is a deliberately long translation log line that must visually wrap "
    "inside the journal viewport when the window becomes narrower instead of "
    "requiring a horizontal scrollbar."
)
window._append_log(long_line, "dim")

for width, height, expected_columns in (
    (1240, 760, 2),
    (1366, 768, 2),
    (1520, 940, 4),
):
    window.resize(width, height)
    app.processEvents()

    assert window.log_view.lineWrapMode() == QPlainTextEdit.LineWrapMode.WidgetWidth
    assert window.log_view.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert long_line in window.log_view.toPlainText()

    status_positions = grid_positions(window.status_grid, window._status_cards)
    task_positions = grid_positions(window.task_metrics_grid, window._task_metrics)
    used_status_columns = {column for _row, column, _rs, _cs in status_positions}
    used_task_columns = {column for _row, column, _rs, _cs in task_positions}
    assert len(used_status_columns) == expected_columns, (width, status_positions)
    assert len(used_task_columns) == expected_columns, (width, task_positions)

    if expected_columns == 2:
        assert max(row for row, _column, _rs, _cs in status_positions) == 1
        assert max(row for row, _column, _rs, _cs in task_positions) == 1
    else:
        assert {row for row, _column, _rs, _cs in status_positions} == {0}
        assert {row for row, _column, _rs, _cs in task_positions} == {0}

window.close()
app.processEvents()
print("responsive Qt smoke PASS")
