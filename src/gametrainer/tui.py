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

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.text import Text


console = Console()


@dataclass(frozen=True)
class TuiConfig:
    project_name: str = "GameTrainer"
    changelog_relpath: str = "docs/CHANGELOG.md"
    train_script_relpath: str = "scripts/train.py"
    play_script_relpath: str = "scripts/play.py"


def _project_root() -> Path:
    # src/gametrainer/tui.py -> src/gametrainer -> src -> project root
    return Path(__file__).resolve().parents[2]


def _safe_read_text(path: Path, max_chars: int = 25_000) -> str:
    try:
        data = path.read_text(encoding="utf-8")
    except Exception as e:
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
    except Exception:
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


def _menu() -> Panel:
    menu = Text()
    menu.append("Choose an option:\n\n", style="bold")
    menu.append("  [1] Train (learn)\n")
    menu.append("  [2] Play (inference)\n")
    menu.append("  [3] View changelog\n")
    menu.append("  [4] Update / install deps (pip)\n")
    menu.append("  [5] Quit\n")
    return Panel(menu, title="Main Menu", border_style="magenta", padding=(1, 2))


def _run_script(relpath: str, extra_args: Optional[list[str]] = None) -> int:
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


def run_tui(cfg: Optional[TuiConfig] = None) -> int:
    cfg = cfg or TuiConfig()

    while True:
        console.clear()
        console.print(_header(cfg))
        console.print(_menu())

        choice = IntPrompt.ask("Selection", choices=["1", "2", "3", "4", "5"], default="5")

        if choice == 1:
            # Let user optionally choose ViT size without forcing it.
            size = Prompt.ask("ViT size", choices=["tiny", "small", "base"], default="small")
            freeze = Prompt.ask("Freeze backbone?", choices=["y", "n"], default="n") == "y"
            args: list[str] = [size]
            if freeze:
                args.append("--freeze")
            console.print("\nLaunching training...\n")
            return _run_script(cfg.train_script_relpath, extra_args=args)

        if choice == 2:
            console.print("\nLaunching play/inference...\n")
            return _run_script(cfg.play_script_relpath)

        if choice == 3:
            root = _project_root()
            path = (root / cfg.changelog_relpath).resolve()
            console.clear()
            console.print(_header(cfg))
            console.print(Panel(_safe_read_text(path), title=str(path.relative_to(root)), border_style="yellow"))
            Prompt.ask("\nPress Enter to return", default="")
            continue

        if choice == 4:
            console.clear()
            console.print(_header(cfg))
            console.print(Panel("Choose what to install:\n\n  [1] Core (.)\n  [2] Core + RL (.[rl])\n  [3] Back", border_style="green"))
            sub = IntPrompt.ask("Selection", choices=["1", "2", "3"], default="3")
            if sub == 1:
                code = _pip_install_editable(with_rl=False)
                Prompt.ask(f"\nDone (exit code {code}). Press Enter to return", default="")
            elif sub == 2:
                code = _pip_install_editable(with_rl=True)
                Prompt.ask(f"\nDone (exit code {code}). Press Enter to return", default="")
            continue

        return 0

