from __future__ import annotations

from pathlib import Path
import re

PATH = Path("mineai/gui_qt/main_window.py")
text = PATH.read_text(encoding="utf-8")


def replace_method(source: str, name: str, replacement: str) -> str:
    pattern = re.compile(rf"^    def {re.escape(name)}\(.*?(?=^    def |^def run\(|\Z)", re.M | re.S)
    updated, count = pattern.subn(replacement.rstrip() + "\n\n", source, count=1)
    if count != 1:
        raise RuntimeError(f"method {name!r}: expected one match, got {count}")
    return updated


text = text.replace("from html import escape\n", "")
text = text.replace("from PyQt6.QtCore import QTimer, Qt\n", "from PyQt6.QtCore import QTimer, Qt, QUrl\n")
text = text.replace(
    "from PyQt6.QtGui import QIcon, QPixmap\n",
    "from PyQt6.QtGui import QColor, QDesktopServices, QIcon, QPixmap, QTextCharFormat, QTextCursor\n",
)
text = text.replace("    QTextEdit,\n", "    QPlainTextEdit,\n")
text = text.replace(
    "from mineai.gui_qt.theme import APP_QSS\n",
    "from mineai.gui_qt.i18n import t, translator\n"
    "from mineai.gui_qt.log_model import LogEntry, LogSegment, entry_from_message, matches_entry\n"
    "from mineai.gui_qt.theme import theme_qss\n",
)
text = text.replace(
    "from mineai.gui_qt.widgets import Card, LabeledValue, SegmentedProgressBar, StatCard, StatusPill\n",
    "from mineai.gui_qt.widgets import Card, HelpMarker, LabeledValue, SegmentedProgressBar, StatCard, StatusPill\n",
)
text = text.replace(
    "LOG_COLORS = {",
    "LOG_PATH = Path(\"mineai_log.txt\").resolve()\nMAX_LOG_ENTRIES = 50_000\nMAX_LOG_BLOCKS = 25_000\n\n\nLOG_COLORS = {",
    1,
)

old_init = '''        self.setWindowTitle(f"MineAI Modpack Translator — {__version__}")
        icon_path = _resolve_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1520, 940)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(APP_QSS)

        self.job_state = JobState()
'''
new_init = '''        translator.set_language(settings.get("GENERAL", "ui_language"))
        self._ui_language = translator.language
        self._theme_name = settings.get("GENERAL", "theme") or "Dark"
        self.setWindowTitle(f"{t('app.title')} — {__version__}")
        icon_path = _resolve_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1520, 940)
        self.setMinimumSize(1180, 760)
        self.setAcceptDrops(True)
        self.setStyleSheet(theme_qss(self._theme_name))

        self.job_state = JobState()
'''
if old_init not in text:
    raise RuntimeError("init header snippet not found")
text = text.replace(old_init, new_init, 1)
text = text.replace(
    "        self._log_entries: list[tuple[str, str]] = []\n",
    "        self._log_entries: list[LogEntry] = []\n"
    "        self._log_file = None\n"
    "        try:\n"
    "            self._log_file = LOG_PATH.open(\"a\", encoding=\"utf-8\", buffering=1)\n"
    "        except OSError:\n"
    "            self._log_file = None\n",
    1,
)
text = text.replace(
    "        self._refresh_footer()\n\n        self.refresh_timer",
    "        self._refresh_footer()\n        self._apply_theme(self._theme_name)\n\n        self.refresh_timer",
    1,
)

text = replace_method(text, "_build_header", '''    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("Header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 12, 22, 12)
        layout.setSpacing(10)

        logo = QLabel("◈")
        icon_path = _resolve_icon_path()
        if icon_path:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                logo.setPixmap(
                    pixmap.scaled(
                        32,
                        32,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            else:
                logo.setStyleSheet("color: #8B6BE5; font-size: 28px; font-weight: 800;")
        else:
            logo.setStyleSheet("color: #8B6BE5; font-size: 28px; font-weight: 800;")
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        title = QLabel(t("app.title"))
        title.setObjectName("AppTitle")
        version = QLabel(__version__)
        version.setObjectName("VersionLabel")
        titles.addWidget(title)
        titles.addWidget(version)
        layout.addLayout(titles)
        layout.addStretch(1)

        self.system_pill = StatusPill()
        layout.addWidget(self.system_pill)
        layout.addSpacing(14)

        self.settings_button = QPushButton(t("header.settings"))
        self.settings_button.setObjectName("HeaderButton")
        self.settings_button.clicked.connect(self._open_settings)
        layout.addWidget(self.settings_button)

        self.prompts_button = QPushButton(t("header.prompts"))
        self.prompts_button.setObjectName("HeaderButton")
        self.prompts_button.clicked.connect(self._open_prompts)
        layout.addWidget(self.prompts_button)

        self.migration_button = QPushButton(t("header.migration"))
        self.migration_button.setObjectName("HeaderButton")
        self.migration_button.setToolTip(t("tooltip.migration"))
        self.migration_button.clicked.connect(self._open_migration)
        layout.addWidget(self.migration_button)
        return header''')

