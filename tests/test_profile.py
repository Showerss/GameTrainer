"""
Brick 1 (M4): lock Profile's load-and-validate promise with tests.

Profile's whole job is to fail LOUDLY at load time instead of quietly mid-run
-- see docs/m4/M4_ToDo.md, Brick 1. Each test below changes ONE thing about a
known-good profile so the reason a load fails is never ambiguous.

Mirrors tests/test_gridworld.py: same path-insertion trick, plain functions.
"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))
from src.gametrainer.profile import Profile

# A known-good GridWorld profile. Individual tests below change ONE field so
# the reason a load fails is never ambiguous. Numbers match train_gridworld.py.
GOOD_GRIDWORLD = dict(
    ground="gridworld",
    perception="numeric",
    reward="gridworld",
    step_cost=-0.01,
    goal_reward=1.0,
    total_timesteps=25_000,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.0,
    margin_over_baseline=0.5,
)

# A known-good CartPole profile. reward: builtin -- no step_cost/goal_reward.
GOOD_CARTPOLE = dict(
    ground="cartpole",
    perception="numeric",
    reward="builtin",
    total_timesteps=25_000,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.0,
    margin_over_baseline=22.0,
)


def _write(tmpdir, fields: dict, filename: str = "profile.yaml") -> str:
    path = Path(tmpdir) / filename
    path.write_text(yaml.dump(fields))
    return str(path)


def test_valid_gridworld_profile_loads_expected_fields():
    with TemporaryDirectory() as tmpdir:
        profile = Profile.from_yaml(_write(tmpdir, GOOD_GRIDWORLD))

    assert profile.ground == "gridworld"
    assert profile.perception == "numeric"
    assert profile.reward == "gridworld"
    assert profile.step_cost == -0.01
    assert profile.goal_reward == 1.0
    assert profile.total_timesteps == 25_000
    assert profile.learning_rate == 3e-4
    assert profile.margin_over_baseline == 0.5
    assert profile.min_goal_rate is None


def test_valid_cartpole_profile_loads_without_reward_numbers():
    """CartPole declares reward: builtin -- no step_cost/goal_reward needed."""
    with TemporaryDirectory() as tmpdir:
        profile = Profile.from_yaml(_write(tmpdir, GOOD_CARTPOLE))

    assert profile.reward == "builtin"
    assert profile.step_cost is None
    assert profile.goal_reward is None


def test_unknown_ground_raises_naming_legal_options():
    bad = {**GOOD_GRIDWORLD, "ground": "supermario"}
    with TemporaryDirectory() as tmpdir:
        path = _write(tmpdir, bad)
        with pytest.raises(ValueError) as exc_info:
            Profile.from_yaml(path)

    message = str(exc_info.value)
    assert "supermario" in message
    assert "cartpole" in message and "gridworld" in message


def test_missing_required_field_raises():
    bad = {k: v for k, v in GOOD_GRIDWORLD.items() if k != "total_timesteps"}
    with TemporaryDirectory() as tmpdir:
        path = _write(tmpdir, bad, filename="broken.yaml")
        with pytest.raises(ValueError) as exc_info:
            Profile.from_yaml(path)

    message = str(exc_info.value)
    assert "total_timesteps" in message
    assert "broken.yaml" in message


def test_pixels_perception_on_cartpole_raises():
    """CartPole has no rgb_array Ground built -- say so at load time, not mid-run."""
    bad = {**GOOD_CARTPOLE, "perception": "pixels"}
    with TemporaryDirectory() as tmpdir:
        path = _write(tmpdir, bad)
        with pytest.raises(ValueError) as exc_info:
            Profile.from_yaml(path)

    assert "cartpole" in str(exc_info.value)


def test_unknown_perception_raises_naming_legal_options():
    bad = {**GOOD_GRIDWORLD, "perception": "vibes"}
    with TemporaryDirectory() as tmpdir:
        path = _write(tmpdir, bad)
        with pytest.raises(ValueError) as exc_info:
            Profile.from_yaml(path)

    message = str(exc_info.value)
    assert "numeric" in message and "pixels" in message


def test_gridworld_reward_missing_numbers_raises():
    bad = {k: v for k, v in GOOD_GRIDWORLD.items() if k != "step_cost"}
    with TemporaryDirectory() as tmpdir:
        path = _write(tmpdir, bad)
        with pytest.raises(ValueError) as exc_info:
            Profile.from_yaml(path)

    assert "step_cost" in str(exc_info.value)
