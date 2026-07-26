"""Control: can a BLIND agent score what the 'trained' ViT agent scored?

The ViT agent's logits were constant, i.e. it plays a fixed coin flip:
DOWN 53.3% / RIGHT 46.6%, ignoring the picture entirely. Replay exactly that
policy with no vision at all. If it matches +0.905, then this GridWorld does
not require eyes to solve, and M3's training reward proves nothing about the ViT.
"""
import sys
from pathlib import Path

# Repo root: docs/m3/experiments/<this file> -> up three levels.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np

from src.gametrainer.gridworld import GridWorldEnv

RNG = np.random.default_rng(0)
DOWN, RIGHT = GridWorldEnv.DOWN, GridWorldEnv.RIGHT
P_DOWN = 0.533  # the exact distribution the ViT agent converged to

env = GridWorldEnv()
rewards, lengths, goals = [], [], 0
for _ in range(200):
    env.reset()
    total, done = 0.0, False
    while not done:
        action = DOWN if RNG.random() < P_DOWN else RIGHT
        _, reward, terminated, truncated, info = env.step(action)
        total += reward
        done = terminated or truncated
    goals += int(terminated)
    rewards.append(total)
    lengths.append(info["steps"])

print("BLIND open-loop agent (never looks at the observation), 200 episodes")
print(f"  mean reward : {np.mean(rewards):+.3f}")
print(f"  mean steps  : {np.mean(lengths):.1f}")
print(f"  goal rate   : {goals / 200 * 100:.0f}%")
print()
print("  ViT agent during training : +0.905 reward, 10.5 steps")
