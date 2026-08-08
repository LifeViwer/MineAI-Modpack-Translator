# MineAI PyQt6 Dark Dashboard Preview

This branch contains an optional PyQt6 presentation layer built on top of the current beta runtime.

- Existing `TranslationJob`, `JobState`, engines, processors, caches and output safety remain the source of truth.
- The production CustomTkinter entrypoint is intentionally unchanged.
- Launch the preview with `python -m mineai.gui_qt` after installing `requirements-qt.txt`.
- Engine readiness is configuration readiness, not a network connectivity claim.
- Dashboard counters, rate and ETA are derived from the existing thread-safe `JobState` snapshot.

This file is staging documentation and is not required in the clean review branch.
