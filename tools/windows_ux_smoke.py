from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication

from mineai.gui_qt.main_window import TranslatorQtWindow
from mineai.gui_qt.theme import theme_qss
from mineai.gui_qt.widgets import ScrollSafeComboBox, ScrollSafeSpinBox


class FakeWheel:
    def __init__(self) -> None:
        self.ignored = False

    def ignore(self) -> None:
        self.ignored = True


def assert_visible_inside(window, widget, label: str) -> None:
    if not widget.isVisible() or widget.visibleRegion().isEmpty():
        return
    top_left = widget.mapTo(window, widget.rect().topLeft())
    bottom_right = widget.mapTo(window, widget.rect().bottomRight())
    assert top_left.x() >= 0 and top_left.y() >= 0, (label, top_left)
    assert bottom_right.x() < window.width(), (label, bottom_right.x(), window.width())
    assert bottom_right.y() < window.height(), (label, bottom_right.y(), window.height())


app = QApplication.instance() or QApplication([])
window = TranslatorQtWindow()
window.resize(1240, 760)
window.show()
app.processEvents()

for name in (
    "settings_button",
    "prompts_button",
    "migration_button",
    "interface_language",
    "theme_button",
    "analyze_button",
    "start_button",
    "pause_button",
    "stop_button",
):
    assert_visible_inside(window, getattr(window, name), name)

heights = {
    window.analyze_button.height(),
    window.start_button.height(),
    window.pause_button.height(),
    window.stop_button.height(),
}
assert heights == {40}, heights
assert not window.folder_button.icon().isNull()

for control in (
    window.version_combo,
    window.language_combo,
    window.engine_combo,
    window.google_mode_combo,
    window.ai_mode_combo,
    window.log_filter,
):
    assert isinstance(control, ScrollSafeComboBox)
    event = FakeWheel()
    control.wheelEvent(event)
    assert event.ignored
assert isinstance(window.ai_batch_spin, ScrollSafeSpinBox)
event = FakeWheel()
window.ai_batch_spin.wheelEvent(event)
assert event.ignored

window._refresh_runtime_dashboard()
app.processEvents()
assert not window.task_percent.isVisible()
assert not window.segmented_progress.isVisible()
assert len(window._task_metrics) == 2

window.job_state.start()
window.job_state.set_total_strings(100)
window.job_state.begin_progress()
window.job_state.start_time = time.time() - 125
window.job_state.increment_translated(20)
window._runtime_ended_at = time.time()
window.job_state.finish()
window._refresh_runtime_dashboard()
first = window.task_elapsed.value.text()
time.sleep(0.08)
window._refresh_runtime_dashboard()
second = window.task_elapsed.value.text()
assert first == second, (first, second)

light = theme_qss("Light")
assert "#EEF1F5" in light
assert "QFrame#Card { background-color: #F8F9FC" in light

for size in ((1366, 768), (1520, 940), (1240, 760)):
    window.resize(*size)
    app.processEvents()
    for name in ("interface_language", "theme_button", "start_button", "stop_button"):
        assert_visible_inside(window, getattr(window, name), f"{name}@{size}")

window.close()
app.processEvents()
print("Windows UX Qt smoke: PASS")
