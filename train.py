"""
Training Script for Stardew Valley RL Agent

This script initializes the environment and starts the training loop
using the PPO (Proximal Policy Optimization) algorithm.

To run:
    python train.py
"""

import os
import time
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback

from src.python.core.rl.env import StardewEnv
from src.python.core.dependencies import ensure_dependencies, check_progress_bar_available

# Configuration
TOTAL_TIMESTEPS = 100_000
CHECKPOINT_FREQ = 10_000
MODEL_DIR = "models/ppo_stardew"
LOG_DIR = "logs"


class ActionLoggingCallback(BaseCallback):
    """
    Callback to log action distribution and verify agent is exploring.
    Time complexity: O(1) per step, O(n) for logging where n is number of action types.

    Following clean code principles: Single Responsibility - handles action logging only.
    """
    # All 11 action names
    ACTION_NAMES = [
        "NO-OP", "UP(W)", "DOWN(S)", "LEFT(A)", "RIGHT(D)",
        "LEFT_CLICK", "RIGHT_CLICK",
        "MOUSE_UP", "MOUSE_DOWN", "MOUSE_LEFT", "MOUSE_RIGHT"
    ]

    def __init__(self, log_freq: int = 1000, verbose: int = 1):
        super().__init__(verbose)
        self.log_freq = log_freq
        self.action_counts = np.zeros(len(self.ACTION_NAMES))

    def _on_step(self) -> bool:
        # Track action distribution from locals
        actions = self.locals.get("actions")
        if actions is not None:
            if isinstance(actions, np.ndarray):
                if actions.ndim == 0:
                    action = int(actions.item())
                    self.action_counts[action] += 1
                else:
                    for action in actions.flatten():
                        self.action_counts[int(action)] += 1

        # Log every log_freq steps
        if self.n_calls % self.log_freq == 0:
            total = self.action_counts.sum()
            if total > 0:
                percentages = (self.action_counts / total * 100).round(1)
                print(f"\n[Step {self.n_calls}] Action distribution (last {int(total)} actions):")
                for name, count, pct in zip(self.ACTION_NAMES, self.action_counts, percentages):
                    if count > 0:
                        print(f"  {name}: {int(count)} ({pct}%)")
                print(f"  Total actions logged: {int(total)}\n")
            else:
                print(f"\n[Step {self.n_calls}] WARNING: No actions logged yet!\n")

        return True


def main():
    # 0. Ensure optional dependencies are installed
    ensure_dependencies()
    
    # Check if progress bar is available after potential installation
    progress_bar_available = check_progress_bar_available()
    
    # 1. Create Directories
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # 2. Initialize Environment
    # We wrap it in a DummyVecEnv for stable-baselines3 compatibility
    print("Initializing environment...")
    
    # Verify C++ extension is working before training
    try:
        import src.python.core.clib as clib
        print("  ✓ C++ input extension loaded successfully")
    except ImportError:
        print("  ✗ WARNING: C++ input extension not found!")
        print("     Actions will NOT be sent to the game!")
        print("     Run 'python setup.py build_ext --inplace' to build the extension.")
        response = input("     Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    
    env = DummyVecEnv([lambda: StardewEnv(render_mode='rgb_array')])

    # 3. Initialize Agent (or load existing checkpoint)
    # Teacher Note: RL training can take hours/days. We MUST save and resume
    # from checkpoints, otherwise all learning is lost when you stop training!
    model = None

    # Check for existing models (prioritize final > interrupted > latest checkpoint)
    model_paths = [
        f"{MODEL_DIR}/final_model.zip",
        f"{MODEL_DIR}/interrupted_model.zip",
    ]

    # Also check for numbered checkpoints (e.g., stardew_model_10000_steps.zip)
    if os.path.exists(MODEL_DIR):
        checkpoints = [f for f in os.listdir(MODEL_DIR) if f.startswith("stardew_model_") and f.endswith(".zip")]
        if checkpoints:
            # Sort by step number (extract from filename)
            checkpoints.sort(key=lambda x: int(x.split("_")[2]), reverse=True)
            model_paths.append(os.path.join(MODEL_DIR, checkpoints[0]))

    # Try to load existing model
    for path in model_paths:
        if os.path.exists(path):
            print(f"Found existing model: {path}")
            print("  Loading and resuming training...")
            model = PPO.load(
                path,
                env=env,
                device="auto",
                tensorboard_log=LOG_DIR,
            )
            print(f"  ✓ Model loaded successfully! Resuming from checkpoint.")
            break

    # If no model found, create new one
    if model is None:
        print("No existing model found. Creating new PPO agent...")
        print("  Adding exploration (ent_coef=0.01) to encourage action diversity...")
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
            ent_coef=0.01,  # Entropy coefficient - encourages exploration
        )

    # 4. Setup Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=CHECKPOINT_FREQ,
        save_path=MODEL_DIR,
        name_prefix="stardew_model"
    )
    
    # Action logging callback to monitor what the agent is doing
    action_logger = ActionLoggingCallback(log_freq=1000)

    # 5. Start Training
    print(f"Starting training for {TOTAL_TIMESTEPS} timesteps...")
    print("Switch to the Stardew Valley window NOW!")
    time.sleep(5)  # Give user time to switch windows

    try:
        # Use progress bar if dependencies are available (auto-installed if missing)
        # Following clean code: using callback list to combine multiple callbacks
        from stable_baselines3.common.callbacks import CallbackList
        callback_list = CallbackList([checkpoint_callback, action_logger])
        
        model.learn(
            total_timesteps=TOTAL_TIMESTEPS,
            callback=callback_list,
            progress_bar=progress_bar_available
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
