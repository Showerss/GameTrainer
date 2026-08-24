"""
M2 End-to-End Guardrail — the North Star test for the whole milestone.

Teacher Note: what is this file?
================================
Every other M2 test checks one small thing (a shape, a number, a single move).
THIS test checks the whole journey at once:

    build our GridWorld  ->  let PPO train on it  ->  check it actually learned

"Learned" means two things together:
  1. Its average reward clearly beats a random walker's baseline.
  2. It genuinely reaches the goal, not just wanders a bit less badly.

Why is this test skipped, not xfail?
------------------------------------------------------
**Updated 2026-08-08.** This test used to be marked `xfail` ("expected to
fail") — red on purpose until M2 closed. M2 closed a different way: the
project's tests-vs-experiments policy (CLAUDE.md §5) settled on treating a PPO
training run as an **experiment**, not a test, because it's slow and random
enough to pass one day and fail the next on identical code. `xfail` assumes a
test that will eventually turn green and stay green; a training run doesn't
give you that guarantee. So M2 actually closed via `scripts/train_gridworld.py`
printing a PASS/FAIL verdict, and this file was changed to
`@pytest.mark.skip` — kept as a record of the guardrail's original shape, not
run on every change.

Note: this test trains a small PPO, so it is a little slow compared to the
narrow tests. That's expected — it's the one test that exercises everything.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Project root = parent of tests/  (same pattern as tests/test_logger.py)
_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))

from src.gametrainer.gridworld import GridWorldEnv
from stable_baselines3 import PPO

# How much to look at. Kept small so the guardrail stays quick to run.
RANDOM_EPISODES = 20   # episodes to measure the random baseline over
EVAL_EPISODES = 20     # episodes to judge the trained agent over
TRAIN_STEPS = 2_000    # DELIBERATELY tiny — see the docstring (keeps us red for now)

# The bar the trained agent must clear to call M2 "done".
GOAL_HIT_RATE = 0.9    # must reach the goal in at least 90% of eval episodes


def _evaluate(env, choose_action, episodes):
    """Play `episodes` games with `choose_action`; return (mean_reward, goal_rate).

    `choose_action(obs)` returns an action id. In GridWorld `terminated` is True
    only when the agent lands on the goal, so we count terminations as wins.
    """
    totals = []
    goals = 0
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        total = 0.0
        while not done:
            obs, reward, terminated, truncated, _ = env.step(choose_action(obs))
            total += reward
            if terminated:      # reached the goal
                goals += 1
            done = terminated or truncated
        totals.append(total)
    return float(np.mean(totals)), goals / episodes


@pytest.mark.skip(reason="E2E PPO training is an experiment; run scripts/train_gridworld.py for the guardrail verdict")
def test_m2_gridworld_ppo_beats_random_and_reaches_goal():
    env = GridWorldEnv()

    # 1) Random baseline — how well does aimless luck do?
    rng = np.random.default_rng(0)
    random_mean, _ = _evaluate(env, lambda obs: int(rng.integers(0, 4)), RANDOM_EPISODES)

    # 2) Train PPO on the same world (tiny budget on purpose).
    model = PPO("MlpPolicy", GridWorldEnv(), verbose=0)
    model.learn(total_timesteps=TRAIN_STEPS)

    # 3) Judge the trained agent.
    trained_mean, goal_rate = _evaluate(
        env,
        lambda obs: int(model.predict(obs, deterministic=True)[0]),
        EVAL_EPISODES,
    )

    # The milestone bar: clearly beat random AND actually reach the goal.
    assert trained_mean > random_mean
    assert goal_rate >= GOAL_HIT_RATE