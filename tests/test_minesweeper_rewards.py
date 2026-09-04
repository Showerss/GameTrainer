"""
Brick 4 (M5): lock Minesweeper reward maths with red-first tests.

Per docs/m5/M5_ToDo.md (Brick 4):
- Reward is a pure function of two consecutive board grids (prev_grid, curr_grid).
- Exact numbers: +1 per newly-revealed safe cell, mine_penalty on loss,
  win_reward on win.
- Numbers come from the caller / profile, never hardcoded in the env.
- Termination: mine hit or board cleared -> terminated.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))

from src.gametrainer.minesweeper_vision import FLAGGED, GRID, HIDDEN, MINE
from src.gametrainer.rewards import MinesweeperRewardCalculator


@pytest.fixture
def empty_board():
    """Fresh 8x8 board where every cell is HIDDEN."""
    return np.full((GRID, GRID), HIDDEN, dtype=np.int8)


@pytest.fixture
def calculator():
    """Standard reward calculator: +1 per reveal, -10 mine penalty, +10 win."""
    return MinesweeperRewardCalculator(
        safe_reveal_reward=1.0,
        mine_penalty=-10.0,
        win_reward=10.0,
        total_safe_cells=54,  # 8x8 Easy has 10 mines, so 54 safe cells
    )


def test_no_change_gives_zero_reward(calculator, empty_board):
    """Cursor movement or no-op yields 0 reward."""
    prev = empty_board.copy()
    curr = empty_board.copy()
    assert calculator.reward(prev, curr) == 0.0
    assert calculator.is_terminated(curr) is False


def test_flagging_gives_zero_reward(calculator, empty_board):
    """Flagging a hidden cell does not count as a safe reveal."""
    prev = empty_board.copy()
    curr = empty_board.copy()
    curr[0, 0] = FLAGGED
    assert calculator.reward(prev, curr) == 0.0
    assert calculator.is_terminated(curr) is False


def test_single_safe_reveal(calculator, empty_board):
    """Opening one safe cell gives safe_reveal_reward."""
    prev = empty_board.copy()
    curr = empty_board.copy()
    curr[2, 3] = 1  # revealed neighbour count 1
    assert calculator.reward(prev, curr) == 1.0
    assert calculator.is_terminated(curr) is False


def test_cascade_reveal_multiplies_reward(calculator, empty_board):
    """A cascade opening 5 safe cells awards 5 x safe_reveal_reward."""
    prev = empty_board.copy()
    curr = empty_board.copy()
    curr[0, 0] = 0
    curr[0, 1] = 1
    curr[1, 0] = 1
    curr[1, 1] = 1
    curr[0, 2] = 2
    assert calculator.reward(prev, curr) == 5.0
    assert calculator.is_terminated(curr) is False


def test_hitting_mine_returns_mine_penalty_and_terminates(calculator, empty_board):
    """Revealing a mine awards mine_penalty and terminates."""
    prev = empty_board.copy()
    curr = empty_board.copy()
    curr[4, 4] = MINE
    assert calculator.reward(prev, curr) == -10.0
    assert calculator.is_loss(curr) is True
    assert calculator.is_win(curr) is False
    assert calculator.is_terminated(curr) is True


def test_board_cleared_returns_win_reward_and_terminates(calculator, empty_board):
    """Revealing all 54 safe cells awards win_reward and terminates."""
    prev = empty_board.copy()
    # 53 cells already revealed
    prev.fill(0)
    # 10 mines are hidden, 1 safe cell is hidden
    for i in range(11):
        prev[i // 8, i % 8] = HIDDEN

    curr = prev.copy()
    curr[1, 2] = 1  # the 54th safe cell is revealed

    assert calculator.is_win(curr) is True
    assert calculator.is_loss(curr) is False
    assert calculator.is_terminated(curr) is True
    assert calculator.reward(prev, curr) == 10.0


def test_custom_numbers_from_caller(empty_board):
    """Different profile numbers are respected without hardcoding."""
    custom_calc = MinesweeperRewardCalculator(
        safe_reveal_reward=2.5,
        mine_penalty=-50.0,
        win_reward=100.0,
        total_safe_cells=54,
    )
    prev = empty_board.copy()
    curr = empty_board.copy()
    curr[0, 0] = 2
    assert custom_calc.reward(prev, curr) == 2.5

    curr[1, 1] = MINE
    assert custom_calc.reward(prev, curr) == -50.0


def test_initial_board_with_none_prev(calculator, empty_board):
    """If prev_grid is None (e.g. at reset), all revealed cells count as fresh."""
    curr = empty_board.copy()
    curr[0, 0] = 1
    assert calculator.reward(None, curr) == 1.0
