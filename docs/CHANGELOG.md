# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

**Important:** When maintaining this file, only **append** new entries. Never overwrite or remove existing changelog content.

---

## [Unreleased]

### Fixed

- **Package imports (`src/gametrainer/__init__.py`):** Replaced broken import from non-existent `env_legacy` with `env_vit`. Package now exports `StardewViTEnv` instead of `StardewEnv`. Docstring updated to list actual modules (env_vit, interface, vit_extractor, etc.).
- **Script import (`scripts/transfer_learning.py`):** Replaced import from non-existent `env` module with `src.gametrainer.env_vit.StardewViTEnv`. Added comment that transfer-learning concepts apply to ViT.
- **Test import (`tests/test_logger.py`):** Fixed incorrect path and module. Replaced `sys.path` to `src/python` and `from core.logger import Logger` with project root and `from src.gametrainer.logger import Logger` so the test runs against the actual package.

### Added

- **Action validation in `StardewViTEnv.step()`:** Actions are now validated and clamped to the valid range `[0, action_space.n - 1]` (as int) before execution. Prevents silent no-ops or errors when the policy returns an out-of-range value (e.g. from a mismatched loaded model).
- **Hardware/accelerator detection (`src/gametrainer/hardware.py`):** Added a device picker and a startup banner so training/play runs choose the best available accelerator (CUDA / MPS / CPU) without hard-requiring CUDA.
- **Retro TUI launcher (`src/gametrainer/tui.py`):** Added a retro-style menu (version/author, changelog view, Train, Play) and updated `main.py` so running `python main.py` launches the TUI by default.

### Documentation

- **Design/architecture alignment:** `architecture.md` and `design.md` were updated to describe the current RL implementation (ViT + PPO, Python screen/input, C++ input only). Original (unimplemented) design kept as a reference section. `tasks.md` was updated with an alignment note and current next steps; backlog items from the original design marked as reference only.

- **PROJECT_OVERVIEW.md overhaul:** Rewritten as the single narrative for both humans and AI (CS-student friendly). Removed all decision-tree wording and the “run using local decision trees” workflow; clarified that the bot runs on the trained PPO+ViT model only. Fixed architecture diagram (three clear boxes; core engine no longer lists “Decision tree executor”). Action space updated to match code (12 discrete actions with correct indices). Dependencies updated: removed ffmpeg; input described as C++ SendInput (`clib`), not pyadirectinput; GUI (tkinter) and setup/installer called out as aspirational. Profile section reframed: profiles are for per-game config when wired in; current run path is train → save model → play from model. Build & Run now includes `pip install -e ".[rl]"` for the RL stack.

- **Docs consolidation and glossary:** Consolidated docs into `docs/README.md` + `docs/AGENTS.md` + `docs/CHANGELOG.md` and added a glossary section defining common acronyms (RL, PPO, ViT, SB3, VRAM, etc.).

---

## [M1] — Borrow the Brain

### Added

- **CartPole PPO training script (`scripts/train_cartpole.py`):** New focused training script for Milestone M1. Trains a `stable-baselines3` PPO agent with `MlpPolicy` on `CartPole-v1` for 25,000 timesteps (configurable via `--steps`). Uses `EvalCallback` to log mean reward every 2,000 steps and `CheckpointCallback` to save models to `models/ppo_cartpole/`. Prints a clear pass/fail verdict at the end by comparing the best mean reward against the M0 random baseline (~22 reward/episode). Includes a `--render` flag to watch evaluation episodes live.

### Changed

- **Baseline stats in `scripts/run_cartpole.py`:** Added per-episode reward tracking (episodes completed, mean reward per episode) to the output summary. The docstring now notes that this mean reward is the M0 random-action baseline that M1 must beat. The 100-step random loop itself is unchanged.
- **Quickstart docs (`docs/README.md`):** Added M0 and M1 quickstart sections and a TensorBoard tip for `logs/cartpole`.
