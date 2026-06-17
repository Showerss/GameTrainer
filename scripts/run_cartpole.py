"""
CartPole Run Script - Milestone M0 Verification

This script verifies our local virtual environment and package installation
by initializing Gymnasium's CartPole-v1 environment, running a loop for 100 steps
with random actions, and utilizing the NullInput controller to verify modular input interfaces.
"""

import os
import sys
import gymnasium as gym

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

    print(f"\nRunning simulation for {steps} steps...")
    for step in range(1, steps + 1):
        # Sample a random action (0 or 1)
        action = env.action_space.sample()

        # In a real game environment, we would send input via our hands:
        # Since it's CartPole (programmatic), NullInput does nothing
        hands.tap_key(action)

        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward

        if step % 10 == 0 or step == 1 or step == steps:
            # Print periodic status
            obs_str = ", ".join(f"{x:+.4f}" for x in obs)
            print(f"  Step {step:3d} | Action: {action} | Reward: {reward} | Obs: [{obs_str}]")

        if terminated or truncated:
            obs, info = env.reset()

    env.close()
    print("\n" + "=" * 60)
    print("SUCCESS: CartPole ran for 100 steps without crashing!")
    print(f"Total reward accumulated: {total_reward:.1f}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
