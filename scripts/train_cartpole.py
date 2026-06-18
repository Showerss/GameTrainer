"""
CartPole Training Script - Milestone M1

Teacher Note: What are we doing here?
======================================
In M0 we proved the *loop* works by running CartPole with random actions.
Random actions score about 20–25 reward per episode because the pole just
falls over almost immediately — the agent has no strategy.

In M1 we swap the random action for a *learning* agent called PPO.
PPO watches the reward signal and, over many episodes, adjusts its
strategy to keep the pole balanced longer. By the end you should see
the mean reward climb well above the random baseline.

What is PPO?
------------
Proximal Policy Optimization (PPO) is the "borrowed brain" from the PRD.
It's an algorithm from stable-baselines3 that we don't have to write.
We just hand it an environment and tell it to learn — it handles all
the math of figuring out which actions lead to better rewards.

Why MlpPolicy and not CnnPolicy?
---------------------------------
CartPole's "observation" is 4 numbers (cart position, cart velocity,
pole angle, pole angular velocity) — not an image. MlpPolicy feeds
those numbers through a small fully-connected network, which is perfect
for this. CnnPolicy (used in train.py for Stardew) expects pixels and
would be wasteful here.

Usage:
    python scripts/train_cartpole.py               # default: 25,000 steps
    python scripts/train_cartpole.py --steps 50000  # longer run
    python scripts/train_cartpole.py --render       # watch the agent play
"""

import os
import sys
import argparse
import numpy as np

# Add project root to path so we can import from src/
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback

# We import NullInput to keep the architecture in view even though CartPole
# is programmatic and doesn't need real key presses. Consistent with run_cartpole.py.
from src.gametrainer.input import NullInput

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# M0 random-action baseline (documented in run_cartpole.py output).
# CartPole gives +1 reward per step; a random policy averages ~20–25 steps
# per episode before the pole falls. We use 22 as a conservative baseline.
M0_RANDOM_BASELINE = 22.0

# "Clearly risen" threshold: 2× the random baseline.
# CartPole max is 500; PPO usually reaches 100–500 within 25k steps.
PASS_THRESHOLD = M0_RANDOM_BASELINE * 2  # 44

MODEL_DIR = "models/ppo_cartpole"
LOG_DIR = "logs/cartpole"

