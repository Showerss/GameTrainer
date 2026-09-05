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
from typing import Callable

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from src.gametrainer.input import InputController, NullInput
from src.gametrainer.minesweeper_vision import FLAGGED, GRID, HIDDEN, MINE, read_board
from src.gametrainer.rewards import MinesweeperRewardCalculator
from src.gametrainer.screen import GameWindow


class MinesweeperEnv(gym.Env):
    """An 8x8 Minesweeper environment that follows the Gymnasium contract."""

    metadata = {"render_modes": ["ansi"]}

    GRID_SIZE = GRID  # 8x8 Easy board

    # 6 Discrete actions (docs/m5/M5_ToDo.md)
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    REVEAL = 4
    FLAG = 5

    def __init__(
        self,
        hands: InputController | None = None,
        window: GameWindow | None = None,
        reward_calculator: MinesweeperRewardCalculator | None = None,
        max_steps: int = 100,
        read_board_fn: Callable[[], np.ndarray] | None = None,
        step_delay: float = 0.0,
        render_mode: str | None = None,
    ):
        super().__init__()
        self.render_mode = render_mode
        self.hands: InputController = hands if hands is not None else NullInput()
        self.window = window
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

        if action_int == self.UP:
            self.hands.move_up()
        elif action_int == self.DOWN:
            self.hands.move_down()
        elif action_int == self.LEFT:
            self.hands.move_left()
        elif action_int == self.RIGHT:
            self.hands.move_right()
        elif action_int == self.REVEAL:
            self.hands.reveal()
        elif action_int == self.FLAG:
            self.hands.flag()
        else:
            raise ValueError(f"Invalid action {action_int}; must be in [0, 5]")

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
                HIDDEN: ".",
                FLAGGED: "F",
                MINE: "*",
            }
            lines = []
            for row in self.prev_grid:
                row_str = " ".join(symbols.get(int(c), str(int(c))) for c in row)
                lines.append(row_str)
            return "\n".join(lines)
        return None
