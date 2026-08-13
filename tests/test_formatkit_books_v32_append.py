import json
import unittest

from mineai.constants import LANGUAGES
from mineai.formatkit_books_bridge import plan_book_work


class FormatKitV32AppendTests(unittest.TestCase):
    def test_existing_patchouli_newline_drift_is_not_reused(self):
        path = "assets/demo/patchouli_books/manual/en_us/entries/demo.json"
        source = json.dumps({"name": "Demo Guide", "pages": [{"type": "patchouli:text", "text": "Single paragraph."}]})
        target = json.dumps({"name": "Russian Guide", "pages": [{"type": "patchouli:text", "text": "Broken\nparagraph."}]})
        work = plan_book_work(path, source, "ru_ru", LANGUAGES["Русский"]["regex"], target, "append")
        assert work is not None
        self.assertIn("json:/pages/0/text", work.pending)
        self.assertNotIn("json:/pages/0/text", work.preserved)


if __name__ == "__main__":
    unittest.main()
