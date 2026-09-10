"""
M5 Brick 0 - the guardrail. Written FIRST, before any of the hands exist.

This file plays two roles in the M5 to-do list (docs/m5/M5_ToDo.md):
  * Brick 0 (now): write the bar down while the work still looks easy - the
    four controls, and the exact numbers that decide each one.
  * Brick 7 (later): fill in collect_measurements() against a live LibreMines
    window, so this file can actually run and print PASS.

Running it today prints NOT RUN and exits 1. That is correct and deliberate:
the machinery it measures (Bricks 1-6) does not exist yet, and a guardrail
that passes before the work is done is not a guardrail.

The M5 finish line - ALL FOUR must hold:

  1. Keys live     A scripted sequence moves the cursor to a named cell and
                   acts on it; the board changes in EXACTLY that cell.
  2. NullInput     The same sequence, with the real hands swapped for
                   NullInput, leaves the board UNCHANGED.
  3. Frozen frame  The board changes on screen while an observation built
                   from a frozen frame does NOT.
  4. Reset         Ctrl+R returns the board to all-unrevealed, 20 times in a
                   row, with no human touching anything.

Teacher Note: why controls 2 and 3 are the ones that matter
===========================================================
Control 1 passing on its own proves nothing. A screen that changes while keys
are being sent is exactly what you would see if the keys were landing
nowhere and the game were animating on its own. Control 2 is the negative
case: same sequence, hands disconnected, board must sit perfectly still. Only
the pair of them can say "our keystrokes did that."

Control 3 is the same trick aimed at the eyes instead of the hands. An
observation that keeps changing after you freeze the frame it is built from
is not being read off the screen at all - it is coming from a cached array, or
from some internal game state we accidentally kept a handle on. M3 learned
this the expensive way: a GridWorld that turned out to be solvable blind gave
a beautiful reward curve that meant nothing, because nobody measured the
negative case. Measure the negative case, or you have measured nothing.

Teacher Note: the bar counts CELLS, not pixels
==============================================
The pre-flight spike (M5_ToDo.md) counted changed pixels, because at that
point there was nothing else to count. Two of its numbers explain why that
cannot be the bar here: placing a flag changed 237 pixels, and pressing
reveal on an already-revealed cell - a genuine no-op - changed 342. A pixel
count cannot tell those apart, and it points the wrong way. So the verdict
below is decided on the 8x8 grid of cell states that Brick 2 reads, where
"one cell changed, and it was the cell we aimed at" is an exact statement.
Pixel counts are still printed, as evidence in the style of the spike table,
but they never decide anything.

Usage:
    python scripts/check_hands.py
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# Ensure project root is on sys.path for direct script execution
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.gametrainer.input import KeyboardInput, NullInput
from src.gametrainer.minesweeper_vision import HIDDEN, read_board
from src.gametrainer.screen import GameWindow, WindowNotFound

# Print UTF-8 so status glyphs don't crash on Windows consoles (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# The bar.
#
# These numbers ARE the milestone. CLAUDE.md section 5 forbids moving them
# once the work has started, so they live here, in one place, where changing
# one would be an obvious edit rather than a quiet drift.
# ---------------------------------------------------------------------------

# Controls 1 and 2 act on the board with FLAG (P), not reveal (O).
#
# Teacher Note: revealing cascades. The spike saw a single O change 147,631
# pixels across a large patch of the board, because Minesweeper opens every
# connected empty cell at once. "Changed in exactly that cell" is therefore
# not a statement reveal can ever satisfy, however well the keys work. A flag
# toggles exactly one cell, always. Move-then-flag still exercises the whole
# chain we care about - the keys land, and they land on the cell we aimed at.
EXPECTED_CELLS_CHANGED = 1

# Control 2: with NullInput in place of the real hands, nothing may move.
# Zero, not "a few": a Minesweeper board does not animate between keystrokes,
# so any drift at all here is a bug, not noise.
NULL_INPUT_CELLS_CHANGED = 0

# Control 3: a frozen frame must produce a frozen observation.
FROZEN_CELLS_CHANGED = 0

# Control 3, positive half: the live reading must show the board really did
# change, or "the frozen one didn't" is just a statement about a still screen.
MIN_LIVE_CELLS_CHANGED = 1

# Control 4: how many unattended resets prove episodes can actually repeat.
RESET_TRIALS = 20


# ---------------------------------------------------------------------------
# What the referee is allowed to look at.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Measurements:
    """Every number the verdict may use, and nothing else.

    A plain data carrier, filled in by Brick 7 from a live game window.
    Keeping it separate is what lets the referee below be pure logic - numbers
    in, PASS/FAIL out - so it can be read, reasoned about and tested without a
    game process running anywhere.

    Cells are (row, col), 0-indexed, on the 8x8 Easy board.
    """

    # Control 1 - the real hands.
    target_cell: tuple[int, int]
    live_cells_changed: int
    live_changed_cell: tuple[int, int] | None
    live_pixels_changed: int  # evidence only; never decides

    # Control 2 - NullInput, exact same key sequence.
    null_cells_changed: int
    null_pixels_changed: int  # evidence only; never decides

    # Control 3 - frozen frame vs live frame, same on-screen change.
    frozen_obs_cells_changed: int
    live_obs_cells_changed: int

    # Control 4 - reset, repeated.
    resets_attempted: int
    resets_clean: int
    reset_mouse_clicks: int  # recorded, not judged - see decide_reset()


@dataclass
class ControlResult:
    """One control's verdict, plus the evidence that justifies it."""

    number: int
    name: str
    passed: bool
    evidence: list[str] = field(default_factory=list)


