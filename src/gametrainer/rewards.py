"""
RewardCalculator - Milestone M4, Brick 2 & Milestone M5, Brick 4.

Holds reward numbers and computes step rewards:
- RewardCalculator: GridWorld step reward (step_cost, goal_reward).
- MinesweeperRewardCalculator: Minesweeper board transition reward
  (safe_reveal_reward, mine_penalty, win_reward).
These numbers come from the caller/profile rather than being hardcoded in envs.
See docs/m4/M4_ToDo.md and docs/m5/M5_ToDo.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.gametrainer.minesweeper_vision import MINE


@dataclass(frozen=True)
class RewardCalculator:
    """Reward for one GridWorld step: goal_reward on the goal, step_cost otherwise."""

    step_cost: float
    goal_reward: float

    def reward(self, reached_goal: bool) -> float:
        return self.goal_reward if reached_goal else self.step_cost


@dataclass(frozen=True)
class MinesweeperRewardCalculator:
    """Minesweeper reward maths - Milestone M5, Brick 4.

    Computes exact reward from two consecutive board grids (prev_grid, curr_grid).
    Follows M4's rule: reward numbers live in the profile/caller, not in the env.
    """

    safe_reveal_reward: float = 1.0
    mine_penalty: float = -10.0
    win_reward: float = 10.0
    total_safe_cells: int = 54  # 8x8 Easy: 64 cells - 10 mines

    def count_revealed_safe(self, grid: np.ndarray) -> int:
        """Count cells revealed with neighbor count 0-8."""
        arr = np.asarray(grid)
        return int(((arr >= 0) & (arr <= 8)).sum())

    def is_loss(self, grid: np.ndarray) -> bool:
        """Did the agent hit a mine?"""
        arr = np.asarray(grid)
        return bool((arr == MINE).any())

    def is_win(self, grid: np.ndarray) -> bool:
        """Did the agent reveal all safe cells without hitting a mine?"""
        arr = np.asarray(grid)
        return not self.is_loss(arr) and self.count_revealed_safe(arr) >= self.total_safe_cells

    def is_terminated(self, grid: np.ndarray) -> bool:
        """Game ends on win or loss."""
        return self.is_loss(grid) or self.is_win(grid)

    def reward(self, prev_grid: np.ndarray | None, curr_grid: np.ndarray) -> float:
        """Calculate reward from transition between two board states.

        - mine hit -> mine_penalty
        - win -> win_reward
        - otherwise -> newly_revealed_safe * safe_reveal_reward
        """
        curr = np.asarray(curr_grid)
        if self.is_loss(curr):
            return float(self.mine_penalty)

        if self.is_win(curr):
            return float(self.win_reward)

        if prev_grid is None:
            newly_revealed = self.count_revealed_safe(curr)
        else:
            prev = np.asarray(prev_grid)
            prev_safe = (prev >= 0) & (prev <= 8)
            curr_safe = (curr >= 0) & (curr <= 8)
            newly_revealed = int((curr_safe & ~prev_safe).sum())

        return float(newly_revealed * self.safe_reveal_reward)
