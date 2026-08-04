"""
GameTrainer - Local RL Edition

This is the entry point for the GameTrainer CLI.

Usage:
    python main.py         - Launch the retro TUI menu

The old `train`/`play` mode shortcuts are retired along with Track B (the
Stardew-first prototype) — there is no single Track A script yet that trains
or plays *any* profile (that lands with M4 Brick 5, scripts/train_from_profile.py).
Use the TUI, or run a milestone script directly (see below).
"""

import sys

VALID_MODES = ("train", "play")


def main():
    if len(sys.argv) < 2:
        return _launch_tui()

    mode = sys.argv[1].lower().strip()

    if mode not in VALID_MODES:
        print(f"Error: Unknown mode '{mode}'.")
        _print_usage()
        sys.exit(1)

    print(f"'{mode}' isn't available yet — Track B (its old implementation) was retired.")
    _print_usage()
    sys.exit(1)


def _print_usage():
    """Print usage message. Kept in one place for consistency."""
    print("GameTrainer - Local Reinforcement Learning for Games")
    print("=" * 50)
    print("\nUsage:")
    print("  python main.py          - Launch retro TUI menu")
    print("\nOr run a milestone script directly:")
    print("  python scripts/run_cartpole.py         # M0: random actions baseline")
    print("  python scripts/train_cartpole.py       # M1: PPO on CartPole")
    print("  python scripts/run_gridworld.py        # M2: random actions baseline")
    print("  python scripts/train_gridworld.py      # M2: PPO on GridWorld")
    print("  python scripts/train_gridworld_vit.py  # M3: PPO on GridWorld pixels")


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
