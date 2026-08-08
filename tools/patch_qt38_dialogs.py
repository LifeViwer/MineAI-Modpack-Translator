from pathlib import Path

path = Path("mineai/gui_qt/dialogs.py")
text = path.read_text(encoding="utf-8")

text = text.replace("    QCheckBox,\n", "    QCheckBox,\n    QComboBox,\n", 1)
text = text.replace(
    "from mineai.gui_qt.bridge import MigrationSignals\n",
    "from mineai.gui_qt.bridge import MigrationSignals\n"
    "from mineai.gui_qt.i18n import LANGUAGE_LABELS, t\n"
    "from mineai.gui_qt.widgets import HelpMarker\n",
    1,
)

replacements = {
    'self.setWindowTitle("Настройки MineAI")': 'self.setWindowTitle(t("settings.title"))',
    'tabs.addTab(ai_tab, "Локальный ИИ")': 'tabs.addTab(ai_tab, t("settings.tab.local"))',
    'tabs.addTab(or_tab, "OpenRouter")': 'tabs.addTab(or_tab, t("settings.tab.openrouter"))',
    'tabs.addTab(general_tab, "Общие и API")': 'tabs.addTab(general_tab, t("settings.tab.general"))',
    '"Исполняемый файл KoboldCPP (.exe)"': 't("settings.local_exe")',
    '"Модель (.gguf)"': 't("settings.model")',
    '"Слои GPU"': 't("settings.gpu_layers")',
    'QLabel("Ключ можно создать на openrouter.ai/keys. API URL также подходит для OpenAI-compatible шлюзов.")': 'QLabel(t("settings.or_note"))',
    '"API URL", config.get("OPENROUTER", "api_url")': 't("settings.api_url"), config.get("OPENROUTER", "api_url")',
    '"API ключ OpenRouter", config.get("OPENROUTER", "api_key")': 't("settings.or_key"), config.get("OPENROUTER", "api_key")',
    '"ID модели", config.get("OPENROUTER", "model")': 't("settings.model_id"), config.get("OPENROUTER", "model")',
    '"Site URL (необязательно)", config.get("OPENROUTER", "site_url")': 't("settings.site_url"), config.get("OPENROUTER", "site_url")',
    '"Название приложения (X-Title)", config.get("OPENROUTER", "app_name")': 't("settings.app_title"), config.get("OPENROUTER", "app_name")',
    '"Повторы ИИ при ошибке"': 't("settings.ai_retries")',
    '"Потоки Google Translate"': 't("settings.google_workers")',
    '"API ключ DeepL"': 't("settings.deepl")',
    'QPushButton("Отмена")': 'QPushButton(t("button.cancel"))',
    'QPushButton("Сохранить настройки")': 'QPushButton(t("button.save_settings"))',
    'QPushButton("Обзор")': 'QPushButton(t("button.browse"))',
    'QFileDialog.getOpenFileName(self, "Выберите файл", edit.text(), file_filter)': 'QFileDialog.getOpenFileName(self, t("dialog.choose_file"), edit.text(), file_filter)',
    'self.setWindowTitle("Редактор промптов ИИ")': 'self.setWindowTitle(t("prompts.title"))',
    '("mods", "Интерфейс (Моды)")': '("mods", t("prompts.mods"))',
    '("books", "Книги / Справочники")': '("books", t("prompts.books"))',
    '("quests", "Квесты")': '("quests", t("prompts.quests"))',
    '"Переменные: {lang_name} (язык), {context} (название мода/файла)"': 't("prompts.note")',
    '"Тех. правила (ОПАСНО)"': 't("prompts.technical")',
    '"Изменение технических правил может сломать JSON и маркеры. {markers} — точный список [#N#] текущего запроса."': 't("prompts.tech_note")',
    'QLabel("Все изменения сохранены")': 'QLabel(t("prompts.saved"))',
    'QPushButton("Сбросить")': 'QPushButton(t("button.reset"))',
    'QPushButton("Сохранить")': 'QPushButton(t("button.save_prompt"))',
    'self.dirty_label.setText("● Есть несохранённые изменения")': 'self.dirty_label.setText(t("prompts.dirty"))',
    '"Сбросить промпты?"': 't("prompts.reset_title")',
    '"Все четыре промпта будут заменены значениями по умолчанию. Продолжить?"': 't("prompts.reset_text")',
    'self.dirty_label.setText("Все изменения сохранены")': 'self.dirty_label.setText(t("prompts.saved"))',
    'box.setWindowTitle("Сохранить изменения?")': 'box.setWindowTitle(t("prompts.close_title"))',
    'box.setText("В редакторе промптов есть несохранённые изменения.")': 'box.setText(t("prompts.close_text"))',
    'self.setWindowTitle("Миграция перевода")': 'self.setWindowTitle(t("migration.title"))',
    'QLabel("Миграция готового перевода")': 'QLabel(t("migration.heading"))',
    'QLabel("Импортирует строки из существующего Resource Pack в отдельный imported cache. Исходный ZIP не изменяется.")': 'QLabel(t("migration.note"))',
    'QLabel("RESOURCE PACK (.ZIP)")': 'QLabel(t("migration.resource_pack"))',
    'QLabel("КЭШ НАЗНАЧЕНИЯ")': 'QLabel(t("migration.destination"))',
    'QRadioButton("Нейросети · imported_caches/ai")': 'QRadioButton(t("migration.ai"))',
    'QRadioButton("Google / DeepL · imported_caches/std")': 'QRadioButton(t("migration.std"))',
    'QPushButton("Начать миграцию")': 'QPushButton(t("migration.run"))',
    'QMessageBox.critical(self, "Ошибка", "Выберите валидный ZIP-архив.")': 'QMessageBox.critical(self, t("error.title"), t("migration.invalid_zip"))',
    'self.run_button.setText("Выполнение…")': 'self.run_button.setText(t("migration.running"))',
    'self.result_title.setText("Миграция завершилась с ошибкой")': 'self.result_title.setText(t("migration.error"))',
    'self.result_title.setText("✓ Миграция завершена")': 'self.result_title.setText(t("migration.done"))',
    'self.run_button.setText("Запустить снова")': 'self.run_button.setText(t("migration.rerun"))',
    '"Миграция выполняется"': 't("migration.busy_title")',
    '"Дождитесь завершения миграции перед закрытием окна."': 't("migration.busy_text")',
}
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)

