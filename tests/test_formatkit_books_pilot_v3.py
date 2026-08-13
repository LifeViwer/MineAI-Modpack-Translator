import json
import os
import shutil
import tempfile
import unittest
import zipfile
from types import SimpleNamespace

from mineai.constants import LANGUAGES
from mineai.formatkit_books_bridge import build_book_output, plan_book_work
from mineai.processors.formatkit_books_pilot import (
    FormatKitBooksJarProcessor,
    FormatKitBooksStringEstimator,
    FormatKitModpackAnalyzer,
)
from mineai.runtime.state import JobState
from mineai_formatkit import PatchouliBookJsonAdapter, ValidationError

RU = LANGUAGES["Русский"]


class FormatKitPatchouliV3Tests(unittest.TestCase):
    path = "assets/advancedperipherals/patchouli_books/manual/en_us/entries/peripherals/chat_box.json"

    def test_real_chat_box_literal_dollar_and_patchouli_token_are_protected(self):
        source = json.dumps(
            {
                "name": "Chat Box",
                "pages": [
                    {
                        "type": "patchouli:text",
                        "text": "Start the message with a `$`.$(p)Read the documentation.",
                    }
                ],
            },
            ensure_ascii=False,
        )
        work = plan_book_work(self.path, source, "ru_ru", RU["regex"], None, "force")
        assert work is not None
        text_id = next(k for k in work.pending if "/pages/0/text" in k)
        masked = work.pending[text_id]
        self.assertNotIn("`$`", masked)
        self.assertNotIn("$(p)", masked)
        self.assertEqual(masked.count("[#"), 2)

        output = json.loads(
            build_book_output(
                work,
                {
                    "json:/name": "Чат-окно",
                    text_id: "Начните сообщение с [#0#].[#1#]Читайте документацию.",
                },
            )
        )
        self.assertIn("`$`", output["pages"][0]["text"])
        self.assertIn("$(p)", output["pages"][0]["text"])
        self.assertNotIn("`$$", output["pages"][0]["text"])

    def test_patchouli_sdk_rejects_same_markers_in_wrong_order(self):
        source = '{"pages":[{"type":"patchouli:text","text":"Use $(9)Name$() then $(p)More"}]}'
        adapter = PatchouliBookJsonAdapter()
        plan = adapter.prepare(self.path, source)
        unit = plan.units[0]
        self.assertEqual([f.placeholder for f in unit.protected], ["[#0#]", "[#1#]", "[#2#]"])
        with self.assertRaises(ValidationError):
            adapter.apply(plan, {unit.id: "Текст [#1#]Имя[#0#] далее [#2#]"})

    def test_corrupted_existing_dollar_is_not_reused(self):
        source = '{"pages":[{"type":"patchouli:text","text":"Start with a `$`.$(p)More"}]}'
        target = '{"pages":[{"type":"patchouli:text","text":"Начните с `$$.$(p)Подробнее"}]}'
        work = plan_book_work(self.path, source, "ru_ru", RU["regex"], target, "append")
        assert work is not None
        self.assertEqual(len(work.preserved), 0)
        self.assertEqual(len(work.pending), 1)

    def test_safe_reformatted_existing_patchouli_target_is_reused(self):
        source = '{"name":"Chat Box","pages":[{"type":"patchouli:text","text":"Start with a `$`.$(p)More"}]}'
        target = json.dumps(
            {
                "name": "Чат-окно",
                "pages": [{"type": "patchouli:text", "text": "Начните с `$`.$(p)Подробнее"}],
            },
            ensure_ascii=False,
            indent=4,
        )
        work = plan_book_work(self.path, source, "ru_ru", RU["regex"], target, "append")
        assert work is not None
        self.assertIsNone(work.target_parse_error)
        self.assertEqual(len(work.pending), 0)
        self.assertEqual(len(work.preserved), 2)


