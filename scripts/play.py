"""
Play Script - Run a trained agent

This script loads a trained model and lets it play the game.
Use this to see how well your agent has learned!

To run:
    python scripts/play.py
"""

import os
import sys
import time

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO
from src.gametrainer.env import StardewEnv

MODEL_DIR = "models/ppo_stardew"


def main():
    # Find best model
    model_paths = [
        f"{MODEL_DIR}/final_model.zip",
        f"{MODEL_DIR}/interrupted_model.zip",
    ]

    if os.path.exists(MODEL_DIR):
        checkpoints = [f for f in os.listdir(MODEL_DIR) if f.startswith("stardew_model_") and f.endswith(".zip")]
        if checkpoints:
            checkpoints.sort(key=lambda x: int(x.split("_")[2]), reverse=True)
            model_paths.append(os.path.join(MODEL_DIR, checkpoints[0]))

    model_path = None
    for path in model_paths:
        if os.path.exists(path):
            model_path = path
            break

    if model_path is None:
        print("No trained model found!")
        print("Run 'python scripts/train.py' first to train an agent.")
        return

    print(f"Loading model: {model_path}")
    model = PPO.load(model_path)

    print("Creating environment...")
    env = StardewEnv(render_mode='human')

    print("=" * 60)
    print("PLAYING - Switch to Stardew Valley window!")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    time.sleep(3)

    obs, info = env.reset()
    total_reward = 0
    steps = 0

    try:
        while True:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1

            if steps % 100 == 0:
                print(f"Step {steps}, Total Reward: {total_reward:.2f}")

            if terminated or truncated:
                print(f"\nEpisode finished! Total reward: {total_reward:.2f}")
                obs, info = env.reset()
                total_reward = 0
                steps = 0

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        env.close()


if __name__ == "__main__":
    main()
