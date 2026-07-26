"""Pick a task where the guardrail can actually tell sighted from lucky.

A usable M3 task needs BOTH:
  - the uniform-random baseline (what Brick 0 measures live) to be clearly beaten
  - headroom: sighted_ceiling - random_baseline > MARGIN_OVER_BASELINE (0.40)
  - the random agent to MISS the 80% goal-rate condition, or that condition
    grades nothing

The step budget is the lever: 100 steps to cover 25 cells lets a random walk
stumble into anything. gymnasium's stock TimeLimit wrapper tightens it without
touching GridWorldEnv.
"""
import sys
from pathlib import Path

# Repo root: docs/m3/experiments/<this file> -> up three levels.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
from gymnasium.wrappers import TimeLimit

from src.gametrainer.gridworld import GridWorldEnv, RandomStart

MARGIN = 0.40
GOAL_RATE_TO_PASS = 0.80


def play(make, policy, episodes=400, seed=0):
    rng = np.random.default_rng(seed)
    env = make()
    rewards, goals = [], 0
    for _ in range(episodes):
        env.reset()
        total, done = 0.0, False
        while not done:
            _, reward, terminated, truncated, _ = env.step(policy(env, rng))
            total += reward
            done = terminated or truncated
        goals += int(terminated)
        rewards.append(total)
    return np.mean(rewards), goals / episodes


def uniform(env, rng):
    return env.action_space.sample()


def sighted(env, rng):
    """Walks straight at the goal -- the ceiling a perfect-vision agent hits."""
    g = env.unwrapped
    goal_row, goal_col = g.GOAL
    if g.row < goal_row:
        return GridWorldEnv.DOWN
    if g.row > goal_row:
        return GridWorldEnv.UP
    if g.col < goal_col:
        return GridWorldEnv.RIGHT
    return GridWorldEnv.LEFT


def blind(env, rng):
    """Best fixed coin flip -- must FAIL, or the task does not need eyes."""
    return GridWorldEnv.DOWN if rng.random() < 0.533 else GridWorldEnv.RIGHT


def build(goal, cap):
    def make():
        env = RandomStart(GridWorldEnv(), goal=goal)
        return TimeLimit(env, max_episode_steps=cap) if cap else env
    return make


print(f"{'task':<32}{'uniform random':>22}{'sighted':>18}{'blind':>18}{'headroom':>10}{'verdict':>10}")
print(f"{'':<32}{'reward  goals':>22}{'reward  goals':>18}{'reward  goals':>18}")

for goal, cap in [((2, 2), None), ((2, 2), 25), ((2, 2), 15), ((2, 2), 10),
                  ((4, 4), 15), ((2, 2), 8)]:
    make = build(goal, cap)
    u_reward, u_goals = play(make, uniform)
    s_reward, s_goals = play(make, sighted)
    b_reward, b_goals = play(make, blind)

    headroom = s_reward - u_reward
    usable = (
        headroom > MARGIN                       # the bar is reachable at all
        and u_goals < GOAL_RATE_TO_PASS         # random must FAIL condition 2
        and s_goals >= GOAL_RATE_TO_PASS        # sighted must PASS condition 2
        and b_goals < GOAL_RATE_TO_PASS         # blind must FAIL -> eyes required
    )
    label = f"goal {goal}, cap {cap or 100}"
    print(
        f"{label:<32}{u_reward:>+13.3f}{u_goals * 100:>8.0f}%"
        f"{s_reward:>+11.3f}{s_goals * 100:>6.0f}%"
        f"{b_reward:>+11.3f}{b_goals * 100:>6.0f}%"
        f"{headroom:>+10.3f}{'  USABLE' if usable else '  no':>10}"
    )
