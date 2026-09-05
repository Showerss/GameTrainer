"""
make_env(profile) - Milestone M4, Brick 3 & Milestone M5, Brick 6.

Turns a validated Profile into a Gymnasium env. One function, one if-chain
over the (ground, perception) pairs Profile allows -- no registry, no
dynamic imports. This is the only place a profile's name becomes an object.
See docs/m4/M4_ToDo.md, Brick 3 and docs/m5/M5_ToDo.md, Brick 6.
"""

from __future__ import annotations

from typing import Callable

import gymnasium as gym
import numpy as np

from src.gametrainer.gridworld import GridWorldEnv, make_vision_task
from src.gametrainer.input import InputController, KeyboardInput, NullInput
from src.gametrainer.minesweeper import MinesweeperEnv
from src.gametrainer.perception import PixelObservation
from src.gametrainer.profile import Profile
from src.gametrainer.rewards import MinesweeperRewardCalculator
from src.gametrainer.screen import GameWindow


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
            safe_reveal_reward=profile.safe_reveal_reward
            if profile.safe_reveal_reward is not None
            else 1.0,
            mine_penalty=profile.mine_penalty
            if profile.mine_penalty is not None
            else -10.0,
            win_reward=profile.win_reward
            if profile.win_reward is not None
            else 10.0,
        )

        resolved_hands = hands
        resolved_window = window

        # If live components were not injected, attempt auto-discovery of LibreMines
        if resolved_hands is None and resolved_window is None and read_board_fn is None:
            try:
                resolved_window = GameWindow("LibreMines")
                resolved_hands = KeyboardInput(resolved_window.hwnd)
            except Exception:
                resolved_window = None
                resolved_hands = NullInput()
        elif resolved_hands is None:
            resolved_hands = NullInput()

        return MinesweeperEnv(
            hands=resolved_hands,
            window=resolved_window,
            reward_calculator=reward_calc,
            read_board_fn=read_board_fn,
        )

    raise ValueError(
        f"no env for ground={profile.ground!r} perception={profile.perception!r}"
    )
