from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mineai_formatkit import (  # noqa: E402
    ImmersiveEngineeringManualAdapter,
    MinecraftLangJsonAdapter,
    ModonomiconBookJsonAdapter,
    ModonomiconLangJsonAdapter,
    PatchouliBookJsonAdapter,
    PatchouliTemplateJsonAdapter,
    ValidationError,
)

ADAPTERS = (
    PatchouliBookJsonAdapter(),
    PatchouliTemplateJsonAdapter(),
    ImmersiveEngineeringManualAdapter(),
    ModonomiconBookJsonAdapter(),
)
GENERIC_LOCALE = MinecraftLangJsonAdapter()
MODONOMICON_LOCALE = ModonomiconLangJsonAdapter()


def iter_jars(inputs: list[str]):
    seen_hashes: set[str] = set()
    for raw in inputs:
        path = Path(raw)
        candidates = [path] if path.is_file() else sorted(path.rglob("*.jar"))
        for candidate in candidates:
            if candidate.suffix.lower() != ".jar":
                continue
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            yield candidate, digest


def synthetic_candidate(unit) -> str:
    return "Тест " + unit.text


def bad_candidate(unit) -> str | None:
    if unit.protected:
        return unit.text.replace(unit.protected[0].placeholder, "", 1)
    if "\n" not in unit.text and "\r" not in unit.text:
        return unit.text + "\nBAD"
    if "\\" not in unit.text:
        return unit.text + "\\BAD"
    return None


def audit_plan(adapter, plan) -> int:
    identity = {unit.id: unit.text for unit in plan.units}
    adapter.apply(plan, identity)
    if plan.units:
        adapter.apply(
            plan,
            {unit.id: synthetic_candidate(unit) for unit in plan.units},
        )
        victim = plan.units[0]
        bad = bad_candidate(victim)
        if bad is not None:
            try:
                validator = getattr(adapter, "validate_candidate", None)
                if callable(validator):
                    validator(plan, victim.id, bad)
                else:
                    adapter.apply(plan, {victim.id: bad})
            except (ValidationError, ValueError):
                pass
            else:
                raise ValidationError(
                    f"adversarial candidate unexpectedly accepted for {victim.id}"
                )
    return len(plan.units)


def archive_has_modonomicon(names: list[str]) -> bool:
    adapter = ModonomiconBookJsonAdapter()
    return any(adapter.matches(name) for name in names)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run MineAI-FormatKit adapters against real mod JARs."
    )
    parser.add_argument("inputs", nargs="+", help="JARs or directories containing JARs")
    parser.add_argument("--json", dest="json_path", help="Optional JSON report output")
    args = parser.parse_args()

    stats: dict[str, Counter] = defaultdict(Counter)
    failures: list[dict[str, str]] = []
    jar_count = 0
    manifests: list[dict[str, str]] = []

    for jar, digest in iter_jars(args.inputs):
        jar_count += 1
        manifests.append({"path": str(jar), "sha256": digest})
        try:
            with zipfile.ZipFile(jar, "r") as archive:
                names = archive.namelist()
                has_modono = archive_has_modonomicon(names)
                for name in names:
                    adapter = next(
                        (candidate for candidate in ADAPTERS if candidate.matches(name)),
                        None,
                    )
                    if adapter is None and GENERIC_LOCALE.matches(name):
                        adapter = MODONOMICON_LOCALE if has_modono else GENERIC_LOCALE
                    if adapter is None:
                        continue
                    try:
                        source = archive.read(name).decode("utf-8-sig")
                        plan = adapter.prepare(name, source)
                        units = audit_plan(adapter, plan)
                        bucket = getattr(adapter, "name", type(adapter).__name__)
                        stats[bucket]["files"] += 1
                        stats[bucket]["units"] += units
                        if bucket == "modonomicon-lang-json":
                            stats[bucket]["book_units"] += sum(
                                unit.context.startswith("book.") for unit in plan.units
                            )
                    except Exception as exc:
                        bucket = getattr(adapter, "name", type(adapter).__name__)
                        stats[bucket]["failures"] += 1
                        failures.append(
                            {
                                "jar": str(jar),
                                "path": name,
                                "adapter": bucket,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
        except (OSError, zipfile.BadZipFile) as exc:
            failures.append(
                {
                    "jar": str(jar),
                    "path": "",
                    "adapter": "archive",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    report = {
        "jars": jar_count,
        "adapters": {name: dict(counter) for name, counter in sorted(stats.items())},
        "failures": failures,
        "manifest": manifests,
    }
    print(f"JARs: {jar_count}")
    for name, counter in sorted(stats.items()):
        extra = f" book_units={counter['book_units']}" if counter.get("book_units") else ""
        print(
            f"{name}: files={counter['files']} units={counter['units']}"
            f"{extra} failures={counter['failures']}"
        )
    print(f"TOTAL FAILURES: {len(failures)}")
    for failure in failures[:25]:
        print(
            f"FAIL {failure['adapter']} {failure['jar']}::{failure['path']} "
            f"{failure['error']}"
        )
    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
