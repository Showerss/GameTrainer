# M5 — Add the Hands (real key presses, a real game window)

> **Covers:** the M5 plan — scope, the verified pre-flight spike, design decisions,
> bricks, and the finish line.
> **Status:** current. **Last verified:** 2026-08-26 (Brick 0 written; control 1
> corrected from *reveal* to *flag* and the verdict fixed to cells-not-pixels — see
> the dated note under "Brick 0". Rest of the file re-read and still accurate;
> pre-flight spike from 2026-08-25 unchanged).
> **Authority:** `docs/PRD.md` owns *what* gets built and in what order. This file
> owns *what M5 requires*. Brick-by-brick notes go in `docs/m5/M5_Log.md`; the
> retrospective is `docs/m5/M5_Review.md`, written last.

> **Milestone goal (from PRD §7):** `KeyboardInput` sends real key presses; the loop
> drives a tiny real game window end-to-end.
>
> **Done when…** A separate Minesweeper window (LibreMines) is driven by **real key
> presses** and read by **`mss` screen capture**, with **zero in-memory connection to
> the game**, and `scripts/check_hands.py` prints **PASS on all four controls**.

M4 proved the whole *Ground* is swappable while everything stayed inside one Python
process. M5 is the first milestone where the loop **leaves the process**: the game is
a separate program, the eyes are a screen grab, and the hands are keystrokes the
operating system delivers to a window we do not own.

---

## The bar is plumbing, not learning

**M5 does not require PPO to learn Minesweeper.** Say it out loud, because the
temptation to move this bar mid-milestone will be real (CLAUDE.md §5 forbids it).

Minesweeper from pixels is a partially-observable logic problem whose first move is
pure luck. It is a genuine research problem, not three weeks of evenings. What M5
proves is that **the socket carries real input and real vision** — the same thing
`NullInput` has been standing in for since M0. Whether the borrowed brain then
masters this particular game is M6's business or nobody's.

---

## Pre-flight — the spike (run 2026-08-25, PASS)

Option B ("a game you didn't write") normally dies on two problems: how the agent
restarts the game, and where a score comes from. Both were checked **before**
committing to the milestone.

**Target:** LibreMines v2.3.0, Qt6 Windows build, GPL-3.
Source: `https://github.com/Bollos00/LibreMines` →
`libremines-v2.3.0-windows-qt6.zip`,
sha256 `c8dbcbe925e0d7b418b4dbd639e258a0de9c2e633715d655408914a798a65706`.
Portable — extracts and runs, installs nothing.

**Verified controls:** `W`/`A`/`S`/`D` move the cursor (and any of them *enters*
keyboard mode — no menu needed), `O` reveals, `P` flags, `Ctrl+R` restarts.
`Escape` **exits keyboard mode and must never be sent.**

**Result — synthetic `SendInput` keystrokes against an Easy (8×8, 10 mines) board.**
Windows 11, CPU only, single run, window 716×539 at (2742, 446), captured with
`mss` 10.2.0. Numbers are changed pixels inside the window between consecutive frames:

| Key sent | Pixels changed | Reading |
| :--- | ---: | :--- |
| `W` | 3,248 | keyboard cursor appears on one cell |
| `D` | 6,496 | **exactly 2 × 3,248** — old cell cleared, new cell highlighted |
| `D` | 6,496 | same again — the signature is deterministic, not noise |
| `O` | 147,631 | reveal, with cascade |
| `O` (again) | 342 | already-revealed cell — near-no-op, as expected |
| `P` | 237 | flag toggles on one cell |
| `Ctrl+R` | 44,287 | board resets to all-unrevealed |

Command: `.venv/Scripts/python.exe spike6.py <libremines.exe> <out-prefix>`
(scratchpad only — not committed; it is superseded by Brick 1).

**Verdict: PASS.** LibreMines accepts synthetic input, the cursor is keyboard-driven,
and reset is a keystroke. The `D = 2 × W` arithmetic is the evidence that the keys
are really landing, rather than the screen merely changing for some other reason.

Evidence kept alongside this plan: `spike_board_start.png` (fresh 8×8 board) and
`spike_after_reveal.png` (after the synthetic `O` — cascade revealed, keyboard cursor
visible as the white cell).

### What the spike cost us — three traps, all real, all now known

Recorded because each one silently produced a *wrong* result before it was
understood, and each will cost a day again if forgotten (DOC_STANDARD rule 4):

1. **`INPUT` must be 40 bytes on x64.** A 32-byte struct makes every `SendInput` call
   fail with error 87 (`ERROR_INVALID_PARAMETER`) and **zero pixels change** — which
   reads exactly like "the game ignores synthetic input." It does not. The union must
   be sized by `MOUSEINPUT` (32 bytes), not `KEYBDINPUT` (24 bytes).
