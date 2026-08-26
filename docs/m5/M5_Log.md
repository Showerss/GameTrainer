# M5 — Build Log (the lab notebook)

> **Covers:** what actually happened while building M5, brick by brick, as it happened.
> **Status:** current — **open**. **Last verified:** 2026-08-26 (Brick 0 written and
> running; Bricks 1–8 not started).
> **Authority:** `docs/m5/M5_ToDo.md` owns *the plan*. This file owns *the record of
> doing it*. `docs/m5/M5_Review.md` (written last) owns *what it all meant*.

---

## How to use this file

Fill in a brick's block **when it closes**, not at the end.

- **Write it the day it happens** — a log from memory is a story, not evidence.
- **Numbers carry their conditions** (rule 3): number, baseline (same run),
  hardware, wall-clock, command. No exceptions.
- **Wrong results stay in** — strike through, add a dated correction. Never delete.
- **Surprises are the most important section** — log the moment something looks
  off, before you know what it means.

---

## State of play

| | |
| :--- | :--- |
| **Milestone** | M5 — Add the Hands (real key presses, a real game window) |
| **Started** | 2026-08-25 (pre-flight spike + plan) |
| **Branch** | `m5-implementation` |
| **Current brick** | Brick 1 — window handle + DPI-correct capture |
| **Hardware** | CPU (Windows 11, Python 3.14). No GPU in play — M5 is plumbing, not training |
| **Closed** | not yet |

---

## Brick 0 — The guardrail (written first)

**Status:** ✅ done 2026-08-26
**File(s):** `scripts/check_hands.py` (referee only — nothing to measure yet)

- **The bar:** four controls, all four required. (1) move to a named cell and
  flag it — **exactly** that cell changes. (2) same sequence with `NullInput` —
  **nothing** changes. (3) freeze the frame — the screen changes but the
  observation does **not**. (4) `Ctrl+R` gives a fresh board **20×**, unattended.
- **What I built:** the referee only. A `Measurements` dataclass holding every
  number the verdict is allowed to see, one `decide_*` function per control, and
  `decide_verdict()` on top. All pure logic — numbers in, PASS/FAIL out — so it
  can be read and tested with no game running.
- **What it does today:** `collect_measurements()` raises `NotImplementedError`,
  naming the bricks it waits on. The script prints the bar, then **NOT RUN**, and
  exits 1. Deliberate: a guardrail that reports success before the work is done is
  worse than no guardrail. Filling it in is Brick 7.
- **Decision — flag, not reveal:** control 1 originally said *reveal*. Reveal
  cascades (the spike's one `O` changed 147,631 px across many cells), so "changes
  in exactly that cell" was a condition it could never satisfy. Flag toggles
  exactly one cell, always. `M5_ToDo.md` corrected in place with a dated note.
- **Decision — cells, not pixels:** the spike's own numbers killed the pixel bar.
  A flag changed **237 px**; a no-op reveal on an already-revealed cell changed
  **342 px**. A pixel count cannot tell "something happened" from "nothing
  happened", and here it points the wrong way. The verdict counts changed **cells**
  on the 8×8 grid; pixel counts are printed as evidence and decide nothing.
- **Verified by:** `.venv/Scripts/python.exe scripts/check_hands.py` → prints the
  finish line, then `M5 VERDICT: NOT RUN`, exit code 1. `ruff check` clean.
  Instant; no training, no game process.

> **Lesson carried from M3:** control 1 on its own proves nothing — a screen that
> changes while keys are sent looks identical whether or not the keys mattered.
> Controls 2 and 3 are the negative cases, and they are the whole point.

---
