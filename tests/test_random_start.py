"""
Brick 4 (M3): lock the promises of the wrapper that makes the maze need eyes.

Why this wrapper exists at all -- the finding that forced it:
the first pixel training run reached +0.905 reward while the agent was
completely blind. Its action probabilities were identical at every position
(53% DOWN / 47% RIGHT), and a hand-written blind agent playing that same fixed
coin flip scored +0.907. A Ground that can be solved blind cannot prove the
eyes work.

Two separate things made it solvable blind, and the second is the sneaky one:
  1. the start was always (0,0), so one memorised route always worked;
  2. the goal sat in the CORNER, and "always move down or right" funnels you
     into a corner from anywhere, because walls stop you instead of costing you
     the run. Measured: randomising the start ALONE left a blind agent scoring
     +0.947 at a 100% goal rate. It fixed nothing.

So this wrapper does both -- random start, and the goal moved to the middle,
where overshooting is a real mistake.

The promises worth pinning here are the ones that fail in silence:

  - The start really does vary. If it quietly always returned (0,0) the fix
    would be void, the agent would go back to playing blind, and nothing
    anywhere would raise.
  - The goal really moves, and the env underneath ACTS on the new goal. We move
    it by shadowing a class attribute; if that silently failed, episodes would
    still end at the old corner and the maze would stay blind-solvable while
    every other test here still passed.
  - The agent never starts ON the goal. That episode is won before it begins;
    it teaches nothing and quietly inflates mean reward.
  - The picture agrees with where things really are. This is the whole point:
    if the drawing and the true positions disagreed, we would be asking the
    agent to learn from a lie.
  - The Gymnasium contract survives a second layer of wrapping -- reset() still
    a 2-tuple, step() still a 5-tuple.
"""

import sys
from pathlib import Path

import numpy as np

# Project root = parent of tests/  (so `from src.gametrainer...` works)
_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))
from src.gametrainer.gridworld import GridWorldEnv, RandomStart, make_vision_task
from src.gametrainer.perception import PixelObservation


def make_env():
    """The M3 training stack: the vision task (Ground) seen as a picture (eyes)."""
    return PixelObservation(make_vision_task())


def cell_centre(index: int) -> int:
    """Pixel coordinate at the middle of grid row/column `index`."""
    return int((index + 0.5) * 224 / GridWorldEnv.SIZE)


def pixel_at(image, row, col):
    """The RGB colour drawn for grid square (row, col)."""
    return image[cell_centre(row), cell_centre(col)]


def test_the_start_square_actually_varies():
    """The promise the whole wrapper exists for.

    A wrapper that silently always started at (0,0) would raise nothing, train
    happily, and hand back the same blind agent we already caught once.
    """
    env = RandomStart(GridWorldEnv())
    seen = set()
    for _ in range(50):
        env.reset()
        seen.add((env.unwrapped.row, env.unwrapped.col))

    assert len(seen) > 1, f"agent always started at {seen}"


def test_never_starts_on_the_goal():
    """An episode that begins already won teaches nothing and inflates reward."""
    env = RandomStart(GridWorldEnv())
    for _ in range(50):
        env.reset()

        assert (env.unwrapped.row, env.unwrapped.col) != env.goal


def test_goal_moves_off_the_corner():
    """The corner goal is what let a blind 'always down-right' agent win."""
    env = RandomStart(GridWorldEnv())
    env.reset()

    assert env.goal == (2, 2)
    assert env.goal != GridWorldEnv.GOAL  # the M2 corner, deliberately abandoned
    assert env.unwrapped.GOAL == (2, 2)   # the env underneath agrees


def test_env_actually_terminates_at_the_new_goal():
    """The promise the whole fix rests on: the Ground ACTS on the moved goal.

    We move the goal by shadowing a class attribute. If that silently failed,
    episodes would keep ending at the old corner, the maze would stay solvable
    blind, and every other test in this file would still pass.
    """
    env = RandomStart(GridWorldEnv(), goal=(2, 2))
    env.reset()
    env.unwrapped.row, env.unwrapped.col = 1, 2  # one square above the new goal

    _obs, reward, terminated, _truncated, _info = env.step(GridWorldEnv.DOWN)

    assert terminated
    assert reward == GridWorldEnv.GOAL_REWARD


def test_start_is_always_inside_the_grid():
    """Off-grid coordinates would draw nothing and break the reward maths."""
    env = RandomStart(GridWorldEnv())
    for _ in range(50):
        env.reset()

        assert 0 <= env.unwrapped.row < GridWorldEnv.SIZE
        assert 0 <= env.unwrapped.col < GridWorldEnv.SIZE


