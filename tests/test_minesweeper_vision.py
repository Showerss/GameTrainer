"""
Brick 2 (M5): red-first -- lock the tile classifier against a real screenshot.

read_board() turns one captured LibreMines frame into an 8x8 grid of cell
states. The frame is the whole window (2576x1408 in this fixture, because the
game opened maximized), so the function has to *find* the board before it can
read it: the board is a small patch of a large picture, and its geometry is not
stable across launches. See docs/m5/M5_Log.md, Brick 1 "Surprise".

Why this brick gets a test when Brick 1 did not (CLAUDE.md 5): a misread tile
does not crash. It quietly poisons the observation and the reward, exactly the
way M3's blind-solvable GridWorld quietly flattered a reward curve. So the
answer key below was read off the fixture by eye and confirmed by hand
(2026-08-30). It is ground truth, not output -- never regenerate it from
read_board().

Coverage limit, on purpose: this fixture holds 6 of the 12 cell states --
hidden, flagged, blank, 1, 2, 3. It has no 4-8 and no mine. Those are rarer
and need their own fixture; a second one can be added when a board produces
them naturally.

Mirrors tests/test_rewards.py: same path-insertion trick, plain functions.
"""

import sys
from pathlib import Path

import cv2

_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))
from src.gametrainer.minesweeper_vision import FLAGGED, HIDDEN, MINE, read_board

FIXTURE = Path(__file__).parent / "fixtures" / "board_easy_01.png"

# The answer key, kept in the shape it was verified in: one character per cell.
#   .  hidden      _  revealed blank      F  flag      1-8  revealed digit
# Cross-check that held at verification time: the panel's mine counter read 9
# of 10, so exactly one flag is placed -- and there is exactly one F below.
_ANSWER_KEY = [
    "........",
    "....212.",
    "..311_22",
    "..1___1F",
    "..111_11",
    "....21__",
    ".....21_",
    "....2.1_",
]

_SYMBOLS = {".": HIDDEN, "_": 0, "F": FLAGGED, "*": MINE}


def _decode(rows):
    """Turn the picture-shaped answer key into the integers read_board returns."""
    return [
        [_SYMBOLS[ch] if ch in _SYMBOLS else int(ch) for ch in row]
        for row in rows
    ]


def _load_fixture():
    """Load the fixture, loudly. cv2.imread returns None on a missing file."""
    frame = cv2.imread(str(FIXTURE))
    assert frame is not None, f"fixture image not readable: {FIXTURE}"
    return frame


def test_fixture_reads_back_as_the_verified_grid():
    assert read_board(_load_fixture()).tolist() == _decode(_ANSWER_KEY)


def test_board_is_eight_by_eight():
    assert read_board(_load_fixture()).shape == (8, 8)
