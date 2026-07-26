"""Where does the position signal die: the picture, the ViT, or the head?

Walk the agent to 5 distinct cells and measure, at each stage of the pipeline,
how different those 5 states look.
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

model = PPO.load(os.path.join(_root, "models", "ppo_gridworld_vit", "final_model"))
extractor = model.policy.features_extractor

env = PixelObservation(GridWorldEnv(render_mode="rgb_array"))
CELLS = [(0, 0), (0, 4), (2, 2), (4, 0), (3, 4)]

obs_list, feat_list, logit_list = [], [], []
for (r, c) in CELLS:
    env.reset()
    env.unwrapped.row, env.unwrapped.col = r, c
    obs = env.unwrapped.render()
    tensor, _ = model.policy.obs_to_tensor(obs)
    with torch.no_grad():
        feats = extractor(tensor.float() / 255.0)
        logits = model.policy.get_distribution(tensor).distribution.logits[0]
    obs_list.append(obs.astype(np.float32))
    feat_list.append(feats[0].numpy())
    logit_list.append(logits.numpy())

obs_arr = np.stack(obs_list)
feat_arr = np.stack(feat_list)
logit_arr = np.stack(logit_list)


def spread(name, arr):
    """How much does this stage vary across the 5 cells, relative to its size?"""
    per_dim_std = arr.std(axis=0)
    magnitude = np.abs(arr).mean()
    print(f"  {name:<22} mean|value|={magnitude:10.4f}   "
          f"std across cells={per_dim_std.mean():10.6f}   "
          f"ratio={per_dim_std.mean() / magnitude:.5f}")


print("HOW MUCH DOES EACH STAGE CHANGE BETWEEN THE 5 CELLS?")
spread("raw pixels", obs_arr.reshape(5, -1))
spread("ViT features (192)", feat_arr)
spread("policy logits (4)", logit_arr)

print()
print("PAIRWISE COSINE SIMILARITY OF ViT FEATURES (1.000 = indistinguishable)")
norm = feat_arr / np.linalg.norm(feat_arr, axis=1, keepdims=True)
cos = norm @ norm.T
print("        " + "".join(f"{str(c):>9}" for c in CELLS))
for i, c in enumerate(CELLS):
    print(f"{str(c):>8}" + "".join(f"{cos[i, j]:9.4f}" for j in range(len(CELLS))))

print()
print("ACTION PROBABILITIES PER CELL [UP DOWN LEFT RIGHT]")
for (r, c), lg in zip(CELLS, logit_arr):
    p = np.exp(lg - lg.max())
    p /= p.sum()
    print(f"  {str((r, c)):>7}  {np.round(p, 4)}")

print()
print("SANITY: are the pictures actually different?")
for i in range(1, len(CELLS)):
    diff = (obs_arr[0] != obs_arr[i]).sum()
    print(f"  {CELLS[0]} vs {CELLS[i]}: {diff:,} of {obs_arr[0].size:,} pixel values differ")
