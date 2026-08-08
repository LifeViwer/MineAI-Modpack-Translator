from pathlib import Path

# Windows QPushButton size hints include text width. Ignore horizontal hints so
# the equal layout stretch really produces a 50/50 Actions row on every DPI.
path = Path("mineai/gui_qt/main_window.py")
text = path.read_text(encoding="utf-8")
old = "    QScrollArea,\n    QSpinBox,\n"
new = "    QScrollArea,\n    QSizePolicy,\n    QSpinBox,\n"
if old not in text:
    raise RuntimeError("main_window QSizePolicy import point not found")
text = text.replace(old, new, 1)
old = '''        for button in (self.analyze_button, self.start_button, self.pause_button, self.stop_button):\n            button.setFixedHeight(40)\n'''
new = '''        for button in (self.analyze_button, self.start_button, self.pause_button, self.stop_button):\n            button.setFixedHeight(40)\n            button.setMinimumWidth(0)\n            button.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)\n'''
if old not in text:
    raise RuntimeError("Actions button sizing block not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")

path = Path("tests/test_qt_view_model.py")
text = path.read_text(encoding="utf-8")
text = text.replace("from pathlib import Path\nfrom pathlib import Path\n", "from pathlib import Path\n")
old = "from mineai.gui_qt.view_model import compact_runtime_status, dashboard_columns, engine_readiness, format_duration, stats_from_snapshot"
new = "from mineai.gui_qt.view_model import compact_runtime_status, dashboard_columns, detected_source_roots, engine_readiness, format_duration, stats_from_snapshot"
if old in text:
    text = text.replace(old, new, 1)
elif "detected_source_roots" not in text.split("\n", 10)[0:10].__str__():
    raise RuntimeError("Could not add detected_source_roots import")
path.write_text(text, encoding="utf-8")

path = Path("tests/test_qt_ux_hardening.py")
text = path.read_text(encoding="utf-8")
old = '        self.assertIn("#EEF1F5", light)\n'
new = '        self.assertIn("#E4E8EE", light)\n        self.assertIn("QPushButton#PrimaryButton { background-color: #7652D6", light)\n'
if old not in text:
    raise RuntimeError("Old Light palette assertion not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("round2 followup applied")
