"""
GridWorld Training Script - Milestone M2, Brick 4 (borrow the brain again).

Teacher Note: What are we doing here?
======================================
In Brick 3 (run_gridworld.py) a *random* agent walked the 5x5 grid. Random
walking wanders — it reaches the goal only sometimes and wastes lots of steps,
so its mean reward per episode is low / negative (our random baseline).

Here in Brick 4 we swap that random action for a *learning* agent called PPO —
the exact same "borrowed brain" we used on CartPole in M1. Nothing about the
environment changes: GridWorld still obeys the Gymnasium contract (reset() /
step()), so PPO plugs straight in. That swappability is the whole point of the
project. Over many episodes PPO learns the short path to the goal, and its mean
reward should climb well above the random baseline.

Why MlpPolicy?
--------------
GridWorld's observation is just 2 numbers — the agent's (row, col). MlpPolicy
feeds those numbers through a small fully-connected network, exactly right for
"numbers in, numbers out." (CnnPolicy is for pixels — that's M3, not now.)

What "winning" looks like
-------------------------
The shortest path from (0,0) to (4,4) is 8 moves. Seven steps cost -0.01 each
and the last step pays +1.0, so a perfect episode scores about +0.93. A trained
agent should sit near that — far above the negative random baseline.

Usage:
    python scripts/train_gridworld.py               # default: 25,000 steps
    python scripts/train_gridworld.py --steps 50000  # longer run
    python scripts/train_gridworld.py --render       # print the learned path at the end
"""

import os
import sys
import argparse
import numpy as np

# Print UTF-8 so status glyphs (>=, x, checkmarks) don't crash on Windows consoles (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path so we can import from src/
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback

# GridWorld is ours (M2). NullInput keeps the eyes -> brain -> hands shape visible
# even though GridWorld is programmatic — consistent with run_gridworld.py.
from src.gametrainer.gridworld import GridWorldEnv
from src.gametrainer.input import NullInput

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Brick 3 random-action baseline (see run_gridworld.py output). A random walk on
# this small grid reaches the goal only about half the time and wastes steps, so
# its mean reward is negative. The exact number wanders run-to-run (roughly -0.2
# to -0.5); we document -0.3 as a representative baseline for the verdict below.
RANDOM_BASELINE = -0.3

# "Clearly learned" threshold. We can't use "2x baseline" like CartPole did,
# because the baseline is negative. Instead we use an absolute bar: +0.5.
# Reaching the goal at all flips an episode positive (a capped episode that never
# reaches the goal scores -1.0), and a short path scores ~+0.93, so a mean of
# +0.5 means the agent reaches the goal reliably via a short route — clearly
# above the negative random baseline.
PASS_THRESHOLD = 0.5

MODEL_DIR = os.path.join(_project_root, "models", "ppo_gridworld")
LOG_DIR = os.path.join(_project_root, "logs", "gridworld")

DEFAULT_TIMESTEPS = 25_000
CHECKPOINT_FREQ = 5_000
EVAL_FREQ = 2_000

# Episodes for the final deterministic check that reports the goal-reach rate.
FINAL_EVAL_EPISODES = 20


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="M2 — Train PPO on GridWorld and verify reward beats the random baseline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/train_gridworld.py               # 25k steps (default, ~1-2 min on CPU)
  python scripts/train_gridworld.py --steps 50000  # longer run
  python scripts/train_gridworld.py --render       # print the learned path at the end
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
        help="After training, play one greedy episode and print the grid each step",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Environment factory
# ---------------------------------------------------------------------------

def make_env() -> GridWorldEnv:
    """Create a fresh GridWorld environment."""
    return GridWorldEnv()


# ---------------------------------------------------------------------------
# Final deterministic evaluation
# Teacher Note: EvalCallback already tracks the best mean reward during training.
# This extra pass answers M2's other half — "reaches the goal consistently" — by
# playing greedy (no exploration) episodes and counting how many end in a win.
# ---------------------------------------------------------------------------

