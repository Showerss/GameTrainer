"""Which GridWorld variant actually REQUIRES vision?

The test for "requires vision" is the gap between two agents on the same task:
  - blind  : the best fixed coin flip, never looks
  - sighted: an oracle that knows where it and the goal are, walks straight there

A small gap means the task is solvable blind and cannot prove the eyes work.
A large gap means looking is worth something, which is what M3 needs.
"""
import sys
from pathlib import Path

# Repo root: docs/m3/experiments/<this file> -> up three levels.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np

from src.gametrainer.gridworld import GridWorldEnv, RandomStart

DOWN, RIGHT = GridWorldEnv.DOWN, GridWorldEnv.RIGHT
UP, LEFT = GridWorldEnv.UP, GridWorldEnv.LEFT


class RandomGoal(RandomStart):
    """Random start AND a random goal square, set per-episode.

    Setting grid.GOAL on the instance shadows the class attribute, so both
    step() and _render_rgb() pick it up. GridWorldEnv is still not edited.
    """

    def reset(self, **kwargs):
        obs, info = super().reset(**kwargs)
        grid = self.unwrapped
        row, col = grid.row, grid.col
        while (row, col) == (grid.row, grid.col):
            row = int(self.np_random.integers(grid.SIZE))
            col = int(self.np_random.integers(grid.SIZE))
        grid.GOAL = (row, col)
        return obs, info


# Note: variant C ("random start, centre goal") was a local class when this was
# first run. It is now just RandomStart's own behaviour, so it uses the shipped
# wrapper directly. Variant B must pass the corner goal EXPLICITLY -- RandomStart
# now defaults to the centre, so omitting it would silently rerun variant C.


def play(env, policy, episodes=300, seed=0):
    rng = np.random.default_rng(seed)
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


def blind(env, rng):
    """Never looks. The coin flip PPO converged to on the fixed-start grid."""
    return DOWN if rng.random() < 0.533 else RIGHT


def sighted(env, rng):
    """Looks at both squares and walks straight at the goal."""
    g = env.unwrapped
    goal_row, goal_col = g.GOAL
    if g.row < goal_row:
        return DOWN
    if g.row > goal_row:
        return UP
    if g.col < goal_col:
        return RIGHT
    return LEFT


CORNER = GridWorldEnv.GOAL  # (4, 4) -- the original, blind-solvable placement
CENTRE = (2, 2)

VARIANTS = [
    ("A  fixed start,  corner goal (original)", lambda: GridWorldEnv()),
    ("B  random start, corner goal", lambda: RandomStart(GridWorldEnv(), goal=CORNER)),
    ("C  random start, centre goal (chosen)", lambda: RandomStart(GridWorldEnv(), goal=CENTRE)),
    ("D  random start, RANDOM goal", lambda: RandomGoal(GridWorldEnv())),
]

print(f"{'variant':<44}{'blind':>18}{'sighted':>18}{'gap':>8}")
print(f"{'':<44}{'reward   goals':>18}{'reward   goals':>18}")
for name, factory in VARIANTS:
    b_reward, b_goals = play(factory(), blind)
    s_reward, s_goals = play(factory(), sighted)
    print(
        f"{name:<44}{b_reward:>+9.3f}{b_goals * 100:>7.0f}%"
        f"{s_reward:>+9.3f}{s_goals * 100:>7.0f}%{s_reward - b_reward:>+8.3f}"
    )
