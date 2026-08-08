from pathlib import Path

service_path = Path("mineai/engines/service.py")
service = service_path.read_text(encoding="utf-8")
old = '            callbacks.on_log(f" > {item.original[:40]} -> {text[:40]}{dup}", "dim")\n'
new = '            callbacks.on_log(f" > {item.original} -> {text}{dup}", "dim")\n'
if old not in service:
    raise SystemExit("translation log preview snippet not found")
service = service.replace(old, new, 1)
service_path.write_text(service, encoding="utf-8")

test_path = Path("tests/test_translation_service.py")
tests = test_path.read_text(encoding="utf-8")
anchor = '''    def test_short_technical_identity_is_not_retranslated(self):\n'''
test = '''    def test_success_log_keeps_full_source_and_translation_text(self):\n        source = (\n            "A deliberately long source sentence that exceeds forty characters "\n            "and must remain complete in the GUI journal"\n        )\n        translated = (\n            "Это намеренно длинная переведённая строка длиннее сорока символов, "\n            "которая должна полностью отображаться в журнале"\n        )\n        engine = _Engine(lambda items: {next(iter(items)): translated})\n        logs = []\n        result = _Service(engine, _MemoryCache(), _Config()).translate_dict(\n            {"key": source},\n            TARGET_LANG,\n            _callbacks(logs),\n        )\n\n        self.assertEqual(result, {"key": translated})\n        self.assertIn((f" > {source} -> {translated}", "dim"), logs)\n\n'''
if anchor not in tests:
    raise SystemExit("test insertion anchor not found")
tests = tests.replace(anchor, test + anchor, 1)
test_path.write_text(tests, encoding="utf-8")

print("full translation log patch applied")
