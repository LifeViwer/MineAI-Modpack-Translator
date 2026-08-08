from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected snippet not found in {path}: {old[:160]!r}")
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one snippet in {path}, found {text.count(old)}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Main window: widen sidebar, elide long readiness text and localize mode controls.
replace_once(
    "mineai/gui_qt/main_window.py",
    "        self.setMinimumSize(1180, 760)\n",
    "        self.setMinimumSize(1240, 760)\n",
)
replace_once(
    "mineai/gui_qt/main_window.py",
    "from mineai.gui_qt.widgets import Card, HelpMarker, LabeledValue, SegmentedProgressBar, StatCard, StatusPill\n",
    "from mineai.gui_qt.widgets import Card, ElidedLabel, HelpMarker, LabeledValue, SegmentedProgressBar, StatCard, StatusPill\n",
)
replace_once(
    "mineai/gui_qt/main_window.py",
    "        host.setFixedWidth(390)\n",
    "        host.setFixedWidth(430)\n",
)
replace_once(
    "mineai/gui_qt/main_window.py",
    '''        self.engine_ready_label = QLabel(t("engine.checking"))\n        self.engine_ready_label.setObjectName("ReadyText")\n''',
    '''        self.engine_ready_label = ElidedLabel(t("engine.checking"))\n        self.engine_ready_label.setObjectName("ReadyText")\n''',
)
replace_once(
    "mineai/gui_qt/main_window.py",
    '''        batch_label = QLabel(t("field.ai_batch"))\n        ai_grid.addWidget(batch_label, 1, 0)\n        ai_grid.addWidget(HelpMarker(t("tooltip.ai_batch")), 1, 1)\n''',
    '''        self.ai_batch_label = QLabel(t("field.ai_batch_limit"))\n        ai_grid.addWidget(self.ai_batch_label, 1, 0)\n        ai_grid.addWidget(HelpMarker(t("tooltip.ai_batch")), 1, 1)\n''',
)
replace_once(
    "mineai/gui_qt/main_window.py",
    '''        self.mode_buttons: dict[str, QPushButton] = {}\n        for value, label in (("append", "Append"), ("skip", "Skip"), ("force", "Force")):\n            button = QPushButton(label)\n            button.setObjectName("SegmentButton")\n            button.setCheckable(True)\n            if value == "append":\n                button.setChecked(True)\n            self.mode_group.addButton(button)\n            self.mode_buttons[value] = button\n            mode_row.addWidget(button, 1)\n''',
    '''        self.mode_buttons: dict[str, QPushButton] = {}\n        for value in ("append", "skip", "force"):\n            button = QPushButton(t(f"mode.{value}"))\n            button.setObjectName("SegmentButton")\n            button.setCheckable(True)\n            button.setToolTip(t(f"tooltip.mode_{value}"))\n            if value == "append":\n                button.setChecked(True)\n            self.mode_group.addButton(button)\n            self.mode_buttons[value] = button\n            mode_row.addWidget(button, 1)\n''',
)
replace_once(
    "mineai/gui_qt/main_window.py",
    '''        self.output_rp = QPushButton(t("output.resourcepack"))\n        self.output_inplace = QPushButton(t("output.inplace"))\n        for button in (self.output_rp, self.output_inplace):\n''',
    '''        self.output_rp = QPushButton(t("output.resourcepack"))\n        self.output_inplace = QPushButton(t("output.inplace"))\n        self.output_rp.setToolTip(t("tooltip.output_resourcepack"))\n        self.output_inplace.setToolTip(t("tooltip.output_inplace"))\n        for button in (self.output_rp, self.output_inplace):\n''',
)