class FormatKitIeManualV3Tests(unittest.TestCase):
    path = "assets/immersiveengineering/manual/en_us/arc_furnace.txt"

    def test_manual_preserves_exact_line_structure_and_tokens(self):
        source = (
            "Arc Furnace\n"
            "Use <link;machines/arc_furnace;Arc Furnace> to smelt ores.\n"
            "Keep §6power§r supplied.\n"
        )
        work = plan_book_work(self.path, source, "ru_ru", RU["regex"], None, "force")
        assert work is not None
        translated = {}
        for unit_id, text in work.pending.items():
            markers = [part for part in text.split() if part.startswith("[#")]
            if "Arc Furnace" == text:
                translated[unit_id] = "Дуговая печь"
            elif "smelt ores" in text:
                translated[unit_id] = "Используйте для переплавки руд."
            elif "power" in text.lower():
                # Formatting markers are protected and must remain in order.
                translated[unit_id] = "Поддерживайте [#0#]энергию[#1#]."
            elif text == "Arc Furnace":
                translated[unit_id] = "Дуговая печь"
            else:
                translated[unit_id] = "Дуговая печь"
        output = build_book_output(work, translated)
        self.assertEqual(output.count("\n"), source.count("\n"))
        self.assertEqual(len(output.splitlines()), len(source.splitlines()))
        self.assertIn("<link;machines/arc_furnace;", output)
        self.assertIn("§6", output)
        self.assertIn("§r", output)
        work.adapter.validate(source, output)

    def test_manual_rejects_reordered_section_markers(self):
        source = "Keep §6power§r supplied.\n"
        work = plan_book_work(self.path, source, "ru_ru", RU["regex"], None, "force")
        assert work is not None
        unit_id = next(iter(work.pending))
        with self.assertRaises(ValidationError):
            build_book_output(work, {unit_id: "Поддерживайте [#1#]энергию[#0#]."})


class FormatKitBookParityV3Tests(unittest.TestCase):
    def _make_jar(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)
        path = os.path.join(temp_dir, "books.jar")
        patchouli = json.dumps(
            {
                "name": "Chat Box",
                "pages": [{"type": "patchouli:text", "text": "Start with a `$`.$(p)More"}],
            }
        )
        manual = "Arc Furnace\nUse <link;machines/arc_furnace;Arc Furnace>.\nKeep §6power§r supplied.\n"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr(
                "assets/advancedperipherals/patchouli_books/manual/en_us/entries/chat_box.json",
                patchouli,
            )
            z.writestr("assets/immersiveengineering/manual/en_us/arc_furnace.txt", manual)
        return path

    def test_analyzer_and_estimator_share_formatkit_book_counts(self):
        path = self._make_jar()
        state = JobState(); state.start()
        rows = []
        analyzed = FormatKitModpackAnalyzer(state)._analyze_jar(
            path, "ru_ru.json", RU["regex"], False, True,
            lambda *row: rows.append(row), "Books",
        )
        estimated = FormatKitBooksStringEstimator(state)._estimate_jar(
            path, "ru_ru.json", RU, "force", False, True, True
        )
        self.assertEqual(analyzed[0], estimated)
        self.assertGreater(estimated, 0)
        self.assertTrue(any(row[2] == "Книга(JSON)" for row in rows))
        self.assertTrue(any(row[2] == "Книга(MD)" for row in rows))

    def test_processor_routes_patchouli_through_formatkit(self):
        path = self._make_jar()
        class Service:
            config = SimpleNamespace(getboolean=lambda *_args, **_kwargs: True)
            def translate_dict(self, pending, _lang, _callbacks, **_kwargs):
                out = {}
                for key, value in pending.items():
                    if "Chat Box" in value:
                        out[key] = "Чат-окно"
                    elif value.count("[#") == 2:
                        out[key] = "Начните с [#0#].[#1#]Подробнее"
                    elif value == "Arc Furnace":
                        out[key] = "Дуговая печь"
                    elif "power" in value.lower():
                        out[key] = "Поддерживайте [#0#]энергию[#1#]."
                    else:
                        out[key] = value
                return out
        class Writer:
            def __init__(self): self.writes = {}
            def write(self, p, payload): self.writes[p] = payload
        logs=[]; writer=Writer()
        processor = FormatKitBooksJarProcessor(
            Service(), SimpleNamespace(should_run=lambda: True),
            SimpleNamespace(on_log=lambda text, color: logs.append(text)),
        )
        with zipfile.ZipFile(path) as z:
            locale={e.filename.lower():e for e in z.infolist()}
            item=z.getinfo("assets/advancedperipherals/patchouli_books/manual/en_us/entries/chat_box.json")
            ok=processor._process_book_json(z,None,item,locale,RU,"force","resourcepack",writer,"Advancedperipherals",set())
        self.assertTrue(ok)
        self.assertIn("assets/advancedperipherals/patchouli_books/manual/ru_ru/entries/chat_box.json", writer.writes)
        output=json.loads(writer.writes[next(iter(writer.writes))].decode())
        self.assertIn("`$`", output["pages"][0]["text"])
        self.assertTrue(any("Patchouli/FormatKit" in line for line in logs))


if __name__ == "__main__":
    unittest.main()
