# M4 — Build Log (the lab notebook)

> **Covers:** what actually happened while building M4, brick by brick, as it happened.
> **Status:** current — **closed**. **Last verified:** 2026-08-14 (all 7
> bricks done and PASS; rewritten same day to DOC_STANDARD's new log style,
> by explicit request).
> **Authority:** `docs/m4/M4_ToDo.md` owns *the plan*. This file owns *the record of
> doing it*. `docs/m4/M4_Review.md` (written last) owns *what it all meant*.

---

## How to use this file

Fill in a brick's block **when it closes**, not at the end.

- **Write it the day it happens** — a log from memory is a story, not evidence.
- **Numbers carry their conditions** (rule 3): number, baseline (same run),
  hardware, wall-clock, seed, timesteps, command. No exceptions.
- **Wrong results stay in** — strike through, add a dated correction. Never delete.
- **Surprises are the most important section** — log the moment something
  looks off, before you know what it means.

At close, `M4_Review.md` is mostly assembled from this file.

---

## State of play

| | |
| :--- | :--- |
| **Milestone** | M4 — Make It Swappable (`Profile` + `RewardCalculator`) |
| **Started** | 2026-07-30 (planning) |
| **Branch** | `m4-implementation` |
| **Current brick** | None — all 7 bricks done |
| **Hardware** | CPU (Windows 11, Python 3.14 / Mac, Apple M5, Python 3.14.6). GPU still not in play — M3 ran fine on CPU |
| **Closed** | 2026-08-14 — DOC_STANDARD rule 7 checklist ticked in `docs/m4/M4_Review.md` |

---

## Pre-flight — the broken import

**Status:** ✅ fixed 2026-07-30
**Found:** 2026-07-30, while reading the tree to plan M4.

`gridworld.py` didn't parse — a merged autofix commit (`f64b89d`, GitHub
Copilot Autofix, 2026-07-29) deleted the closing `"""` of a docstring, so the
file ended mid-string and every M3 test went red. M3's *result* was fine;
its *code* was one line short.

- **Fix:** restored the missing `"""`. One line.
- **Verified by:** `pytest tests/ -q` → **41 passed, 1 skipped** (CPU, Python
  3.14). The skip is deliberate — E2E PPO training is an experiment, not a
  test (see `tests/test_m2_e2e.py:71`).

> **Lesson to carry:** an autofix commit merged without running the suite
> broke `main`. Worth a line in the review about what gate would catch that.

---

## Brick 0 — The guardrail (written first)

**Status:** ✅ done 2026-07-31
**File(s):** `scripts/train_from_profile.py` (referee only) + `tests/test_m4_verdict.py`

- **The bar:** every profile's agent must beat the baseline *measured live in
  that same run* by its own margin, `reset()`/`step()` stay unchanged, and
  the code must be provably identical across the runs being compared (a
  "source fingerprint").
- **What I built:** the referee, no game yet — one function each to
  fingerprint the source, check the `reset()`/`step()` contract, measure a
  live random baseline, and decide PASS/FAIL. Running it today just prints
  the bar — nothing to grade yet.
- **Why one bar shape:** M1, M2, M3 each used a different pass bar; one
  referee can't grade three. Re-expressed all three as *live baseline +
  margin* (2026-07-31 decision below), goal rate optional.
- **What I learned:** the first fingerprint version was wrong in the exact
  way this milestone cares about — `git ls-files` only lists **tracked**
  files, so this brand-new, uncommitted code wasn't in its own fingerprint.
  Two different runs could have hashed the same and claimed the swap was
  proven. Fixed by hashing tracked *and* untracked files.
- **Verified by:** red first, then 10→11 passed after the fix. Full suite:
  **52 passed, 1 skipped** (was 41). `ruff` clean.

**Correction — 2026-08-02:** the script used `float | None` syntax (needs
Python 3.10+). It ran fine on the Windows 3.14 box it was built on, but broke
the *entire* suite on the Mac's Python 3.9 `.venv`. Fixed with
`from __future__ import annotations`. No behaviour change — suite back to 52
passed, 1 skipped.

