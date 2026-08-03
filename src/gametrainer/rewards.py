"""
RewardCalculator - Milestone M4, Brick 2.

Holds the two GridWorld reward numbers (step_cost, goal_reward) and picks
between them. These numbers used to be constants baked into GridWorldEnv;
now they're passed in, so a Profile can carry them instead of a .py edit.
See docs/m4/M4_ToDo.md, Brick 2.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RewardCalculator:
    """Reward for one GridWorld step: goal_reward on the goal, step_cost otherwise."""

    step_cost: float
    goal_reward: float

    def reward(self, reached_goal: bool) -> float:
        return self.goal_reward if reached_goal else self.step_cost
