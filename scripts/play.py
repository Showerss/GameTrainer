"""
Play Script - Run a trained ViT agent

This script loads a trained model and lets it play the game.
Use this to see how well your agent has learned!

To run:
    python scripts/play.py

Teacher Note: Inference vs Training
===================================
During training, the agent explores (tries random actions to learn).
During inference (playing), we use deterministic=True to always pick
the action the model thinks is best.
"""

import os
import sys
import time

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO
from src.gametrainer.env_vit import StardewViTEnv

# Check both model directories (old CNN and new ViT)
MODEL_DIRS = [
    "models/ppo_stardew_vit",  # New ViT models (preferred)
    "models/ppo_stardew",       # Old CNN models (fallback)
]


def main():
    # Find best model across all directories
    model_path = None

    for model_dir in MODEL_DIRS:
        if not os.path.exists(model_dir):
            continue

        # Check for models in order of preference
        candidates = [
            f"{model_dir}/final_model.zip",
            f"{model_dir}/interrupted_model.zip",
        ]

        # Add numbered checkpoints
        checkpoints = [f for f in os.listdir(model_dir)
                      if f.endswith(".zip") and "model" in f.lower()]
        if checkpoints:
            checkpoints.sort(reverse=True)  # Most recent first
            for cp in checkpoints:
                candidates.append(os.path.join(model_dir, cp))

        for path in candidates:
            if os.path.exists(path):
                model_path = path
                break

        if model_path:
            break

    if model_path is None:
        print("No trained model found!")
        print("Run 'python scripts/train.py' first to train an agent.")
        return

    print(f"Loading model: {model_path}")

    try:
        model = PPO.load(model_path)
        print("  [OK] Model loaded successfully")
    except Exception as e:
        print(f"  [!!] Failed to load model: {e}")
        return

    print("\nCreating environment...")
    env = StardewViTEnv(render_mode='human')

    print("\n" + "=" * 60)
    print("PLAYING - Switch to Stardew Valley window!")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    time.sleep(3)

    obs, info = env.reset()
    total_reward = 0
    steps = 0
    episodes = 0

    try:
        while True:
            # Get action from model (deterministic = always best action)
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)

            total_reward += reward
            steps += 1

            # Log progress
            if steps % 100 == 0:
                print(f"Step {steps:5d} | Episode Reward: {total_reward:+.2f}")

            # Episode ended
            if terminated or truncated:
                episodes += 1
                print(f"\n[Episode {episodes}] Finished!")
                print(f"  Steps: {steps}")
                print(f"  Total Reward: {total_reward:.2f}")
                print()

                obs, info = env.reset()
                total_reward = 0
                steps = 0

    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        print(f"Final stats: {episodes} episodes, {steps} steps in current episode")

    finally:
        env.close()


if __name__ == "__main__":
    main()
