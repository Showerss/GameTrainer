"""
Brick 3 (M4): lock make_env(profile) with tests.

make_env's whole job is turning a validated Profile into a Gymnasium env --
see docs/m4/M4_ToDo.md, Brick 3. Each of the three profiles gets its own
check_env pass and its own observation_space check, so a wrong wrapper order
or a forgotten reward number shows up here, not 19 minutes into training.

Mirrors tests/test_profile.py: same path-insertion trick, plain functions,
Profiles built directly (not from_yaml) so this stays fast and doesn't
depend on YAML files Brick 4 hasn't created yet.
"""

import sys
from pathlib import Path

import pytest
from gymnasium.wrappers import TimeLimit

_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))
from src.gametrainer.factory import make_env
from src.gametrainer.gridworld import GridWorldEnv, RandomStart
from src.gametrainer.perception import PixelObservation
from src.gametrainer.profile import Profile

# Same three shapes Brick 4 will save as YAML.
CARTPOLE = Profile(
    ground="cartpole", perception="numeric", reward="builtin",
    total_timesteps=25_000, learning_rate=3e-4, n_steps=2048, batch_size=64,
    n_epochs=10, gamma=0.99, gae_lambda=0.95, clip_range=0.2, ent_coef=0.0,
    margin_over_baseline=22.0,
)

GRIDWORLD = Profile(
    ground="gridworld", perception="numeric", reward="gridworld",
    step_cost=-0.01, goal_reward=1.0,
    total_timesteps=25_000, learning_rate=3e-4, n_steps=2048, batch_size=64,
    n_epochs=10, gamma=0.99, gae_lambda=0.95, clip_range=0.2, ent_coef=0.0,
    margin_over_baseline=0.5,
)

GRIDWORLD_PIXELS = Profile(
    ground="gridworld", perception="pixels", reward="gridworld",
    step_cost=-0.01, goal_reward=1.0,
    total_timesteps=20_000, learning_rate=3e-4, n_steps=512, batch_size=64,
    n_epochs=4, gamma=0.99, gae_lambda=0.95, clip_range=0.2, ent_coef=0.0,
    margin_over_baseline=0.40,
)


def test_cartpole_env_passes_check_env_and_matches_space():
    sb3_checker = pytest.importorskip("stable_baselines3.common.env_checker")
    env = make_env(CARTPOLE)
    sb3_checker.check_env(env)
    assert env.observation_space.shape == (4,)


def test_gridworld_numeric_env_passes_check_env_and_matches_space():
    sb3_checker = pytest.importorskip("stable_baselines3.common.env_checker")
    env = make_env(GRIDWORLD)
    sb3_checker.check_env(env)
    assert env.observation_space.shape == (2,)


def test_gridworld_pixels_env_passes_check_env_and_matches_space():
    sb3_checker = pytest.importorskip("stable_baselines3.common.env_checker")
    env = make_env(GRIDWORLD_PIXELS)
    sb3_checker.check_env(env)
    assert env.observation_space.shape == (224, 224, 3)
    assert env.observation_space.low.min() == 0
    assert env.observation_space.high.max() == 255


def test_gridworld_pixels_wrapper_order_is_task_inside_pixels_outside():
    """Pins the M3 rule: task/RandomStart INSIDE, PixelObservation OUTSIDE."""
    env = make_env(GRIDWORLD_PIXELS)
    assert isinstance(env, PixelObservation)
    assert isinstance(env.env, TimeLimit)
    assert isinstance(env.env.env, RandomStart)


def test_gridworld_reward_numbers_come_from_the_profile_not_the_class():
    """Negative control: if the YAML were decorative and GridWorldEnv's own
    class constants (-0.01 / 1.0) were still driving the reward, this would
    fail. Numbers here are deliberately not the class defaults."""
    custom = Profile(
        ground="gridworld", perception="numeric", reward="gridworld",
        step_cost=-5.0, goal_reward=99.0,
        total_timesteps=1, learning_rate=1, n_steps=1, batch_size=1, n_epochs=1,
        gamma=1, gae_lambda=1, clip_range=1, ent_coef=1, margin_over_baseline=1,
    )
    env = make_env(custom)
    env.reset()
    _, reward, _, _, _ = env.step(GridWorldEnv.UP)  # walks into the wall, no goal
    assert reward == -5.0


def test_unknown_ground_perception_pair_raises():
    """cartpole+pixels is blocked at Profile.from_yaml, but a directly built
    Profile can still reach make_env -- it must fail loudly, not silently
    build the wrong thing."""
    bad = Profile(
        ground="cartpole", perception="pixels", reward="builtin",
        total_timesteps=1, learning_rate=1, n_steps=1, batch_size=1, n_epochs=1,
        gamma=1, gae_lambda=1, clip_range=1, ent_coef=1, margin_over_baseline=1,
    )
    with pytest.raises(ValueError):
        make_env(bad)