text = replace_method(text, "_build_project_card", '''    def _build_project_card(self) -> QWidget:
        card = Card(t("card.project"))
        label = QLabel(t("field.minecraft_folder"))
        label.setObjectName("FieldLabel")
        card.body.addWidget(label)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(6)
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        self.folder_button = QPushButton("📁")
        self.folder_button.setFixedWidth(42)
        self.folder_button.setToolTip(t("tooltip.folder"))
        self.folder_button.clicked.connect(self._select_folder)
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(self.folder_button)
        card.body.addLayout(folder_row)

        self.folder_state = QLabel(t("folder.not_selected"))
        self.folder_state.setObjectName("MutedLabel")
        card.body.addWidget(self.folder_state)

        selectors = QGridLayout()
        selectors.setHorizontalSpacing(8)
        version_label = QLabel(t("field.minecraft_version"))
        version_label.setObjectName("FieldLabel")
        language_label = QLabel(t("field.target_language"))
        language_label.setObjectName("FieldLabel")
        self.version_combo = QComboBox()
        self.version_combo.addItems(MC_VERSIONS)
        self.language_combo = QComboBox()
        self.language_combo.addItems(list(LANGUAGES.keys()))
        self.language_combo.currentTextChanged.connect(self._refresh_system_readiness)
        selectors.addWidget(version_label, 0, 0)
        selectors.addWidget(self.version_combo, 1, 0)
        selectors.addWidget(language_label, 2, 0)
        selectors.addWidget(self.language_combo, 3, 0)
        card.body.addLayout(selectors)
        return card''')

text = replace_method(text, "_build_engine_card", '''    def _build_engine_card(self) -> QWidget:
        card = Card(t("card.engine"))
        row = QHBoxLayout()
        row.setSpacing(8)
        label = QLabel(t("field.engine"))
        label.setObjectName("FieldLabel")
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(list(ENGINE_OPTIONS.keys()))
        self.engine_combo.currentTextChanged.connect(self._engine_changed)
        row.addWidget(label)
        row.addWidget(self.engine_combo, 1)
        card.body.addLayout(row)

        ready = QFrame()
        ready.setObjectName("ReadyBox")
        ready_layout = QHBoxLayout(ready)
        ready_layout.setContentsMargins(9, 6, 7, 6)
        self.engine_ready_label = QLabel(t("engine.checking"))
        self.engine_ready_label.setObjectName("ReadyText")
        configure = QPushButton(t("button.configure"))
        configure.setFixedWidth(92)
        configure.clicked.connect(self._open_settings)
        ready_layout.addWidget(self.engine_ready_label, 1)
        ready_layout.addWidget(configure)
        card.body.addWidget(ready)

        self.google_options = QWidget()
        google_layout = QHBoxLayout(self.google_options)
        google_layout.setContentsMargins(0, 0, 0, 0)
        google_layout.addWidget(QLabel(t("field.google_mode")))
        self.google_mode_combo = QComboBox()
        self.google_mode_combo.addItem(t("google.single"), "single")
        self.google_mode_combo.addItem(t("google.batch"), "batch")
        google_layout.addWidget(self.google_mode_combo, 1)
        card.body.addWidget(self.google_options)

        self.ai_options = QWidget()
        ai_grid = QGridLayout(self.ai_options)
        ai_grid.setContentsMargins(0, 0, 0, 0)
        ai_grid.setHorizontalSpacing(8)
        ai_grid.setVerticalSpacing(7)
        ai_grid.addWidget(QLabel(t("field.ai_mode")), 0, 0, 1, 2)
        self.ai_mode_combo = QComboBox()
        self.ai_mode_combo.addItem(t("ai.safe"), "safe")
        self.ai_mode_combo.addItem(t("ai.context"), "context")
        ai_grid.addWidget(self.ai_mode_combo, 0, 2)

        batch_label = QLabel(t("field.ai_batch"))
        ai_grid.addWidget(batch_label, 1, 0)
        ai_grid.addWidget(HelpMarker(t("tooltip.ai_batch")), 1, 1)
        self.ai_batch_spin = QSpinBox()
        self.ai_batch_spin.setRange(1, 40)
        self.ai_batch_spin.setValue(20)
        self.ai_batch_spin.valueChanged.connect(self._refresh_footer)
        ai_grid.addWidget(self.ai_batch_spin, 1, 2)

        fallback_host = QWidget()
        fallback_layout = QHBoxLayout(fallback_host)
        fallback_layout.setContentsMargins(0, 0, 0, 0)
        self.ai_fallback = QCheckBox(t("field.google_fallback"))
        self.ai_fallback.setChecked(settings.getboolean("AI", "fallback_google"))
        fallback_layout.addWidget(self.ai_fallback)
        fallback_layout.addWidget(HelpMarker(t("tooltip.fallback")))
        fallback_layout.addStretch(1)
        ai_grid.addWidget(fallback_host, 2, 0, 1, 3)
        card.body.addWidget(self.ai_options)
        return card''')