def _mark(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


# ---------------------------------------------------------------------------
# The four controls. Pure functions: Measurements in, ControlResult out.
# ---------------------------------------------------------------------------

def decide_keys_live(m: Measurements) -> ControlResult:
    """Control 1 - the positive case: our keys moved the cursor and acted."""
    changed_one = m.live_cells_changed == EXPECTED_CELLS_CHANGED
    changed_target = m.live_changed_cell == m.target_cell
    return ControlResult(
        1,
        "Keys live",
        changed_one and changed_target,
        [
            f"  target cell:              {m.target_cell}",
            (
                f"  cells changed:            {m.live_cells_changed}"
                f"  (needs exactly {EXPECTED_CELLS_CHANGED})"
            ),
            f"  cell that changed:        {m.live_changed_cell}",
            f"  pixels changed:           {m.live_pixels_changed:,}  (evidence only)",
            f"  [{_mark(changed_one)}] exactly one cell changed",
            f"  [{_mark(changed_target)}] it was the cell we aimed at",
        ],
    )


def decide_null_input(m: Measurements) -> ControlResult:
    """Control 2 - the negative case: no hands, no movement."""
    still = m.null_cells_changed == NULL_INPUT_CELLS_CHANGED
    return ControlResult(
        2,
        "NullInput swapped in",
        still,
        [
            (
                f"  cells changed:            {m.null_cells_changed}"
                f"  (needs exactly {NULL_INPUT_CELLS_CHANGED})"
            ),
            f"  pixels changed:           {m.null_pixels_changed:,}  (evidence only)",
            f"  [{_mark(still)}] same sequence, hands disconnected, board unchanged",
        ],
    )


def decide_frozen_frame(m: Measurements) -> ControlResult:
    """Control 3 - the eyes are reading the screen, not a cached array."""
    live_moved = m.live_obs_cells_changed >= MIN_LIVE_CELLS_CHANGED
    frozen_still = m.frozen_obs_cells_changed == FROZEN_CELLS_CHANGED
    return ControlResult(
        3,
        "Frozen frame",
        live_moved and frozen_still,
        [
            (
                f"  live obs cells changed:   {m.live_obs_cells_changed}"
                f"  (needs >= {MIN_LIVE_CELLS_CHANGED})"
            ),
            (
                f"  frozen obs cells changed: {m.frozen_obs_cells_changed}"
                f"  (needs exactly {FROZEN_CELLS_CHANGED})"
            ),
            f"  [{_mark(live_moved)}] the board really did change on screen",
            f"  [{_mark(frozen_still)}] the frozen-frame observation did not follow",
        ],
    )


def decide_reset(m: Measurements) -> ControlResult:
    """Control 4 - episodes can repeat, unattended.

    Teacher Note: reset_mouse_clicks is printed but never judged. The open
    question in M5_ToDo.md is whether Ctrl+R keeps the difficulty or drops
    back to the chooser; if it drops back, each episode costs one scripted
    mouse click. A click the script sends is still "no human," so it does not
    fail this control - but hiding it would misrepresent how the loop runs, so
    it goes in the report either way (DOC_STANDARD rule 4).
    """
    enough = m.resets_attempted >= RESET_TRIALS
    all_clean = m.resets_clean == m.resets_attempted
    return ControlResult(
        4,
        "Reset",
        enough and all_clean,
        [
            (
                f"  resets attempted:         {m.resets_attempted}"
                f"  (needs >= {RESET_TRIALS})"
            ),
            f"  boards all-unrevealed:    {m.resets_clean} / {m.resets_attempted}",
            f"  mouse clicks used:        {m.reset_mouse_clicks}  (recorded, not judged)",
            f"  [{_mark(enough)}] ran the full {RESET_TRIALS} trials",
            f"  [{_mark(all_clean)}] every reset produced a fresh board",
        ],
    )


def decide_verdict(m: Measurements) -> tuple[bool, list[ControlResult]]:
    """Apply all four controls. M5 PASSes only if every one of them does."""
    results = [
        decide_keys_live(m),
        decide_null_input(m),
        decide_frozen_frame(m),
        decide_reset(m),
    ]
    return all(r.passed for r in results), results


# ---------------------------------------------------------------------------
# Reporting.
# ---------------------------------------------------------------------------

def print_finish_line() -> None:
    """Show the bar this run must clear. Printed before anything is measured."""
    print("The M5 finish line (all four required to PASS):")
    print("  1. Keys live     - move to a named cell and flag it; EXACTLY that")
    print("                     cell changes")
    print("  2. NullInput     - same sequence, no hands: NOTHING changes")
    print("  3. Frozen frame  - screen changes, frozen-frame observation does not")
    print(f"  4. Reset         - Ctrl+R gives a fresh board {RESET_TRIALS}x, unattended")
    print()
    print("  Controls 2 and 3 are the ones that matter: they are the negative")
    print("  cases. Control 1 alone cannot tell a working keystroke from a")
    print("  coincidence.")
    print()


# ---------------------------------------------------------------------------
# Measurement - Brick 7's job.
# ---------------------------------------------------------------------------

def collect_measurements(
    title: str = "LibreMines",
    step_delay: float = 0.15,
) -> Measurements:
    """Drive a live LibreMines window and return what the referee needs.

    Uses:
      - GameWindow(title) to find and capture the window
      - KeyboardInput(hwnd) to focus and send real SendInput keystrokes
      - NullInput() for the negative control
      - read_board(frame) to parse cell states from pixels
    """
    with GameWindow(title) as window:
        hands = KeyboardInput(window.hwnd)
        hands.focus()

        # ------------------------------------------------------------------
        # Control 1: Keys live (Move to a target cell and flag it)
        # ------------------------------------------------------------------
        # Reset to ensure clean start
        hands.restart()
        time.sleep(step_delay * 2)

        initial_frame = window.grab()
        initial_grid = read_board(initial_frame)

        # Move to target cell (1, 2): down 1, right 2, from top-left (0, 0).
        #
        # Teacher Note: the first W/A/S/D press only ACTIVATES keyboard-cursor
        # mode - measured live 2026-09-07: one move_down() alone after a
        # restart left the cursor at (0, 0), not (1, 0). It does not count as
        # a move in any direction. So reaching (1, 2) needs one extra
        # activation press before the two real moves below - four keys sent
        # for a two-step walk, not three.
        target_cell = (1, 2)
        hands.move_down()  # activates keyboard mode; lands at (0, 0)
        time.sleep(step_delay)
        hands.move_down()  # down 1: (0, 0) -> (1, 0)
        time.sleep(step_delay)
        hands.move_right()  # right 1: (1, 0) -> (1, 1)
        time.sleep(step_delay)
        hands.move_right()  # right 2: (1, 1) -> (1, 2)
        time.sleep(step_delay)
        hands.flag()
        time.sleep(step_delay)

        frame_after_flag = window.grab()
        grid_after_flag = read_board(frame_after_flag)

        diff_mask = initial_grid != grid_after_flag
        live_cells_changed = int(np.sum(diff_mask))
        changed_coords = np.argwhere(diff_mask)
        live_changed_cell = (
            (int(changed_coords[0][0]), int(changed_coords[0][1]))
            if len(changed_coords) == 1
            else None
        )
        live_pixels_changed = int(np.sum(initial_frame != frame_after_flag))

        # ------------------------------------------------------------------
        # Control 2: NullInput swapped in (Negative control)
        # Same sequence of moves + flag, but dispatched to NullInput.
        # ------------------------------------------------------------------
        hands.restart()
        time.sleep(step_delay * 2)

        null_initial_frame = window.grab()
        null_initial_grid = read_board(null_initial_frame)

        null_hands = NullInput()
        null_hands.move_down()
        time.sleep(step_delay)
        null_hands.move_right()
        time.sleep(step_delay)
        null_hands.move_right()
        time.sleep(step_delay)
        null_hands.flag()
        time.sleep(step_delay)

        null_after_frame = window.grab()
        null_after_grid = read_board(null_after_frame)

        null_cells_changed = int(np.sum(null_initial_grid != null_after_grid))
        null_pixels_changed = int(np.sum(null_initial_frame != null_after_frame))

        # ------------------------------------------------------------------
        # Control 3: Frozen frame vs Live frame
        # Freeze a frame, then change the board on screen.
        # ------------------------------------------------------------------
        frozen_frame = window.grab()
        frozen_obs_before = read_board(frozen_frame)

        # Act with real hands to mutate the board on screen
        hands.move_down()
        time.sleep(step_delay)
        hands.flag()
        time.sleep(step_delay)

        live_frame = window.grab()
        live_obs = read_board(live_frame)
        frozen_obs_after = read_board(frozen_frame)

        live_obs_cells_changed = int(np.sum(live_obs != frozen_obs_before))
        frozen_obs_cells_changed = int(np.sum(frozen_obs_after != frozen_obs_before))

        # ------------------------------------------------------------------
        # Control 4: Reset (20 unattended Ctrl+R trials)
        # ------------------------------------------------------------------
        resets_attempted = RESET_TRIALS
        resets_clean = 0
        reset_mouse_clicks = 0

        for _ in range(RESET_TRIALS):
            # Dirty the board by flagging a cell so it's not all unrevealed
            hands.move_right()
            time.sleep(step_delay)
            hands.flag()
            time.sleep(step_delay)

            # Send reset chord (Ctrl+R)
            hands.restart()
            time.sleep(step_delay * 2)

            reset_frame = window.grab()
            reset_grid = read_board(reset_frame)

            # All 8x8 cells must return to HIDDEN
            if np.all(reset_grid == HIDDEN):
                resets_clean += 1

        return Measurements(
            target_cell=target_cell,
            live_cells_changed=live_cells_changed,
            live_changed_cell=live_changed_cell,
            live_pixels_changed=live_pixels_changed,
            null_cells_changed=null_cells_changed,
            null_pixels_changed=null_pixels_changed,
            frozen_obs_cells_changed=frozen_obs_cells_changed,
            live_obs_cells_changed=live_obs_cells_changed,
            resets_attempted=resets_attempted,
            resets_clean=resets_clean,
            reset_mouse_clicks=reset_mouse_clicks,
        )


def main() -> int:
    print("=" * 68)
    print("GAMETRAINER - M5: Add the Hands (controls)")
    print("=" * 68)
    print()
    print_finish_line()

    try:
        measurements = collect_measurements()
    except NotImplementedError as not_built:
        print("=" * 68)
        print("M5 VERDICT: NOT RUN")
        print("=" * 68)
        print(f"  {not_built}")
        print("  Nothing was measured, so nothing passed.")
        print("=" * 68)
        return 1
    except (WindowNotFound, RuntimeError, OSError) as err:
        print("=" * 68)
        print("M5 VERDICT: NOT RUN (Game window or environment unavailable)")
        print("=" * 68)
        print(f"  {err}")
        print("  Running live controls requires Windows or macOS with LibreMines open.")
        print("=" * 68)
        return 1

    passed, results = decide_verdict(measurements)

    print("=" * 68)
    print(f"M5 VERDICT: {'PASS' if passed else 'FAIL'}")
    print("=" * 68)
    for result in results:
        print(f"[{_mark(result.passed)}] Control {result.number} - {result.name}")
        for line in result.evidence:
            print(line)
        print()
    print("=" * 68)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
