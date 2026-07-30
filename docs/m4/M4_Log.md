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
| **Current brick** | Brick 0 — the guardrail (pre-flight repair done) |
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

**Status:** ⬜ not started
**File(s):** `scripts/train_from_profile.py`

- **The bar, in one sentence:** _(fill in)_
- **What I built:** _(fill in)_
- **What I learned:** _(fill in)_
- **Verified by:** _(command + output)_

---

## Brick 1 — `Profile` loads and validates

**Status:** ⬜ not started
**File(s):** `tests/test_profile.py` → `src/gametrainer/profile.py`

- **Red test first — what it asserted:** _(fill in)_
- **What I built:** _(fill in)_
- **Decisions made here:** _(fill in — e.g. dataclass vs dict, which fields are required)_
- **What I learned:** _(fill in)_
- **Verified by:** _(fill in)_

---

## Brick 2 — `RewardCalculator`

**Status:** ⬜ not started
**File(s):** `tests/test_rewards.py` → `src/gametrainer/rewards.py`

- **Red test first — what it asserted:** _(fill in)_
- **What moved out of `GridWorldEnv`:** _(fill in)_
- **Proof behaviour didn't change:** _(fill in — M2/M3 tests green, unedited)_
- **What I learned:** _(fill in)_
- **Verified by:** _(fill in)_

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
| _(fill in)_ | | | |

---

## Surprises & corrections

The section the retrospective is actually made of. Log it when you notice it, not
when you understand it.

| Date | What surprised me | What it turned out to mean | What changed as a result |
| :--- | :--- | :--- | :--- |
| 2026-07-30 | `main` had a syntax error in `gridworld.py` from a merged autofix commit | M3's code was one line short of running; the result itself was fine | Pre-flight repair added ahead of Brick 0 |
| _(fill in)_ | | | |

---

## Open questions

Things I don't know yet. Answer them here as they resolve, with the date.

- [ ] Does moving reward logic out of `GridWorldEnv` change *any* M2/M3 number? (It must not.)
- [ ] Should the old per-game train scripts stay after the runner exists, or become thin wrappers? (Plan says: leave them alone — they're the M1–M3 record.)
- [ ] Does `CONTEXT.md`'s "Profile" glossary entry get rewritten for Track A, or split into two entries?
- [ ] What gate would have caught the autofix syntax error before merge — CI, or a pre-push hook?
