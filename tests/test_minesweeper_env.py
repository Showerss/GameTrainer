"""
Brick 5 (M5): lock the Minesweeper Gymnasium contract with tests.

Per docs/m5/M5_ToDo.md (Brick 5):
- The env: MinesweeperEnv obeys the universal Gymnasium contract.
- Action space: Discrete(6) -> UP, DOWN, LEFT, RIGHT, REVEAL, FLAG.
- Observation space: 8x8 grid of cell states (0-11, int8).
- reset() -> 2-tuple (obs, info), triggers hands.restart() (Ctrl+R).
- step(action) -> 5-tuple (obs, reward, terminated, truncated, info).
- check_env runs clean.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import gymnasium as gym
import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))

from src.gametrainer.minesweeper import MinesweeperEnv
from src.gametrainer.minesweeper_vision import FLAGGED, GRID, HIDDEN, MINE
from src.gametrainer.rewards import MinesweeperRewardCalculator


def test_action_and_observation_spaces():
    """Action space has 6 discrete moves, observation is an 8x8 int8 grid."""
    env = MinesweeperEnv()
    assert isinstance(env.action_space, gym.spaces.Discrete)
    assert env.action_space.n == 6
    assert isinstance(env.observation_space, gym.spaces.Box)
    assert env.observation_space.shape == (GRID, GRID)
    assert env.observation_space.dtype == np.int8
    assert env.observation_space.low.min() == 0
    assert env.observation_space.high.max() == MINE


def test_reset_returns_two_tuple():
    """reset() must return (obs, info) matching the contract."""
    env = MinesweeperEnv()
    result = env.reset()

    assert isinstance(result, tuple) and len(result) == 2
    obs, info = result
    assert env.observation_space.contains(obs)
    assert isinstance(info, dict)


def test_step_returns_five_tuple():
    """step() must return (obs, reward, terminated, truncated, info)."""
    env = MinesweeperEnv()
    env.reset()
    result = env.step(env.action_space.sample())

    assert isinstance(result, tuple) and len(result) == 5
    obs, reward, terminated, truncated, info = result
    assert env.observation_space.contains(obs)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_hands_dispatched_correctly():
    """Actions 0-5 and reset() call the right methods on the input controller."""
    mock_hands = MagicMock()
    env = MinesweeperEnv(hands=mock_hands)

    env.reset()
    mock_hands.restart.assert_called_once()

    action_to_method = {
        MinesweeperEnv.UP: mock_hands.move_up,
        MinesweeperEnv.DOWN: mock_hands.move_down,
        MinesweeperEnv.LEFT: mock_hands.move_left,
        MinesweeperEnv.RIGHT: mock_hands.move_right,
        MinesweeperEnv.REVEAL: mock_hands.reveal,
        MinesweeperEnv.FLAG: mock_hands.flag,
    }

    for action, method in action_to_method.items():
        env.step(action)
        method.assert_called_once()


def test_reward_and_termination_on_step():
    """Step computes reward and termination from consecutive board reads."""
    board_state = np.full((GRID, GRID), HIDDEN, dtype=np.int8)

    def mock_read():
        return board_state

    calculator = MinesweeperRewardCalculator(
        safe_reveal_reward=1.0,
        mine_penalty=-10.0,
        win_reward=10.0,
    )
    env = MinesweeperEnv(reward_calculator=calculator, read_board_fn=mock_read)
    env.reset()

    # Reveal 2 safe cells
    board_state[0, 0] = 1
    board_state[0, 1] = 2
    _, reward, terminated, truncated, _ = env.step(MinesweeperEnv.REVEAL)
    assert reward == 2.0
    assert terminated is False
    assert truncated is False

    # Flagging gives 0 reward and doesn't terminate
    board_state[0, 2] = FLAGGED
    _, reward, terminated, truncated, _ = env.step(MinesweeperEnv.FLAG)
    assert reward == 0.0
    assert terminated is False

    # Hit a mine
    board_state[4, 4] = MINE
    _, reward, terminated, truncated, _ = env.step(MinesweeperEnv.REVEAL)
    assert reward == -10.0
    assert terminated is True
    assert truncated is False


def test_step_cap_truncates():
    """Exceeding max_steps truncates the episode without terminating."""
    env = MinesweeperEnv(max_steps=5)
    env.reset()

    truncated = False
    for _ in range(5):
        _, _, terminated, truncated, _ = env.step(MinesweeperEnv.UP)

    assert truncated is True
    assert terminated is False


def test_render_ansi():
    """Text rendering formats board cells cleanly."""
    env = MinesweeperEnv(render_mode="ansi")
    env.reset()
    rendered = env.render()
    assert isinstance(rendered, str)
    assert "." in rendered


def test_gymnasium_check_env_clean():
    """Official Gymnasium check_env runs without errors."""
    env = MinesweeperEnv()
    check_env(env)


def test_sb3_check_env_clean():
    """Stable-Baselines3 check_env runs clean if SB3 is installed."""
    sb3_checker = pytest.importorskip("stable_baselines3.common.env_checker")
    env = MinesweeperEnv()
    sb3_checker.check_env(env)