text = replace_method(text, "_build_scope_card", '''    def _build_scope_card(self) -> QWidget:
        card = Card(t("card.scope"))
        self.scope_mods = QCheckBox(t("scope.mods"))
        self.scope_books = QCheckBox(t("scope.books"))
        self.scope_quests = QCheckBox(t("scope.quests"))
        for checkbox in (self.scope_mods, self.scope_books, self.scope_quests):
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._refresh_system_readiness)
            card.body.addWidget(checkbox)
        return card''')

text = replace_method(text, "_build_mode_card", '''    def _build_mode_card(self) -> QWidget:
        card = Card(t("card.mode"))
        mode_label = QLabel(t("field.processing"))
        mode_label.setObjectName("FieldLabel")
        card.body.addWidget(mode_label)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_buttons: dict[str, QPushButton] = {}
        for value, label in (("append", "Append"), ("skip", "Skip"), ("force", "Force")):
            button = QPushButton(label)
            button.setObjectName("SegmentButton")
            button.setCheckable(True)
            if value == "append":
                button.setChecked(True)
            self.mode_group.addButton(button)
            self.mode_buttons[value] = button
            mode_row.addWidget(button, 1)
        card.body.addLayout(mode_row)

        output_label = QLabel(t("field.output"))
        output_label.setObjectName("FieldLabel")
        card.body.addWidget(output_label)
        output_row = QHBoxLayout()
        output_row.setSpacing(6)
        self.output_group = QButtonGroup(self)
        self.output_group.setExclusive(True)
        self.output_rp = QPushButton(t("output.resourcepack"))
        self.output_inplace = QPushButton(t("output.inplace"))
        for button in (self.output_rp, self.output_inplace):
            button.setObjectName("SegmentButton")
            button.setCheckable(True)
            self.output_group.addButton(button)
            output_row.addWidget(button, 1)
        output_row.addWidget(HelpMarker(t("tooltip.inplace")))
        self.output_rp.setChecked(True)
        self.output_rp.toggled.connect(self._output_changed)
        card.body.addLayout(output_row)

        self.pack_name = QLineEdit("MineAI_Pack")
        self.pack_name.setPlaceholderText(t("output.pack_placeholder"))
        card.body.addWidget(self.pack_name)
        return card''')