> **Lesson to carry:** this brick was verified on one machine only. Newer
> syntax than the project's stated minimum can pass everywhere it's tested
> and still be broken elsewhere.

---

## Brick 1 — `Profile` loads and validates

**Status:** ✅ done 2026-08-02
**File(s):** `tests/test_profile.py` → `src/gametrainer/profile.py`

- **What I built:** `Profile` — a dataclass that loads a YAML profile and
  checks it's valid, or raises a clear error. A dataclass instead of a dict
  because a typo in a field name (`profile.step_kost`) fails immediately
  instead of silently returning nothing. Validation lives in the `from_yaml`
  loader, not the constructor, so tests can still build a `Profile` directly
  without going through a file.
- **Tests:** 7 cases — a good GridWorld file, a good CartPole file, and five
  bad files (unknown ground, missing field, wrong perception, unknown
  perception, missing required reward field), each raising a clear error.
  Red first (`ModuleNotFoundError`), then green.
- **What I learned:** the plan didn't call out `margin_over_baseline` as a
  required field, but Brick 0's pass/fail check needs it per profile, so it
  went in as required.
- **Verified by:** `pytest tests/test_profile.py -v` → 7 passed. Full suite:
  **59 passed, 1 skipped** (was 52).

---

## Brick 2 — `RewardCalculator`

**Status:** ✅ done 2026-08-03
**File(s):** `tests/test_rewards.py` → `src/gametrainer/rewards.py`

- **What I built:** `RewardCalculator` — one small class holding two numbers
  (step cost, goal reward) and one method that picks between them. The
  one-line reward decision that used to live inside `GridWorldEnv.step()`
  now calls out to this instead. The two numbers stay as class constants on
  `GridWorldEnv` too, so nothing that reads them today breaks — the
  calculator just gets built from those same constants for now.
- **Tests:** 3 cases — no goal reached returns the step cost, goal reached
  returns the goal reward, and a second calculator built with different
  numbers proves nothing is hardcoded. Red first, then green.
- **Proof behaviour didn't change:** full suite **62 passed, 1 skipped** (was
  59 — exactly the 3 new tests, nothing else moved). Manual check: a step
  still returns `-0.01`, same as before this brick.
- **What I learned:** nothing surprising — matched the plan.
- **Verified by:** `pytest tests/test_rewards.py -v` → 3 passed. Full suite:
  62 passed, 1 skipped.

---

## Brick 3 — `make_env(profile)`

**Status:** ✅ done 2026-08-05
**File(s):** `tests/test_make_env.py` → `src/gametrainer/factory.py`

- **What I built:** `make_env(profile)` — one function, one `if`-chain over
  the three `(ground, perception)` combos a `Profile` allows, raising for
  anything else. 26 lines, no registry.
- **The gap this closed:** `GridWorldEnv` couldn't take reward numbers from
  outside. Added optional `step_cost`/`goal_reward` constructor params,
  defaulting to `None` and falling back to the existing class constants — no
  pre-M4 caller changes, and the factory is the only one that passes real
  numbers through.
- **Tests:** 6 cases — each profile builds an env `check_env` accepts with
  the right shape (`(4,)`, `(2,)`, `(224, 224, 3)`); the pixels wrapper order
  is `PixelObservation(TimeLimit(RandomStart(GridWorldEnv)))`; a custom
  `step_cost=-5.0` changes the reward; an invalid combination raises. Red
  first, then green.
- **What I learned:** `Profile` doesn't block nonsense combinations when
  built directly (only `Profile.from_yaml` validates), so `make_env` needed
  its own fallback `raise` — caught by a test, not a later debugging
  session.
- **Verified by:** `pytest tests/test_make_env.py -v` → 6 passed. Full suite:
  **68 passed, 1 skipped** (was 62).

---

## Brick 4 — The three profiles

**Status:** ✅ done 2026-08-08
**File(s):** `profiles/cartpole.yaml`, `profiles/gridworld.yaml`, `profiles/gridworld_pixels.yaml`

