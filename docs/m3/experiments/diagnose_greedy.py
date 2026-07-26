"""Why does greedy eval score -1.00 when training reached +0.905?

Two candidate causes, identical symptoms:
  A) the greedy (argmax) policy is stuck in a movement cycle
  B) the observation reaching model.predict() differs from training's
"""
import os
import sys
from pathlib import Path

# Repo root: docs/m3/experiments/<this file> -> up three levels.
_root = str(Path(__file__).resolve().parents[3])
sys.path.insert(0, _root)

import numpy as np
import torch
from stable_baselines3 import PPO

from src.gametrainer.gridworld import GridWorldEnv
from src.gametrainer.perception import PixelObservation

NAMES = {0: "UP", 1: "DOWN", 2: "LEFT", 3: "RIGHT"}

model = PPO.load(os.path.join(_root, "models", "ppo_gridworld_vit", "final_model"))
print(f"model.observation_space = {model.observation_space}")

env = PixelObservation(GridWorldEnv(render_mode="rgb_array"))
print(f"env.observation_space   = {env.observation_space}")
print()

# --- Candidate A: trace the greedy path, with action probabilities ----------
obs, _ = env.reset()
print("GREEDY PATH (first 14 steps)")
print(f"{'step':>4} {'pos':>7}  {'action':<6}  probabilities [UP DOWN LEFT RIGHT]")
for i in range(14):
    tensor, _ = model.policy.obs_to_tensor(obs)
    with torch.no_grad():
        probs = model.policy.get_distribution(tensor).distribution.probs[0].numpy()
    action, _ = model.predict(obs, deterministic=True)
    pos = (env.unwrapped.row, env.unwrapped.col)
    print(f"{i:>4} {str(pos):>7}  {NAMES[int(action)]:<6}  {np.round(probs, 3)}")
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        print(f"  -> episode ended at step {i+1}, terminated={terminated}")
        break

# --- Candidate B: does the raw HWC obs get transposed the same as training? -
obs, _ = env.reset()
tensor_from_hwc, _ = model.policy.obs_to_tensor(obs)
manual_chw = np.transpose(obs, (2, 0, 1))
tensor_from_chw, _ = model.policy.obs_to_tensor(manual_chw)
print()
print("OBSERVATION HANDLING")
print(f"  raw env obs shape      : {obs.shape}")
print(f"  after obs_to_tensor    : {tuple(tensor_from_hwc.shape)}")
print(f"  matches manual CHW     : {torch.equal(tensor_from_hwc, tensor_from_chw)}")

# --- Control: how does the STOCHASTIC policy do on the same env? ------------
rewards, goals = [], 0
for _ in range(20):
    obs, _ = env.reset()
    done = False
    total = 0.0
    while not done:
        action, _ = model.predict(obs, deterministic=False)
        obs, reward, terminated, truncated, _ = env.step(action)
        total += reward
        done = terminated or truncated
    goals += int(terminated)
    rewards.append(total)
print()
print("CONTROL — same env, same model, sampling instead of argmax")
print(f"  mean reward: {np.mean(rewards):+.3f}   goals: {goals}/20")