text = replace_method(text, "_build_action_card", '''    def _build_action_card(self) -> QWidget:
        card = Card(t("card.actions"))
        action_row = QHBoxLayout()
        self.analyze_button = QPushButton(t("button.analysis"))
        self.start_button = QPushButton(t("button.start"))
        self.start_button.setObjectName("PrimaryButton")
        self.analyze_button.setToolTip(t("tooltip.analysis"))
        self.start_button.setToolTip(t("tooltip.start"))
        self.analyze_button.clicked.connect(self._start_analysis)
        self.start_button.clicked.connect(self._start_translation)
        action_row.addWidget(self.analyze_button)
        action_row.addWidget(self.start_button, 1)
        card.body.addLayout(action_row)

        run_row = QHBoxLayout()
        self.pause_button = QPushButton(t("button.pause"))
        self.pause_button.setObjectName("WarningButton")
        self.stop_button = QPushButton(t("button.stop"))
        self.stop_button.setObjectName("DangerButton")
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.pause_button.clicked.connect(self._toggle_pause)
        self.stop_button.clicked.connect(self._stop)
        run_row.addWidget(self.pause_button, 1)
        run_row.addWidget(self.stop_button, 1)
        card.body.addLayout(run_row)

        self.lock_hint = QLabel(t("lock.hint"))
        self.lock_hint.setObjectName("MutedLabel")
        card.body.addWidget(self.lock_hint)
        return card''')

text = replace_method(text, "_build_status_card", '''    def _build_status_card(self) -> QWidget:
        card = Card(t("card.status"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        self.kpi_processed = StatCard(t("kpi.processed"), "KpiBlue")
        self.kpi_success = StatCard(t("kpi.success"), "KpiGreen")
        self.kpi_errors = StatCard(t("kpi.errors"), "KpiAmber")
        self.kpi_eta = StatCard(t("kpi.remaining"), "KpiViolet")
        for widget, glyph, color in (
            (self.kpi_processed, "▣", "#60A5FA"),
            (self.kpi_success, "✓", "#5EEAD4"),
            (self.kpi_errors, "!", "#FBBF24"),
            (self.kpi_eta, "◷", "#A78BFA"),
        ):
            widget.icon.setText(glyph)
            widget.icon.setStyleSheet(
                f"background: transparent; border: none; color: {color}; font-size: 18px; font-weight: 800;"
            )
        for col, widget in enumerate((self.kpi_processed, self.kpi_success, self.kpi_errors, self.kpi_eta)):
            grid.addWidget(widget, 0, col)
            grid.setColumnStretch(col, 1)
        card.body.addLayout(grid)
        return card''')

text = replace_method(text, "_build_task_card", '''    def _build_task_card(self) -> QWidget:
        card = Card(t("card.task"))
        title_row = QHBoxLayout()
        self.task_title = QLabel(t("task.idle"))
        self.task_title.setObjectName("StrongLabel")
        self.task_percent = QLabel("0.0%")
        self.task_percent.setObjectName("KpiValue")
        title_row.addWidget(self.task_title, 1)
        title_row.addWidget(self.task_percent)
        card.body.addLayout(title_row)

        self.task_status = QLabel(t("task.ready"))
        self.task_status.setObjectName("MutedLabel")
        self.task_status.setWordWrap(True)
        card.body.addWidget(self.task_status)

        self.segmented_progress = SegmentedProgressBar()
        self.segmented_progress.set_theme(self._theme_name)
        card.body.addWidget(self.segmented_progress)

        metrics = QHBoxLayout()
        metrics.setSpacing(18)
        self.task_lines = LabeledValue(t("task.line"))
        self.task_speed = LabeledValue(t("task.speed"))
        self.task_elapsed = LabeledValue(t("task.elapsed"))
        self.task_remaining = LabeledValue(t("task.remaining"))
        for widget in (self.task_lines, self.task_speed, self.task_elapsed, self.task_remaining):
            metrics.addWidget(widget)
        metrics.addStretch(1)
        card.body.addLayout(metrics)
        return card''')

