"""
Retro-ish TUI launcher for GameTrainer.

This is intentionally lightweight: it does not try to be a full-screen app.
It provides a clean menu for humans to:
- see version/author
- view changelog
- start training
- start play/inference
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.text import Text

console = Console()


@dataclass(frozen=True)
class TuiConfig:
    project_name: str = "GameTrainer"
    changelog_relpath: str = "docs/CHANGELOG.md"


def _project_root() -> Path:
    # src/gametrainer/tui.py -> src/gametrainer -> src -> project root
    return Path(__file__).resolve().parents[2]


def _safe_read_text(path: Path, max_chars: int = 25_000) -> str:
    try:
        data = path.read_text(encoding="utf-8")
    except OSError as e:
        return f"[Could not read {path}: {type(e).__name__}: {e}]"
    if len(data) > max_chars:
        return data[:max_chars] + "\n\n[... truncated ...]\n"
    return data


def _get_meta() -> tuple[str, str]:
    """
    Best-effort: read __version__/__author__ from package.
    """
    try:
        from src.gametrainer import __author__, __version__
        return str(__version__), str(__author__)
    except (ImportError, AttributeError):
        return "unknown", "unknown"


def _header(cfg: TuiConfig) -> Panel:
    version, author = _get_meta()
    art = Text()
    art.append("╔══════════════════════════════════════════════════════╗\n", style="bold cyan")
    art.append("║", style="bold cyan")
    art.append(f" {cfg.project_name:<52}", style="bold white")
    art.append("║\n", style="bold cyan")
    art.append("║", style="bold cyan")
    art.append(f" Version: {version:<42}", style="white")
    art.append("║\n", style="bold cyan")
    art.append("║", style="bold cyan")
    art.append(f" Authored by: {author:<38}", style="white")
    art.append("║\n", style="bold cyan")
    art.append("╚══════════════════════════════════════════════════════╝", style="bold cyan")
    return Panel(art, border_style="cyan", padding=(1, 2))


def _run_script(relpath: str, extra_args: list[str] | None = None) -> int:
    root = _project_root()
    script_path = (root / relpath).resolve()
    if not script_path.is_file():
        console.print(f"[bold red]Error:[/bold red] Script not found: {script_path}")
        return 1

    argv = [sys.executable, str(script_path)]
    if extra_args:
        argv.extend(extra_args)

    # Run in project root so relative paths inside scripts behave.
    return subprocess.call(argv, cwd=str(root))


def _pip_install_editable(with_rl: bool) -> int:
    root = _project_root()
    pkg = ".[rl]" if with_rl else "."
    console.print(f"\nInstalling editable package: [bold]{pkg}[/bold]\n")
    return subprocess.call([sys.executable, "-m", "pip", "install", "-e", pkg], cwd=str(root))


# ---------------------------------------------------------------------------
# Screens: menu options that open something instead of launching a script.
# Each returns an exit code to leave the TUI, or None to go back to the menu.
# ---------------------------------------------------------------------------

# M4: the shipped profiles, as (label, path). The submenu is built from this.
PROFILES = [
    ("CartPole (cartpole.yaml)", "profiles/cartpole.yaml"),
    ("GridWorld flat (gridworld.yaml)", "profiles/gridworld.yaml"),
    ("GridWorld pixels (gridworld_pixels.yaml)", "profiles/gridworld_pixels.yaml"),
    ("Minesweeper (minesweeper.yaml)", "profiles/minesweeper.yaml"),
]


def _numbered(labels: list[str]) -> str:
    """One '  [N] label' line per label. N is the position, so it can't drift."""
    return "\n".join(f"  [{number}] {label}" for number, label in enumerate(labels, start=1))


def _profile_screen(cfg: TuiConfig) -> int | None:
    # M4: pick a shipped profile, then hand off to train_from_profile.py --profile <path>.
    console.clear()
    console.print(_header(cfg))
    labels = [label for label, _path in PROFILES] + ["Back"]
    console.print(Panel(
        "Choose a profile:\n\n" + _numbered(labels),
        title="Train from Profile",
        border_style="magenta",
    ))
    choices = [str(n) for n in range(1, len(labels) + 1)]
    sub = IntPrompt.ask("Selection", choices=choices, default=choices[-1])
    if sub > len(PROFILES):
        return None
    path = PROFILES[sub - 1][1]
    console.print(f"\nLaunching train_from_profile.py --profile {path} …\n")
    return _run_script("scripts/train_from_profile.py", ["--profile", path])