# Reusable elided readiness label + immediate help-marker tooltips.
replace_once(
    "mineai/gui_qt/widgets.py",
    "from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QToolButton, QVBoxLayout, QWidget\n",
    "from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QToolButton, QToolTip, QVBoxLayout, QWidget\n",
)
replace_once(
    "mineai/gui_qt/widgets.py",
    '''\n\nclass HelpMarker(QToolButton):\n''',
    '''\n\nclass ElidedLabel(QLabel):\n    """Single-line label that never forces its container wider than available space."""\n\n    def __init__(self, text: str = "", parent=None) -> None:\n        super().__init__(parent)\n        self._full_text = ""\n        self.setMinimumWidth(0)\n        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)\n        self.setText(text)\n\n    def setText(self, text: str) -> None:\n        self._full_text = str(text)\n        self._refresh_elision()\n\n    def fullText(self) -> str:\n        return self._full_text\n\n    def _refresh_elision(self) -> None:\n        width = self.contentsRect().width()\n        if width <= 1:\n            visible = self._full_text\n        else:\n            visible = self.fontMetrics().elidedText(\n                self._full_text,\n                Qt.TextElideMode.ElideRight,\n                width,\n            )\n        super().setText(visible)\n        self.setToolTip(self._full_text)\n\n    def resizeEvent(self, event) -> None:\n        super().resizeEvent(event)\n        self._refresh_elision()\n\n\nclass HelpMarker(QToolButton):\n''',
)
replace_once(
    "mineai/gui_qt/widgets.py",
    '''        self.setFixedSize(20, 20)\n        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)\n\n\nclass Card(QFrame):\n''',
    '''        self.setFixedSize(20, 20)\n        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)\n\n    def _show_help(self) -> None:\n        text = self.toolTip()\n        if text:\n            QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), text, self)\n\n    def enterEvent(self, event) -> None:\n        self._show_help()\n        super().enterEvent(event)\n\n    def mousePressEvent(self, event) -> None:\n        self._show_help()\n        super().mousePressEvent(event)\n\n    def leaveEvent(self, event) -> None:\n        QToolTip.hideText()\n        super().leaveEvent(event)\n\n\nclass Card(QFrame):\n''',
)

# RU localization and explanatory tooltips.
replace_once(
    "mineai/gui_qt/i18n.py",
    '        "field.ai_batch": "Пакет",\n',
    '        "field.ai_batch": "Пакет",\n        "field.ai_batch_limit": "Пакет (макс. 40)",\n',
)
replace_once(
    "mineai/gui_qt/i18n.py",
    '''        "field.processing": "Обработка",\n        "field.output": "Выход",\n        "output.resourcepack": "Resource Pack",\n        "output.inplace": "In-place",\n        "output.pack_placeholder": "Имя Resource Pack / Datapack",\n''',
    '''        "field.processing": "Обработка",\n        "field.output": "Выход",\n        "mode.append": "Дополнить",\n        "mode.skip": "Пропустить",\n        "mode.force": "Заново",\n        "output.resourcepack": "Ресурс-пак",\n        "output.inplace": "Прямо в JAR",\n        "output.pack_placeholder": "Имя ресурс-пака / датапака",\n''',
)
replace_once(
    "mineai/gui_qt/i18n.py",
    '''        "tooltip.migration": "Импортировать существующий Resource Pack в отдельный кэш переводов.",\n        "tooltip.inplace": "Изменяет JAR-файлы модов напрямую. Используйте только если понимаете риск; Resource Pack безопаснее.",\n        "tooltip.fallback": "Если AI не смог получить валидный перевод, разрешить резервную попытку через Google Translate.",\n        "tooltip.smart_glue": "Объединяет фрагменты предложений перед переводом, чтобы улучшить связность текста. Может менять границы исходных строк.",\n        "tooltip.ai_batch": "Количество строк, отправляемых AI за один запрос. Большие пачки быстрее, но требуют больше контекста и памяти модели.",\n''',
    '''        "tooltip.migration": "Импортировать существующий Resource Pack в отдельный кэш переводов.",\n        "tooltip.inplace": "Изменяет JAR-файлы модов напрямую. Используйте только если понимаете риск; Resource Pack безопаснее.",\n        "tooltip.mode_append": "Дополняет существующий перевод: переводит только отсутствующие или всё ещё совпадающие с исходником строки, сохраняя уже переведённые.",\n        "tooltip.mode_skip": "Пропускает почти готовые файлы (если переведено 90% или больше); остальные дополняет только недостающими строками.",\n        "tooltip.mode_force": "Переводит подходящие строки заново, даже если для них уже есть перевод.",\n        "tooltip.output_resourcepack": "Записывает результат в отдельный ресурс-пак / датапак и не изменяет исходные JAR-файлы.",\n        "tooltip.output_inplace": "Записывает перевод непосредственно в JAR-файлы модов. Этот режим рискованнее ресурс-пака и требует подтверждения перед запуском.",\n        "tooltip.fallback": "Если AI не смог получить валидный перевод, разрешить резервную попытку через Google Translate.",\n        "tooltip.smart_glue": "Объединяет фрагменты предложений перед переводом, чтобы улучшить связность текста. Может менять границы исходных строк.",\n        "tooltip.ai_batch": "Количество строк, отправляемых AI за один запрос. Большие пачки быстрее, но требуют больше контекста и памяти модели. Для моделей на 8B лучше использовать 15 строк или меньше.",\n''',
)

