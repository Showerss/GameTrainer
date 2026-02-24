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

### Documentation

- **Design/architecture alignment:** `architecture.md` and `design.md` were updated to describe the current RL implementation (ViT + PPO, Python screen/input, C++ input only). Original (unimplemented) design kept as a reference section. `tasks.md` was updated with an alignment note and current next steps; backlog items from the original design marked as reference only.

---
