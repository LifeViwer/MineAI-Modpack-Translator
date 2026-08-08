import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication, QToolButton

from mineai.gui_qt.main_window import TranslatorQtWindow
from mineai.gui_qt.theme import theme_qss

app = QApplication.instance() or QApplication([])
window = TranslatorQtWindow()
window.show()
app.processEvents()

assert isinstance(window.interface_language, QToolButton)
assert window.interface_language.width() == 46
assert window.analyze_button.height() == window.start_button.height() == window.pause_button.height() == window.stop_button.height()
assert abs(window.analyze_button.width() - window.start_button.width()) <= 2

window.engine_combo.setCurrentText("Google")
window._rebuild_ui_for_locale()
app.processEvents()
assert not window.google_options.isHidden()
assert window.ai_options.isHidden()

ai_index = next(i for i in range(window.engine_combo.count()) if window.engine_combo.itemText(i) in ("Локальный ИИ", "Local AI"))
window.engine_combo.setCurrentIndex(ai_index)
window._rebuild_ui_for_locale()
app.processEvents()
assert window.google_options.isHidden()
assert not window.ai_options.isHidden()

light = theme_qss("Light")
assert "QPushButton#PrimaryButton { background-color: #7652D6" in light
assert "QSpinBox::up-button, QSpinBox::down-button" in light
assert "QToolButton#HeaderLanguageToggle" in light
assert "QWidget {\n    background-color: #12131C;" not in light

log_tools = [w for w in window.findChildren(QToolButton) if w.objectName() == "LogToolButton"]
assert len(log_tools) == 3

window.close()
print("qt round2 smoke PASS")
