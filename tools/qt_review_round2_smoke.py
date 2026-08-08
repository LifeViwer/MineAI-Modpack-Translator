from pathlib import Path
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from mineai.config import settings
from mineai.gui_qt.i18n import translator, t
from mineai.gui_qt.i18n_runtime import tr as rt
from mineai.gui_qt.main_window import TranslatorQtWindow
from mineai.gui_qt.widgets import ElidedLabel, HelpMarker


def assert_inside(widget, top) -> None:
    if not widget.isVisible():
        return
    p = widget.mapTo(top, widget.rect().topLeft())
    rect = widget.rect().translated(p)
    bounds = top.rect()
    assert rect.left() >= 0, (widget, rect, bounds)
    assert rect.top() >= 0, (widget, rect, bounds)
    assert rect.right() <= bounds.right(), (widget, rect, bounds)
    assert rect.bottom() <= bounds.bottom(), (widget, rect, bounds)


app = QApplication.instance() or QApplication([])
translator.set_language("ru")
settings.set("GENERAL", "ui_language", "ru")
settings.set("GENERAL", "theme", "Dark")

with tempfile.TemporaryDirectory() as temp_dir:
    model = Path(temp_dir) / (
        "YandexGPT-5-Lite-8B-instruct-Q4_K_M-very-long-local-model-name-"
        "that-must-never-break-the-sidebar-layout.gguf"
    )
    model.touch()
    settings.set("AI", "model_path", str(model))

    window = TranslatorQtWindow()
    window.resize(window.minimumSize())
    window.show()
    app.processEvents()

    assert window.minimumWidth() == 1240
    sidebar = window.findChild(type(window.centralWidget()), "SidebarHost")
    assert sidebar is not None
    assert sidebar.width() == 430

    window.engine_combo.setCurrentText(rt("engine.local"))
    app.processEvents()
    assert isinstance(window.engine_ready_label, ElidedLabel)
    assert model.name in window.engine_ready_label.fullText()
    assert model.name in window.engine_ready_label.toolTip()
    assert window.engine_ready_label.text().endswith("…"), window.engine_ready_label.text()
    assert_inside(window.engine_ready_label, window)

    assert [window.mode_buttons[key].text() for key in ("append", "skip", "force")] == [
        "Дополнить", "Пропустить", "Заново"
    ]
    assert window.output_rp.text() == "Ресурс-пак"
    assert window.output_inplace.text() == "Прямо в JAR"
    for key in ("append", "skip", "force"):
        assert window.mode_buttons[key].toolTip()
        assert_inside(window.mode_buttons[key], window)
    assert window.output_rp.toolTip()
    assert window.output_inplace.toolTip()
    assert_inside(window.output_rp, window)
    assert_inside(window.output_inplace, window)
    assert "40" in window.ai_batch_label.text()
    assert "15 строк или меньше" in t("tooltip.ai_batch")

    marker = HelpMarker("instant help")
    assert callable(marker._show_help)
    marker._show_help()

    translator.set_language("en")
    settings.set("GENERAL", "ui_language", "en")
    window._ui_language = "en"
    window._rebuild_ui_for_locale()
    app.processEvents()
    assert [window.mode_buttons[key].text() for key in ("append", "skip", "force")] == [
        "Append", "Skip", "Force"
    ]
    assert window.output_rp.text() == "Resource Pack"
    assert window.output_inplace.text() == "In-place"
    assert "40" in window.ai_batch_label.text()

    window.close()
    app.processEvents()

print("Qt review round 2 smoke PASS")
