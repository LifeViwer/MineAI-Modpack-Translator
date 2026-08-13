import json
import unittest

from mineai.constants import LANGUAGES
from mineai.formatkit_books_bridge import build_book_output, plan_book_work


class FormatKitV32PatchouliTests(unittest.TestCase):
    def test_newline_candidate_falls_back_without_losing_neighbor(self):
        path = "assets/demo/patchouli_books/manual/en_us/entries/demo.json"
        source = json.dumps({"name": "Demo Guide", "pages": [{"type": "patchouli:text", "text": "First paragraph."}, {"type": "patchouli:text", "text": "Second paragraph."}]})
        work = plan_book_work(path, source, "ru_ru", LANGUAGES["Русский"]["regex"], None, "force")
        assert work is not None
        output = json.loads(build_book_output(work, {"json:/pages/0/text": "Translated first paragraph.", "json:/pages/1/text": "Broken\nparagraph."}))
        self.assertEqual(output["pages"][0]["text"], "Translated first paragraph.")
        self.assertEqual(output["pages"][1]["text"], "Second paragraph.")


if __name__ == "__main__":
    unittest.main()
