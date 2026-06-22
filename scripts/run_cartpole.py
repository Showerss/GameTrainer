"""
CartPole Run Script - Milestone M0 Verification

This script verifies our local virtual environment and package installation
by initializing Gymnasium's CartPole-v1 environment, running a loop for 100 steps
with random actions, and utilizing the NullInput controller to verify modular input interfaces.

Baseline note (for M1):
    The mean reward per episode printed at the end is the *random-action baseline*.
    M1 (train_cartpole.py) must beat this number to confirm PPO is learning.
"""

import os
import sys
import gymnasium as gym

# Print UTF-8 so any status glyphs don't crash on Windows consoles (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path for imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from src.gametrainer.input import NullInput


def main():
    print("=" * 60)
    print("RUNNING CARTPOLE M0 VERIFICATION SCRIPT")
    print("=" * 60)

    # Instantiate NullInput as defined in architecture
    print("Initializing NullInput controller...")
    hands = NullInput()

    print("Initializing Gymnasium CartPole-v1 environment...")
    try:
        # Try human render mode first
        env = gym.make("CartPole-v1", render_mode="human")
        print("  [OK] Initialized with human rendering.")
    except Exception as e:
        print(f"  [!] Human rendering not available ({e}). Falling back to no-render mode.")
        env = gym.make("CartPole-v1")

    obs, info = env.reset()
    print(f"Initial Observation: {obs}")

    total_reward = 0.0
    steps = 100

    # Track per-episode rewards so we can report a mean at the end.
    # Each episode starts fresh after the pole falls (terminated/truncated).
    episode_rewards = []
    current_episode_reward = 0.0

    print(f"\nRunning simulation for {steps} steps...")
    for step in range(1, steps + 1):
        # Sample a random action (0 or 1)
        action = env.action_space.sample()

        # In a real game environment, we would send input via our hands:
        # Since it's CartPole (programmatic), NullInput does nothing
        hands.tap_key(action)

        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        current_episode_reward += reward

        if step % 10 == 0 or step == 1 or step == steps:
            # Print periodic status
            obs_str = ", ".join(f"{x:+.4f}" for x in obs)
            print(f"  Step {step:3d} | Action: {action} | Reward: {reward} | Obs: [{obs_str}]")

        if terminated or truncated:
            episode_rewards.append(current_episode_reward)
            current_episode_reward = 0.0
            obs, info = env.reset()

    # Count the final partial episode if it didn't terminate in time
    if current_episode_reward > 0:
        episode_rewards.append(current_episode_reward)

    env.close()

    mean_ep_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0

    print("\n" + "=" * 60)
    print("SUCCESS: CartPole ran for 100 steps without crashing!")
    print(f"Total reward accumulated:        {total_reward:.1f}")
    print(f"Episodes completed:              {len(episode_rewards)}")
    print(f"Mean reward per episode:         {mean_ep_reward:.1f}")
    print()
    print("M0 random baseline (for M1 comparison):")
    print(f"  ~{mean_ep_reward:.0f} reward/episode with random actions")
    print("  M1 (train_cartpole.py) must clearly exceed this to pass.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
