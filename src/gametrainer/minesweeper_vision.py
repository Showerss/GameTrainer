"""
minesweeper_vision.py - M5 Brick 2. One screenshot in, one 8x8 board out.

Brick 1 gave us pixels: a capture of the whole game window, at whatever size
the game decided to open at. This file is the other half of the eyes - it
finds the board inside that picture and reads every cell. Nothing here knows
about keys, rewards or Gymnasium; those are Bricks 3, 4 and 5.

Teacher Note: why this brick is tested when Brick 1 was not
===========================================================
A capture that fails throws an error you cannot miss. A *misread tile* throws
nothing. It quietly hands the agent a wrong board, the reward follows that
wrong board, and the training curve looks perfectly healthy while meaning
nothing - which is exactly how M3's blind-solvable GridWorld flattered a
result. So every rule below was measured off a real screenshot
(tests/fixtures/board_easy_01.png), and anything that could not be measured
raises instead of guessing.

How a cell is read (all figures measured 2026-09-03 on that fixture)
====================================================================
A cell is one flat background with at most one glyph drawn on it:

    background 70,70,70 (grey)  -> the cell is still hidden
    background 26,26,26 (dark)  -> the cell has been revealed
    "ink" = any pixel far from that background = the glyph

Ink comes in two kinds, and that split is what makes the reading safe:

    coloured ink -> something we can name by its colour (a digit, the flag)
    grey ink     -> something we cannot name yet -> raise, never guess

The margins are not close. Hidden and blank cells measured 0.0% ink; the
faintest real glyph (the flag) measured 13.4%; digits measured 46-54%. The
threshold sits at 5%, between "nothing at all" and the faintest real thing.

Teacher Note: red means two different things
============================================
The flag and the digit 3 are the *same* red (0, 0, 255 in BGR). No amount of
looking at the colour can separate them - only what lies underneath can. Red
on grey is a flag on a hidden cell; red on dark is a 3 on a revealed one.
Background first, glyph second, always.

Known gap, on purpose
=====================
The fixture holds 6 of the 12 cell states: hidden, flagged, blank, 1, 2, 3.
It has no 4-8 and no mine, so their appearance has never been measured here.
Rather than invent colours for them, an unrecognised glyph raises
UnreadableCell naming what it saw. Loud and wrong beats quiet and wrong: a
guessed colour for a 5 would be indistinguishable from a correct one right up
until it poisoned a reward. The missing states get measured the day a second
fixture is captured (Brick 5 needs the mine, since that is how an episode
ends).

Every colour here also belongs to the theme the game happened to open with.
A different LibreMines minefield theme is a different set of numbers.
"""

from __future__ import annotations

import cv2
import numpy as np

# Easy is 8x8, and M5 plays no other size (docs/m5/M5_ToDo.md, "The design").
GRID = 8

# Cell states. 0-8 are the revealed neighbour counts, so the three states that
# are not a number simply continue the same run of integers: no negatives and
# no gaps, which keeps every state a valid index into a 12-long table if a
# later brick wants one-hot or MultiDiscrete.
HIDDEN = 9
FLAGGED = 10
MINE = 11

# --- The measured palette (BGR, the order OpenCV and Brick 1 both use) ---
_HIDDEN_BODY = np.array([70, 70, 70])
_REVEALED_BODY = np.array([26, 26, 26])
_DIGIT_COLOURS = {1: (255, 104, 0), 2: (0, 130, 0), 3: (0, 0, 255)}

# --- Thresholds, each one sitting in a measured gap ---
_BODY_TOLERANCE = 12  # how far a background pixel may drift and still count
_BODY_FRACTION = 0.20  # a real cell is >=42% background; a glyph never is
_INK_DISTANCE = 40  # how far from the background a pixel must be to be ink
_COLOURFUL = 60  # channel spread that separates a colour from a grey
_INK_FRACTION = 0.05  # measured: nothing = 0.0%, faintest real glyph = 13.4%
_COLOUR_TOLERANCE = 40  # how close a glyph colour must be to a known one
_SAMPLE_FRACTION = 0.6  # read the middle 60% of a cell: misses bevel and gap

# --- Finding the board in the window ---
_BACKGROUND_MIN = 200  # the window's own background is near-white (236-251)
_MIN_CELL_PIXELS = 8  # a board thinner than 8px a cell cannot be read
_SQUARENESS = 0.05  # the minefield is square; allow 5% for rounding
_MIN_FILL = 0.80  # measured 95%: cells and gaps nearly fill their own box


class BoardNotFound(Exception):
    """No square block of board-coloured pixels in this frame.

    Most likely the game is showing its Easy/Medium/Hard chooser rather than a
    board - trap #3 from the pre-flight spike, where keys do nothing until a
    game has actually been started.
    """


class UnreadableCell(Exception):
    """A cell does not look like anything this module has been taught."""


