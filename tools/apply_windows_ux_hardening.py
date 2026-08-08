from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f'Expected block not found in {path}: {old[:100]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


def replace_all(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        if new in text:
            return
        raise RuntimeError(f'Expected text not found in {path}: {old!r}')
    p.write_text(text.replace(old, new), encoding='utf-8')


widgets = 'mineai/gui_qt/widgets.py'
replace_once(
    widgets,
    'from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QToolButton, QToolTip, QVBoxLayout, QWidget\n',
    'from PyQt6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QSpinBox, QToolButton, QToolTip, QVBoxLayout, QWidget\n',
)
replace_once(
    widgets,
    '\n\nclass ElidedLabel(QLabel):\n',
    '''\n\nclass ScrollSafeComboBox(QComboBox):\n    """ComboBox that never changes selection from an accidental wheel scroll."""\n\n    def wheelEvent(self, event) -> None:\n        event.ignore()\n\n    def paintEvent(self, event) -> None:\n        super().paintEvent(event)\n        painter = QPainter(self)\n        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)\n        painter.setPen(self.palette().text().color())\n        painter.drawText(\n            self.width() - 27,\n            0,\n            18,\n            self.height(),\n            int(Qt.AlignmentFlag.AlignCenter),\n            "⌄",\n        )\n\n\nclass ScrollSafeSpinBox(QSpinBox):\n    """SpinBox that leaves the mouse wheel to the containing settings panel."""\n\n    def wheelEvent(self, event) -> None:\n        event.ignore()\n\n\nclass ElidedLabel(QLabel):\n''',
)

view_model = 'mineai/gui_qt/view_model.py'
replace_once(view_model, 'from dataclasses import dataclass\nimport time\n', 'from dataclasses import dataclass\nimport re\nimport time\n')
replace_once(
    view_model,
    '\n\ndef format_duration(seconds: float) -> str:\n',
    '''\n\ndef compact_runtime_status(text: str) -> str:\n    """Remove dashboard metrics from JobState.get_full_status() text.\n\n    The same counters already exist in the KPI cards. Keeping only an engine/status\n    fragment prevents the current-task card from duplicating the whole dashboard.\n    Ordinary status messages (start/stop/errors) are returned unchanged.\n    """\n    value = str(text or "").strip()\n    if "Осталось:" not in value or " | " not in value:\n        return value\n\n    ignored_prefixes = ("Переведено:", "Обработано:", "Ошибки:", "Осталось:")\n    compact: list[str] = []\n    for part in value.split(" | "):\n        part = re.sub(r"^\\[[^]]+\\]\\s*", "", part.strip())\n        if not part or part.startswith(ignored_prefixes):\n            continue\n        compact.append(part)\n    return " | ".join(compact)\n\n\ndef format_duration(seconds: float) -> str:\n''',
)

i18n = 'mineai/gui_qt/i18n.py'
replace_all(i18n, '"field.google_fallback": "Fallback через Google",', '"field.google_fallback": "Допереводить через Google",')
replace_once(i18n, '"task.ready": "Готов к работе",\n', '"task.ready": "Готов к работе",\n        "task.running": "Выполняется…",\n')
replace_once(i18n, '"task.ready": "Ready",\n', '"task.ready": "Ready",\n        "task.running": "Running…",\n')

main = 'mineai/gui_qt/main_window.py'
replace_once(main, 'from pathlib import Path\nimport sys\nimport threading\n', 'from pathlib import Path\nimport sys\nimport threading\nimport time\n')
replace_once(main, '    QSpinBox,\n    QPlainTextEdit,\n', '    QSpinBox,\n    QStyle,\n    QPlainTextEdit,\n')
replace_once(
    main,
    'from mineai.gui_qt.view_model import ENGINE_OPTIONS, dashboard_columns, engine_readiness, format_duration, stats_from_snapshot\n',
    'from mineai.gui_qt.view_model import ENGINE_OPTIONS, compact_runtime_status, dashboard_columns, engine_readiness, format_duration, stats_from_snapshot\n',
)
replace_once(
    main,
    'from mineai.gui_qt.widgets import Card, ElidedLabel, HelpMarker, LabeledValue, SegmentedProgressBar, StatCard, StatusPill\n',
    'from mineai.gui_qt.widgets import Card, ElidedLabel, HelpMarker, LabeledValue, ScrollSafeComboBox, ScrollSafeSpinBox, SegmentedProgressBar, StatCard, StatusPill\n',
)
replace_once(main, '        self._allow_close = False\n        self._log_entries', '        self._allow_close = False\n        self._runtime_ended_at: float | None = None\n        self._log_entries')
replace_once(main, '        root = QWidget()\n        self.setCentralWidget(root)\n', '        root = QWidget()\n        root.setObjectName("AppRoot")\n        self.setCentralWidget(root)\n')
replace_once(main, '        self.interface_language = QComboBox()\n', '        self.interface_language = ScrollSafeComboBox()\n')
replace_once(main, '        self.interface_language.setFixedWidth(72)\n', '        self.interface_language.setFixedWidth(58)\n')
replace_once(main, '        host_layout.setSpacing(10)\n', '        host_layout.setSpacing(0)\n')
replace_once(
    main,
    '        content = QWidget()\n        layout = QVBoxLayout(content)\n',
    '        content = QWidget()\n        content.setObjectName("SidebarContent")\n        scroll.viewport().setObjectName("SidebarViewport")\n        layout = QVBoxLayout(content)\n',
)
replace_once(
    main,
    '        self.folder_edit = QLineEdit()\n        self.folder_edit.setReadOnly(True)\n        self.folder_button = QPushButton("📁")\n        self.folder_button.setFixedWidth(42)\n        self.folder_button.setToolTip(t("tooltip.folder"))\n',
    '        self.folder_edit = QLineEdit()\n        self.folder_edit.setReadOnly(True)\n        self.folder_button = QToolButton()\n        self.folder_button.setObjectName("FolderButton")\n        self.folder_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))\n        self.folder_button.setFixedSize(42, 34)\n        self.folder_button.setToolTip(t("tooltip.folder"))\n',
)
replace_all(main, 'self.version_combo = QComboBox()', 'self.version_combo = ScrollSafeComboBox()')
replace_all(main, 'self.language_combo = QComboBox()', 'self.language_combo = ScrollSafeComboBox()')
replace_all(main, 'self.engine_combo = QComboBox()', 'self.engine_combo = ScrollSafeComboBox()')
replace_all(main, 'self.google_mode_combo = QComboBox()', 'self.google_mode_combo = ScrollSafeComboBox()')
replace_all(main, 'self.ai_mode_combo = QComboBox()', 'self.ai_mode_combo = ScrollSafeComboBox()')
replace_all(main, 'self.log_filter = QComboBox()', 'self.log_filter = ScrollSafeComboBox()')
replace_all(main, 'self.ai_batch_spin = QSpinBox()', 'self.ai_batch_spin = ScrollSafeSpinBox()')
replace_once(
    main,
    '        label = QLabel(t("field.engine"))\n        label.setObjectName("FieldLabel")\n',
    '        label = QLabel(t("field.engine"))\n        label.setObjectName("FieldLabel")\n        label.setFixedWidth(92)\n',
)
replace_once(
    main,
    '        google_layout.addWidget(QLabel(t("field.google_mode")))\n',
    '        google_label = QLabel(t("field.google_mode"))\n        google_label.setFixedWidth(92)\n        google_layout.addWidget(google_label)\n',
)

old_action = '''    def _build_action_card(self) -> QWidget:\n        card = Card(t("card.actions"))\n        action_row = QHBoxLayout()\n        self.analyze_button = QPushButton(t("button.analysis"))\n        self.start_button = QPushButton(t("button.start"))\n        self.start_button.setObjectName("PrimaryButton")\n        self.analyze_button.setToolTip(t("tooltip.analysis"))\n        self.start_button.setToolTip(t("tooltip.start"))\n        self.analyze_button.clicked.connect(self._start_analysis)\n        self.start_button.clicked.connect(self._start_translation)\n        action_row.addWidget(self.analyze_button)\n        action_row.addWidget(self.start_button, 1)\n        card.body.addLayout(action_row)\n\n        run_row = QHBoxLayout()\n        self.pause_button = QPushButton(t("button.pause"))\n        self.pause_button.setObjectName("WarningButton")\n        self.stop_button = QPushButton(t("button.stop"))\n        self.stop_button.setObjectName("DangerButton")\n        self.pause_button.setEnabled(False)\n        self.stop_button.setEnabled(False)\n        self.pause_button.clicked.connect(self._toggle_pause)\n        self.stop_button.clicked.connect(self._stop)\n        run_row.addWidget(self.pause_button, 1)\n        run_row.addWidget(self.stop_button, 1)\n        card.body.addLayout(run_row)\n\n        self.lock_hint = QLabel(t("lock.hint"))\n        self.lock_hint.setObjectName("MutedLabel")\n        card.body.addWidget(self.lock_hint)\n        return card\n'''
new_action = '''    def _build_action_card(self) -> QWidget:\n        panel = QFrame()\n        panel.setObjectName("SidebarActions")\n        body = QVBoxLayout(panel)\n        body.setContentsMargins(12, 10, 12, 10)\n        body.setSpacing(7)\n\n        title = QLabel(t("card.actions").upper())\n        title.setObjectName("SectionTitle")\n        body.addWidget(title)\n\n        action_row = QHBoxLayout()\n        action_row.setSpacing(7)\n        self.analyze_button = QPushButton(t("button.analysis"))\n        self.start_button = QPushButton(t("button.start"))\n        self.start_button.setObjectName("PrimaryButton")\n        self.analyze_button.setToolTip(t("tooltip.analysis"))\n        self.start_button.setToolTip(t("tooltip.start"))\n        self.analyze_button.clicked.connect(self._start_analysis)\n        self.start_button.clicked.connect(self._start_translation)\n        action_row.addWidget(self.analyze_button)\n        action_row.addWidget(self.start_button, 1)\n        body.addLayout(action_row)\n\n        run_row = QHBoxLayout()\n        run_row.setSpacing(7)\n        self.pause_button = QPushButton(t("button.pause"))\n        self.pause_button.setObjectName("WarningButton")\n        self.stop_button = QPushButton(t("button.stop"))\n        self.stop_button.setObjectName("DangerButton")\n        self.pause_button.setEnabled(False)\n        self.stop_button.setEnabled(False)\n        self.pause_button.clicked.connect(self._toggle_pause)\n        self.stop_button.clicked.connect(self._stop)\n        run_row.addWidget(self.pause_button, 1)\n        run_row.addWidget(self.stop_button, 1)\n        body.addLayout(run_row)\n\n        for button in (self.analyze_button, self.start_button, self.pause_button, self.stop_button):\n            button.setFixedHeight(40)\n\n        self.lock_hint = QLabel(t("lock.hint"))\n        self.lock_hint.setObjectName("MutedLabel")\n        body.addWidget(self.lock_hint)\n        return panel\n'''
replace_once(main, old_action, new_action)

old_task = '''    def _build_task_card(self) -> QWidget:\n        card = Card(t("card.task"))\n        title_row = QHBoxLayout()\n        self.task_title = QLabel(t("task.idle"))\n        self.task_title.setObjectName("StrongLabel")\n        self.task_percent = QLabel("0.0%")\n        self.task_percent.setObjectName("KpiValue")\n        title_row.addWidget(self.task_title, 1)\n        title_row.addWidget(self.task_percent)\n        card.body.addLayout(title_row)\n\n        self.task_status = QLabel(t("task.ready"))\n        self.task_status.setObjectName("MutedLabel")\n        self.task_status.setWordWrap(True)\n        card.body.addWidget(self.task_status)\n\n        self.segmented_progress = SegmentedProgressBar()\n        self.segmented_progress.set_theme(self._theme_name)\n        card.body.addWidget(self.segmented_progress)\n\n        self.task_metrics_grid = QGridLayout()\n        self.task_metrics_grid.setHorizontalSpacing(18)\n        self.task_metrics_grid.setVerticalSpacing(8)\n        self.task_lines = LabeledValue(t("task.line"))\n        self.task_speed = LabeledValue(t("task.speed"))\n        self.task_elapsed = LabeledValue(t("task.elapsed"))\n        self.task_remaining = LabeledValue(t("task.remaining"))\n        self._task_metrics = (self.task_lines, self.task_speed, self.task_elapsed, self.task_remaining)\n        for col, widget in enumerate(self._task_metrics):\n            self.task_metrics_grid.addWidget(widget, 0, col)\n            self.task_metrics_grid.setColumnStretch(col, 1)\n        card.body.addLayout(self.task_metrics_grid)\n        return card\n'''
new_task = '''    def _build_task_card(self) -> QWidget:\n        card = Card(t("card.task"))\n        title_row = QHBoxLayout()\n        self.task_title = QLabel(t("task.idle"))\n        self.task_title.setObjectName("StrongLabel")\n        self.task_percent = QLabel("0.0%")\n        self.task_percent.setObjectName("TaskPercent")\n        title_row.addWidget(self.task_title, 1)\n        title_row.addWidget(self.task_percent)\n        card.body.addLayout(title_row)\n\n        self.task_status = ElidedLabel(t("task.ready"))\n        self.task_status.setObjectName("MutedLabel")\n        card.body.addWidget(self.task_status)\n\n        self.segmented_progress = SegmentedProgressBar()\n        self.segmented_progress.set_theme(self._theme_name)\n        card.body.addWidget(self.segmented_progress)\n\n        self.task_metrics_grid = QGridLayout()\n        self.task_metrics_grid.setHorizontalSpacing(24)\n        self.task_metrics_grid.setVerticalSpacing(8)\n        self.task_speed = LabeledValue(t("task.speed"))\n        self.task_elapsed = LabeledValue(t("task.elapsed"))\n        self._task_metrics = (self.task_speed, self.task_elapsed)\n        for col, widget in enumerate(self._task_metrics):\n            self.task_metrics_grid.addWidget(widget, 0, col)\n            self.task_metrics_grid.setColumnStretch(col, 1)\n        card.body.addLayout(self.task_metrics_grid)\n\n        self.task_percent.setVisible(False)\n        self.segmented_progress.setVisible(False)\n        for widget in self._task_metrics:\n            widget.setVisible(False)\n        return card\n'''
replace_once(main, old_task, new_task)
replace_once(main, '        self._place_grid_widgets(self.task_metrics_grid, self._task_metrics, columns)\n', '        self._place_grid_widgets(self.task_metrics_grid, self._task_metrics, min(columns, 2))\n')
replace_once(main, '        self.job_state.start()\n        self._clear_log()\n', '        self.job_state.start()\n        self._runtime_ended_at = None\n        self._clear_log()\n')
replace_once(main, '    def _worker_finished(self, _kind: str) -> None:\n        self._job = None\n        self._worker = None\n', '    def _worker_finished(self, _kind: str) -> None:\n        if self._runtime_ended_at is None and self.job_state.snapshot().start_time:\n            self._runtime_ended_at = time.time()\n        self._job = None\n        self._worker = None\n')
replace_once(main, '    def _stop(self) -> None:\n        if self._job is not None:\n', '    def _stop(self) -> None:\n        if self._runtime_ended_at is None and self.job_state.snapshot().start_time:\n            self._runtime_ended_at = time.time()\n        if self._job is not None:\n')
replace_once(
    main,
    '''    def _set_status(self, text: str, progress) -> None:\n        self.task_status.setText(text)\n        if progress is not None:\n            value = max(0.0, min(1.0, float(progress)))\n            self.segmented_progress.setValue(value)\n            self.task_percent.setText(f"{value * 100:.1f}%")\n        self._refresh_runtime_dashboard()\n''',
    '''    def _set_status(self, text: str, progress) -> None:\n        compact = compact_runtime_status(text)\n        snapshot = self.job_state.snapshot()\n        display_text = compact or (t("task.running") if snapshot.is_running else str(text))\n        self.task_status.setText(display_text)\n        self.task_status.setToolTip(str(text) if str(text) != display_text else display_text)\n        if progress is not None:\n            value = max(0.0, min(1.0, float(progress)))\n            self.segmented_progress.setValue(value)\n            self.task_percent.setText(f"{value * 100:.1f}%")\n        self._refresh_runtime_dashboard()\n''',
)
replace_once(main, '        stats = stats_from_snapshot(snapshot, eta_text=self.job_state.eta_text())\n', '        frozen_now = self._runtime_ended_at if (not snapshot.is_running and self._runtime_ended_at is not None) else None\n        stats = stats_from_snapshot(snapshot, now=frozen_now, eta_text=self.job_state.eta_text())\n')
replace_once(
    main,
    '''        if stats.total:\n            self.segmented_progress.setValue(stats.percent / 100.0)\n            self.task_percent.setText(f"{stats.percent:.1f}%")\n            self.task_lines.value.setText(f"{stats.processed:,} / {stats.total:,}".replace(",", " "))\n        else:\n            self.task_lines.value.setText("—")\n        self.task_speed.value.setText(rt("stats.rate", rate=stats.lines_per_minute) if stats.lines_per_minute else "—")\n        self.task_elapsed.value.setText(format_duration(stats.elapsed_seconds) if stats.elapsed_seconds else "—")\n        self.task_remaining.value.setText(stats.eta_text if snapshot.is_running else "—")\n''',
    '''        has_task_progress = bool(snapshot.is_running or stats.total)\n        self.task_percent.setVisible(has_task_progress)\n        self.segmented_progress.setVisible(has_task_progress)\n        for widget in self._task_metrics:\n            widget.setVisible(has_task_progress)\n\n        if stats.total:\n            self.segmented_progress.setValue(stats.percent / 100.0)\n            self.task_percent.setText(f"{stats.percent:.1f}%")\n        else:\n            self.segmented_progress.setValue(0.0)\n            self.task_percent.setText("0.0%")\n        self.task_speed.value.setText(rt("stats.rate", rate=stats.lines_per_minute) if stats.lines_per_minute else "—")\n        self.task_elapsed.value.setText(format_duration(stats.elapsed_seconds) if stats.elapsed_seconds else "—")\n''',
)

theme = 'mineai/gui_qt/theme.py'
replace_once(
    theme,
    'QMainWindow, QDialog { background-color: #12131C; }\nQLabel, QCheckBox, QRadioButton { background-color: transparent; border: none; }\nQWidget#SidebarHost { background-color: transparent; border: none; }\nQWidget#DashboardBody { background-color: transparent; border: none; }\n',
    'QMainWindow, QDialog { background-color: #12131C; }\nQLabel, QCheckBox, QRadioButton { background-color: transparent; border: none; }\nQWidget#AppRoot, QWidget#DashboardBody, QWidget#SidebarHost, QWidget#SidebarContent, QWidget#SidebarViewport { background-color: #12131C; border: none; }\nQScrollArea#Sidebar { background-color: #12131C; border: none; }\nQFrame#SidebarActions { background-color: #171824; border: none; border-top: 1px solid #2B2C3D; }\n',
)
replace_once(theme, 'QComboBox::drop-down { width: 30px; border: none; background: transparent; }\n', 'QComboBox::drop-down { width: 30px; border: none; background: transparent; }\nQComboBox::down-arrow { image: none; width: 0; height: 0; }\n')
replace_once(theme, 'QToolButton#ThemeToggle:hover { background-color: #2B2D40; border-color: #8B6BE5; color: #FFFFFF; }\n', 'QToolButton#ThemeToggle:hover { background-color: #2B2D40; border-color: #8B6BE5; color: #FFFFFF; }\nQToolButton#FolderButton { background-color: #292B3D; color: #E2E8F0; border: 1px solid #393B50; border-radius: 8px; padding: 0; }\nQToolButton#FolderButton:hover { background-color: #33354A; border-color: #4B4E66; }\n')
replace_once(theme, 'QLabel#KpiValue { color: #F8FAFC; font-size: 22px; font-weight: 750; }\n', 'QLabel#KpiValue { color: #F8FAFC; font-size: 22px; font-weight: 750; }\nQLabel#TaskPercent { color: #F8FAFC; font-size: 19px; font-weight: 750; }\n')
replacements = {
    'QWidget { background-color: #F5F6FA; color: #202231; }': 'QWidget { background-color: #EEF1F5; color: #283142; }',
    'QMainWindow, QDialog { background-color: #F5F6FA; }': 'QMainWindow, QDialog { background-color: #EEF1F5; }',
    'QWidget#SidebarHost, QWidget#DashboardBody { background-color: transparent; }': 'QWidget#AppRoot, QWidget#SidebarHost, QWidget#SidebarContent, QWidget#SidebarViewport, QWidget#DashboardBody { background-color: #EEF1F5; }\nQScrollArea#Sidebar { background-color: #EEF1F5; }\nQFrame#SidebarActions { background-color: #F3F5F8; border-color: #D7DBE4; }',
    'QToolTip { background-color: #FFFFFF; color: #202231; border-color: #C9CEDA; }': 'QToolTip { background-color: #F8F9FC; color: #283142; border-color: #C8CED8; }',
    'QFrame#Header, QFrame#Footer { background-color: #FFFFFF; border-color: #D9DDE7; }': 'QFrame#Header, QFrame#Footer { background-color: #F6F7FA; border-color: #D7DBE4; }',
    'QFrame#Card { background-color: #FFFFFF; border-color: #D9DDE7; }': 'QFrame#Card { background-color: #F8F9FC; border-color: #D7DBE4; }',
    'QFrame#InnerCard { background-color: #F8F9FC; border-color: #D9DDE7; }': 'QFrame#InnerCard { background-color: #F3F5F8; border-color: #D7DBE4; }',
    'QLineEdit, QComboBox, QSpinBox { background-color: #FFFFFF; color: #202231; border-color: #C9CEDA; selection-background-color: #6B46C1; }': 'QLineEdit, QComboBox, QSpinBox { background-color: #F4F6F9; color: #283142; border-color: #C8CED8; selection-background-color: #6B46C1; }',
    'QComboBox QAbstractItemView { background-color: #FFFFFF; color: #202231; border-color: #C9CEDA; }': 'QComboBox QAbstractItemView { background-color: #F8F9FC; color: #283142; border-color: #C8CED8; }',
    'QCheckBox::indicator, QRadioButton::indicator { background-color: #FFFFFF; border-color: #AEB6C6; }': 'QCheckBox::indicator, QRadioButton::indicator { background-color: #F6F7FA; border-color: #AEB6C6; }',
    'QRadioButton::indicator:checked { background-color: #6B46C1; border-color: #FFFFFF; }': 'QRadioButton::indicator:checked { background-color: #6B46C1; border-color: #F6F7FA; }',
}
for old, new in replacements.items():
    replace_once(theme, old, new)
replace_once(theme, 'QToolButton#ThemeToggle:hover { background-color: #E6E8EF; border-color: #7655D0; color: #4D2C9B; }\n', 'QToolButton#ThemeToggle:hover { background-color: #E6E8EF; border-color: #7655D0; color: #4D2C9B; }\nQToolButton#FolderButton { background-color: #EEF0F4; color: #374151; border-color: #CDD2DD; }\nQToolButton#FolderButton:hover { background-color: #E1E4EC; border-color: #B6BDCB; }\n')

test_vm = 'tests/test_qt_view_model.py'
replace_once(test_vm, 'from mineai.gui_qt.view_model import dashboard_columns, engine_readiness, format_duration, stats_from_snapshot\n', 'from mineai.gui_qt.view_model import compact_runtime_status, dashboard_columns, engine_readiness, format_duration, stats_from_snapshot\n')
replace_once(
    test_vm,
    '\n\nclass EngineReadinessTests(unittest.TestCase):\n',
    '''\n\nclass RuntimeStatusPresentationTests(unittest.TestCase):\n    def test_generated_dashboard_metrics_are_removed_from_task_status(self):\n        text = (\n            "[Моды 4/513] Переведено: 1169/123755 | "\n            "Обработано: 1173/123755 | Ошибки: 4 | "\n            "KoboldCPP: пакет 15 | Осталось: 2 ч 13 мин"\n        )\n        self.assertEqual(compact_runtime_status(text), "KoboldCPP: пакет 15")\n\n    def test_ordinary_status_is_preserved(self):\n        self.assertEqual(compact_runtime_status("Остановлено"), "Остановлено")\n\n\nclass EngineReadinessTests(unittest.TestCase):\n''',
)

qt_test = Path('tests/test_qt_windows_ux.py')
qt_test_content = '''import os\nimport unittest\n\nos.environ.setdefault("QT_QPA_PLATFORM", "offscreen")\n\ntry:\n    from PyQt6.QtWidgets import QApplication\n    from mineai.gui_qt.widgets import ScrollSafeComboBox, ScrollSafeSpinBox\nexcept ImportError:\n    QApplication = None\n    ScrollSafeComboBox = None\n    ScrollSafeSpinBox = None\n\n\n@unittest.skipIf(QApplication is None, "PyQt6 is not installed")\nclass WheelSafetyTests(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.app = QApplication.instance() or QApplication([])\n\n    def test_combo_ignores_wheel(self):\n        combo = ScrollSafeComboBox()\n        event = _FakeWheelEvent()\n        combo.wheelEvent(event)\n        self.assertTrue(event.ignored)\n\n    def test_spinbox_ignores_wheel(self):\n        spin = ScrollSafeSpinBox()\n        event = _FakeWheelEvent()\n        spin.wheelEvent(event)\n        self.assertTrue(event.ignored)\n\n\nclass _FakeWheelEvent:\n    def __init__(self):\n        self.ignored = False\n\n    def ignore(self):\n        self.ignored = True\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
if not qt_test.exists():
    qt_test.write_text(qt_test_content, encoding='utf-8')
elif qt_test.read_text(encoding='utf-8') != qt_test_content:
    raise RuntimeError('Unexpected existing tests/test_qt_windows_ux.py')

print('Windows UX hardening patch applied.')
