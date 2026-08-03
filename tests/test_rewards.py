"""
Brick 2 (M4): lock RewardCalculator's decision with tests.

RewardCalculator's whole job is to hold the two GridWorld reward numbers
(step_cost, goal_reward) and pick between them -- numbers that used to be
constants baked into GridWorldEnv now come from the caller instead. See
docs/m4/M4_ToDo.md, Brick 2.

Mirrors tests/test_profile.py: same path-insertion trick, plain functions.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))
from src.gametrainer.rewards import RewardCalculator


def test_not_on_goal_returns_step_cost():
    calculator = RewardCalculator(step_cost=-0.01, goal_reward=1.0)
    assert calculator.reward(reached_goal=False) == -0.01


def test_on_goal_returns_goal_reward():
    calculator = RewardCalculator(step_cost=-0.01, goal_reward=1.0)
    assert calculator.reward(reached_goal=True) == 1.0


def test_numbers_come_from_the_caller_not_the_class():
    """Different instances, different numbers -- nothing is hardcoded."""
    calculator = RewardCalculator(step_cost=-5.0, goal_reward=99.0)
    assert calculator.reward(reached_goal=False) == -5.0
    assert calculator.reward(reached_goal=True) == 99.0