2. **DPI virtualisation silently misaligns the capture.** Without
   `SetProcessDpiAwarenessContext(-4)`, `GetWindowRect` returns logical coordinates
   while `mss` grabs physical pixels. On this machine the capture landed on a browser
   window one monitor over, and every diff was meaningless. Set DPI awareness
   **before any window call**.
3. **Keys do nothing on the difficulty menu.** LibreMines opens on an
   Easy/Medium/Hard/Custom chooser; `W`/`O`/`P` are gameplay-only. Every key read as
   0 px changed until a game was actually started. A board must exist before the loop
   begins.

Also observed: window geometry is **not** stable across launches (it reopened on a
second monitor at a different size), `SetForegroundWindow` hits the Windows
foreground lock and needs the `AttachThreadInput` dance, and the game process dies
with its parent when the parent's process tree is killed.

---

## Scope discipline (what M5 is NOT)

- ❌ **PPO is not required to learn Minesweeper.** See "The bar is plumbing" above.
  A learning curve is a *nice-to-have* observation for the Log, never the finish line.
- ❌ **No Stardew.** That's M6, and it's a reward problem, not an input one.
- ❌ **No mouse-driven play.** The mouse is used **once**, to click a difficulty and
  start the first game; every action after that is a keystroke, and every reset is
  `Ctrl+R`. This asymmetry gets a comment in the profile, where it is read.
- ❌ **No OCR.** The score is not a number on screen — reward comes from the *board*,
  read as a grid of fixed-size tiles.
- ❌ **No new Grounds.** CartPole, GridWorld and Minesweeper are enough.
- ❌ **No touching PPO.** Same rule as every milestone.
- ❌ **No breaking the Gymnasium contract.** `reset()` → 2-tuple, `step()` → 5-tuple,
  unchanged. If it bends to make Minesweeper fit, M5 has failed at the one thing this
  project is for.
- ❌ **The game binary is not committed.** 31 MB of GPL-3 build artefacts don't belong
  in this repo — it's a documented, checksummed download step.

---

## The design (proposed — confirm before Brick 1)

| Decision | Choice | Why |
| :--- | :--- | :--- |
| **The Ground** | LibreMines v2.3.0, Easy (8×8, 10 mines) | A small board keeps episodes short and the tile grid readable. Verified above |
| **Where it lives** | `games/libremines/`, git-ignored, sha256 recorded in the profile | The repo records *how to get it*, not the bytes |
| **The action space** | **6 discrete actions**: up, down, left, right, reveal, flag | This is the payoff for picking a keyboard game. A click-driven Minesweeper needs 8×8×2 = 128 actions; a cursor-driven one needs 6 |
| **The observation** | An 8×8 grid of cell-state integers, read by template matching | Deterministic and testable. Cells are fixed-size and high-contrast; digits 1–8 are distinctly coloured |
| **The eyes** | `mss` grab of the window rect → OpenCV tile classification | Both already in `setup.py`; installed into the venv 2026-08-25 |
| **The hands** | `KeyboardInput` via `SendInput`, Python `ctypes` | The C++ `clib.cpp` is **not** needed — Qt reads the normal Windows message queue, proven above. It stays opt-in and unused |
| **Reward** | `+1` per newly-revealed safe cell, `mine_penalty` on loss, `win_reward` on win — numbers from the profile | Follows M4's rule: reward numbers live in YAML, not in the env |
| **Termination** | mine hit or board cleared → `terminated`; step cap → `truncated` | The contract's own distinction, used honestly |
| **Reset** | `Ctrl+R` | Verified. The single reason option B was affordable here |

> **The one decision to confirm:** *should the observation be the 8×8 integer grid, or
> raw pixels through M3's ViT?* This plan says the **integer grid**. M5's promise is
> the hands; re-running the ViT here would add ~19 min per experiment and re-prove
> something M3 already proved. The pixel path stays available as a second profile if
> we want it later — the perception seam is exactly what M3 and M4 built.

---

## How we build M5: testing policy

Follows **CLAUDE.md §5**. What earns a test here:

1. **The Gymnasium contract.** `MinesweeperEnv` must pass `check_env`, and
   `reset()`/`step()` shapes must be indistinguishable from CartPole's and
   GridWorld's. This is the promise the whole project rests on.
2. **Tile classification has a single right answer.** Given a saved screenshot, every
   cell reads back as the right state. Red-first, against committed fixture images —
   fast, deterministic, no game process needed.
3. **Reward maths has a single right answer.** Given two consecutive board states,
   the reward is exact. A pure function of two grids — trivially testable.
4. **Window/focus/input glue gets no unit test, on purpose.** It fails loudly the
   first time it runs, and it cannot be tested without a live window. It is covered
   instead by the Brick 0 controls, which is where a *behavioural* check belongs.

