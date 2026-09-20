"""
make_env(profile) - Milestone M4, Brick 3 & Milestone M5, Brick 6.

Turns a validated Profile into a Gymnasium env. One function, one if-chain
over the (ground, perception) pairs Profile allows -- no registry, no
dynamic imports. This is the only place a profile's name becomes an object.
See docs/m4/M4_ToDo.md, Brick 3 and docs/m5/M5_ToDo.md, Brick 6.
"""

from __future__ import annotations

from collections.abc import Callable

import gymnasium as gym
import numpy as np

from src.gametrainer.gridworld import GridWorldEnv, make_vision_task
from src.gametrainer.input import InputController, KeyboardInput, NullInput
from src.gametrainer.minesweeper import MinesweeperEnv
from src.gametrainer.perception import PixelObservation
from src.gametrainer.profile import Profile
from src.gametrainer.rewards import MinesweeperRewardCalculator
from src.gametrainer.screen import GameWindow

_LIVE_CAPTURE_DELAY = 0.5


def _require_profile_number(value: float | None, field: str) -> float:
    """Reject unset Minesweeper reward numbers instead of silently defaulting."""
    if value is None:
        raise ValueError(f"minesweeper profile field '{field}' must be set")
    return float(value)


def make_env(
    profile: Profile,
    *,
    hands: InputController | None = None,
    window: GameWindow | None = None,
    read_board_fn: Callable[[], np.ndarray] | None = None,
) -> gym.Env:
    """Build the env a Profile describes. Raises ValueError on an unknown pair."""
    if profile.ground == "cartpole" and profile.perception == "numeric":
        return gym.make("CartPole-v1")

    if profile.ground == "gridworld" and profile.perception == "numeric":
        return GridWorldEnv(step_cost=profile.step_cost, goal_reward=profile.goal_reward)

    if profile.ground == "gridworld" and profile.perception == "pixels":
        task = make_vision_task(step_cost=profile.step_cost, goal_reward=profile.goal_reward)
        return PixelObservation(task)

    if profile.ground == "minesweeper" and profile.perception == "numeric":
        reward_calc = MinesweeperRewardCalculator(
            safe_reveal_reward=_require_profile_number(
                profile.safe_reveal_reward, "safe_reveal_reward"
            ),
            mine_penalty=_require_profile_number(profile.mine_penalty, "mine_penalty"),
            win_reward=_require_profile_number(profile.win_reward, "win_reward"),
        )

        resolved_hands = hands
        resolved_window = window
        owns_window = False

        # If live components were not injected, attempt auto-discovery of LibreMines
        if resolved_hands is None and resolved_window is None and read_board_fn is None:
            resolved_window = GameWindow("LibreMines")
            resolved_hands = KeyboardInput(resolved_window.hwnd)
            resolved_hands.focus()
            owns_window = True
        elif resolved_hands is None:
            resolved_hands = NullInput()

        live_window = resolved_window is not None and read_board_fn is None

        return MinesweeperEnv(
            hands=resolved_hands,
            window=resolved_window,
            reward_calculator=reward_calc,
            read_board_fn=read_board_fn,
            step_delay=_LIVE_CAPTURE_DELAY if live_window else 0.0,
            owns_window=owns_window,
        )

    raise ValueError(
        f"no env for ground={profile.ground!r} perception={profile.perception!r}"
    )
