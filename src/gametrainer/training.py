"""
Shared training setup for the M1 and M2 scripts (R1, Brick 7).

train_cartpole.py (M1) and train_gridworld.py (M2) used to spell out the same
PPO numbers, the same two callbacks and the same "read evaluations.npz" block,
line for line. They live here once now. Each script still owns its own bar,
baseline and verdict -- only the plumbing is shared.
"""

from __future__ import annotations

import os

import numpy as np
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback

# The PPO numbers M1 and M2 both train with.
# Teacher Note: these are SB3's sensible defaults for small "numbers in" tasks.
# M3 (pixels) and M4 (profiles) set their own, so they don't use this.
CLASSIC_PPO_SETTINGS = {
    "learning_rate": 3e-4,  # How big each learning step is
    "n_steps": 2048,        # Steps collected before each update
    "batch_size": 64,       # Mini-batch size for the update
    "n_epochs": 10,         # How many passes over each batch
    "gamma": 0.99,          # Discount factor (value of future rewards)
    "gae_lambda": 0.95,     # Bias-variance trade-off in advantage estimation
    "clip_range": 0.2,      # PPO's "proximal" clipping — keeps updates conservative
    "ent_coef": 0.0,        # Entropy bonus (0 = no extra exploration push needed)
}

CHECKPOINT_FREQ = 5_000  # save a checkpoint this often (steps)
EVAL_FREQ = 2_000        # score the agent on a separate env this often (steps)


def make_training_callbacks(eval_env, model_dir: str, log_dir: str, name_prefix: str) -> list:
    """The two helpers that run alongside training: save checkpoints, and evaluate.

    EvalCallback plays 10 episodes on a separate env every EVAL_FREQ steps,
    prints the mean reward, and writes it to log_dir/evaluations.npz.
    """
    checkpoint_cb = CheckpointCallback(
        save_freq=CHECKPOINT_FREQ,
        save_path=model_dir,
        name_prefix=name_prefix,
        verbose=0,
    )
    eval_cb = EvalCallback(
        eval_env,
        n_eval_episodes=10,
        eval_freq=EVAL_FREQ,
        log_path=log_dir,
        best_model_save_path=model_dir,
        verbose=1,  # Print eval results to console
        warn=False,
    )
    return [checkpoint_cb, eval_cb]


def best_eval_reward(log_dir: str) -> float | None:
    """Best mean reward EvalCallback recorded, or None if it never wrote a log."""
    results_path = os.path.join(log_dir, "evaluations.npz")
    if not os.path.exists(results_path):
        return None
    data = np.load(results_path)
    # EvalCallback stores rewards in 'results' (shape: [n_evals, n_episodes])
    return float(data["results"].mean(axis=1).max())
