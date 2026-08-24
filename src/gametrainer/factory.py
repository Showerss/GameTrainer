"""
make_env(profile) - Milestone M4, Brick 3.

Turns a validated Profile into a Gymnasium env. One function, one if-chain
over the (ground, perception) pairs Profile allows -- no registry, no
dynamic imports. This is the only place a profile's name becomes an object.
See docs/m4/M4_ToDo.md, Brick 3.
"""

from __future__ import annotations

import gymnasium as gym

from src.gametrainer.gridworld import GridWorldEnv, make_vision_task
from src.gametrainer.perception import PixelObservation
from src.gametrainer.profile import Profile


def make_env(profile: Profile) -> gym.Env:
    """Build the env a Profile describes. Raises ValueError on an unknown pair."""
    if profile.ground == "cartpole" and profile.perception == "numeric":
        return gym.make("CartPole-v1")

    if profile.ground == "gridworld" and profile.perception == "numeric":
        return GridWorldEnv(step_cost=profile.step_cost, goal_reward=profile.goal_reward)

    if profile.ground == "gridworld" and profile.perception == "pixels":
        task = make_vision_task(step_cost=profile.step_cost, goal_reward=profile.goal_reward)
        return PixelObservation(task)

    raise ValueError(
        f"no env for ground={profile.ground!r} perception={profile.perception!r}"
    )
