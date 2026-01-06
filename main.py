"""
GameTrainer - Local RL Edition

This is the entry point for the GameTrainer CLI.
Use this to launch training or inference sessions.

Usage:
    python main.py train   - Start training the agent
    python main.py play    - Run a trained agent
"""

import sys
import subprocess
import os


def main():
    if len(sys.argv) < 2:
        print("GameTrainer - Local Reinforcement Learning for Games")
        print("=" * 50)
        print("\nUsage:")
        print("  python main.py train   - Start training")
        print("  python main.py play    - Run trained agent")
        print("\nOr run scripts directly:")
        print("  python scripts/train.py")
        print("  python scripts/play.py")
        return

    mode = sys.argv[1].lower()

    if mode == "train":
        print("Launching training session...")
        subprocess.run([sys.executable, "scripts/train.py"])
    elif mode == "play":
        print("Launching play session...")
        subprocess.run([sys.executable, "scripts/play.py"])
    else:
        print(f"Unknown mode: {mode}")
        print("Use 'train' or 'play'")


if __name__ == "__main__":
    main()