text = replace_method(text, "_build_log_card", '''    def _build_log_card(self) -> QWidget:
        card = Card(t("card.log"))
        toolbar = QHBoxLayout()
        self.log_filter = QComboBox()
        self.log_filter.addItem(t("log.all"), "all")
        self.log_filter.addItem(t("log.translated"), "translated")
        self.log_filter.addItem(t("log.issues"), "issues")
        self.log_filter.addItem(t("log.analysis"), "analysis")
        self.log_filter.currentIndexChanged.connect(self._render_log)

        self.log_search = QLineEdit()
        self.log_search.setPlaceholderText(t("log.search"))
        self.log_search.setClearButtonEnabled(True)
        self.log_search.setMaximumWidth(300)
        self.log_search.textChanged.connect(self._render_log)

        self.log_autoscroll = QCheckBox(t("log.autoscroll"))
        self.log_autoscroll.setChecked(True)

        open_log = QPushButton(t("button.open_log"))
        clear = QPushButton(t("button.clear"))
        save = QPushButton(t("button.save"))
        open_log.clicked.connect(self._open_log_file)
        clear.clicked.connect(self._clear_log)
        save.clicked.connect(self._save_log)

        toolbar.addWidget(self.log_filter)
        toolbar.addWidget(self.log_search, 1)
        toolbar.addWidget(self.log_autoscroll)
        toolbar.addStretch(1)
        toolbar.addWidget(open_log)
        toolbar.addWidget(clear)
        toolbar.addWidget(save)
        card.body.addLayout(toolbar)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("LogView")
        self.log_view.setReadOnly(True)
        self.log_view.setUndoRedoEnabled(False)
        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.log_view.document().setMaximumBlockCount(MAX_LOG_BLOCKS)
        card.body.addWidget(self.log_view, 1)
        return card''')

text = replace_method(text, "_build_footer", '''    def _build_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("Footer")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 8, 24, 8)
        self.footer_status = QLabel(t("footer.ready"))
        self.footer_status.setObjectName("ReadyText")
        self.footer_details = QLabel("")
        self.footer_details.setObjectName("MutedLabel")
        layout.addWidget(self.footer_status)
        layout.addStretch(1)
        layout.addWidget(self.footer_details)
        return footer''')

text = replace_method(text, "_select_folder", '''    def _select_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, t("dialog.minecraft_folder"), settings.get("GENERAL", "mc_dir"))
        if path:
            self._set_minecraft_directory(path)''')

text = replace_method(text, "_refresh_folder_state", '''    def _refresh_folder_state(self) -> None:
        raw = settings.get("GENERAL", "mc_dir").strip()
        if not raw:
            self.folder_state.setText(t("folder.not_selected"))
            self.folder_state.setObjectName("MutedLabel")
        else:
            root = Path(raw)
            if not root.is_dir():
                self.folder_state.setText(t("folder.missing"))
                self.folder_state.setObjectName("DangerText")
            else:
                markers = []
                if (root / "mods").is_dir():
                    markers.append("mods/ ✓")
                if (root / "config").is_dir():
                    markers.append("config/ ✓")
                suffix = "   " + "   ".join(markers) if markers else ""
                self.folder_state.setText(t("folder.found") + suffix)
                self.folder_state.setObjectName("ReadyText")
        self.folder_state.style().unpolish(self.folder_state)
        self.folder_state.style().polish(self.folder_state)''')

text = replace_method(text, "_refresh_system_readiness", '''    def _refresh_system_readiness(self, *_args) -> None:
        raw = settings.get("GENERAL", "mc_dir").strip()
        if not raw or not Path(raw).is_dir():
            self.system_pill.set_ready(False, t("ready.folder"))
            return
        if not any((self.scope_mods.isChecked(), self.scope_books.isChecked(), self.scope_quests.isChecked())):
            self.system_pill.set_ready(False, t("ready.scope"))
            return
        ready, status_text = engine_readiness(settings, self.engine_combo.currentText())
        if not ready:
            self.system_pill.set_ready(False, status_text)
            return
        self.system_pill.set_ready(True, t("ready.all"))''')

text = replace_method(text, "_refresh_footer", '''    def _refresh_footer(self, *_args) -> None:
        workers = settings.getint("GENERAL", "google_workers", 5)
        retries = settings.getint("AI", "ai_retries", 3)
        batch = self.ai_batch_spin.value() if hasattr(self, "ai_batch_spin") else 20
        self.footer_details.setText(t("footer.details", workers=workers, batch=batch, retries=retries))''')

text = replace_method(text, "_after_settings_saved", '''    def _after_settings_saved(self) -> None:
        new_language = settings.get("GENERAL", "ui_language") or "ru"
        new_theme = settings.get("GENERAL", "theme") or "Dark"
        language_changed = new_language != self._ui_language
        translator.set_language(new_language)
        self._ui_language = translator.language
        self._apply_theme(new_theme)
        if language_changed:
            QTimer.singleShot(0, self._rebuild_ui_for_locale)
            return
        self._refresh_engine_state()
        self._refresh_system_readiness()
        self._refresh_footer()''')

