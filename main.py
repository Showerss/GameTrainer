"""
GameTrainer - Local RL Edition

This is the entry point for the GameTrainer CLI.
Use this to launch training or inference sessions.

Usage:
    python main.py         - Launch the retro TUI menu
    python main.py train   - Start training the agent
    python main.py play    - Run a trained agent
"""

import sys
import subprocess
import os

VALID_MODES = ("train", "play")


def main():
    if len(sys.argv) < 2:
        return _launch_tui()

    mode = sys.argv[1].lower().strip()

    if len(sys.argv) > 2:
        print(f"Warning: Ignoring extra arguments ({sys.argv[2:]}). Only the mode is used.")
        print("  (Pass script-specific options directly, e.g. python scripts/train.py small --steps 50000)\n")

    if mode not in VALID_MODES:
        print(f"Error: Unknown mode '{mode}'.")
        _print_usage()
        sys.exit(1)

    script = "scripts/train.py" if mode == "train" else "scripts/play.py"
    if not os.path.isfile(script):
        print(f"Error: Script not found: {script}")
        sys.exit(1)

    print(f"Launching {mode} session...")
    try:
        result = subprocess.run([sys.executable, script])
    except OSError as e:
        print(f"Error: Failed to run script: {e}")
        sys.exit(1)
    if result.returncode != 0:
        sys.exit(result.returncode)
    return 0


def _print_usage():
    """Print usage message. Kept in one place for consistency."""
    print("GameTrainer - Local Reinforcement Learning for Games")
    print("=" * 50)
    print("\nUsage:")
    print("  python main.py         - Launch retro TUI menu")
    print("  python main.py train   - Start training")
    print("  python main.py play    - Run trained agent")
    print("\nOr run scripts directly:")
    print("  python scripts/train.py")
    print("  python scripts/play.py")


def _launch_tui() -> int:
    """
    Launch the retro TUI menu.

    Kept separate so CLI usage remains unchanged for automation.
    """
    try:
        from src.gametrainer.tui import run_tui
    except Exception as e:
        print(f"[!!] Failed to launch TUI: {type(e).__name__}: {e}")
        print("\nFalling back to CLI usage.\n")
        _print_usage()
        return 1
    return int(run_tui())


if __name__ == "__main__":
    sys.exit(main())