# EN equivalents keep locale parity.
replace_once(
    "mineai/gui_qt/i18n.py",
    '        "field.ai_batch": "Batch",\n',
    '        "field.ai_batch": "Batch",\n        "field.ai_batch_limit": "Batch (max. 40)",\n',
)
replace_once(
    "mineai/gui_qt/i18n.py",
    '''        "field.processing": "Processing",\n        "field.output": "Output",\n        "output.resourcepack": "Resource Pack",\n        "output.inplace": "In-place",\n        "output.pack_placeholder": "Resource Pack / Datapack name",\n''',
    '''        "field.processing": "Processing",\n        "field.output": "Output",\n        "mode.append": "Append",\n        "mode.skip": "Skip",\n        "mode.force": "Force",\n        "output.resourcepack": "Resource Pack",\n        "output.inplace": "In-place",\n        "output.pack_placeholder": "Resource Pack / Datapack name",\n''',
)
replace_once(
    "mineai/gui_qt/i18n.py",
    '''        "tooltip.migration": "Import an existing Resource Pack into a separate translation cache.",\n        "tooltip.inplace": "Changes mod JAR files directly. Use only if you understand the risk; Resource Pack mode is safer.",\n        "tooltip.fallback": "If AI cannot produce a valid translation, allow a fallback attempt through Google Translate.",\n        "tooltip.smart_glue": "Joins sentence fragments before translation to improve coherence. It can change original line boundaries.",\n        "tooltip.ai_batch": "Number of lines sent to AI in one request. Larger batches are faster but require more model context and memory.",\n''',
    '''        "tooltip.migration": "Import an existing Resource Pack into a separate translation cache.",\n        "tooltip.inplace": "Changes mod JAR files directly. Use only if you understand the risk; Resource Pack mode is safer.",\n        "tooltip.mode_append": "Completes an existing translation: only missing entries or entries still equal to the source are translated, while existing translations are preserved.",\n        "tooltip.mode_skip": "Skips files that are already at least 90% translated; other files are completed with missing entries only.",\n        "tooltip.mode_force": "Translates eligible source entries again even when a translation already exists.",\n        "tooltip.output_resourcepack": "Writes the result to a separate Resource Pack / Datapack without modifying original mod JAR files.",\n        "tooltip.output_inplace": "Writes translations directly into mod JAR files. This is riskier than Resource Pack mode and requires confirmation before starting.",\n        "tooltip.fallback": "If AI cannot produce a valid translation, allow a fallback attempt through Google Translate.",\n        "tooltip.smart_glue": "Joins sentence fragments before translation to improve coherence. It can change original line boundaries.",\n        "tooltip.ai_batch": "Number of lines sent to AI in one request. Larger batches are faster but require more model context and memory. For 8B models, 15 lines or fewer is recommended.",\n''',
)

# Pure regression tests stay PyQt-independent so the normal suite still works without optional Qt.
replace_once(
    "tests/test_qt_ux_hardening.py",
    '''    def test_engine_readiness_uses_current_interface_language(self):\n''',
    '''    def test_mode_labels_and_batch_guidance_are_localized(self):\n        self.assertEqual(t("mode.append"), "Дополнить")\n        self.assertEqual(t("mode.skip"), "Пропустить")\n        self.assertEqual(t("mode.force"), "Заново")\n        self.assertEqual(t("output.resourcepack"), "Ресурс-пак")\n        self.assertEqual(t("output.inplace"), "Прямо в JAR")\n        self.assertIn("макс. 40", t("field.ai_batch_limit"))\n        self.assertIn("15 строк или меньше", t("tooltip.ai_batch"))\n        self.assertIn("90%", t("tooltip.mode_skip"))\n\n        translator.set_language("en")\n        self.assertEqual(t("mode.append"), "Append")\n        self.assertEqual(t("output.resourcepack"), "Resource Pack")\n        self.assertIn("max. 40", t("field.ai_batch_limit"))\n        self.assertIn("15 lines or fewer", t("tooltip.ai_batch"))\n\n    def test_engine_readiness_uses_current_interface_language(self):\n''',
)

print("Qt review round 2 patch applied")