text = replace_method(text, "_open_migration", '''    def _open_migration(self, initial_zip: str | None = None) -> None:
        if self._worker and self._worker.is_alive():
            return
        mc_dir = settings.get("GENERAL", "mc_dir").strip()
        if not mc_dir or not Path(mc_dir).is_dir() or not (Path(mc_dir) / "mods").is_dir():
            QMessageBox.warning(self, t("dialog.migration"), t("dialog.migration_need_mods"))
            return
        dialog = MigrationDialog(
            mc_dir,
            self.language_combo.currentText(),
            self.cache_std,
            self.cache_ai,
            lambda msg, tag="white": self.signals.log.emit(msg, tag),
            self,
            initial_zip=initial_zip,
        )
        dialog.exec()''')

text = replace_method(text, "_validate_preflight", '''    def _validate_preflight(self, *, translation: bool) -> bool:
        mc_dir = settings.get("GENERAL", "mc_dir").strip()
        if not mc_dir:
            QMessageBox.warning(self, t("dialog.minecraft_folder"), t("dialog.folder_first"))
            return False
        if not Path(mc_dir).is_dir():
            QMessageBox.warning(self, t("dialog.folder_missing"), t("dialog.folder_missing_text", path=mc_dir))
            return False
        if not any((self.scope_mods.isChecked(), self.scope_books.isChecked(), self.scope_quests.isChecked())):
            QMessageBox.warning(self, t("dialog.nothing"), t("dialog.nothing_text"))
            return False
        if translation:
            ready, status_text = engine_readiness(settings, self.engine_combo.currentText())
            if not ready:
                QMessageBox.warning(self, t("dialog.engine"), status_text)
                return False
            if self.output_inplace.isChecked():
                answer = QMessageBox.warning(
                    self,
                    t("dialog.inplace_title"),
                    t("dialog.inplace_text"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return False
        return True''')

# Small status/localization replacements outside replaced methods.
text = text.replace('self.footer_status.setText("●  Выполняется задача")', 'self.footer_status.setText(t("footer.running"))')
text = text.replace('self.task_title.setText("Анализ сборки" if kind == "analysis" else "Подготовка перевода")', 'self.task_title.setText(t("status.analysis") if kind == "analysis" else t("status.translation_prepare"))')
text = text.replace('self.task_status.setText("Запуск…")', 'self.task_status.setText(t("status.starting"))')
text = text.replace('name = "анализа" if kind == "analysis" else "перевода"\n        self._append_log(f"Ошибка {name}:\\n{error}", "red")\n        self._set_status(f"Ошибка {name}", None)', 'label = t("status.error_analysis") if kind == "analysis" else t("status.error_translation")\n        self._append_log(f"{label}:\\n{error}", "red")\n        self._set_status(label, None)')
text = text.replace('self.footer_status.setText("●  Готов к работе")', 'self.footer_status.setText(t("footer.ready"))')
text = text.replace('self.pause_button.setText("▶  Продолжить")', 'self.pause_button.setText(t("button.resume"))')
text = text.replace('self._append_log("Пауза", "yellow")', 'self._append_log(t("status.pause"), "yellow")')
text = text.replace('self.pause_button.setText("⏸  Пауза")', 'self.pause_button.setText(t("button.pause"))')
text = text.replace('self._append_log("Продолжение", "green")', 'self._append_log(t("status.resume"), "green")')
text = text.replace('self._set_status("Остановка…", None)', 'self._set_status(t("status.stopping"), None)')
text = text.replace('self._set_status("Завершение работы…", None)', 'self._set_status(t("status.closing"), None)')
text = text.replace('self.footer_status.setText("●  Завершение задачи")', 'self.footer_status.setText(t("footer.closing"))')

