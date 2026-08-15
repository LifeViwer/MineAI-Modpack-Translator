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
    PatchouliBookJsonAdapter,
    ValidationError,
)

ADAPTERS = (
    ModonomiconBookJsonAdapter(),
    PatchouliBookJsonAdapter(),
    ImmersiveEngineeringManualAdapter(),
)
GENERIC_LOCALE = MinecraftLangJsonAdapter()


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


def proven_bad_candidate(unit) -> str | None:
    """Return a mutation that is definitely invalid for this exact unit.

    Do not invent generic policy here. A plain locale string without protected
    structure may legitimately contain punctuation, backslashes or line breaks
    depending on its runtime contract. Removing a FormatKit-owned protected
    placeholder, however, is always a proven invariant violation.
    """

    if unit.protected:
        return unit.text.replace(unit.protected[0].placeholder, "", 1)
    return None


def audit_plan(adapter, plan) -> int:
    identity = {unit.id: unit.text for unit in plan.units}
    adapter.apply(plan, identity)
    if plan.units:
        adapter.apply(
            plan,
            {unit.id: synthetic_candidate(unit) for unit in plan.units},
        )
        for victim in plan.units:
            bad = proven_bad_candidate(victim)
            if bad is None:
                continue
            try:
                # The integration profile deliberately keeps the public adapter
                # as the single source of truth. No MineAI-local validation
                # helper or private parser method participates in certification.
                adapter.apply(plan, {victim.id: bad})
            except (ValidationError, ValueError):
                break
            raise ValidationError(
                f"protected-fragment mutation unexpectedly accepted for {victim.id}"
            )
    return len(plan.units)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the pinned MineAI FormatKit profile against real mod JARs."
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
                for name in archive.namelist():
                    adapter = next(
                        (candidate for candidate in ADAPTERS if candidate.matches(name)),
                        None,
                    )
                    if adapter is None and GENERIC_LOCALE.matches(name):
                        adapter = GENERIC_LOCALE
                    if adapter is None:
                        continue
                    try:
                        source = archive.read(name).decode("utf-8-sig")
                        plan = adapter.prepare(name, source)
                        units = audit_plan(adapter, plan)
                        bucket = getattr(adapter, "name", type(adapter).__name__)
                        stats[bucket]["files"] += 1
                        stats[bucket]["units"] += units
                        if bucket == "minecraft-lang-json":
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
        "formatkit_source_sha": __import__("mineai_formatkit").FORMATKIT_SOURCE_SHA,
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
