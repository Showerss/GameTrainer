# `rich` not installed — the TUI can't launch

**Found:** 2026-06-22 (while fixing M1 review issue #3)
**Severity:** 🟡 Onboarding blocker for the TUI. Does **not** affect M0/M1 CartPole scripts.
**Status:** Not fixed. Logged for you to tackle later.

---

## One-line summary

`python main.py` can't draw its menu because the library that draws it — **`rich`** —
isn't installed in the venv, and isn't declared as a dependency anywhere in `setup.py`.

> **`rich`** = a Python library for pretty terminal output (colored panels, boxes,
> prompts). The TUI menu is built entirely on it.

---

## What happens right now

Run `python main.py` and you don't get the retro menu. Instead `main.py` catches the
failed import and falls back to plain CLI help text:

```
[!!] Failed to launch TUI: ModuleNotFoundError: No module named 'rich'

Falling back to CLI usage.
```

The exact error, if you import the TUI directly:

```
ModuleNotFoundError: No module named 'rich'
  File "src/gametrainer/tui.py", line 21, in <module>
    from rich.console import Console
```

So it fails *silently-ish*: the program doesn't crash (there's a `try/except` in
`main.py` → `_launch_tui()`), it just quietly drops you to the text fallback. Easy to
miss that the menu is supposed to exist at all.

---

## The evidence (two facts)

1. **`tui.py` hard-depends on `rich`.** Top of `src/gametrainer/tui.py`:
   ```python
   from rich.console import Console
   from rich.panel import Panel
   from rich.prompt import IntPrompt, Prompt
   from rich.text import Text
   ```
   These run at import time, so the whole module fails if `rich` is absent.

2. **`rich` is declared nowhere.** In `setup.py`:
   - `install_requires`: `opencv-python, mss, numpy, pydantic, pyyaml, pynput` — no `rich`.
   - `extras_require`: `dev` (pytest/black/mypy), `ai` (anthropic), `rl` (gymnasium/sb3/torch/…) — no `rich`.

   So no `pip install` command in the README ever pulls it in. It only works on a
   machine where `rich` happens to be installed for some other reason.

---

## Why it matters

The README labels `python main.py` (the TUI) as the **recommended** first thing a
newcomer runs. If `rich` isn't present, that recommended entry point appears broken on
a fresh setup — the worst possible first impression, during the exact phase (M0/M1)
where the menu now *correctly* points at CartPole.

This is an **undeclared dependency**: the code needs `rich`, but the install
instructions don't install it. Classic "works on my machine."

---

## The fix (two parts — do both)

### Part A — make it install with the project (the real fix)

Add `rich` to `install_requires` in `setup.py`:

```python
install_requires=[
    "opencv-python",
    "mss",
    "numpy",
    "pydantic",
    "pyyaml",
    "pynput",
    "rich",          # <-- add this: the TUI menu is built on it
],
```

> Decision to make: is `rich` a *core* dependency (`install_requires`) or only needed
> for the TUI? Since `main.py` is presented as the main entry point and already
> degrades gracefully without it, putting it in `install_requires` is the simplest
> honest choice. (Alternative: a `"tui"` extra, but that's more ceremony than it's
> worth right now.)

### Part B — install it into your current venv (to use it today)

`setup.py` only helps *future* installs. Your existing venv still needs it:

```powershell
pip install rich
# or, to re-resolve everything after editing setup.py:
pip install -e ".[rl]"
```

---

## How to verify it's fixed

```powershell
# 1. rich imports cleanly
python -c "import rich; print('rich', rich.__version__)"

# 2. the TUI module imports without error
python -c "from src.gametrainer.tui import run_tui; print('TUI import OK')"

# 3. the real thing: the retro menu actually draws
python main.py
```

Success = step 3 shows the menu with `[1] Verify setup - CartPole …` at the top,
instead of the "Failed to launch TUI" fallback.

---

## Scope notes

- **Not an M1 blocker.** M0/M1 run via `python scripts/run_cartpole.py` and
  `python scripts/train_cartpole.py`, which don't import `rich`. Those work today.
- This was discovered while fixing **M1 review issue #3** (the TUI menu pointing at the
  wrong milestone). That fix is done; the menu is correct — you just can't *see* it
  until `rich` is installed.
