# M4 — Build Log (the lab notebook)

> **Covers:** what actually happened while building M4, brick by brick, as it happened.
> **Status:** current — **in progress**. **Last verified:** 2026-07-30 (M4 not started).
> **Authority:** `docs/m4/M4_ToDo.md` owns *the plan*. This file owns *the record of
> doing it*. `docs/m4/M4_Review.md` (written last) owns *what it all meant*.

---

## How to use this file

Fill in a brick's block **when that brick closes**, not at the end of the milestone.
Rules that keep it honest:

- **Write it the day it happens.** A log reconstructed from memory a week later is
  a story, not evidence.
- **Numbers carry their conditions** (DOC_STANDARD rule 3): the number, the baseline
  measured *in the same run*, hardware, wall-clock, seed, timesteps, and the exact
  command. No exceptions, including for runs that failed.
- **Wrong results stay in.** Strike them through, add a dated correction underneath.
  Never delete. The correction is the more valuable half of the record.
- **"Surprises" is the most important section in this file.** M3's whole retrospective
  hung on one surprise (the agent was blind). Log the moment you notice something is
  off, before you know what it means.

At close, `M4_Review.md` is mostly assembled from this file — that's the point of
keeping it.

---

## State of play

| | |
| :--- | :--- |
| **Milestone** | M4 — Make It Swappable (`Profile` + `RewardCalculator`) |
| **Started** | 2026-07-30 (planning) |
| **Branch** | `m4-implementation` |
| **Current brick** | Brick 3 — `make_env(profile)` (Bricks 0–2 done) |
| **Hardware** | CPU (Windows 11, Python 3.14). GPU still not in play — M3 ran fine on CPU |
| **Closed** | _(date, once Brick 7 ticks DOC_STANDARD rule 7)_ |

---

## Pre-flight — the broken import

**Status:** ✅ fixed 2026-07-30
**Found:** 2026-07-30, while reading the tree to plan M4.

