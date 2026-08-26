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
| **Current brick** | Brick 2 — tile classification (red-first) |
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

## Brick 1 — Window handle + DPI-correct capture

**Status:** ✅ done 2026-08-26
**File(s):** `src/gametrainer/screen.py`

- **What I built:** `GameWindow` — finds a window by title substring, and
  returns its pixels as a `(h, w, 3)` BGR numpy array. Two module functions
  underneath it (`find_window`, `window_rect`) and one guard
  (`set_dpi_awareness`). No game knowledge in this file; reading a board out of
  the pixels is Brick 2.
- **The DPI trap, handled:** `SetProcessDpiAwarenessContext(-4)` runs at
  **import time**, before anything in the process can ask about a window. Import
  order is load-bearing, so it is not left to a caller to remember. It raises if
  the call fails for any reason other than "already set" — a silent failure here
  produces captures aligned to nothing, which is the worst way to be wrong.
  `user32` is loaded with `use_last_error=True`, or `get_last_error()` would
  report a stale code and the guard would be decorative.
- **Rect re-read every grab, not cached.** Resolves an M5 open question. The
  spike found window geometry unstable across launches, and `MoveWindow`
  reporting success while the window sat elsewhere. Re-reading costs nothing and
  removes a class of "numbers looked fine, capture was stale" bug.
- **Game given a permanent home:** copied to `games/libremines/` (was living in
  a throwaway session scratchpad). `games/` added to `.gitignore`. Zip sha256
  re-checked: `c8dbcbe9…a65706` — **matches** the value recorded in `M5_ToDo.md`.
- **Verified by:** launched the game, captured, saved the PNG, **and looked at
  it**. Window `LibreMines`, rect `2576×1408 @ (-8, -8)` (maximized this launch;
  the spike's was `716×539` — geometry really is unstable). Frame came back
  `(1408, 2576, 3)` uint8 — dimensions match the rect exactly, and the image is
  unmistakably the LibreMines difficulty chooser. `ruff` clean; suite **68
  passed, 1 skipped** (unchanged — nothing imports this yet).
- **No unit test, deliberately** (testing policy #4). This is window/focus glue:
  it cannot be tested without a live window, and it fails loudly the first time
  it runs. Its behavioural check is Brick 0's controls.
- **Deferred to v2:** capturing a **minimised** window. Size and position are
  already handled — title lookup plus a per-grab rect re-read follows the window
  anywhere — but a minimised window isn't drawn, so there is nothing to capture.
  Recorded in `docs/PRD.md` §8, which owns scope. Not an M5 problem: keystrokes
  need the window in the foreground anyway.

**Surprise:** the game opened **maximized** this time, not at the spike's
`716×539`. Two consequences worth carrying: the board occupies a small fraction
of a large frame, so Brick 2 must *locate* the board rather than assume it fills
the window; and any tile geometry hardcoded from one launch will be wrong on the
next.

> **Trap #3 seen live:** the very first capture is the Easy/Medium/Hard chooser,
> not a board. Exactly what the spike warned about — keys do nothing until a game
> is started. Something has to click a difficulty before the loop can begin.

---
