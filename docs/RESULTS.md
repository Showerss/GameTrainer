# Results

> **Covers:** every milestone's headline result, with its baseline and the conditions it ran under.
> **Status:** current. **Last verified:** 2026-10-17.
> **Authority:** this is the **only** results table in the repo. Other docs link here instead of copying it, because copies drift apart.

## How to read this page

- **Baseline** = what a random player scores. A result only counts if it beats the baseline.
- **Live baseline** = measured in the same run, not remembered. *Why:* the game can change under you.
- Every row gives hardware and time, so anyone can try to repeat it.
- No run is seeded (seeded = the randomness is fixed so reruns match), so reruns wobble a little.

## Headline results

| Milestone | What it proves | Baseline | Result | Time · Hardware | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **M0** Setup | The Gymnasium loop runs | random CartPole: ~22 steps | 100 random steps, no crash | seconds · CPU | PASS |
| **M1** Borrow the brain | PPO learns CartPole | ~22 | **500.0** (the max score) | 21 s · Ryzen 7 9700X, CPU | PASS |
| **M2** Build a ground | PPO learns our GridWorld | **−0.09** (see note) | **+0.93**, goal 20/20 in 8 steps | 15 s · Ryzen 7 9700X, CPU | PASS |
| **M3** Add the eyes | PPO learns from pictures only | +0.34 (live) | **+0.98**, goal 100% | 14.2 min · Ryzen 7 9700X, CPU | PASS |
| **M4** Make it swappable | 3 profiles, 1 runner, 0 code edits | live, per profile | all 3 PASS (table below) | 7 s – 7 min · Apple M5, CPU | PASS |
| **M5** Add the hands | Real keys drive a real game window | 4 controls (below) | **4/4**, 20/20 clean resets | 25 s · Windows 11 x64 | PASS |

M1–M3 rows are the **R1 re-runs (2026-10-17)**. They re-prove the old results on the cleaned-up code. Original runs: M1 22 → 500, M2 +0.93, M3 +0.99 vs baseline +0.48 in 19.2 min. Those are in the M0–M3 review PDFs.

## Note: the M2 baseline (corrected 2026-10-17)

Older docs gave three numbers for GridWorld's random baseline: **−0.3**, **−0.14** and **+0.13**. All three were real readings. They were just **too small a sample**.

| Sample size | What you get |
| :--- | :--- |
| 20 episodes | anywhere from −0.55 to +0.27 |
| 50 episodes | anywhere from −0.39 to +0.17 |
| 6,000 episodes | **−0.09** (three seeds: −0.089, −0.096, −0.100) |

Measured 2026-10-17 with `referee.measure_random_baseline` on `GridWorldEnv()`, Ryzen 7 9700X, CPU, 0.7 s per 2,000 episodes.
*Lesson:* random players are noisy, so a baseline needs many episodes. That's why M3 onward measure 50 live, every run.

## M4 detail: one runner, three games

Command: `python scripts/train_from_profile.py --profile profiles/<name>.yaml`. Mac, Apple M5, CPU, Python 3.14.6, unseeded.

| Date | Profile | Live baseline | Trained | Goal rate | Time | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-08-11 | `cartpole.yaml` | +20.88 | +500.00 | n/a | 6.8 s | PASS |
| 2026-08-13 | `gridworld.yaml` | −0.14 | +0.93 | n/a | 9.1 s | PASS |
| 2026-08-13 | `gridworld_pixels.yaml` | +0.25 | +0.55 | 65% (needs 80%) | 7.3 min | **FAIL** |
| 2026-08-13 | `gridworld_pixels.yaml` (rerun) | +0.46 | +0.99 | 100% | 7.0 min | PASS |

The FAIL stays in the table on purpose. Same code, different luck: proof that unseeded runs wobble (`docs/m4/M4_Review.md`).

## M5 detail: the four controls

Command: `python scripts/check_hands.py`, LibreMines v2.3.0, Easy 8×8.

| Date | Platform | 1. Keys live | 2. NullInput | 3. Frozen frame | 4. Reset | Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-09-07 | macOS, Apple Silicon | 1 cell, the target | 0 cells | live 1 / frozen 0 | 20/20 | 16.8 s |
| 2026-09-15 | Windows 11 x64 | 1 cell, the target | 0 cells | live 1 / frozen 0 | 20/20 | 22.4 s |
| 2026-10-17 | Windows 11 x64 (R1 re-run) | 1 cell, the target | 0 cells | live 1 / frozen 0 | 20/20 | 25 s |

*Why controls 2 and 3 matter most:* they're **negative controls**, tests where nothing should happen. They prove our keys and our eyes caused the change, not luck.
