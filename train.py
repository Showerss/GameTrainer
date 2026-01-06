"""
Training Script for Stardew Valley RL Agent

This script initializes the environment and starts the training loop
using the PPO (Proximal Policy Optimization) algorithm.

To run:
    python train.py
"""

import os
import time
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

from src.python.core.rl.env import StardewEnv

# Configuration
TOTAL_TIMESTEPS = 100_000
CHECKPOINT_FREQ = 10_000
MODEL_DIR = "models/ppo_stardew"
LOG_DIR = "logs"

def main():
    # 1. Create Directories
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # 2. Initialize Environment
    # We wrap it in a DummyVecEnv for stable-baselines3 compatibility
    print("Initializing environment...")
    env = DummyVecEnv([lambda: StardewEnv(render_mode='rgb_array')])

    # 3. Initialize Agent
    # We use CnnPolicy because our observation is an image (pixels)
    print("Initializing PPO agent...")
    model = PPO(
        "CnnPolicy",
        env,
        verbose=1,
        tensorboard_log=LOG_DIR,
        device="auto",  # Will use GPU if available (CUDA/ROCm)
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
    )

    # 4. Setup Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=CHECKPOINT_FREQ,
        save_path=MODEL_DIR,
        name_prefix="stardew_model"
    )

    # 5. Start Training
    print(f"Starting training for {TOTAL_TIMESTEPS} timesteps...")
    print("Switch to the Stardew Valley window NOW!")
    time.sleep(5)  # Give user time to switch windows

    try:
        model.learn(
            total_timesteps=TOTAL_TIMESTEPS,
            callback=checkpoint_callback,
            progress_bar=True
        )
        print("Training complete!")
        
        # Save final model
        model.save(f"{MODEL_DIR}/final_model")
        
    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving current model...")
        model.save(f"{MODEL_DIR}/interrupted_model")

finally:
    env.close()

if __name__ == "__main__":
    main()