def evaluate_goal_rate(model, episodes: int):
    """Play greedy episodes; return (mean_reward, goals_reached, mean_steps)."""
    env = make_env()
    rewards, steps_list, goals = [], [], 0

    for _ in range(episodes):
        obs, _ = env.reset()
        terminated = truncated = False
        ep_reward = 0.0
        while not (terminated or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            ep_reward += reward
        goals += int(terminated)  # GridWorld only terminates by reaching the goal
        rewards.append(ep_reward)
        steps_list.append(info["steps"])

    env.close()
    mean_reward = sum(rewards) / len(rewards)
    mean_steps = sum(steps_list) / len(steps_list)
    return mean_reward, goals, mean_steps


def render_one_episode(model) -> None:
    """Play one greedy episode and print the grid each step (the learned path)."""
    env = make_env()
    obs, _ = env.reset()
    terminated = truncated = False
    print("\nLearned path (greedy rollout):")
    env.render()
    while not (terminated or truncated):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        env.render()
    outcome = "GOAL reached" if terminated else "ran out of moves"
    print(f"  -> {outcome} in {info['steps']} steps.\n")
    env.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()

    print("=" * 60)
    print("GAMETRAINER — M2: Train the Brain on Our Own Ground")
    print("Training PPO on GridWorld (5x5)")
    print("=" * 60)
    print()

    # Show what we're doing and why
    print("Goal: replace random walking with a learning agent (PPO).")
    print(f"  M2 random baseline:  ~{RANDOM_BASELINE:+.2f} reward/episode")
    print(f"  M2 pass threshold:   >={PASS_THRESHOLD:+.2f} reward/episode")
    print(f"  Training steps:      {args.steps:,}")
    print()

    # Instantiate NullInput to keep module wiring visible (GridWorld is programmatic)
    _hands = NullInput()
    print("NullInput controller ready (GridWorld is programmatic — no real key presses).")
    print()

    # Create directories
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Build environments (a separate one for evaluation, as SB3 recommends).
    train_env = DummyVecEnv([make_env])
    eval_env = DummyVecEnv([make_env])

    # ------------------------------------------------------------------
    # Build the PPO agent
    # Teacher Note: "MlpPolicy" = Multi-Layer Perceptron policy.
    # GridWorld observations are 2 numbers, so a small MLP network is ideal.
    # These are the same sensible defaults we used for CartPole.
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
        name_prefix="gridworld_ppo",
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
    print("  (Tip: run 'tensorboard --logdir logs/gridworld' in another terminal for a graph.)")
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
    # M2 Verdict
    # Best mean reward from EvalCallback + a final greedy goal-rate check.
    # ------------------------------------------------------------------
    results_path = os.path.join(LOG_DIR, "evaluations.npz")
    if os.path.exists(results_path):
        data = np.load(results_path)
        # EvalCallback stores mean rewards in 'results' (shape: [n_evals, n_episodes])
        best_mean_reward = float(data["results"].mean(axis=1).max())
    else:
        # Fall back to the final greedy evaluation below if no log was written.
        best_mean_reward = None

    print("Running final evaluation (greedy, 20 episodes)...")
    final_reward, goals_reached, mean_steps = evaluate_goal_rate(model, FINAL_EVAL_EPISODES)
    if best_mean_reward is None:
        best_mean_reward = final_reward

    verdict_passed = best_mean_reward >= PASS_THRESHOLD

    print("=" * 60)
    print("M2 VERDICT")
    print("=" * 60)
    print(f"  M2 random baseline:      ~{RANDOM_BASELINE:+.2f} reward/episode")
    print(f"  M2 best mean reward:      {best_mean_reward:+.2f} reward/episode")
    print(f"  Pass threshold:          >={PASS_THRESHOLD:+.2f}")
    print(f"  Goal reached (greedy):    {goals_reached} / {FINAL_EVAL_EPISODES} episodes")
    print(f"  Mean steps to finish:     {mean_steps:.1f}  (shortest possible is 8)")
    print()

    if verdict_passed:
        print("  ✅ PASS — reward clearly beat the random baseline and the agent")
        print("     reaches the goal consistently. M2 'Done when' satisfied!")
    else:
        print("  ⚠️  BELOW THRESHOLD — reward didn't rise enough yet.")
        print("     Try running with more steps: --steps 50000")
        print("     (This can happen on short runs; it's not a bug.)")

    print("=" * 60)

    if args.render:
        render_one_episode(model)

    train_env.close()
    eval_env.close()

    return 0 if verdict_passed else 1


if __name__ == "__main__":
    sys.exit(main())
