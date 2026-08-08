from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


main = "mineai/gui_qt/main_window.py"
replace_once(
    main,
    '''    def _set_status(self, text: str, progress) -> None:\n        compact = compact_runtime_status(text)\n        snapshot = self.job_state.snapshot()\n        display_text = compact or (t("task.running") if snapshot.is_running else str(text))\n        self.task_status.setText(display_text)\n''',
    '''    def _set_status(self, text: str, progress) -> None:\n        compact = compact_runtime_status(text)\n        snapshot = self.job_state.snapshot()\n        generated_metrics = "Осталось:" in str(text) and " | " in str(text)\n        if compact:\n            display_text = compact\n        elif generated_metrics:\n            display_text = t("task.running") if snapshot.is_running else self.task_status.fullText()\n        else:\n            display_text = str(text)\n        self.task_status.setText(display_text)\n''',
)
replace_once(
    main,
    '''        total_text = f"{stats.processed:,} / {stats.total:,}".replace(",", " ") if stats.total else "—"\n        self.kpi_processed.value.setText(total_text)\n        self.kpi_processed.meta.setText(f"{stats.percent:.1f}%")\n        self.kpi_processed.progress.setValue(int(stats.percent * 10))\n\n        self.kpi_success.value.setText(f"{stats.successful:,}".replace(",", " "))\n        self.kpi_success.meta.setText(rt("stats.processed_share", percent=stats.success_percent) if stats.processed else "—")\n        self.kpi_success.progress.setValue(int(stats.success_percent * 10))\n\n        self.kpi_errors.value.setText(str(stats.failed))\n        self.kpi_errors.meta.setText(rt("stats.processed_share", percent=stats.error_percent) if stats.processed else "—")\n        self.kpi_errors.progress.setValue(int(stats.error_percent * 10))\n\n        self.kpi_eta.value.setText(stats.eta_text if snapshot.is_running else (rt("stats.done") if stats.total and stats.remaining_lines == 0 else "—"))\n        remaining_text = f"{stats.remaining_lines:,}".replace(",", " ")\n        self.kpi_eta.meta.setText(rt("stats.remaining_lines", count=remaining_text) if stats.total else "—")\n        self.kpi_eta.progress.setValue(int(stats.percent * 10) if stats.total else 0)\n''',
    '''        if stats.total:\n            total_text = f"{stats.processed:,} / {stats.total:,}".replace(",", " ")\n            self.kpi_processed.value.setText(total_text)\n            self.kpi_processed.meta.setText(f"{stats.percent:.1f}%")\n            self.kpi_processed.progress.setValue(int(stats.percent * 10))\n\n            self.kpi_success.value.setText(f"{stats.successful:,}".replace(",", " "))\n            self.kpi_success.meta.setText(rt("stats.processed_share", percent=stats.success_percent) if stats.processed else "—")\n            self.kpi_success.progress.setValue(int(stats.success_percent * 10))\n\n            self.kpi_errors.value.setText(str(stats.failed))\n            self.kpi_errors.meta.setText(rt("stats.processed_share", percent=stats.error_percent) if stats.processed else "—")\n            self.kpi_errors.progress.setValue(int(stats.error_percent * 10))\n\n            self.kpi_eta.value.setText(stats.eta_text if snapshot.is_running else (rt("stats.done") if stats.remaining_lines == 0 else "—"))\n            remaining_text = f"{stats.remaining_lines:,}".replace(",", " ")\n            self.kpi_eta.meta.setText(rt("stats.remaining_lines", count=remaining_text))\n            self.kpi_eta.progress.setValue(int(stats.percent * 10))\n        else:\n            for card in (self.kpi_processed, self.kpi_success, self.kpi_errors, self.kpi_eta):\n                card.value.setText("—")\n                card.meta.setText("—")\n                card.progress.setValue(0)\n''',
)

theme = "mineai/gui_qt/theme.py"
replace_once(
    theme,
    'QTabWidget::pane { border-color: #D9DDE7; background: #FFFFFF; }',
    'QTabWidget::pane { border-color: #D7DBE4; background: #F8F9FC; }',
)
replace_once(
    theme,
    'QPushButton#SegmentButton:checked { background-color: #392965; border-color: #7655D0; color: #FFFFFF; }\n',
    'QPushButton#SegmentButton:checked { background-color: #392965; border-color: #7655D0; color: #FFFFFF; }\nQFrame#SidebarActions QPushButton,\nQFrame#SidebarActions QPushButton#PrimaryButton,\nQFrame#SidebarActions QPushButton#WarningButton,\nQFrame#SidebarActions QPushButton#DangerButton { min-height: 38px; max-height: 38px; }\n',
)

test_theme = "tests/test_qt_ux_hardening.py"
replace_once(test_theme, 'self.assertIn("#F5F6FA", light)', 'self.assertIn("#EEF1F5", light)')

print("Windows UX follow-up patch applied.")