# Replace the old level/HTML log block in one shot.
log_pattern = re.compile(r"^    @staticmethod\n    def _log_level\(.*?(?=^    def closeEvent)", re.M | re.S)
log_replacement = '''    def _append_log(self, message: str, tag: str = "white") -> None:
        color = LOG_COLORS.get(tag, LOG_COLORS["white"])
        self._push_log_entry(entry_from_message(tag, message, color), persist=True)

    def _append_analysis_row(self, icon: str, name: str, kind: str, trans_c: int, en_c: int, pct: int) -> None:
        pct_color = LOG_COLORS["green"] if pct >= 90 else (LOG_COLORS["yellow"] if pct >= 50 else LOG_COLORS["red"])
        visible_name = name[:38]
        plain = f"{icon} {visible_name}  [{kind}]  {trans_c}/{en_c}  {pct}%"
        entry = LogEntry(
            plain_text=plain,
            level="success" if pct >= 90 else ("warning" if pct >= 50 else "error"),
            category="analysis",
            segments=(
                LogSegment(f"{icon} {visible_name}", LOG_COLORS["cyan"]),
                LogSegment("  [", LOG_COLORS["white"]),
                LogSegment(kind, LOG_COLORS["magenta"]),
                LogSegment("]  ", LOG_COLORS["white"]),
                LogSegment(f"{trans_c}/{en_c}", LOG_COLORS["white"]),
                LogSegment("  ", LOG_COLORS["white"]),
                LogSegment(f"{pct}%", pct_color),
            ),
        )
        self._push_log_entry(entry, persist=True)

    def _push_log_entry(self, entry: LogEntry, *, persist: bool) -> None:
        self._log_entries.append(entry)
        if len(self._log_entries) > MAX_LOG_ENTRIES:
            del self._log_entries[: len(self._log_entries) - MAX_LOG_ENTRIES]
        if persist and self._log_file is not None:
            try:
                self._log_file.write(entry.plain_text + "\\n")
            except OSError:
                pass
        if hasattr(self, "log_filter") and self._log_entry_visible(entry):
            self._append_entry_to_view(entry)

    def _log_entry_visible(self, entry: LogEntry) -> bool:
        filter_key = self.log_filter.currentData() if hasattr(self, "log_filter") else "all"
        query = self.log_search.text() if hasattr(self, "log_search") else ""
        return matches_entry(entry, filter_key or "all", query)

    def _append_entry_to_view(self, entry: LogEntry, *, allow_scroll: bool = True) -> None:
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.log_view.document().isEmpty():
            cursor.insertBlock()
        for segment in entry.segments:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(segment.color))
            fmt.setFontFamily("Cascadia Mono")
            cursor.insertText(segment.text, fmt)
        self.log_view.setTextCursor(cursor)
        if allow_scroll and self.log_autoscroll.isChecked():
            bar = self.log_view.verticalScrollBar()
            bar.setValue(bar.maximum())

    def _render_log(self, *_args) -> None:
        if not hasattr(self, "log_view"):
            return
        bar = self.log_view.verticalScrollBar()
        previous_scroll = bar.value()
        self.log_view.setUpdatesEnabled(False)
        try:
            self.log_view.clear()
            for entry in self._log_entries:
                if self._log_entry_visible(entry):
                    self._append_entry_to_view(entry, allow_scroll=False)
        finally:
            self.log_view.setUpdatesEnabled(True)
        if self.log_autoscroll.isChecked():
            bar.setValue(bar.maximum())
        else:
            bar.setValue(min(previous_scroll, bar.maximum()))

    def _clear_log(self) -> None:
        self._log_entries.clear()
        self.log_view.clear()

    def _open_log_file(self) -> None:
        if self._log_file is not None:
            try:
                self._log_file.flush()
            except OSError:
                pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(LOG_PATH)))

    def _save_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, t("button.save"), "mineai_log_export.txt", "Text files (*.txt);;All files (*)")
        if not path:
            return
        lines = [entry.plain_text for entry in self._log_entries if self._log_entry_visible(entry)]
        try:
            Path(path).write_text("\\n".join(lines) + ("\\n" if lines else ""), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, t("error.title"), str(exc))

    def _set_minecraft_directory(self, path: str) -> None:
        root = Path(path)
        if not root.is_dir():
            return
        settings.set("GENERAL", "mc_dir", str(root))
        self.folder_edit.setText(str(root))
        self._refresh_folder_state()
        self._refresh_system_readiness()

    def _apply_theme(self, theme: str) -> None:
        self._theme_name = "Light" if str(theme).casefold() == "light" else "Dark"
        stylesheet = theme_qss(self._theme_name)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet)
        self.setStyleSheet(stylesheet)
        if hasattr(self, "segmented_progress"):
            self.segmented_progress.set_theme(self._theme_name)

    def _capture_ui_state(self) -> dict[str, object]:
        return {
            "version": self.version_combo.currentText(),
            "target_language": self.language_combo.currentText(),
            "engine": self.engine_combo.currentText(),
            "google_mode": self.google_mode_combo.currentData(),
            "ai_mode": self.ai_mode_combo.currentData(),
            "ai_batch": self.ai_batch_spin.value(),
            "fallback": self.ai_fallback.isChecked(),
            "scope": (self.scope_mods.isChecked(), self.scope_books.isChecked(), self.scope_quests.isChecked()),
            "mode": self._mode_value(),
            "resourcepack": self.output_rp.isChecked(),
            "pack_name": self.pack_name.text(),
        }

    def _rebuild_ui_for_locale(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        state = self._capture_ui_state()
        old = self.takeCentralWidget()
        if old is not None:
            old.deleteLater()
        self._build_ui()
        self.folder_edit.setText(settings.get("GENERAL", "mc_dir"))
        self.version_combo.setCurrentText(str(state["version"]))
        self.language_combo.setCurrentText(str(state["target_language"]))
        self.engine_combo.setCurrentText(str(state["engine"]))
        google_index = self.google_mode_combo.findData(state["google_mode"])
        if google_index >= 0:
            self.google_mode_combo.setCurrentIndex(google_index)
        ai_index = self.ai_mode_combo.findData(state["ai_mode"])
        if ai_index >= 0:
            self.ai_mode_combo.setCurrentIndex(ai_index)
        self.ai_batch_spin.setValue(int(state["ai_batch"]))
        self.ai_fallback.setChecked(bool(state["fallback"]))
        for checkbox, checked in zip((self.scope_mods, self.scope_books, self.scope_quests), state["scope"]):
            checkbox.setChecked(bool(checked))
        self.mode_buttons[str(state["mode"])].setChecked(True)
        self.output_rp.setChecked(bool(state["resourcepack"]))
        self.output_inplace.setChecked(not bool(state["resourcepack"]))
        self.pack_name.setText(str(state["pack_name"]))
        self._refresh_folder_state()
        self._refresh_engine_state()
        self._refresh_system_readiness()
        self._refresh_footer()
        self._apply_theme(self._theme_name)
        self._render_log()

    def dragEnterEvent(self, event) -> None:
        mime = event.mimeData()
        if not mime.hasUrls():
            return
        for url in mime.urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_dir() or (path.is_file() and path.suffix.casefold() == ".zip"):
                event.acceptProposedAction()
                return

    def dropEvent(self, event) -> None:
        local_paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        directory = next((path for path in local_paths if path.is_dir()), None)
        if directory is not None:
            self._set_minecraft_directory(str(directory))

        zip_path = next((path for path in local_paths if path.is_file() and path.suffix.casefold() == ".zip"), None)
        if zip_path is not None:
            answer = QMessageBox.question(
                self,
                t("dialog.drop_zip_title"),
                t("dialog.drop_zip_text", path=str(zip_path)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._open_migration(str(zip_path))
        event.acceptProposedAction()

    def _close_log_sink(self) -> None:
        if self._log_file is None:
            return
        try:
            self._log_file.flush()
            self._log_file.close()
        except OSError:
            pass
        self._log_file = None

'''
text, count = log_pattern.subn(log_replacement, text, count=1)
if count != 1:
    raise RuntimeError(f"log block: expected one match, got {count}")

# Ensure close paths release the line-buffered file handle.
text = text.replace(
    "        if self._allow_close or not (self._worker and self._worker.is_alive()):\n            event.accept()\n            return\n",
    "        if self._allow_close or not (self._worker and self._worker.is_alive()):\n            self._close_log_sink()\n            event.accept()\n            return\n",
    1,
)

run_pattern = re.compile(r"^def run\(\) -> int:\n.*\Z", re.M | re.S)
run_replacement = '''def run() -> int:
    translator.set_language(settings.get("GENERAL", "ui_language"))
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("MineAI Translator")
    app.setStyleSheet(theme_qss(settings.get("GENERAL", "theme")))
    window = TranslatorQtWindow()
    window.show()
    return app.exec()
'''
text, count = run_pattern.subn(run_replacement, text, count=1)
if count != 1:
    raise RuntimeError("run function not found")

PATH.write_text(text, encoding="utf-8")
print("patched", PATH)
