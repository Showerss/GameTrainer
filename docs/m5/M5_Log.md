# M5 — Build Log (the lab notebook)

> **Covers:** what actually happened while building M5, brick by brick, as it happened.
> **Status:** current — **open**. **Last verified:** 2026-09-05 (Bricks 0–5 done;
> Bricks 6–8 not started).
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
| **Current brick** | Brick 6 — The profile + factory wiring |
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

## Brick 2 — Tile classification (red-first)

**Status:** ✅ done 2026-09-03
**File(s):** `tests/test_minesweeper_vision.py` (red, written 2026-08-30) →
`src/gametrainer/minesweeper_vision.py`

- **What I built:** `read_board(frame)` — one full-window capture in, an 8×8
  grid of cell states out. Two jobs underneath: `find_board()` locates the
  minefield in the picture, `classify_cell()` reads each of the 64 cells.
  States are `0`–`8`, `HIDDEN`, `FLAGGED`, `MINE`.
- **The board is found, never assumed.** Brick 1's surprise — the game opens at
  a different size every launch — means no geometry can be hardcoded. What does
  hold is the *shape*: the minefield is the one big **square** block of dark
  pixels on a near-white window. So: largest dark blob that is square (±5%) and
  solid (≥80% filled). In the fixture that is **(18, 41), 1326×1326** — 165.75
  px a cell. The window frame is dark too, but at 2568×1408 it fails squareness.
- **How a cell is read:** one flat background with at most one glyph drawn on it. Grey
  `70,70,70` = hidden, dark `26,26,26` = revealed; any pixel far from that
  background is "ink". Coloured ink is something we can name (1 = blue
  `255,104,0`, 2 = green `0,130,0`, 3 = red `0,0,255`). Grey ink is not.
- **Red means two different things.** The flag and the digit 3 are the *same*
  red. Nothing in the colour separates them — only what is underneath does. Red
  on grey is a flag; red on dark is a 3. Background first, glyph second.
- **The margins, measured across all 64 cells of the fixture:** hidden and blank
  cells carry **0.0%** ink; the faintest real glyph (the flag) **13.4%**; digits
  **46–54%**. The threshold sits at **5%**, in a gap with nothing in it.
- **An unknown glyph raises rather than guesses.** The fixture has no 4–8 and no
  mine, so those have never been measured here. Under a colour-only rule a black
  7 or a mine would read as "blank" — a silent wrong answer feeding the reward,
  which is the M3 lesson exactly. Ink with no colour in it raises
  `UnreadableCell`, naming what it saw. `MINE` is defined but never returned
  yet; Brick 5 needs it (a mine ends the episode) and gets a fixture with one.
- **Verified by:** `.venv/Scripts/python.exe -m pytest tests/test_minesweeper_vision.py -q`
  → **2 passed in 0.36 s**. Full suite **70 passed, 1 skipped in 2.64 s** (was
  68 + 1; the two new ones are this brick). `ruff check` clean. CPU, Windows 11,
  Python 3.14.
- **Checked by hand, not kept as tests:** the same fixture rescaled 0.35×–1.5×
  and moved onto a larger desktop reads back the **identical** grid, so the
  geometry instability really is handled. All-white and all-dark frames both
  raise `BoardNotFound` — which is what the difficulty chooser will do.

**Surprise — the eyes cost 133 ms.** `read_board` on a 2576×1408 frame takes
**133 ms** on CPU (`find_board` 43 ms, the 64 cells 81 ms), mean of 20 runs.
That is a ceiling of **~7 steps a second** before the game, the keys or PPO have
done anything — the first real number on the ToDo's open question "what is the
step rate through a live window?". Harmless for Brick 0's four scripted
controls; it is the number that decides whether any *learning* observation is
affordable later. Most of it is scanning a mostly-empty maximized window, so the
cheap fix, if we ever need one, is a smaller game window.

---

## Brick 3 — KeyboardInput (the real hands)

**Status:** ✅ done 2026-09-04
**File(s):** `src/gametrainer/input.py` (committed 2026-09-03 in `90dbe64`)