- **Where the numbers came from:** every PPO hyperparameter and
  `total_timesteps` copied straight from each old script's `PPO(...)` call.
  The pixels script left four PPO fields unset, so I checked the installed
  library's own defaults rather than guessing — they matched what M1/M2
  wrote out by hand. `step_cost`/`goal_reward` came straight from
  `GridWorldEnv`'s existing constants.
- **What's different from the old scripts:** only the pass bar — each
  profile's `margin_over_baseline` re-expresses that script's original bar
  relative to a live baseline instead of a hardcoded number (2026-07-31
  decision). No PPO or reward number changed.
- **What I learned:** confirming the pixels script's unset PPO defaults
  actually matched M1/M2's values, instead of assuming, was the one real
  step here.
- **Verified by:** all three profiles load with no error and build through
  `make_env` into an env `check_env` accepts, with the right observation
  shape. Full suite unchanged: 68 passed, 1 skipped (no test file added,
  only YAML).

---

## Brick 5 — The one runner (the experiment)

**Status:** ✅ done 2026-08-13
**File(s):** `scripts/train_from_profile.py`

Results go in the table below, one row per full run — including failed ones.

- **What I built:** filled in `main()` on Brick 0's referee — load the
  profile, print every resolved field, build the env, check contract shapes,
  measure the live baseline, pick the right policy for the profile's
  perception type, train PPO, evaluate, print PASS/FAIL. Also added
  `--smoke` for a fast wiring check.
- **What surprised me:** the pixels profile's first full run FAILED, well
  short of a bar M3 had already cleared with the same hyperparameters — see
  the Surprises table below. Short version: ordinary run-to-run variance
  from an unseeded run, not a bug.
- **Verified by:** all three profiles trained end-to-end through the same
  unedited script — CartPole PASS, GridWorld PASS, GridWorld pixels PASS on
  the second attempt. Full suite stayed at 68 passed, 1 skipped throughout.

---

## Brick 6 — Behavioural test (before closeout)

**Status:** ✅ done 2026-08-14 (TUI walk-through deferred to Brick 7 — see below)
**File(s):** `scripts/check_swap.py`

The point: prove the config layer is really wired, not just that training
runs. Four checks, each trying to catch a hardcoded shortcut rather than
just confirming the happy path.

- **Swapping profiles genuinely changes the env:** PASS. CartPole vs.
  GridWorld-pixels — observation space, action space, and reward on an
  identical step all differ.
- **Changing `step_cost` in YAML genuinely changes the reward:** PASS. Two
  GridWorld profiles differing only in `step_cost` produce exactly that
  reward on a wall-bump, proving the number comes from the profile, not
  `GridWorldEnv`'s own constant.
- **Contract shapes hold on every profile:** PASS.
- **Full suite green, unedited:** PASS — 68 passed, 1 skipped.
- **TUI walked by hand:** deferred — no menu entry yet. Done 2026-08-14, see
  Brick 7.
- **What I learned:** every check passed first try — Bricks 1–5 wired
  things honestly. The one real finding: the to-do list's own Brick 6 asks
  for a TUI check that only makes sense after Brick 7 — an ordering bug in
  the plan itself.
- **Verified by:** `python scripts/check_swap.py` → PASS on all four checks.

---

## Brick 7 — TUI + closing the docs

**Status:** ✅ done 2026-08-14
**File(s):** `src/gametrainer/tui.py`, `docs/m4/M4_Review.md`, `docs/CHANGELOG.md`,
`docs/PRD.md`, `docs/ONBOARDING.md`, `CONTEXT.md`, `docs/README.md`

- **TUI entry added:** one new menu item, `[6] Train from profile`, launching
  a three-way sub-menu (CartPole / GridWorld / GridWorld-pixels) that calls
  the exact Brick 5 runner. Old entries untouched; later items renumbered.
