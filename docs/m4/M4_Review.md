# M4 — Milestone Review (the sprint retrospective)

> **Covers:** what Milestone 4 proved, what failed along the way, and what we learned.
> **Status:** current. **Last verified:** 2026-08-14 (all 7 bricks complete; 3 profiles verified PASS via one unedited runner; check_swap 4/4 PASS; DOC_STANDARD rule 7 ticked).
> **Authority:** `docs/m4/M4_ToDo.md` owns the plan. `docs/m4/M4_Log.md` owns the lab notebook. This file owns *what it all meant*. Written to `docs/DOC_STANDARD.md`.

---

## 1. Executive Summary

Milestone 4 proved the central architectural thesis of GameTrainer: **any ground, any brain, one socket.**

Prior to M4, running each game required a dedicated, hard-coded training script (`scripts/train_cartpole.py`, `scripts/train_gridworld.py`, `scripts/train_gridworld_vit.py`). M4 replaced that per-game sprawl with a universal, config-driven architecture:
1. **The Blueprint:** Validated `.yaml` profiles (`Profile` dataclass in `src/gametrainer/profile.py`).
2. **The Seam:** A single factory function (`make_env(profile)` in `src/gametrainer/factory.py`).
3. **The Referee:** Isolated functional reward calculation (`RewardCalculator` in `src/gametrainer/rewards.py`).
4. **The Universal Runner:** One runner (`scripts/train_from_profile.py`) that trains any profile end-to-end with **zero Python code edits between runs**.

Swappability was verified live across CartPole, GridWorld, and GridWorld-through-pixels, and locked by four negative controls in `scripts/check_swap.py`.

---

## 2. Results Table (Rule 3)

Every full training run and verification check recorded under reproducible conditions:

| Date | Profile | Command | Baseline (live) | Trained mean | Goal rate | Steps | Wall-clock | HW / Platform | Seed | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-08-11 | `cartpole.yaml` | `python scripts/train_from_profile.py --profile profiles/cartpole.yaml` | +20.88 | +500.00 | n/a | 25,000 | 6.8s total | Mac, Apple M5, CPU, Python 3.14.6 | unseeded | **PASS** |
| 2026-08-13 | `gridworld.yaml` | `python scripts/train_from_profile.py --profile profiles/gridworld.yaml` | -0.14 | +0.93 | n/a | 25,000 | 9.1s total | Mac, Apple M5, CPU, Python 3.14.6 | unseeded | **PASS** |
| 2026-08-13 | `gridworld_pixels.yaml` | `python scripts/train_from_profile.py --profile profiles/gridworld_pixels.yaml` | +0.25 | +0.55 | 65% (needs 80%) | 20,000 | 7.3 min train | Mac, Apple M5, CPU, Python 3.14.6 | unseeded | **FAIL** (unseeded run variance) |
| 2026-08-13 | `gridworld_pixels.yaml` (rerun) | `python scripts/train_from_profile.py --profile profiles/gridworld_pixels.yaml` | +0.46 | +0.99 | 100% (needs 80%) | 20,000 | 7.0 min train | Mac, Apple M5, CPU, Python 3.14.6 | unseeded | **PASS** (reproduced M3 +0.99) |
| 2026-08-14 | `cartpole.yaml` (via TUI) | `printf '6\n1\n' \| python main.py` | +19.58 | +500.00 | n/a | 25,000 | 0.1 min train | Mac, Apple M5, CPU, Python 3.14.6 | unseeded | **PASS** (TUI launch verified) |

All 4 negative controls in `scripts/check_swap.py` PASS:
1. Missing profile fails loudly at startup with descriptive validation error.
2. Altered reward numbers in YAML directly alter step reward return.
3. Swapping perception mode alters observation space shape from `(2,)` to `(3, 224, 224)`.
4. Source code fingerprint matches across profile runs, proving zero code changes occurred.

---

## 3. What We Learned & Key Surprises

1. **Monolithic wrapper classes are an anti-pattern.**
   The early PRD design proposed a monolithic `GameEnvironment` class that wrapped perception, input, and reward into an outer God Object. During implementation, we realized this added unnecessary indirection and broke Gymnasium compatibility. Replacing it with a functional factory (`make_env`) and native Gymnasium observation wrappers kept the architecture modular and clean.

2. **The untracked files fingerprint leak.**
   Our first implementation of the source code fingerprint used `git ls-files`. However, `git ls-files` only enumerates committed/tracked files. Brand-new uncommitted scripts were completely invisible to the hash, meaning code could be altered without changing the fingerprint. We corrected the command to include untracked files (`git ls-files -c -o --exclude-standard`) and locked it with a dedicated test.

3. **Python version compatibility on development workstations.**
   Using Python 3.10+ union syntax (`float | None`) caused test collection crashes on workstation virtual environments running Python 3.9.6. Adding `from __future__ import annotations` across all modules restored compatibility and prompted the introduction of a GitHub Actions CI test workflow.

4. **RL training variance without random seeds.**
   The first run of `gridworld_pixels.yaml` scored `+0.55` (failing the 80% goal rate threshold), while the identical rerun scored `+0.99` (100% goal rate). Because early milestone scripts did not pin random seeds, fresh policy initialization and stochastic start tiles can produce variance. Benchmarking against live baselines rather than static thresholds prevented false regression flags.

---

## 4. What We'd Redo If Starting Over

1. **Pin seeds for reference benchmark comparisons:**
   While unseeded training proves general policy robustness, comparative regression testing between milestones benefits from fixed seeds to eliminate stochastic variance.

2. **Retire Track B prototype code earlier:**
   Carrying dead prototype files from the early Stardew experiment created mental clutter and required ongoing disclaimers across documentation. Deleting Track B cleanly mid-M4 dramatically simplified the repo.

---

## 5. DOC_STANDARD Rule 7 Closeout Checklist

- [x] `docs/m4/M4_Review.md` exists, with a results table meeting Rule 3.
- [x] `docs/CHANGELOG.md` has the milestone entry.
- [x] Every doc whose claims the milestone changed has a bumped **Last verified** (`M4_Log.md`, `M4_Review.md`, `CHANGELOG.md`, `ONBOARDING.md`, `PRD.md`).
- [x] No two docs contradict each other (Rule 2).
