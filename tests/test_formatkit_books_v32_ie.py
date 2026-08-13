import unittest

from mineai.constants import LANGUAGES
from mineai.formatkit_books_bridge import build_book_output, plan_book_work
from mineai_formatkit import ImmersiveEngineeringManualAdapter, TranslationPlan, TranslationUnit


class FormatKitV32IeTests(unittest.TestCase):
    def test_newline_candidate_falls_back_without_losing_neighbor(self):
        path = "assets/immersiveengineering/manual/en_us/demo.txt"
        source = "First line.\nSecond line.\n"
        work = plan_book_work(path, source, "ru_ru", LANGUAGES["Русский"]["regex"], None, "force")
        assert work is not None
        ids = list(work.pending)
        output = build_book_output(work, {ids[0]: "Translated first line.", ids[1]: "Broken\nline."})
        self.assertEqual(output, "Translated first line.\nSecond line.\n")

    def test_current_bounds_and_reset_boundary_are_vendored(self):
        path = "assets/immersiveengineering/manual/en_us/demo.txt"
        plan = ImmersiveEngineeringManualAdapter().prepare(path, "Use §2graphite§r. However, continue.\n")
        self.assertIn("§r. ", [fragment.value for fragment in plan.units[0].protected])
        with self.assertRaisesRegex(ValueError, "Invalid translation unit range"):
            TranslationPlan("demo", "abc", (TranslationUnit("bad", "x", 2, 2, "test"),))


if __name__ == "__main__":
    unittest.main()
