"""
MinesweeperEnv - Milestone M5, Brick 5.

The universal Gymnasium plug for LibreMines (v2.3.0, Easy 8x8).
Connects:
- Hands: KeyboardInput (or NullInput) -> sends W/A/S/D/O/P/Ctrl+R
- Eyes: GameWindow -> read_board() -> 8x8 grid of cell states
- Reward: MinesweeperRewardCalculator -> scores board transitions
- Contract: Gymnasium Env standard (reset() -> 2-tuple, step() -> 5-tuple).
See docs/m5/M5_ToDo.md, Brick 5.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from enum import IntEnum
from typing import ClassVar

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from src.gametrainer.input import InputController, NullInput
from src.gametrainer.minesweeper_vision import (
    FLAGGED,
    GRID,
    HIDDEN,
    MINE,
    CellState,
    read_board,
)
from src.gametrainer.rewards import MinesweeperRewardCalculator
from src.gametrainer.screen import GameWindow


class MinesweeperAction(IntEnum):
    """Minesweeper discrete action IDs (0 to 5)."""

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    REVEAL = 4
    FLAG = 5


class MinesweeperEnv(gym.Env):
    """An 8x8 Minesweeper environment that follows the Gymnasium contract."""

    metadata: ClassVar[dict[str, list[str]]] = {"render_modes": ["ansi"]}

    GRID_SIZE = GRID  # 8x8 Easy board

    # 6 Discrete actions (docs/m5/M5_ToDo.md)
    UP = MinesweeperAction.UP
    DOWN = MinesweeperAction.DOWN
    LEFT = MinesweeperAction.LEFT
    RIGHT = MinesweeperAction.RIGHT
    REVEAL = MinesweeperAction.REVEAL
    FLAG = MinesweeperAction.FLAG

    def __init__(
        self,
        hands: InputController | None = None,
        window: GameWindow | None = None,
        reward_calculator: MinesweeperRewardCalculator | None = None,
        max_steps: int = 100,
        read_board_fn: Callable[[], np.ndarray] | None = None,
        step_delay: float = 0.0,
        render_mode: str | None = None,
        owns_window: bool = False,
    ):
        super().__init__()
        self.render_mode = render_mode
        self.hands: InputController = hands if hands is not None else NullInput()
        self.window = window
        self._owns_window = owns_window
        self.reward_calculator = (
            reward_calculator
            if reward_calculator is not None
            else MinesweeperRewardCalculator()
        )
        self.max_steps = max_steps
        self.read_board_fn = read_board_fn
        self.step_delay = step_delay

        # ACTION SPACE: 6 discrete actions
        self.action_space = spaces.Discrete(6)

        # OBSERVATION SPACE: 8x8 grid of cell states (0-11, int8)
        # 0-8: revealed neighbor count, 9: HIDDEN, 10: FLAGGED, 11: MINE
        self.observation_space = spaces.Box(
            low=0,
            high=MINE,
            shape=(self.GRID_SIZE, self.GRID_SIZE),
            dtype=np.int8,
        )

        self._steps = 0
        self.prev_grid: np.ndarray | None = None

    def _read_obs(self) -> np.ndarray:
        """Capture the current board state as an (8, 8) int8 grid."""
        if self.read_board_fn is not None:
            grid = self.read_board_fn()
        elif self.window is not None:
            frame = self.window.grab()
            grid = read_board(frame)
        else:
            # Fallback when no window or mock function is provided
            grid = np.full(
                (self.GRID_SIZE, self.GRID_SIZE), HIDDEN, dtype=np.int8
            )
        return np.asarray(grid, dtype=np.int8)

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[np.ndarray, dict]:
        """Reset the environment: triggers Ctrl+R on hands and reads fresh board."""
        super().reset(seed=seed)
        self._steps = 0

        self.hands.restart()
        if self.step_delay > 0:
            time.sleep(self.step_delay)
        self.hands.move_down()

        obs = self._read_obs()
        self.prev_grid = obs.copy()
        return obs, {}

    def step(
        self, action: int | np.integer
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        """Send action to hands, read new board, compute reward and termination."""
        action_arr = np.asarray(action)
        if action_arr.shape != ():
            action = action_arr.item()
        action_int = int(action)

        try:
            action_enum = MinesweeperAction(action_int)
        except ValueError:
            raise ValueError(f"Invalid action {action_int}; must be in [0, 5]") from None

        if action_enum == MinesweeperAction.UP:
            self.hands.move_up()
        elif action_enum == MinesweeperAction.DOWN:
            self.hands.move_down()
        elif action_enum == MinesweeperAction.LEFT:
            self.hands.move_left()
        elif action_enum == MinesweeperAction.RIGHT:
            self.hands.move_right()
        elif action_enum == MinesweeperAction.REVEAL:
            self.hands.reveal()
        elif action_enum == MinesweeperAction.FLAG:
            self.hands.flag()

        if self.step_delay > 0:
            time.sleep(self.step_delay)

        self._steps += 1
        curr_grid = self._read_obs()

        reward = float(self.reward_calculator.reward(self.prev_grid, curr_grid))
        terminated = bool(self.reward_calculator.is_terminated(curr_grid))
        truncated = bool((self._steps >= self.max_steps) and not terminated)

        self.prev_grid = curr_grid.copy()
        info = {"steps": self._steps}

        return curr_grid, reward, terminated, truncated, info

    def render(self) -> str | None:
        """Render board as text representation if requested."""
        if self.render_mode == "ansi":
            if self.prev_grid is None:
                return ""
            symbols = {
                CellState.HIDDEN: ".",
                CellState.FLAGGED: "F",
                CellState.MINE: "*",
            }
            lines = []
            for row in self.prev_grid:
                row_str = " ".join(symbols.get(int(c), str(int(c))) for c in row)
                lines.append(row_str)
            return "\n".join(lines)
        return None

    def close(self) -> None:
        if self._owns_window and self.window is not None:
            self.window.close()
            self.window = None
        super().close()
