import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication, QToolButton
    from mineai.gui_qt.main_window import TranslatorQtWindow
    from mineai.gui_qt.widgets import ScrollSafeComboBox, ScrollSafeSpinBox
except ImportError:
    QApplication = None
    QToolButton = None
    TranslatorQtWindow = None
    ScrollSafeComboBox = None
    ScrollSafeSpinBox = None


@unittest.skipIf(QApplication is None, "PyQt6 is not installed")
class WheelSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_combo_ignores_wheel(self):
        combo = ScrollSafeComboBox()
        event = _FakeWheelEvent()
        combo.wheelEvent(event)
        self.assertTrue(event.ignored)

    def test_spinbox_ignores_wheel(self):
        spin = ScrollSafeSpinBox()
        event = _FakeWheelEvent()
        spin.wheelEvent(event)
        self.assertTrue(event.ignored)

    def test_spinbox_paints_both_step_indicators(self):
        spin = _ProbeSpinBox()
        try:
            spin.resize(180, 36)
            spin.show()
            self.app.processEvents()
            spin.indicator_calls.clear()
            spin.repaint()
            self.app.processEvents()

            directions = {upward for _, upward in spin.indicator_calls}
            self.assertEqual(directions, {True, False})
            self.assertTrue(all(rect.isValid() and not rect.isEmpty() for rect, _ in spin.indicator_calls))
        finally:
            spin.close()

    def test_locale_rebuild_keeps_google_and_ai_panels_synchronized(self):
        window = TranslatorQtWindow()
        try:
            window.engine_combo.setCurrentText("Google")
            window._rebuild_ui_for_locale()
            self.assertFalse(window.google_options.isHidden())
            self.assertTrue(window.ai_options.isHidden())

            ai_index = next(
                i for i in range(window.engine_combo.count())
                if window.engine_combo.itemText(i) in ("Локальный ИИ", "Local AI")
            )
            window.engine_combo.setCurrentIndex(ai_index)
            window._rebuild_ui_for_locale()
            self.assertTrue(window.google_options.isHidden())
            self.assertFalse(window.ai_options.isHidden())
        finally:
            window.close()

    def test_language_control_is_compact_toggle(self):
        window = TranslatorQtWindow()
        try:
            self.assertIsInstance(window.interface_language, QToolButton)
            self.assertIn(window.interface_language.text(), {"RU", "EN"})
            self.assertEqual(window.interface_language.width(), 46)
        finally:
            window.close()


class _ProbeSpinBox(ScrollSafeSpinBox if ScrollSafeSpinBox is not None else object):
    def __init__(self):
        super().__init__()
        self.indicator_calls = []

    def _draw_step_chevron(self, painter, rect, upward):
        self.indicator_calls.append((rect, upward))


class _FakeWheelEvent:
    def __init__(self):
        self.ignored = False

    def ignore(self):
        self.ignored = True


if __name__ == "__main__":
    unittest.main()
