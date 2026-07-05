"""
GridWorld Run Script - Milestone M2, Brick 3 (the random baseline).

GridWorld is *ours* (M2), but it obeys the same Gymnasium contract as the
borrowed CartPole, so this runner looks almost identical to run_cartpole.py:
spin up the env, take random actions, and report the mean reward per episode.

That number is the *random baseline*. Random walking rarely stumbles onto the
goal of a 5x5 grid within the step cap, so expect a low / negative score.
Brick 4 (train_gridworld.py) trains PPO and must clearly beat this to pass M2.
"""

import os
import sys

# Print UTF-8 so any status glyphs don't crash on Windows consoles (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path for imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from src.gametrainer.input import NullInput
from src.gametrainer.gridworld import GridWorldEnv


def main():
    print("=" * 60)
    print("RUNNING GRIDWORLD M2 BASELINE SCRIPT (random agent)")
    print("=" * 60)

    # The "hands" of the architecture. GridWorld is programmatic (like CartPole),
    # so NullInput makes every key press a no-op — but wiring it in keeps the
    # eyes -> brain -> hands shape visible, exactly as run_cartpole.py does.
    print("Initializing NullInput controller...")
    hands = NullInput()

    print("Initializing GridWorld environment...")
    env = GridWorldEnv()

    # Map each discrete action to the movement "key" the hands would press.
    move = {
        GridWorldEnv.UP: hands.move_up,
        GridWorldEnv.DOWN: hands.move_down,
        GridWorldEnv.LEFT: hands.move_left,
        GridWorldEnv.RIGHT: hands.move_right,
    }

    episodes = 20
    episode_rewards = []
    goals_reached = 0

    print(f"\nRunning {episodes} episodes of random actions...\n")
    for ep in range(1, episodes + 1):
        obs, info = env.reset()
        ep_reward = 0.0
        terminated = truncated = False

        # Play one full episode: keep moving until we win or hit the step cap.
        while not (terminated or truncated):
            action = env.action_space.sample()
            move[action]()  # hands press a key; NullInput does nothing
            obs, reward, terminated, truncated, info = env.step(action)
            ep_reward += reward

        reached = terminated  # GridWorld only terminates by reaching the goal
        goals_reached += int(reached)
        episode_rewards.append(ep_reward)

        outcome = "GOAL" if reached else "cap "
        print(f"  Episode {ep:2d} | {outcome} | steps: {info['steps']:3d} | reward: {ep_reward:+.2f}")

    env.close()

    mean_ep_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0

    print("\n" + "=" * 60)
    print("SUCCESS: GridWorld ran without crashing!")
    print(f"Episodes completed:              {episodes}")
    print(f"Goals reached (random):          {goals_reached} / {episodes}")
    print(f"Mean reward per episode:         {mean_ep_reward:+.2f}")
    print()
    print("M2 random baseline (for Brick 4 comparison):")
    print(f"  ~{mean_ep_reward:+.2f} reward/episode with random actions")
    print("  train_gridworld.py (PPO) must clearly exceed this to pass M2.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