The boundary to guard: **the screen is a new place where a silent wrong answer can
enter.** A misread tile doesn't crash — it quietly poisons the reward, exactly the way
M3's blind-solvable GridWorld quietly flattered a reward curve. That's why tile
reading is red-first against fixtures, and why control #3 below exists at all.

---

## The to-do list

| # | Brick | File(s) | Done when… |
| :--- | :--- | :--- | :--- |
| **0** | **Guardrail — write this first** | `scripts/check_hands.py` | All four controls print **PASS** |
| 1 | Window handle + capture, DPI-correct | `src/gametrainer/screen.py` | Finds the LibreMines window and returns an aligned frame; the DPI trap is handled |
| 2 | 🔴 test → tile classification | `tests/test_minesweeper_vision.py` → `src/gametrainer/minesweeper_vision.py` | A fixture screenshot reads back as the correct 8×8 grid |
| 3 | `KeyboardInput` — the real hands | `src/gametrainer/input.py` | `KeyboardInput` joins `NullInput` behind the same interface; 40-byte `INPUT`; foreground-guarded |
| 4 | 🔴 test → reward from two grids | `tests/test_minesweeper_rewards.py` → `rewards.py` | Exact numbers for reveal / mine / win, read from the profile |
| 5 | The env — the contract | `tests/test_minesweeper_env.py` → `src/gametrainer/minesweeper.py` | `check_env` clean; `reset()` 2-tuple, `step()` 5-tuple |
| 6 | The profile + factory wiring | `profiles/minesweeper.yaml`, `factory.py` | `make_env` builds it from YAML — **no Python edited** to select it |
| 7 | The controls (the proof) | `scripts/check_hands.py` | Brick 0 goes **PASS** |
| 8 | Close the docs | `M5_Log.md`, `M5_Review.md`, `CHANGELOG.md`, `ONBOARDING.md` | DOC_STANDARD rule 7 checklist fully ticked |

Brick 0 is the finish line; Bricks 1–6 are the work; Brick 7 is the proof; Brick 8 is
closing.

---

## Brick 0 — The guardrail (write this FIRST)

**File:** `scripts/check_hands.py`

Write the bar down *before* building anything. M5 PASSes only if **all four** hold:

| # | Control | PASS means | Why it exists |
| :--- | :--- | :--- | :--- |
| 1 | **Keys live** | A scripted sequence moves the cursor to a named cell and **flags** it; the captured board changes in **exactly** that cell | The positive case |
| 2 | **`NullInput` swapped in** | The same sequence leaves the board **unchanged** | Proves the real keystrokes are what moved it — not time, not animation |
| 3 | **Frozen frame** | The board changes on screen while the observation does **not** | Proves we are reading live pixels, not a cached array |
| 4 | **Reset** | `Ctrl+R` returns the board to all-unrevealed, **20 times in a row**, with no human | Proves episodes can actually repeat |

Controls 2 and 3 are the ones that matter. Control 1 passing on its own proves
nothing: a screen that changes while keys are being sent is exactly what you would see
if the keys were irrelevant. This is the same lesson as M3's blind-solvable
GridWorld — **measure the negative case, or you have measured nothing.**

**Correction — 2026-08-26, while writing Brick 0:** control 1 originally said
*reveals* it. Reveal **cascades** — the spike's single `O` changed 147,631 pixels
across many cells — so "changes in exactly that cell" was a condition reveal could
never satisfy, however well the keys worked. Changed to **flag** (`P`), which toggles
exactly one cell, always. Move-then-flag still tests the whole chain: the keys land,
and they land on the cell we aimed at. Recorded rather than silently rewritten
(rule 4); this tightens the bar, it does not lower it.

**Also decided at Brick 0:** the verdict is counted in **cells, not pixels**. The
spike's own numbers say why — a flag changed 237 pixels while a no-op reveal on an
already-revealed cell changed 342. Pixel counts still get printed as evidence, in the
style of the pre-flight table, but they decide nothing.

> **Verify:** `python scripts/check_hands.py` prints PASS for all four, with the cell
> counts that justify each and the pixel counts alongside as evidence.

---

## Open questions for the Log

- Does `Ctrl+R` preserve the difficulty, or return to the chooser? If it returns to
  the chooser, control 4 needs one mouse click per episode, and that must be recorded
  honestly rather than hidden.
- What is the real step rate through a live window on this machine? Unknown until
  Brick 1. It decides whether *any* learning observation is affordable at all.
- Window geometry is not stable across launches. Pin it, or re-read the rect every
  frame? The spike showed `MoveWindow` reporting success while the window sat
  elsewhere; re-reading the rect each frame worked.
