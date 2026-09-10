# M5 — Build Log (the lab notebook)

> **Covers:** what actually happened while building M5, brick by brick, as it happened.
> **Status:** current — **open**. **Last verified:** 2026-09-07 (Bricks 0–6 done;
> Brick 7 verified **PASS live on macOS** — the Windows live run is still
> outstanding; Brick 8 doc closeout not yet started).
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
| **Current brick** | Brick 7 — `check_hands.py` PASSes live on macOS; the Windows live run is still outstanding |
| **Hardware** | CPU only, no GPU in play — M5 is plumbing, not training. Windows 11 + Python 3.14 for Bricks 0–6; macOS 26.3.1 (Apple Silicon, arm64) + Python 3.14.7 added for Brick 7's live run |
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

**Amended 2026-09-07 (found during Brick 7's live macOS run):** `classify_cell`
only knew two backgrounds — hidden and revealed. A hidden cell with the
keyboard cursor on it is a third, measured, flat grey. `board_easy_01.png`
never contains that state; it was captured with the mouse. Full story,
measurements and the two new fixtures are logged under Brick 7 below, since
that is where and why it was found — recorded once, not duplicated here.

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
  - Termination helpers: `is_loss`, `is_win`, and `is_terminated` spectacles.
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

## Brick 6 — The profile + factory wiring

**Status:** ✅ done 2026-09-05
**File(s):** `profiles/minesweeper.yaml`, `src/gametrainer/profile.py`, `src/gametrainer/factory.py`, `tests/test_profile.py`, `tests/test_make_env.py`

- **What I built:**
  - `Profile` validation updated: added `"minesweeper"` to legal grounds and rewards, added reward field validation (`safe_reveal_reward`, `mine_penalty`, `win_reward`), and restricted pixels perception for Minesweeper in M5.
  - `profiles/minesweeper.yaml`: Flat YAML profile specifying ground `minesweeper`, perception `numeric`, reward numbers, and PPO hyperparameters.
  - `make_env(profile)`: Factory branch building `MinesweeperEnv` configured directly from the YAML profile, with auto-discovery of live `LibreMines` window/hands and clean fallback to headless/null components in CI.
- **Verified by:**
  - `pytest tests/test_profile.py`: **10 passed in 0.05 s**.
  - `pytest tests/test_make_env.py`: **9 passed in 1.02 s**.
  - Full test suite: **93 passed, 1 skipped in 2.89 s**.
  - `ruff check`: clean across entire repo.
  - **No Python edited** to select Minesweeper — loading `profiles/minesweeper.yaml` builds the entire environment ready to train or run.

---

## Brick 7 — The controls (the proof)

**Status:** ✅ macOS — verified **PASS**, live, 2026-09-07. 🟡 Windows — wired
2026-09-06, still not run live. `M5_ToDo.md`'s own bar was written against
`SendInput`/Windows specifically, so this brick isn't closed until that run
happens too — see "Still open" at the end of this entry.
**File(s):** `scripts/check_hands.py`, `tests/test_check_hands.py`,
`src/gametrainer/screen.py`, `src/gametrainer/input.py`, `setup.py`,
`src/gametrainer/minesweeper_vision.py`, `tests/test_minesweeper_vision.py`

- **What I built (2026-09-06, unchanged today):**
  - Implemented `collect_measurements()` in `scripts/check_hands.py` to drive all 4 controls against LibreMines:
    1. **Control 1 (Keys live):** Resets board, navigates cursor down 1 and right 2 to cell `(1, 2)`, flags it, and verifies exactly cell `(1, 2)` changes state (`HIDDEN` -> `FLAGGED`).
    2. **Control 2 (NullInput):** Swaps in `NullInput()`, dispatches identical moves + flag, and verifies 0 cells change (the negative case).
    3. **Control 3 (Frozen frame):** Grabs a frozen frame, flags a cell with live hands to alter the screen, and asserts that the frozen-frame observation stays completely stationary while the live observation reflects the screen update.
    4. **Control 4 (Reset):** Loops 20 times unattended, dirtying the board by flagging a cell, sending `Ctrl+R`, and verifying all 64 cells cleanly return to `HIDDEN`.
  - Added unit test suite `tests/test_check_hands.py` to test the pure referee logic (`decide_keys_live`, `decide_null_input`, `decide_frozen_frame`, `decide_reset`, `decide_verdict`) with passing and failing synthetic `Measurements`.

- **Scope changed mid-brick, with sign-off, not silently — 2026-09-07.** The
  2026-09-06 entry above scheduled cross-platform native input as "Future
  Milestone M7" and left this brick "ready for a live run on Windows host."
  Windows still hasn't happened. What happened instead: the agent runs
  directly on this Mac, so rather than wait for a Windows session, the user
  asked for a macOS `KeyboardInput`/`GameWindow` backend now, so Brick 7 could
  actually be proven live today. Recorded as a correction, per DOC_STANDARD
  rule 4, rather than quietly overwriting the earlier "M7" note — the M7 plan
  still stands for Linux; macOS just arrived early.

- **The macOS backend, built and proven live (`screen.py`, `input.py`):**
  mirrors the Windows Brick 1/Brick 3 split exactly — one platform branch per
  function, same public interface, same class names:
  - **Window finding:** `Quartz.CGWindowListCopyWindowInfo`, matched by
    **owning app name**, not title — `kCGWindowName` (the title bar text)
    comes back `None` for LibreMines even with every permission granted,
    measured rather than assumed. Returns the app's PID; there is no HWND
    equivalent on this platform, so `GameWindow`/`KeyboardInput` just carry it
    under the same `hwnd` name and never need to know the difference.
  - **Capture:** `mss`, unchanged, fed the Quartz-reported rect. **No DPI
    trap** — verified by capturing a real window and looking at the PNG:
    `CGWindowListCopyWindowInfo` bounds and `mss.grab()` already agree in
    points on this machine, no scale-factor correction needed. Windows and
    macOS disagree about whether "window coordinates" already mean "screen
    pixels," and only a real capture said which this one is.
  - **Focus:** `NSRunningApplication.activateWithOptions_`. Simpler than
    Windows — no foreground-lock/`AttachThreadInput` dance needed; any process
    with Accessibility access can activate another app directly. The OS
    permission prompt for that (System Settings -> Privacy & Security ->
    Accessibility, granted once, by the user, mid-session, to the terminal
    host process) is the macOS parallel to the whole of Windows' `focus()`.
  - **Keys:** `Quartz.CGEventCreateKeyboardEvent` + `CGEventPost`, macOS
    virtual keycodes (`kVK_*`) translated from the shared `VK_*` constants via
    a small lookup table. `CGEventPost` returns nothing, unlike `SendInput` —
    no "N delivered" count to check, so this half of `KeyboardInput` has no
    equivalent of the Windows `_send()`'s `OSError` on a short delivery. The
    only proof a macOS keystroke landed is the behavioural one below.

- **Trap — the official macOS build doesn't launch, out of the box.**
  `libremines-v2.3.0-macos-arm64-qt6.dmg` (sha256
  `eda50945663e1f8ec7218e174bdc4f8f72b873c60c359b39210c340d89fbf8d9`, 41,216,061
  bytes, same v2.3.0 GitHub release as the Windows zip) is ad-hoc-signed but
  the signature covers **no resources** — `spctl -a -vv` says so outright
  ("code has no resources but signature indicates they must be present").
  macOS `SIGKILL`s the process (`CODESIGNING`/"Invalid Page", confirmed in
  four crash reports under `~/Library/Logs/DiagnosticReports/`) the moment it
  tries to load a bundled `.dylib` — which reads exactly like a broken build,
  not a signature problem. Fixed locally: `codesign --remove-signature`, then
  `codesign --deep --force --sign - libremines.app`, re-sealing all 159
  resources under one ad-hoc signature. Not a repo problem — `games/` is
  git-ignored, same as the Windows build — but worth recording once so the
  next machine doesn't lose a session to it.

- **Trap — `Ctrl+R` does nothing on macOS. `Cmd+R` is the real shortcut.**
  LibreMines' own keybinding, unchanged from the Windows spike, is written
  once as "Ctrl+R" (confirmed in the app's bundled README). Qt follows Mac
  convention and remaps that to the **Command** key at runtime, not physical
  Control. Tried three ways before finding this, each against the real
  running game: a raw Control keydown/keyup pair around R, an explicit
  `CGEventFlagMaskControl` set on the R event, and macOS's own `System Events`
  `keystroke "r" using control down` — all three left the board completely
  unchanged (same flag, same mine counter, everything, before and after).
  `keystroke "r" using command down` reset it instantly; a raw `CGEventPost`
  with `CGEventFlagMaskCommand` set on the R event did too. `tap_chord`'s
  macOS branch uses the latter. Recorded in `input.py` as a Teacher Note, same
  style as the Windows `INPUT`-struct-size trap.

- **Bug found and fixed — Brick 2's `classify_cell` didn't know about the
  keyboard cursor.** Moving onto a cell tints its background a third flat
  grey, `(185, 185, 185)` — measured live, 100% fill, on every cell tried,
  flagged or not. `board_easy_01.png` (Brick 2's fixture) never contains this
  state; it was captured with the mouse, and the highlight only appears in
  keyboard mode. `classify_cell` now recognises three backgrounds instead of
  two (`_CURSOR_BODY`, alongside the existing `_HIDDEN_BODY`/`_REVEALED_BODY`);
  a cursor-highlighted cell reads as `HIDDEN`, same as an unhighlighted one,
  and the flag/digit logic on top is unchanged. Two new single-cell fixtures
  (`tests/fixtures/cell_cursor_hidden.png`, `cell_cursor_flagged.png`,
  captured live 2026-09-07) and two new red-first tests in
  `tests/test_minesweeper_vision.py`. **Almost certainly not mac-specific** —
  this is the game's own cursor, not something the OS draws — so the Windows
  live run would very likely have hit the identical `UnreadableCell` the first
  time it tried Control 1.

- **Bug found and fixed — `check_hands.py`'s own Control 1 had an
  off-by-one.** The comment said "down 1, right 2" lands on `(1, 2)`; measured
  live, it landed on `(0, 2)` — the crash that surfaced the `classify_cell`
  gap above was at "row 0, column 2," not row 1. Traced key-by-key: the
  **first** W/A/S/D press only *activates* keyboard-cursor mode and lands the
  cursor at `(0, 0)` — it does not itself count as a move, in any direction.
  Every press after that moves normally (confirmed: two `move_right()` calls
  walked the cursor cleanly `(0,0) -> (0,1) -> (0,2)`). Fixed by sending one
  throwaway `move_down()` to activate mode before the two moves meant to
  count, so `target_cell = (1, 2)` is reached for real — four keys sent for a
  two-step walk, not three. Controls 2-4 were never at risk: none of them
  hardcode a target cell, so landing the activation press on `(0, 0)` instead
  of further along never mattered for what they measure.

- **Verified by — the actual milestone bar, live, on this Mac:**
  `.venv/bin/python scripts/check_hands.py` (LibreMines' theme forced to
  Aqua/light via `defaults write io.github.Bollos00.LibreMines
  NSRequiresAquaSystemAppearance -bool YES`, scoped to this one app, so the
  board matches the fixture's theme rather than this machine's system Dark
  Mode) ->

  ```
  M5 VERDICT: PASS
  [PASS] Control 1 - Keys live       (1 cell changed, target (1,2), exactly)
  [PASS] Control 2 - NullInput       (0 cells changed, 0 pixels)
  [PASS] Control 3 - Frozen frame    (live obs: 1 changed; frozen obs: 0)
  [PASS] Control 4 - Reset           (20/20 resets clean, 0 mouse clicks)
  ```

  Exit code 0. Apple Silicon (arm64), macOS 26.3.1, Python 3.14.7, mss 10.2.0,
  pyobjc-framework-Quartz 12.2.1 (already pulled in transitively by `pynput`;
  declared directly in `setup.py` too, darwin-gated, since this code imports
  `Quartz`/`AppKit` itself). Full suite: **102 passed, 1 skipped** (was 100 + 1
  before today's two new vision tests). `ruff check` clean on every file
  touched today.

- **Two permissions only a human could grant, mid-session:** macOS
  Accessibility (System Settings -> Privacy & Security -> Accessibility,
  granted to the terminal host process this session ran under) for
  `CGEventPost` to reach another app, and Screen Recording (already granted
  before today) for `mss` to capture real pixels. Both are one-time,
  per-machine toggles — the closest macOS parallel to Windows needing no
  elevated privilege at all, just a foreground window.

- **Known follow-up, not fixed today — `make_env`'s live auto-discovery is
  now reachable on macOS too.** `factory.py`'s bare `make_env(MINESWEEPER)`
  tries `GameWindow("LibreMines")` and falls back to `NullInput` only on
  exception (Brick 6 design, unchanged today). Before today this always fell
  back on macOS, because `GameWindow` always raised there; now that it
  doesn't, a real LibreMines window left open on the developer's desktop
  while running `pytest` gets picked up and actually driven by
  `test_minesweeper_env_passes_check_env_and_matches_space` (it calls
  `stable_baselines3`'s `check_env`, which really exercises `reset()`/
  `step()`). Caused one flaky failure mid-session, immediately after a live
  `check_hands.py` run; not reproduced across three clean repeats with the
  game fully closed afterward. Left alone deliberately — this is a Brick 6
  test-isolation question (should that test inject stub `hands`/`window`
  instead of relying on auto-discovery-plus-fallback?), and the identical risk
  already existed on Windows, just never triggered there by accident. Needs a
  decision, not a quiet patch.

- **Still open: the Windows live run itself.** Everything above proves the
  macOS backend and fixes two bugs that would very likely have hit Windows
  too, but `M5_ToDo.md`'s own bar was written against `SendInput`/Windows
  specifically, and nobody has run `check_hands.py` there since Brick 3's
  platform guard was added 2026-09-06. That run — with both fixes above
  already in place — is what actually closes this brick.

---