`src/gametrainer/gridworld.py` does not parse. Commit `f64b89d` ("Potential fix for
pull request finding", Copilot Autofix, 2026-07-29) removed the closing `"""` of
`make_vision_task`'s docstring, so the function body sits inside the docstring and
the file ends mid-string:

```
File "src/gametrainer/gridworld.py", line 223
SyntaxError: unterminated triple-quoted string literal (detected at line 235)
```

Everything importing GridWorld is red — the entire M3 suite. M3's *result* is fine;
its *code* is one line short.

- **What I did:** restored the single deleted `"""` line before `return TimeLimit(`.
  One line added, nothing else touched.
- **Verified by:** `python -m pytest tests/ -q` → **41 passed, 1 skipped in 5.43s**
  (CPU, Python 3.14). The skip is deliberate: `tests/test_m2_e2e.py:71` — "E2E PPO
  training is an experiment; run `scripts/train_gridworld.py` for the guardrail
  verdict." Contract spot-check also clean: `make_vision_task().reset()` → 2-tuple
  with obs shape `(2,)`, `step()` → 5-tuple.

> **Lesson to carry:** an autofix commit merged without running the suite cost a
> broken `main`. Worth a line in the review about what gate would have caught it.

---

## Brick 0 — The guardrail (written first)

**Status:** ✅ done 2026-07-31
**File(s):** `scripts/train_from_profile.py` (referee only) + `tests/test_m4_verdict.py`

- **The bar, in one sentence:** every profile's agent beats the baseline *measured
  live in that same run* by the margin its own YAML demands, `reset()`/`step()`
  shapes are unchanged, and the **source fingerprint is identical** across the runs
  being compared.
- **What I built:** the four referee pieces, no game yet — `source_fingerprint()`,
  `check_contract_shapes()`, `measure_random_baseline(make_env)`, and the pure
  `decide_verdict()`. Running the script today prints the bar and says plainly that
  there is nothing to grade yet (exit 1), rather than faking a run.
- **Decisions made here:**
  - **One bar shape for three milestones.** M1 said "2× baseline", M2 "≥ +0.5",
    M3 "live baseline + 0.40, goal ≥ 80%". One referee can't grade three shapes, so
    all three are re-expressed in M3's: *live baseline + margin*, plus an optional
    goal rate. CartPole's "2 × 22 = 44" becomes "baseline + 22" — same bar, now
    measured instead of remembered. The M1–M3 scripts are untouched.
  - **Goal rate is optional, and "not applicable" is explicit.** CartPole has no goal
    to reach. A profile that demands `min_goal_rate` on a Ground that can't measure
    one raises instead of silently passing.
- **What I learned:** *the first version of the fingerprint was wrong, and it was
  wrong in the exact way the milestone cares about.* `git ls-files "*.py"` lists only
  files git already **tracks** — so the runner and its test, both brand new and
  uncommitted, were **not in their own fingerprint**. Two runs of genuinely different
  code would have printed the same hash and claimed the swap was proven. Fixed with
  `-c -o --exclude-standard` (tracked + untracked, minus ignored) and pinned by
  `test_fingerprint_covers_uncommitted_files`.
- **Verified by:**
  - Red first: `pytest tests/test_m4_verdict.py -q` → `ModuleNotFoundError:
    No module named 'scripts.train_from_profile'`, then green at **10 passed**
    (11 after the fingerprint fix).
  - `python -m pytest tests/ -q` → **52 passed, 1 skipped in 2.32s** (CPU, Python 3.14).
    Was 41 before this brick; the M0–M3 tests were not edited.
  - `python -m ruff check .` → All checks passed.
  - `python scripts/train_from_profile.py --profile profiles/gridworld.yaml` → prints
    the bar, the fingerprint, and the "nothing to grade yet" notice; exit code 1.

**Correction — 2026-08-02:** `scripts/train_from_profile.py` used `float | None`
(PEP 604 union syntax), which needs Python 3.10+. It ran fine on the Windows
3.14 box this brick was built on, but on a Mac with this repo's `.venv`
(Python 3.9.6 — matching `setup.py`'s `python_requires=">=3.9"`), importing the
file raised `TypeError` at collection time and took the *entire* test suite
down with it, not just this file. Fixed by adding
`from __future__ import annotations` (the same pattern already used in
`hardware.py` and `tui.py`), which makes annotations lazy so they're never
evaluated at runtime. No behaviour change. Verified: `pytest tests/ -q` →
52 passed, 1 skipped — same count the brick originally reported.

> **Lesson to carry:** Brick 0 was verified on one machine only. A file using
> newer syntax than the project's stated minimum can pass everywhere it was
> tested and still be broken elsewhere. Worth a line in the review.

---

## Brick 1 — `Profile` loads and validates

**Status:** ✅ done 2026-08-02
**File(s):** `tests/test_profile.py` → `src/gametrainer/profile.py`

- **Red test first — what it asserted:** seven cases — a known-good GridWorld
  profile loads to the exact field values; a known-good CartPole profile loads
  with `step_cost`/`goal_reward` left `None` (its `reward: builtin`); an
  unknown `ground:` raises `ValueError` naming the legal options; a missing
  required field raises naming the field *and* the file; `perception: pixels`
  on `ground: cartpole` raises; an unknown `perception:` raises naming legal
  options; `reward: gridworld` with `step_cost` missing raises. Confirmed red
  first — `ModuleNotFoundError: No module named 'src.gametrainer.profile'`.
- **What I built:** `Profile`, a frozen dataclass, plus one classmethod
  `Profile.from_yaml(path)` that loads the file, checks it, and returns a
  `Profile` or raises. One `if`-chain, no registry, no dynamic imports.
- **Decisions made here:**
  - **Dataclass, not dict** — per the plan: `profile.step_cost` fails fast on
    a typo, `profile["step_kost"]` fails mid-run.
  - **Fields:** `ground`, `perception`, `reward` (`"builtin" | "gridworld"`),
    `total_timesteps`, the seven PPO hyperparameters used verbatim across
    `train_cartpole.py` / `train_gridworld.py` / `train_gridworld_vit.py`
    (`learning_rate`, `n_steps`, `batch_size`, `n_epochs`, `gamma`,
    `gae_lambda`, `clip_range`, `ent_coef`), and `margin_over_baseline` are
    required for every profile. `step_cost`, `goal_reward` (required only
    when `reward: gridworld`) and `min_goal_rate` (optional — CartPole has no
    goal) default to `None`. No field exists that Brick 0's referee or the
    three existing scripts don't already use — nothing spec­ulative.
  - **Validation lives in `from_yaml`, not `__init__`** — direct construction
    (`Profile(ground=..., ...)`) stays available for tests; the YAML path is
    where "validated on load" is enforced.
  - **Did not touch Track B's `ConfigLoader`** — per the plan, it swallows
    errors and returns `{}`.
- **What I learned:** nothing surprising — this brick matched the plan
  closely. The one adjustment: the plan's Brick 1 write-up didn't list
  `margin_over_baseline` explicitly, but Brick 0's `decide_verdict()` needs it
  per profile (M1/M2/M3 each had a different bar), so it went in as a required
  field rather than a Brick 5 afterthought.
- **Verified by:** `pytest tests/test_profile.py -v` → 7 passed. Full suite:
  `pytest tests/ -q` → **59 passed, 1 skipped** (was 52 before this brick — the
  7 new tests, nothing else moved).

---

## Brick 2 — `RewardCalculator`

**Status:** ✅ done 2026-08-03
**File(s):** `tests/test_rewards.py` → `src/gametrainer/rewards.py`

- **Red test first — what it asserted:** three cases — given `reached_goal=False`
  it returns `step_cost`; given `reached_goal=True` it returns `goal_reward`;
  a second instance built with different numbers returns those different
  numbers, proving nothing is hardcoded on the class. Confirmed red first —
  `ModuleNotFoundError: No module named 'src.gametrainer.rewards'`.
- **What moved out of `GridWorldEnv`:** the one-line ternary in `step()`
  (`reward = self.GOAL_REWARD if reached_goal else self.STEP_COST`) became a
  call to `self._reward_calculator.reward(reached_goal)`. `STEP_COST` and
  `GOAL_REWARD` stay as class constants — existing tests reference
  `GridWorldEnv.STEP_COST`/`GridWorldEnv.GOAL_REWARD` directly, so removing
  them would have forced a test edit, which the plan rules out. `__init__`
  builds the calculator from those same two constants, so today's behaviour
  is identical; a Profile can hand the calculator different numbers from
  Brick 3 onward.
- **Proof behaviour didn't change:** `pytest tests/ -q` → **62 passed, 1
  skipped** (was 59 before this brick — exactly the 3 new `test_rewards.py`
  cases; zero pre-existing test file touched, confirmed via `git diff --stat`
  showing only `gridworld.py` modified). Manual check:
  `GridWorldEnv().step(DOWN)` reward is still `-0.01`.
- **What I learned:** nothing surprising — matched the plan. The module
  docstring at the top of `gridworld.py` said "No Profile, no RewardCalculator
  abstraction yet," which this brick makes false, so it got a one-line
  correction alongside the code (not scope creep — it's describing the exact
  change being made).
- **Verified by:** `pytest tests/test_rewards.py -v` → 3 passed. Full suite:
  `pytest tests/ -q` → 62 passed, 1 skipped.

---

## Brick 3 — `make_env(profile)`

**Status:** ⬜ not started
**File(s):** `tests/test_make_env.py` → `src/gametrainer/factory.py`

- **Red test first — what it asserted:** _(fill in)_
- **Observation space per profile (measured, not assumed):** _(fill in)_
- **Wrapper order used:** _(fill in — M3 settled this; note it if it drifted)_
- **What I learned:** _(fill in)_
- **Verified by:** _(fill in)_

---

## Brick 4 — The three profiles

**Status:** ⬜ not started
**File(s):** `profiles/cartpole.yaml`, `profiles/gridworld.yaml`, `profiles/gridworld_pixels.yaml`

- **Where each number came from:** _(fill in — script + line it was copied from)_
- **Anything that differs from the old scripts, and why:** _(fill in — ideally "nothing")_
- **What I learned:** _(fill in)_
- **Verified by:** _(fill in)_

---

## Brick 5 — The one runner (the experiment)

**Status:** ⬜ not started
**File(s):** `scripts/train_from_profile.py`

Results go in the table below, one row per full run — including failed ones.

- **What I built:** _(fill in)_
- **What surprised me:** _(fill in)_
- **Verified by:** _(fill in)_

---

## Brick 6 — Behavioural test (before closeout)

**Status:** ⬜ not started
**File(s):** `scripts/check_swap.py`

The negative controls matter more than the happy path — this brick exists to catch a
config layer that isn't really wired.

- **Control 1 — swapping profiles genuinely changes the env:** _(fill in — result)_
- **Control 2 — changing `step_cost` in YAML genuinely changes the reward:** _(fill in)_
- **Control 3 — contract shapes on every profile:** _(fill in)_
- **Full suite green (M0–M3 unedited):** _(fill in)_
- **TUI walked by hand:** _(fill in)_
- **`git status` clean between runs:** _(fill in)_
- **What I learned:** _(fill in)_

---

## Brick 7 — TUI + closing the docs

**Status:** ⬜ not started

- **TUI entry added:** _(fill in)_
- **Docs bumped (`Last verified`):** _(fill in — list them)_
- **DOC_STANDARD rule 7 checklist:** _(fill in)_

---

## Results table

Every full run gets a row — **including the ones that failed**. A milestone with no
failed rows is a milestone that wasn't measured.

| Date | Profile | Command | Baseline (live) | Trained mean | Goal rate | Steps | Wall-clock | HW | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| _(fill in)_ | | | | | | | | | |

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
| 2026-07-31 | The profile carries the reward **numbers** (confirmed) | Profile names a calculator class only | "Config-only" isn't real if retuning the game needs a `.py` edit |
| 2026-07-31 | One bar shape: *live baseline + margin* (+ optional goal rate) | Keep M1's "2× baseline" and M2's absolute "+0.5" as separate shapes | One referee can't grade three shapes. Re-expresses identically and drops two hardcoded baselines (DOC_STANDARD rule 3) |
| 2026-07-31 | Fingerprint hashes tracked **and** untracked `.py` files | Tracked only (`git ls-files`); or trust `git status` to be clean | What ran matters, not what was committed. Tracked-only gave a false PASS on brand-new files |
| _(fill in)_ | | | |

---

## Surprises & corrections

The section the retrospective is actually made of. Log it when you notice it, not
when you understand it.

| Date | What surprised me | What it turned out to mean | What changed as a result |
| :--- | :--- | :--- | :--- |
| 2026-07-30 | `main` had a syntax error in `gridworld.py` from a merged autofix commit | M3's code was one line short of running; the result itself was fine | Pre-flight repair added ahead of Brick 0 |
| 2026-07-31 | The swap proof didn't cover the files it was written in | `git ls-files` lists only **tracked** files, so new uncommitted code was invisible to its own fingerprint — a false PASS on M4's central claim | Switched to `-c -o --exclude-standard`; pinned by a test that fails if anyone simplifies it back |
| 2026-08-02 | `pytest tests/` couldn't even collect on the Mac | Brick 0 used `float \| None` (needs Python 3.10+); this repo's Mac `.venv` is 3.9.6, matching `setup.py`'s stated minimum — the Windows 3.14 box it was built on hid the incompatibility | Added `from __future__ import annotations` to `train_from_profile.py`, matching `hardware.py`/`tui.py`; suite back to 52 passed, 1 skipped |

---

## Open questions

Things I don't know yet. Answer them here as they resolve, with the date.

- [ ] Does moving reward logic out of `GridWorldEnv` change *any* M2/M3 number? (It must not.)
- [ ] Should the old per-game train scripts stay after the runner exists, or become thin wrappers? (Plan says: leave them alone — they're the M1–M3 record.)
- [ ] Does `CONTEXT.md`'s "Profile" glossary entry get rewritten for Track A, or split into two entries?
- [ ] What gate would have caught the autofix syntax error before merge — CI, or a pre-push hook?