old_smart = '''        self.smart_glue = QCheckBox(t("settings.smart_glue")) if False else QCheckBox("Умный склейщик предложений")
'''
# The source is expected to still have the original three-line smart-glue block.
source_smart = '''        self.smart_glue = QCheckBox("Умный склейщик предложений")
        self.smart_glue.setChecked(config.getboolean("GENERAL", "smart_glue"))
        general_layout.addWidget(self.smart_glue)
'''
smart = '''        smart_row = QHBoxLayout()
        self.smart_glue = QCheckBox(t("settings.smart_glue"))
        self.smart_glue.setChecked(config.getboolean("GENERAL", "smart_glue"))
        smart_row.addWidget(self.smart_glue)
        smart_row.addWidget(HelpMarker(t("tooltip.smart_glue")))
        smart_row.addStretch(1)
        general_layout.addLayout(smart_row)
'''
if source_smart not in text:
    raise RuntimeError("smart glue block not found")
text = text.replace(source_smart, smart, 1)

needle = '''        self.deepl_key = self._line_row(general_layout, t("settings.deepl"), config.get("API", "deepl_key"), secret=True)
        general_layout.addStretch(1)
'''
addition = '''        self.deepl_key = self._line_row(general_layout, t("settings.deepl"), config.get("API", "deepl_key"), secret=True)

        general_layout.addWidget(self._field_label(t("settings.ui_language")))
        self.ui_language = QComboBox()
        for code, label in LANGUAGE_LABELS.items():
            self.ui_language.addItem(label, code)
        language_index = self.ui_language.findData(config.get("GENERAL", "ui_language"))
        self.ui_language.setCurrentIndex(language_index if language_index >= 0 else 0)
        general_layout.addWidget(self.ui_language)

        general_layout.addWidget(self._field_label(t("settings.theme")))
        self.theme = QComboBox()
        self.theme.addItem(t("theme.dark"), "Dark")
        self.theme.addItem(t("theme.light"), "Light")
        theme_index = self.theme.findData(config.get("GENERAL", "theme"))
        self.theme.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        general_layout.addWidget(self.theme)
        general_layout.addStretch(1)
'''
if needle not in text:
    raise RuntimeError("general settings insertion point not found")
text = text.replace(needle, addition, 1)

old_general = '''        self.config.set_many("GENERAL", {
            "smart_glue": self.smart_glue.isChecked(),
            "google_workers": self.google_workers.value(),
        })
'''
new_general = '''        self.config.set_many("GENERAL", {
            "smart_glue": self.smart_glue.isChecked(),
            "google_workers": self.google_workers.value(),
            "ui_language": self.ui_language.currentData() or "ru",
            "theme": self.theme.currentData() or "Dark",
        })
'''
if old_general not in text:
    raise RuntimeError("settings save block not found")
text = text.replace(old_general, new_general, 1)

# Drag-and-drop can prefill the migration ZIP without changing the migration API.
old_sig = '    def __init__(self, mc_dir: str, lang_label: str, cache_std, cache_ai, log_callback, parent=None) -> None:\n'
new_sig = '    def __init__(self, mc_dir: str, lang_label: str, cache_std, cache_ai, log_callback, parent=None, *, initial_zip: str | None = None) -> None:\n'
if old_sig not in text:
    raise RuntimeError("MigrationDialog signature not found")
text = text.replace(old_sig, new_sig, 1)
text = text.replace('        self.zip_edit = QLineEdit()\n', '        self.zip_edit = QLineEdit(initial_zip or "")\n', 1)

old_result = '''            destination = "Нейросети" if cache_type == "ai" else "Google / DeepL"
            self.result_title.setText(t("migration.done"))
            self.result_title.setObjectName("ReadyText")
            self.result_details.setText(
                f"Импортировано: {count} уникальных строк\\n"
                f"Кэш назначения: {destination}\\n"
                "Детализация пропусков/конфликтов недоступна в текущем migration API."
            )
'''
new_result = '''            destination = t("migration.destination_ai") if cache_type == "ai" else t("migration.destination_std")
            self.result_title.setText(t("migration.done"))
            self.result_title.setObjectName("ReadyText")
            self.result_details.setText(t("migration.result", count=count, destination=destination))
'''
if old_result in text:
    text = text.replace(old_result, new_result, 1)

path.write_text(text, encoding="utf-8")
print("patched", path)
