"""
GameTrainer - Local RL Edition

This is the entry point for the GameTrainer CLI.

Usage:
    python main.py         - Launch the retro TUI menu

The old `train`/`play` mode shortcuts are retired along with Track B (the
Stardew-first prototype). Profile-driven training is available directly through
`scripts/train_from_profile.py`; play/inference is not wired yet. Use the TUI or
run a milestone script directly (see below).
"""

import importlib.util
from pathlib import Path
import subprocess
import sys

VALID_MODES = ("train", "play")


def _check_missing_dependencies() -> list[tuple[str, str]]:
    """
    Check for core dependencies using standard library only.

    Returns a list of (module_name, package_name) pairs that are missing.
    """
    checks = [
        ("rich", "rich"),
        ("cv2", "opencv-python"),
        ("mss", "mss"),
        ("numpy", "numpy"),
        ("pydantic", "pydantic"),
        ("yaml", "pyyaml"),
        ("pynput", "pynput"),
        ("typing_extensions", "typing-extensions>=4.7"),
    ]
    if sys.platform == "darwin":
        checks.extend([
            ("Quartz", "pyobjc-framework-Quartz"),
            ("Cocoa", "pyobjc-framework-Cocoa"),
        ])

    missing = []
    for mod_name, pkg_name in checks:
        if importlib.util.find_spec(mod_name) is None:
            missing.append((mod_name, pkg_name))
    return missing


def _ensure_dependencies() -> bool:
    """
    Verify core dependencies are installed before launching.

    If any are missing, prompts the user to install them interactively.
    Returns True if dependencies are satisfied, False otherwise.
    """
    missing = _check_missing_dependencies()
    if not missing:
        return True

    print("\n" + "=" * 50)
    print("GameTrainer - Missing Dependencies Detected")
    print("=" * 50)
    print("The following required dependencies are not installed in this environment:\n")
    for mod_name, pkg_name in missing:
        print(f"  • {pkg_name} (module: {mod_name})")

    # If running non-interactively (e.g. CI script or piped input), do not block
    if not sys.stdin.isatty():
        print("\nPlease run: pip install -e .")
        return False

    print("\nHow would you like to proceed?")
    print("  [1] Install Core dependencies (pip install -e .)")
    print("  [2] Install Core + RL dependencies (pip install -e \".[rl]\")")
    print("  [3] Exit")

    choice = input("\nSelection [1-3] (default: 1): ").strip()
    if choice in ("", "1"):
        target = "."
    elif choice == "2":
        target = ".[rl]"
    else:
        print("\nExiting. You can install dependencies manually at any time:")
        print("  pip install -e .\n")
        return False

    root = Path(__file__).resolve().parent
    cmd = [sys.executable, "-m", "pip", "install", "-e", target]
    print(f"\nRunning: {' '.join(cmd)}\n")
    ret = subprocess.call(cmd, cwd=str(root))
    if ret != 0:
        print(f"\n[!!] Installation exited with code {ret}.")
        return False

    print("\nDependencies installed successfully!\n")
    return True


def main():
    if not _ensure_dependencies():
        return 1

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
    print("  python scripts/train_from_profile.py   # M4: train from YAML profile")
    print("  python scripts/check_hands.py          # M5: verify live desktop hands")


def _launch_tui() -> int:
    """
    Launch the retro TUI menu.

    Kept separate so CLI usage remains unchanged for automation.
    """
    try:
        from src.gametrainer.tui import run_tui
    except ImportError as e:
        print(f"[!!] Failed to launch TUI: {type(e).__name__}: {e}")
        print("\nFalling back to CLI usage.\n")
        _print_usage()
        return 1
    return int(run_tui())


if __name__ == "__main__":
    sys.exit(main())