def find_board(frame: np.ndarray) -> tuple[int, int, int]:
    """Locate the minefield inside a full-window capture.

    Returns (x, y, side) - the board's top-left corner and its width in
    pixels. Raises BoardNotFound if nothing in the frame looks like a board.

    Teacher Note: the board is found, never assumed. Brick 1's surprise was
    that LibreMines opened maximized one launch and 716x539 the next, so any
    geometry hardcoded from one screenshot is wrong on the next. What does
    hold across launches is the *shape*: the minefield is one big square block
    of dark pixels sitting on a near-white window background. So: take every
    dark blob, and keep the largest one that is actually square and actually
    solid. The window's own frame is dark too, but it is 2568x1408 - nowhere
    near square - and that is what the squareness check throws out.
    """
    dark = (frame.max(axis=2) < _BACKGROUND_MIN).astype(np.uint8)
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(dark, 8)

    # Label 0 is the background, so candidates start at 1. Largest first: the
    # first blob that passes every check is the board.
    for i in sorted(range(1, count), key=lambda i: -stats[i, cv2.CC_STAT_AREA]):
        x, y, width, height, area = stats[i]
        if min(width, height) < GRID * _MIN_CELL_PIXELS:
            continue
        if abs(width - height) > _SQUARENESS * max(width, height):
            continue
        if area < _MIN_FILL * width * height:
            continue
        return int(x), int(y), int(min(width, height))

    raise BoardNotFound(
        "No square block of board-coloured pixels in this frame. Is the game "
        "showing the difficulty chooser instead of a board?"
    )


def _cell_patch(frame: np.ndarray, board: tuple[int, int, int], row: int, col: int):
    """Cut out the middle of one cell.

    The middle 60% only: a cell is drawn with a raised bevel and is separated
    from its neighbours by a dark gap, and neither carries information. The
    cell pitch is deliberately kept as a float (165.75 px in the fixture) and
    rounded once at the end, so rounding error cannot accumulate across the
    row and walk the sample off the last cell.
    """
    x, y, side = board
    pitch = side / GRID
    half = pitch * _SAMPLE_FRACTION / 2
    centre_y = y + pitch * (row + 0.5)
    centre_x = x + pitch * (col + 0.5)
    return frame[
        int(centre_y - half) : int(centre_y + half),
        int(centre_x - half) : int(centre_x + half),
    ]


def _dominant_colour(pixels: np.ndarray) -> tuple[int, int, int]:
    """The most common colour among these pixels."""
    colours, counts = np.unique(pixels, axis=0, return_counts=True)
    return tuple(int(channel) for channel in colours[counts.argmax()])


def _nearest_digit(colour: tuple[int, int, int]) -> int | None:
    """Which digit is drawn in this colour, or None if we have never seen it."""
    for digit, known in _DIGIT_COLOURS.items():
        if max(abs(a - b) for a, b in zip(colour, known)) <= _COLOUR_TOLERANCE:
            return digit
    return None


def classify_cell(patch: np.ndarray) -> int:
    """Read one cell: 0-8, HIDDEN or FLAGGED.

    Raises UnreadableCell rather than returning a plausible-looking guess.
    """
    pixels = patch.reshape(-1, 3).astype(int)
    colourful = pixels.max(axis=1) - pixels.min(axis=1) > _COLOURFUL

    # Step 1: what is underneath? A hidden cell and a revealed one are two
    # different flat greys, and the answer decides how the glyph is read.
    hidden_share = _share_matching(pixels, _HIDDEN_BODY)
    revealed_share = _share_matching(pixels, _REVEALED_BODY)
    if max(hidden_share, revealed_share) < _BODY_FRACTION:
        raise UnreadableCell(
            f"no recognisable cell background (most common colour "
            f"{_dominant_colour(pixels)}; expected a hidden {tuple(_HIDDEN_BODY)} "
            f"or a revealed {tuple(_REVEALED_BODY)})"
        )
    is_hidden = hidden_share > revealed_share
    background = _HIDDEN_BODY if is_hidden else _REVEALED_BODY

    # Step 2: is anything drawn on top of it, and can we name it?
    ink = np.abs(pixels - background).max(axis=1) > _INK_DISTANCE
    coloured_ink = (ink & colourful).mean()
    grey_ink = (ink & ~colourful).mean()

    if coloured_ink < _INK_FRACTION and grey_ink < _INK_FRACTION:
        return HIDDEN if is_hidden else 0

    if coloured_ink < _INK_FRACTION:
        raise UnreadableCell(
            f"a glyph with no colour in it ({grey_ink:.0%} of the cell). That "
            f"is probably a 7, an 8 or a mine - states this fixture never "
            f"showed, so their appearance has never been measured. Capture a "
            f"fixture containing one before trusting a reading here."
        )

    # A flag is the only coloured thing that can sit on a cell that is still
    # hidden - and it is the same red as a 3, which is why this is decided by
    # the background and not by the colour.
    if is_hidden:
        return FLAGGED

    colour = _dominant_colour(pixels[ink & colourful])
    digit = _nearest_digit(colour)
    if digit is None:
        raise UnreadableCell(
            f"a glyph drawn in {colour}, which matches no digit colour this "
            f"module has measured (known: {sorted(_DIGIT_COLOURS.values())})"
        )
    return digit


def _share_matching(pixels: np.ndarray, colour: np.ndarray) -> float:
    """What fraction of these pixels are this colour, give or take."""
    return float((np.abs(pixels - colour).max(axis=1) <= _BODY_TOLERANCE).mean())


def read_board(frame: np.ndarray) -> np.ndarray:
    """Turn one captured window into an 8x8 grid of cell states.

    The frame is the whole window as Brick 1's GameWindow.grab() returns it:
    a (height, width, 3) BGR array. Returns an (8, 8) array where each cell is
    0-8 (a revealed neighbour count), HIDDEN or FLAGGED.
    """
    board = find_board(frame)
    grid = np.empty((GRID, GRID), dtype=np.int8)
    for row in range(GRID):
        for col in range(GRID):
            try:
                grid[row, col] = classify_cell(_cell_patch(frame, board, row, col))
            except UnreadableCell as exc:
                raise UnreadableCell(f"row {row}, column {col}: {exc}") from exc
    return grid
