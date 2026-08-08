from pathlib import Path

main = Path("mineai/gui_qt/main_window.py")
text = main.read_text(encoding="utf-8")
text = text.replace(
    "from mineai.gui_qt.i18n import t, translator\n",
    "from mineai.gui_qt.i18n import t, translator\nfrom mineai.gui_qt.i18n_runtime import tr as rt\n",
    1,
)
text = text.replace(
    "        self.engine_combo = QComboBox()\n        self.engine_combo.addItems(list(ENGINE_OPTIONS.keys()))\n",
    "        self.engine_combo = QComboBox()\n        self.engine_combo.addItems([\"Google\", \"DeepL\", rt(\"engine.local\"), \"OpenRouter\"])\n",
    1,
)
text = text.replace("self.mode_group = QButtonGroup(self)", "self.mode_group = QButtonGroup(card)", 1)
text = text.replace("self.output_group = QButtonGroup(self)", "self.output_group = QButtonGroup(card)", 1)
text = text.replace(
    '        self.kpi_success.meta.setText(f"{stats.success_percent:.1f}% от обработанных" if stats.processed else "—")\n',
    '        self.kpi_success.meta.setText(rt("stats.processed_share", percent=stats.success_percent) if stats.processed else "—")\n',
    1,
)
text = text.replace(
    '        self.kpi_errors.meta.setText(f"{stats.error_percent:.1f}% от обработанных" if stats.processed else "—")\n',
    '        self.kpi_errors.meta.setText(rt("stats.processed_share", percent=stats.error_percent) if stats.processed else "—")\n',
    1,
)
text = text.replace(
    '        self.kpi_eta.value.setText(stats.eta_text if snapshot.is_running else ("готово" if stats.total and stats.remaining_lines == 0 else "—"))\n',
    '        self.kpi_eta.value.setText(stats.eta_text if snapshot.is_running else (rt("stats.done") if stats.total and stats.remaining_lines == 0 else "—"))\n',
    1,
)
text = text.replace(
    '        self.kpi_eta.meta.setText(f"≈ {stats.remaining_lines:,} строк".replace(",", " ") if stats.total else "—")\n',
    '        remaining_text = f"{stats.remaining_lines:,}".replace(",", " ")\n        self.kpi_eta.meta.setText(rt("stats.remaining_lines", count=remaining_text) if stats.total else "—")\n',
    1,
)
text = text.replace(
    '        self.task_speed.value.setText(f"{stats.lines_per_minute:.0f} строк/мин" if stats.lines_per_minute else "—")\n',
    '        self.task_speed.value.setText(rt("stats.rate", rate=stats.lines_per_minute) if stats.lines_per_minute else "—")\n',
    1,
)
text = text.replace(
    '            "engine": self.engine_combo.currentText(),\n',
    '            "engine_spec": ENGINE_OPTIONS.get(self.engine_combo.currentText(), ("google", "local")),\n',
    1,
)
old = '        self.engine_combo.setCurrentText(str(state["engine"]))\n'
new = '''        engine_spec = tuple(state["engine_spec"])
        for index in range(self.engine_combo.count()):
            label = self.engine_combo.itemText(index)
            if ENGINE_OPTIONS.get(label) == engine_spec:
                self.engine_combo.setCurrentIndex(index)
                break
'''
if old not in text:
    raise RuntimeError("engine restore line not found")
text = text.replace(old, new, 1)
main.write_text(text, encoding="utf-8")

# Finish the remaining Migration browse localization.
dialogs = Path("mineai/gui_qt/dialogs.py")
d = dialogs.read_text(encoding="utf-8")
d = d.replace(
    'QFileDialog.getOpenFileName(self, "Resource Pack", "", "ZIP Archives (*.zip)")',
    'QFileDialog.getOpenFileName(self, t("migration.resource_pack"), self.zip_edit.text(), "ZIP Archives (*.zip)")',
    1,
)
dialogs.write_text(d, encoding="utf-8")
print("final locale fixes applied")