def _changelog_screen(cfg: TuiConfig) -> None:
    root = _project_root()
    path = (root / cfg.changelog_relpath).resolve()
    console.clear()
    console.print(_header(cfg))
    console.print(Panel(_safe_read_text(path), title=str(path.relative_to(root)), border_style="yellow"))
    Prompt.ask("\nPress Enter to return", default="")


def _pip_screen(cfg: TuiConfig) -> None:
    console.clear()
    console.print(_header(cfg))
    console.print(Panel("Choose what to install:\n\n  [1] Core (.)\n  [2] Core + RL (.[rl])\n  [3] Back", border_style="green"))
    sub = IntPrompt.ask("Selection", choices=["1", "2", "3"], default="3")
    if sub in (1, 2):
        code = _pip_install_editable(with_rl=(sub == 2))
        Prompt.ask(f"\nDone (exit code {code}). Press Enter to return", default="")


def _quit_screen(_cfg: TuiConfig) -> int:
    return 0


# ---------------------------------------------------------------------------
# The main menu: one row per option, in the order shown.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MenuItem:
    """One main-menu option. Set `script` to launch a script, or `screen` to open one."""

    label: str
    script: str | None = None   # launch this script (relative to the project root)
    message: str = ""           # printed just before the script starts
    note: str | None = None     # optional dim line under the message
    screen: Callable[[TuiConfig], int | None] | None = None


MENU_ITEMS = [
    # M0: prove the Gymnasium link with random actions. No training, no ViT.
    MenuItem("Verify setup - CartPole, random actions (M0)", "scripts/run_cartpole.py",
             "Launching CartPole setup check (random actions)..."),
    # M1: train the borrowed PPO brain on CartPole.
    MenuItem("Train CartPole - borrowed PPO brain (M1)", "scripts/train_cartpole.py",
             "Launching CartPole training (PPO)..."),
    # M2: the random baseline on our own home-built Ground (GridWorld).
    MenuItem("Run GridWorld - random actions, baseline (M2)", "scripts/run_gridworld.py",
             "Launching GridWorld baseline (random actions)..."),
    # M2: train the borrowed PPO brain on GridWorld — must beat the baseline.
    MenuItem("Train GridWorld - borrowed PPO brain (M2)", "scripts/train_gridworld.py",
             "Launching GridWorld training (PPO)..."),
    # M3: the same GridWorld, but the agent sees only a picture of it, read
    # through a frozen ViT. Slow on CPU — say so before it starts.
    MenuItem("Train GridWorld with ViT eyes - pixels only (M3)", "scripts/train_gridworld_vit.py",
             "Launching GridWorld pixel training (PPO + frozen ViT-Tiny)...",
             note="This takes ~20 min on CPU. It prints a PASS/FAIL verdict at the end."),
    # M4: profile-driven training for any shipped profile.
    MenuItem("Train from profile - CartPole / GridWorld / GridWorld-pixels (M4)",
             screen=_profile_screen),
    # M5: check live desktop hands on LibreMines (Windows/macOS).
    MenuItem("Verify live desktop hands - LibreMines (M5)", "scripts/check_hands.py",
             "Launching live desktop hands check (LibreMines)...",
             note="Requires LibreMines running on your desktop."),
    MenuItem("View changelog", screen=_changelog_screen),
    MenuItem("Update / install deps (pip)", screen=_pip_screen),
    MenuItem("Quit", screen=_quit_screen),
]


def _menu() -> Panel:
    menu = Text()
    menu.append("Choose an option:\n\n", style="bold")
    menu.append(_numbered([item.label for item in MENU_ITEMS]) + "\n")
    return Panel(menu, title="Main Menu", border_style="magenta", padding=(1, 2))


def run_tui(cfg: TuiConfig | None = None) -> int:
    cfg = cfg or TuiConfig()
    choices = [str(n) for n in range(1, len(MENU_ITEMS) + 1)]

    while True:
        console.clear()
        console.print(_header(cfg))
        console.print(_menu())

        choice = IntPrompt.ask("Selection", choices=choices, default=choices[-1])
        item = MENU_ITEMS[choice - 1]

        if item.script is not None:
            console.print(f"\n{item.message}\n")
            if item.note:
                console.print(f"[dim]{item.note}[/dim]\n")
            return _run_script(item.script)

        exit_code = item.screen(cfg)
        if exit_code is not None:
            return exit_code
