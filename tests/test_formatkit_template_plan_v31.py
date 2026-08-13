import unittest

from mineai.constants import LANGUAGES
from mineai.formatkit_books_bridge import is_formatkit_book_path, plan_book_work


RU = LANGUAGES["Русский"]
PATH = "assets/ars_nouveau/patchouli_books/worn_notebook/en_us/templates/glyph_recipe.json"
SOURCE = '{"processor":"GlyphProcessor","components":[{"recipe_name":"#recipe"},{"text":"#tier#"},{"text":"#mana_cost#"},{"text":"#schools#"}]}'


class FormatKitTemplatePlanV31Tests(unittest.TestCase):
    def test_template_is_owned_with_zero_translation_units(self):
        self.assertTrue(is_formatkit_book_path(PATH))
        work = plan_book_work(PATH, SOURCE, "ru_ru", RU["regex"], None, "append")
        self.assertIsNotNone(work)
        assert work is not None
        self.assertEqual(work.total_translatable, 0)
        self.assertEqual(work.pending, {})
        self.assertTrue(work.source_plan.metadata["patchouli_template_immutable"])
        self.assertEqual(
            work.source_plan.metadata["template_placeholders"],
            ("#recipe", "#tier#", "#mana_cost#", "#schools#"),
        )


if __name__ == "__main__":
    unittest.main()