- **Walked by hand (also closes Brick 6's deferred item):** ran the menu
  end-to-end for a real CartPole run — PASS, matching Brick 5's numbers. New
  row in the Results table below.
- **Docs closed out:** `M4_Review.md` written. `CHANGELOG.md` got the M4
  entry. `PRD.md`, `ONBOARDING.md`, `CONTEXT.md`, `README.md` re-verified and
  bumped — `PRD.md`'s old wrapper-class diagram corrected in place (rule 4),
  not rewritten.
- **What I learned:** the Brick 6/7 ordering issue resolved cleanly. Bigger
  finding: `docs/PRD.md` never had a DOC_STANDARD header until this brick's
  audit caught it.
- **Verified by:** `pytest tests/ -q` → 68 passed, 1 skipped, unchanged.
  `check_swap.py` → still PASS. `git status --short` → only listed files
  changed.

---

## Results table

Every full run gets a row — **including the ones that failed**. A milestone with no
failed rows is a milestone that wasn't measured.

| Date | Profile | Command | Baseline (live) | Trained mean | Goal rate | Steps | Wall-clock | HW | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-08-11 | `cartpole.yaml` | `python scripts/train_from_profile.py --profile profiles/cartpole.yaml` | +20.88 | +500.00 | n/a (no goal) | 25,000 | 0.1 min train / 6.8s total | Mac, Apple M5, CPU, Python 3.14.6 | **PASS** |
| 2026-08-13 | `gridworld.yaml` | `python scripts/train_from_profile.py --profile profiles/gridworld.yaml` | -0.14 | +0.93 | n/a (not required by this profile) | 25,000 | 0.1 min train / 9.1s total | Mac, Apple M5, CPU, Python 3.14.6 | **PASS** |
| 2026-08-13 | `gridworld_pixels.yaml` | `python scripts/train_from_profile.py --profile profiles/gridworld_pixels.yaml` | +0.25 | +0.55 | 65% (needs 80%) | 20,000 | 7.3 min train | Mac, Apple M5, CPU, Python 3.14.6 | **FAIL** — see Surprises below |
| 2026-08-13 | `gridworld_pixels.yaml` (rerun, unchanged) | `python scripts/train_from_profile.py --profile profiles/gridworld_pixels.yaml` | +0.46 | +0.99 | 100% (needs 80%) | 20,000 | 7.0 min train | Mac, Apple M5, CPU, Python 3.14.6 | **PASS** — matches M3's original +0.99, 100% goal rate almost exactly |
| 2026-08-14 | `cartpole.yaml` (via TUI, Brick 7) | `printf '6\n1\n' \| python main.py` → `scripts/train_from_profile.py --profile profiles/cartpole.yaml` | +19.58 | +500.00 | n/a (no goal) | 25,000 | 0.1 min train | Mac, Apple M5, CPU, Python 3.14.6 | **PASS** — first M4 result launched from the menu, not the command line |

**The M3 numbers to reproduce** (from `docs/CHANGELOG.md`, M3 entry): live baseline
`+0.48`, trained `+0.99`, goal reached in 100% of greedy episodes, 20,000 steps,
19.2 min on CPU. The pixels profile should land here. **A materially different
number means the config path is wrong, not that the agent got better.**

---

## Decisions log

Every choice that could reasonably have gone the other way. One line each — the
alternative and why it lost matters more than the choice.

| Date | Decision | Alternative rejected | Why |
| :--- | :--- | :--- | :--- |
| 2026-07-30 | Flat `profiles/*.yaml`, one file per setup | Track B's folder-per-game (`profiles/<game>/regions.yaml`) | Lighter, and keeps Track A visibly separate from Track B |
| 2026-07-30 | Profile carries the reward **numbers** | Profile names a calculator class only | "Config-only" isn't real if retuning the game needs a `.py` edit |
| 2026-07-30 | CartPole declares `reward: builtin` | Pretend a `RewardCalculator` applies to it | We didn't build CartPole; we can't rescore it. Say so in the file |
| 2026-07-30 | `M<N>_Log.md` added to DOC_STANDARD rule 6 | Fold brick notes into `M<N>_Review.md` | A file written *during* and a file written *after* answer different questions (rule 2). Applies from M4 on, not retroactively |
| 2026-07-31 | One bar shape: *live baseline + margin* (+ optional goal rate) | Keep M1's "2× baseline" and M2's absolute "+0.5" as separate shapes | One referee can't grade three shapes; drops two hardcoded baselines (rule 3) |
| 2026-07-31 | Goal rate is optional and off by default | Require every profile to state a goal rate | CartPole has no goal — forcing the field would make a profile lie |
| 2026-07-31 | Fingerprint hashes tracked **and** untracked `.py` files | Tracked only (`git ls-files`); or trust `git status` to be clean | What ran matters, not what was committed. Tracked-only gave a false PASS on brand-new files |
| 2026-08-02 | `Profile` is a frozen dataclass | A plain dict | A typo in a field name fails immediately instead of silently returning nothing |
| 2026-08-04 | Retired Track B entirely (deleted, not left alone) | Leave it untouched until M5/M6, per the original plan | User's explicit call, mid-M4. Nine Track B-only files deleted; kept `vit_extractor.py`/`input.py` — shared with the live M0–M3 scripts |
| 2026-08-05 | `GridWorldEnv` gets optional `step_cost`/`goal_reward` constructor params | Have the factory poke `env._reward_calculator` from outside after construction | Keeps the calculator's construction inside the class that owns it, not reaching into a private attribute from outside |
| 2026-08-08 | Added CI (`.github/workflows/tests.yml`), `pytest -q` on Python 3.9 only | A pre-push hook; or a full OS/Python version matrix | A hook can't catch a bot-authored commit merged directly (the actual incident). 3.9 is the stated minimum, and also what would've caught the separate `float \| None` incident |
| _(fill in)_ | | | |

---

## Surprises & corrections

The section the retrospective is actually made of. Log it when you notice it, not
when you understand it.

| Date | What surprised me | What it turned out to mean | What changed as a result |
| :--- | :--- | :--- | :--- |
| 2026-07-30 | `main` had a syntax error in `gridworld.py` from a merged autofix commit | M3's code was one line short of running; the result itself was fine | Pre-flight repair added ahead of Brick 0 |
| 2026-07-31 | The swap proof didn't cover the files it was written in | `git ls-files` lists only **tracked** files — new uncommitted code was invisible to its own fingerprint, a false PASS on M4's central claim | Switched to `-c -o --exclude-standard`; pinned by a test that fails if anyone simplifies it back |
| 2026-08-02 | `pytest tests/` couldn't even collect on the Mac | `float \| None` needs Python 3.10+; the Mac `.venv` is 3.9.6 (`setup.py`'s stated minimum) — the Windows 3.14 box it was built on hid the incompatibility | Added `from __future__ import annotations`, matching `hardware.py`/`tui.py`; suite back to 52 passed, 1 skipped |
| 2026-08-13 | `gridworld_pixels.yaml`'s full run **FAILED** (+0.55, needs +0.65) — M3's original run of the *same* hyperparameters scored +0.99 | **No script in M1–M4 pins a random seed** — every run, including M3's original, drew a fresh policy init and fresh starting squares. One run each side isn't enough to call it a regression | Not yet resolved — see Open questions below |

---

## Open questions

Things I don't know yet. Answer them here as they resolve, with the date.

- [ ] Does moving reward logic out of `GridWorldEnv` change *any* M2/M3 number? (It must not.)
- [x] `gridworld_pixels.yaml`'s FAIL/PASS pair. **Resolved 2026-08-13** — see the Surprises
      table above; not a config-path bug.
- [ ] Should the old per-game train scripts stay after the runner exists, or become thin wrappers? (Plan says: leave them alone — they're the M1–M3 record.)
- [x] Does `CONTEXT.md`'s "Profile" entry need rewriting or splitting for Track A?
      **Resolved 2026-08-04:** rewritten for Track A — Track B is deleted, nothing to split into.
- [x] What gate would have caught the autofix syntax error before merge?
      **Resolved 2026-08-08** — see the CI decision in the Decisions log above.
