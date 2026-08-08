import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from mineai.gui_qt.main_window import TranslatorQtWindow


app = QApplication.instance() or QApplication([])
window = TranslatorQtWindow()
window.resize(1240, 760)
window.show()
app.processEvents()
window._clear_log()

source = " > " + ("Alakarkinos can shift sand and gravel to find items in archaeological sites. " * 10)
target = "Алакаркинос может перемещать песок и гравий, находя предметы на археологических участках. " * 10
message = f"{source} -> {target}"
window._append_log(message, "dim")
app.processEvents()

assert window._log_entries[-1].plain_text == message
assert window.log_view.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
compact_1240 = window.log_view.toPlainText()
assert "…" in compact_1240, compact_1240
assert compact_1240 != message
assert len(compact_1240) < len(message) // 2

window.resize(1520, 940)
app.processEvents()
window._log_resize_timer.timeout.emit()
app.processEvents()
compact_1520 = window.log_view.toPlainText()
assert "…" in compact_1520
assert len(compact_1520) >= len(compact_1240)
assert window._log_entries[-1].plain_text == message

window.log_full_lines.setChecked(True)
app.processEvents()
full = window.log_view.toPlainText()
assert full == message
assert "Алакаркинос" in full

window.log_full_lines.setChecked(False)
app.processEvents()
assert "…" in window.log_view.toPlainText()
assert window._log_entries[-1].plain_text == message

window.close()
app.processEvents()
print("compact log preview smoke: PASS")