- **What I built:** `KeyboardInput` subclassing `InputController`, matching `NullInput`'s interface. Provides LibreMines controls via Windows `SendInput`: W/A/S/D for cursor navigation, O for reveal, P for flag, and `Ctrl+R` (`tap_chord`) for reset.
- **The guards:**
  - 40-byte `INPUT` struct size asserted at import time (`sizeof(_INPUT) == 40`) to prevent silent `SendInput` parameter failure (error 87).
  - Focus check and `focus()` implementation using `AttachThreadInput` + `SetForegroundWindow` to bypass Windows foreground locks; refuses to type if target window is not active.
  - `escape()` explicitly raises `RuntimeError` to prevent exiting keyboard navigation mode.
  - Mouse moves/clicks raise `NotImplementedError` (M5 gameplay is keyboard-only).
  - Non-Windows environments raise `RuntimeError` on instantiation while allowing `NullInput` to run smoothly everywhere.
- **Verified by:** `.venv/bin/python -m pytest` → **70 passed, 1 skipped in 5.29 s** (CPU, macOS/Linux/Windows portable; full suite unbroken). Drop-in interface matches `NullInput`.
- **No unit test, deliberately** (testing policy #4): Window/focus/input injection cannot be tested in CI without a live Windows desktop; full behavioral verification belongs to Brick 0 / Brick 7 controls (`scripts/check_hands.py`).

---

## Brick 4 — Reward from two grids (red-first)

**Status:** ✅ done 2026-09-04
**File(s):** `tests/test_minesweeper_rewards.py` (red) → `src/gametrainer/rewards.py`

- **What I built:** `MinesweeperRewardCalculator` — pure function of two consecutive board grids (`prev_grid`, `curr_grid`).
- **Reward maths:**
  - `mine_penalty` (e.g. `-10.0`) on mine hit (loss).
  - `win_reward` (e.g. `+10.0`) when all 54 safe cells on an 8×8 Easy board are revealed.
  - `safe_reveal_reward` (e.g. `+1.0`) per newly revealed safe cell (`0`–`8`). Cascades scale the reward directly with cells revealed.
  - Moving cursor or flagging gives `0.0`.
  - Termination helpers: `is_loss`, `is_win`, and `is_terminated`.
- **Verified by:** `.venv/bin/python -m pytest tests/test_minesweeper_rewards.py` → **8 passed in 0.06 s**. Full suite **78 passed, 1 skipped in 1.51 s**. `ruff check` clean.

---

## Brick 5 — The env (the Gymnasium contract)

**Status:** ✅ done 2026-09-05
**File(s):** `tests/test_minesweeper_env.py` (red) → `src/gametrainer/minesweeper.py`

- **What I built:** `MinesweeperEnv` subclassing `gymnasium.Env`.
  - **Action space:** `spaces.Discrete(6)` mapped to UP (0), DOWN (1), LEFT (2), RIGHT (3), REVEAL (4), FLAG (5).
  - **Observation space:** `spaces.Box(low=0, high=11, shape=(8, 8), dtype=np.int8)` matching tile classification states (0–8 counts, 9 HIDDEN, 10 FLAGGED, 11 MINE).
  - **The contract:** `reset()` returns 2-tuple `(obs, info)` and triggers `hands.restart()` (`Ctrl+R`); `step()` returns 5-tuple `(obs, reward, terminated, truncated, info)`.
  - **Pluggable dependencies:** Accepts injectable `hands` (`InputController`), `window` (`GameWindow`), `reward_calculator` (`MinesweeperRewardCalculator`), and `read_board_fn` for headless/test operation without requiring a live game window.
  - **Step cap:** `truncated=True` when `_steps >= max_steps` and not terminated.
- **Verified by:**
  - `.venv/Scripts/python.exe -m pytest tests/test_minesweeper_env.py` → **9 passed in 0.95 s**.
  - `gymnasium.utils.env_checker.check_env` runs completely clean.
  - `stable_baselines3.common.env_checker.check_env` clean.
  - Full test suite: **87 passed, 1 skipped in 2.73 s**. `ruff check` clean.

---