DEFAULT_TIMESTEPS = 25_000
CHECKPOINT_FREQ = 5_000
EVAL_FREQ = 2_000


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="M1 — Train PPO on CartPole and verify reward rises above random baseline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/train_cartpole.py               # 25k steps (default, ~1-2 min on CPU)
  python scripts/train_cartpole.py --steps 50000  # longer run, higher reward ceiling
  python scripts/train_cartpole.py --render       # show the CartPole window during eval
        """,
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=DEFAULT_TIMESTEPS,
        help=f"Total training timesteps (default: {DEFAULT_TIMESTEPS:,})",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render the CartPole window during evaluation episodes",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Environment factory helpers
# ---------------------------------------------------------------------------

def make_train_env() -> gym.Env:
    """Create the training environment (no render — faster)."""
    return gym.make("CartPole-v1")


def make_eval_env(render: bool) -> gym.Env:
    """Create a separate evaluation environment."""
    render_mode = "human" if render else None
    try:
        return gym.make("CartPole-v1", render_mode=render_mode)
    except Exception:
        # Fall back silently if human rendering isn't available
        return gym.make("CartPole-v1")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()

    print("=" * 60)
    print("GAMETRAINER — M1: Borrow the Brain")
    print("Training PPO on CartPole-v1")
    print("=" * 60)
    print()

    # Show what we're doing and why
    print("Goal: replace random actions with a learning agent (PPO).")
    print(f"  M0 random baseline:  ~{M0_RANDOM_BASELINE:.0f} reward/episode")
    print(f"  M1 pass threshold:   ≥{PASS_THRESHOLD:.0f} reward/episode (2× baseline)")
    print(f"  Training steps:      {args.steps:,}")
    print()

    # Instantiate NullInput to keep module wiring visible (CartPole is programmatic)
    _hands = NullInput()
    print("NullInput controller ready (CartPole is programmatic — no real key presses).")
    print()

    # Create directories
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Build environments
    train_env = DummyVecEnv([make_train_env])
    eval_env = DummyVecEnv([lambda: make_eval_env(args.render)])

    # ------------------------------------------------------------------
    # Build the PPO agent
    # Teacher Note: "MlpPolicy" = Multi-Layer Perceptron policy.
    # CartPole observations are 4 numbers, so a small MLP network is ideal.
    # The hyperparameters below are sensible defaults for CartPole.
    # ------------------------------------------------------------------
    print("Creating PPO agent (MlpPolicy)...")
    model = PPO(
        "MlpPolicy",
        train_env,
        verbose=0,                  # 0 = quiet; set to 1 for SB3's own logging
        tensorboard_log=LOG_DIR,
        learning_rate=3e-4,         # How big each learning step is
        n_steps=2048,               # Steps collected before each update
        batch_size=64,              # Mini-batch size for the update
        n_epochs=10,                # How many passes over each batch
        gamma=0.99,                 # Discount factor (value of future rewards)
        gae_lambda=0.95,            # Bias-variance trade-off in advantage estimation
        clip_range=0.2,             # PPO's "proximal" clipping — keeps updates conservative
        ent_coef=0.0,               # Entropy bonus (0 = no extra exploration push needed)
    )
    print("[OK] PPO agent created.\n")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    # Save a checkpoint every CHECKPOINT_FREQ steps
    checkpoint_cb = CheckpointCallback(
        save_freq=CHECKPOINT_FREQ,
        save_path=MODEL_DIR,
        name_prefix="cartpole_ppo",
        verbose=0,
    )

    # Evaluate on a separate env every EVAL_FREQ steps and print mean reward
    eval_cb = EvalCallback(
        eval_env,
        n_eval_episodes=10,
        eval_freq=EVAL_FREQ,
        log_path=LOG_DIR,
        best_model_save_path=MODEL_DIR,
        verbose=1,                  # Print eval results to console
        warn=False,
    )

    # ------------------------------------------------------------------
    # Train
    # ------------------------------------------------------------------
    print(f"Starting training for {args.steps:,} timesteps...")
    print("  Watch the 'mean_reward' line in the output — it should rise over time.")
    print("  (Tip: run 'tensorboard --logdir logs/cartpole' in another terminal for a graph.)")
    print("-" * 60)

    model.learn(
        total_timesteps=args.steps,
        callback=[checkpoint_cb, eval_cb],
        progress_bar=False,         # Keep output clean; eval_cb shows per-eval progress
    )

    print("-" * 60)
    print("Training complete.")

    # Save final model
    final_path = os.path.join(MODEL_DIR, "final_model")
    model.save(final_path)
    print(f"Model saved → {final_path}.zip\n")

    # ------------------------------------------------------------------
    # M1 Verdict
    # Read the best mean reward recorded by EvalCallback
    # ------------------------------------------------------------------
    results_path = os.path.join(LOG_DIR, "evaluations.npz")
    verdict_passed = False
    best_mean_reward = 0.0

    if os.path.exists(results_path):
        data = np.load(results_path)
        # EvalCallback stores mean rewards in 'results' (shape: [n_evals, n_episodes])
        mean_rewards = data["results"].mean(axis=1)
        best_mean_reward = float(mean_rewards.max())
    else:
        # Fall back: run a quick manual evaluation
        print("Running final evaluation (10 episodes)...")
        episode_rewards = []
        for _ in range(10):
            obs = eval_env.reset()
            done = False
            ep_reward = 0.0
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, done, _ = eval_env.step(action)
                ep_reward += float(reward[0])
                done = bool(done[0])
            episode_rewards.append(ep_reward)
        best_mean_reward = float(np.mean(episode_rewards))

    verdict_passed = best_mean_reward >= PASS_THRESHOLD

    print("=" * 60)
    print("M1 VERDICT")
    print("=" * 60)
    print(f"  M0 random baseline:     ~{M0_RANDOM_BASELINE:.0f} reward/episode")
    print(f"  M1 best mean reward:     {best_mean_reward:.1f} reward/episode")
    print(f"  Pass threshold (2× M0): ≥{PASS_THRESHOLD:.0f}")
    print()

    if verdict_passed:
        print("  ✅ PASS — reward clearly rose above the random baseline!")
        print("     The borrowed brain (PPO) is working.")
    else:
        print("  ⚠️  BELOW THRESHOLD — reward didn't rise enough yet.")
        print(f"     Try running with more steps: --steps 50000")
        print("     (This can happen on short runs; it's not a bug.)")

    print("=" * 60)

    train_env.close()
    eval_env.close()

    return 0 if verdict_passed else 1


if __name__ == "__main__":
    sys.exit(main())
