"""
Brick #2 (M2): lock the GridWorld contract with tests.

These tests don't add behaviour — they pin down the promises GridWorld must
always keep. The whole project rests on the Gymnasium contract (reset/step
shapes never change), so if a future edit breaks one of these promises, pytest
goes red and tells us immediately.

Mirrors tests/test_logger.py: same path-insertion trick, same plain functions.
"""

import sys
from pathlib import Path

# Project root = parent of tests/  (so `from src.gametrainer...` works)
_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))
from src.gametrainer.gridworld import GridWorldEnv


def test_reset_returns_obs_and_info():
    """reset() must hand back a 2-tuple, and the obs must be a legal point."""
    env = GridWorldEnv()
    result = env.reset()

    assert isinstance(result, tuple) and len(result) == 2
    obs, info = result
    assert env.observation_space.contains(obs)  # inside the Box space
    assert isinstance(info, dict)


def test_step_returns_five_tuple():
    """step() must always hand back the 5-tuple in the right shape/types."""
    env = GridWorldEnv()
    env.reset()
    result = env.step(env.action_space.sample())

    assert isinstance(result, tuple) and len(result) == 5
    obs, reward, terminated, truncated, info = result
    assert env.observation_space.contains(obs)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_reaching_goal_terminates_with_reward():
    """Walking onto the goal sets terminated=True and pays the goal reward."""
    env = GridWorldEnv()
    env.reset()

    # Start (0,0) -> goal (4,4): four DOWNs then four RIGHTs = 8 moves.
    for _ in range(4):
        env.step(GridWorldEnv.DOWN)
    for _ in range(3):
        env.step(GridWorldEnv.RIGHT)
    obs, reward, terminated, truncated, info = env.step(GridWorldEnv.RIGHT)

    assert terminated is True
    assert truncated is False
    assert reward == GridWorldEnv.GOAL_REWARD


def test_step_cap_truncates():
    """Running out of moves (the step cap) sets truncated=True, not terminated."""
    env = GridWorldEnv()
    env.reset()

    # Press UP forever: the agent is stuck at (0,0) and never reaches the goal,
    # so the only way the episode ends is by hitting the MAX_STEPS cap.
    terminated = truncated = False
    for _ in range(GridWorldEnv.MAX_STEPS):
        _, _, terminated, truncated, _ = env.step(GridWorldEnv.UP)

    assert truncated is True
    assert terminated is False


def test_check_env_passes():
    """The official Gymnasium contract checker runs clean.

    Skips automatically if stable_baselines3 isn't installed (it lives in the
    optional 'rl' extra and pulls in torch). Install with: pip install -e ".[rl]"
    """
    import pytest

    sb3_checker = pytest.importorskip("stable_baselines3.common.env_checker")
    sb3_checker.check_env(GridWorldEnv())


def test_each_action_moves_the_right_way():
    """From a middle cell (2,2), every move lands exactly one square over.

    The contract tests above only exercise DOWN/RIGHT (the goal path). This
    pins all four directions so a swapped action id can't slip through.
    """
    # Where the agent should be after each action, starting from (2, 2).
    expected = {
        GridWorldEnv.UP: (1, 2),
        GridWorldEnv.DOWN: (3, 2),
        GridWorldEnv.LEFT: (2, 1),
        GridWorldEnv.RIGHT: (2, 3),
    }

    for action, (want_row, want_col) in expected.items():
        env = GridWorldEnv()
        env.reset()
        # Walk to the middle: (0,0) -> (2,2) with two DOWNs and two RIGHTs.
        env.step(GridWorldEnv.DOWN)
        env.step(GridWorldEnv.DOWN)
        env.step(GridWorldEnv.RIGHT)
        env.step(GridWorldEnv.RIGHT)

        obs, _, _, _, _ = env.step(action)
        assert (int(obs[0]), int(obs[1])) == (want_row, want_col)


def test_walls_block_movement():
    """At the top-left corner, UP and LEFT do nothing — walls stop the agent."""
    env = GridWorldEnv()
    env.reset()  # agent starts at (0, 0)

    obs, _, _, _, _ = env.step(GridWorldEnv.UP)
    assert (int(obs[0]), int(obs[1])) == (0, 0)

    obs, _, _, _, _ = env.step(GridWorldEnv.LEFT)
    assert (int(obs[0]), int(obs[1])) == (0, 0)


def test_ordinary_step_pays_step_cost():
    """A normal move (not onto the goal) costs STEP_COST and doesn't end the game."""
    env = GridWorldEnv()
    env.reset()

    obs, reward, terminated, truncated, info = env.step(GridWorldEnv.DOWN)
    assert reward == GridWorldEnv.STEP_COST
    assert terminated is False
    assert truncated is False


def test_reset_places_agent_at_start():
    """reset() always drops the agent back on the start square (0, 0)."""
    env = GridWorldEnv()
    env.reset()
    # Move away so we know reset truly sends the agent home.
    env.step(GridWorldEnv.DOWN)
    env.step(GridWorldEnv.RIGHT)

    obs, _ = env.reset()
    assert (int(obs[0]), int(obs[1])) == GridWorldEnv.START
