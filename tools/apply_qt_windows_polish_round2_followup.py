from pathlib import Path

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
print("round2 followup applied")