def test_picture_shows_the_agent_and_goal_where_they_really_are():
    """The drawing must agree with the truth, or the agent learns from a lie."""
    env = make_env()
    for _ in range(20):
        obs, _ = env.reset()
        row, col = env.unwrapped.row, env.unwrapped.col

        assert np.array_equal(pixel_at(obs, row, col), GridWorldEnv.AGENT_COLOR)
        assert np.array_equal(pixel_at(obs, *env.unwrapped.GOAL), GridWorldEnv.GOAL_COLOR)


def test_contract_shapes_survive_the_extra_wrapper():
    """Two layers of wrapping, same Gymnasium contract as M2."""
    env = make_env()

    reset_result = env.reset()
    assert isinstance(reset_result, tuple) and len(reset_result) == 2
    obs, info = reset_result
    assert env.observation_space.contains(obs)
    assert isinstance(info, dict)

    step_result = env.step(env.action_space.sample())
    assert isinstance(step_result, tuple) and len(step_result) == 5
    obs, reward, terminated, truncated, info = step_result
    assert env.observation_space.contains(obs)


def test_same_seed_gives_the_same_start():
    """Reproducibility: a seeded run must be repeatable, or no result is either."""
    first = RandomStart(GridWorldEnv())
    first.reset(seed=123)
    expected = (first.unwrapped.row, first.unwrapped.col)

    second = RandomStart(GridWorldEnv())
    second.reset(seed=123)

    assert (second.unwrapped.row, second.unwrapped.col) == expected


def test_check_env_passes():
    """The official Gymnasium contract checker runs clean on the full stack."""
    import pytest

    sb3_checker = pytest.importorskip("stable_baselines3.common.env_checker")
    sb3_checker.check_env(make_env())


# ---------------------------------------------------------------------------
# The promise M3's whole verdict rests on.
#
# This is a real test, not an experiment: no training, no neural network, fixed
# seed, same answer every time, runs in under a second. What it pins is the
# thing that took a wasted 20-minute training run to discover -- that this
# Ground cannot be beaten without looking at it. If someone later moves the goal
# back to a corner or loosens the step budget, the maze silently becomes
# blind-solvable again, the guardrail starts rubber-stamping blind agents, and
# nothing else in this suite would notice.
# ---------------------------------------------------------------------------

GOAL_RATE_TO_PASS = 0.80  # the bar Brick 0 fixed in scripts/train_gridworld_vit.py


def _goal_rate(policy, episodes=200, seed=0):
    """Fraction of episodes this policy finishes by reaching the goal."""
    rng = np.random.default_rng(seed)
    env = make_vision_task(render_mode=None)
    goals = 0
    for _ in range(episodes):
        env.reset()
        terminated = truncated = False
        while not (terminated or truncated):
            _, _, terminated, truncated, _ = env.step(policy(env, rng))
        goals += int(terminated)
    return goals / episodes


def test_a_blind_agent_cannot_pass_this_task():
    """The exact blind policy that scored +0.905 on the old maze must fail here.

    PPO converged to a fixed 53% DOWN / 47% RIGHT coin flip and never looked at
    the picture. On the old corner-goal maze that won 100% of the time.
    """
    def blind_coin_flip(env, rng):
        return GridWorldEnv.DOWN if rng.random() < 0.533 else GridWorldEnv.RIGHT

    assert _goal_rate(blind_coin_flip) < GOAL_RATE_TO_PASS


def test_a_random_agent_cannot_pass_this_task():
    """The live baseline must fail the bar too, or the bar grades nothing."""
    def uniform_random(env, rng):
        return env.action_space.sample()

    assert _goal_rate(uniform_random) < GOAL_RATE_TO_PASS


def test_an_agent_that_can_see_does_pass_this_task():
    """The other half: the task must be winnable, or the bar is impossible.

    This oracle cheats -- it reads the true positions instead of looking at the
    picture. That is the point: it measures what perfect eyes would be worth.
    """
    def walks_to_the_goal(env, rng):
        grid = env.unwrapped
        goal_row, goal_col = grid.GOAL
        if grid.row < goal_row:
            return GridWorldEnv.DOWN
        if grid.row > goal_row:
            return GridWorldEnv.UP
        if grid.col < goal_col:
            return GridWorldEnv.RIGHT
        return GridWorldEnv.LEFT

    assert _goal_rate(walks_to_the_goal) >= GOAL_RATE_TO_PASS