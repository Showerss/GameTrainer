# M4 — Make It Swappable (Profile + RewardCalculator)

> **Covers:** the original M4 plan — scope, design decisions, bricks, and finish line.
> **Status:** completed plan. **Last verified:** 2026-08-14 (M4 closed; retained as the plan-of-record).
> **Authority:** `docs/PRD.md` owns *what* gets built and in what order. This file
> owns *what M4 requires*. Brick-by-brick notes live in `docs/m4/M4_Log.md`;
> the retrospective is `docs/m4/M4_Review.md`, written last.

> **Milestone goal (from PRD §7):** `Profile` + `RewardCalculator` exist; switching
> between CartPole and GridWorld is **config-only, no code edits**.
>
> **Done when…** One runner script trains on CartPole *or* GridWorld *or* GridWorld-
> through-pixels, chosen **only** by which `.yaml` file is passed on the command line,
> with **zero Python edits between the runs** — captured as the **Brick 0 guardrail
> printing PASS**.

M3 proved the *sense organ* is swappable. M4 proves the **whole Ground** is: same
runner, same borrowed brain, different game — and the only thing that changed is a
text file. This is the milestone the PRD calls the portfolio win condition (§7):
*any ground, any brain, one socket.*

The test of success is embarrassingly simple. If I have to open a `.py` file to go
from CartPole to GridWorld, M4 failed, no matter how nice the code looks.

---

## ✅ Pre-flight blocker — cleared 2026-07-30

> **Resolved the same day this plan was written.** The closing `"""` was restored
> and the suite came back green (41 passed, 1 skipped). Kept here, not deleted,
> because the failure is part of the record — see `M4_Log.md` for the verification
> output and the lesson. The description below is what was wrong.

`src/gametrainer/gridworld.py` **does not parse.** Commit `f64b89d`
("Potential fix for pull request finding", Copilot Autofix, 2026-07-29) deleted the
closing `"""` of the `make_vision_task` docstring, so the function body is trapped
inside the docstring:

```
File "src/gametrainer/gridworld.py", line 223
SyntaxError: unterminated triple-quoted string literal (detected at line 235)
```

Every M3 test and script imports this module, so the whole suite is currently
red — not because M3 was wrong, but because a bot ate one line. Restore the `"""`
and confirm the M3 suite is green **before** starting M4. Nothing below is
meaningful on top of a broken import.

> **Verify:** `pytest tests/ -q` collects and passes, and
> `python -c "from src.gametrainer.gridworld import make_vision_task"` is silent.

---

## Scope discipline (what M4 is NOT)

- ❌ **No real key presses, no screen capture.** `KeyboardInput` and `mss` are M5.
- ❌ **No Stardew profile.** That's M6, and it's a *reward* problem, not a config one.
- ❌ **No new game worlds.** CartPole and GridWorld are the two Grounds. Two is
  enough to prove swappability; a third proves nothing extra and costs a week.
- ❌ **No plugin system.** The profile does **not** import arbitrary Python by name
  from YAML. A fixed, named set of choices, validated on load. (See "The risk to watch".)
- ❌ **No re-litigating M3's result.** M4 must *reproduce* `+0.99` through config, not
  beat it. A different number here means the config path is wrong.
- ❌ **No touching PPO.** Same rule as every milestone.
- ❌ **No touching Track B** (`config.py`, `interface.py`, `env_vit.py`). See the
  name-collision note below.

---

## The design (proposed — confirm before Brick 1)

| Decision | Choice | Why |
| :--- | :--- | :--- |
| **What a profile is** | One flat `.yaml` file per setup, in `profiles/` | A folder-per-game is Track B's shape and it's heavier than we need |
| **How it's loaded** | A `Profile` dataclass with explicit fields, validated on load | An unvalidated `dict` moves every typo from load-time to 19 minutes into training |
| **What it selects** | `ground` (cartpole \| gridworld), `perception` (numeric \| pixels), reward numbers, PPO hyperparameters, the pass bar | Exactly the things that differ between our existing scripts — nothing speculative |
| **How the env gets built** | `make_env(profile)` in one factory function | One place where a name becomes an object; the only place that knows the mapping |
| **Where reward logic lives** | `RewardCalculator` reads its numbers from the profile | Today `STEP_COST`/`GOAL_REWARD` are constants inside `GridWorldEnv`. Config-only means they move out |
| **CartPole's reward** | `reward: builtin` — Gymnasium's, untouched | We didn't build CartPole and we can't rescore it. Pretending otherwise would be a lie in a YAML file |
| **The runner** | `scripts/train_from_profile.py`, one file | The three existing train scripts are ~80% the same code. This is the deduplication M4 *is* |
| **Old scripts** | Left alone, still runnable | They're the M1–M3 record. Deleting them to make M4 look tidy destroys evidence |

> **The one decision to confirm:** *does the profile carry the reward **numbers**, or
> just the name of a calculator?* This plan says the numbers (`step_cost: -0.01`,
> `goal_reward: 1.0`). That's what makes "config-only" real — I can retune the game
> without opening Python. The cost is that a nonsense number in YAML produces a
> nonsense game with no compiler to stop me, which is what Brick 1's validation is for.

> **See also:** `docs/m4/backpack_diagram.png` — the PRD's original `GameEnvironment`
> composition idea (§5's UML) versus what M4 actually builds. No wrapper class exists
> or is planned; `GridWorldEnv` does the eyes/hands/scorecard job directly, and
> `make_env(profile)` (Brick 3) is the only place a name becomes an object.

### The name collision (DOC_STANDARD rule 5)

Two different things in this repo were called a "profile":

- **Track A (M4, current):** `src/gametrainer/profile.py` → `Profile`. A flat YAML
  that selects a Ground + perception + reward numbers. **This is the only path now.**
- **Track B (old):** `src/gametrainer/config.py` → `ConfigLoader`. Loaded
  `profiles/<game>/regions.yaml` for the Stardew screen-scraping prototype.

**Correction — 2026-08-04:** Track B was retired (deleted), ahead of the original
"decide its fate at M5/M6" plan — user call, made outside the milestone schedule.
`env_vit.py`, `screen.py`, `interface.py`, `config.py`, `scripts/train.py`,
`play.py`, `capture_templates.py`, `check_input.py`, and `transfer_learning.py`
are gone. The name collision this section describes no longer exists; kept here,
struck through in spirit rather than deleted outright, per DOC_STANDARD rule 4.
See `docs/m4/M4_Log.md` decisions log for the full record.

---

## How we build M4: testing policy

Follows **CLAUDE.md §5**. What earns a test here:

1. **The Gymnasium contract, three times over.** Every profile must produce an env
   that `check_env` accepts and whose `reset()`/`step()` shapes are unchanged. This
   is the promise the whole project rests on, and M4 multiplies the number of ways
   to break it.
2. **Profile loading has a single right answer** — a valid file loads to the right
   values; an invalid one fails **loudly, at load time**. Red-first.
3. **Reward maths has a single right answer** — and it must produce the *exact same
   numbers* M2/M3 produced. That test is the whole safety net for moving the reward
   logic out of the env.
4. **Glue gets no test, on purpose** — the TUI menu entry, `argparse`, print
   statements. They fail loudly the first time they're run.

The boundary to guard: **the profile is a new place where a typo can silently
change the experiment.** A wrong `step_cost` doesn't crash; it quietly makes the
numbers incomparable to M3. That's why validation is a red test and not a shrug.

---

## The to-do list

| # | Brick | File(s) | Done when… |
| :--- | :--- | :--- | :--- |
| **0** | **Guardrail — write this first** | `scripts/train_from_profile.py` verdict | The swap check prints **PASS**: all profiles build, contract shapes hold, no Python edited |
| 1 | 🔴 test → `Profile` loads and validates | `tests/test_profile.py` → `src/gametrainer/profile.py` | A good YAML loads to the right fields; a bad one raises at load time, not mid-run |
| 2 | 🔴 test → `RewardCalculator` | `tests/test_rewards.py` → `src/gametrainer/rewards.py` | Same inputs → the exact M2/M3 numbers; GridWorld gets its reward from it |
| 3 | 🔴 test → `make_env(profile)` | `tests/test_make_env.py` → `src/gametrainer/factory.py` | Each of the 3 profiles builds an env `check_env` accepts |
| 4 | The three profiles | `profiles/*.yaml` | `cartpole`, `gridworld`, `gridworld_pixels` exist and load clean |
| 5 | The one runner (the experiment) | `scripts/train_from_profile.py` | Runs any profile end-to-end and prints its verdict → **Brick 0 goes PASS** |
| 6 | **Behavioural test — before closeout** | `scripts/check_swap.py` (or the runner's `--smoke`) | The swap is *proven*, not assumed — see below |
| 7 | Wire into TUI + close the docs | `tui.py`, `M4_Review.md`, `CHANGELOG.md` | DOC_STANDARD rule 7 checklist fully ticked |

Brick 0 is the finish line; Bricks 1–5 are the work; Brick 6 is the proof; Brick 7 is closing.

---

## Brick details & verify checks

### Brick 0 — The guardrail (write this FIRST)
**File:** `scripts/train_from_profile.py` (its printed verdict)

Write the bar down *before* building anything. M4 PASSes only if **all** hold:

1. **Every profile builds a legal env** — `check_env` clean, `reset()` → 2-tuple,
   `step()` → 5-tuple, obs inside `observation_space`.
2. **Each profile reaches its own bar**, stated in its own YAML — CartPole beats its
   M1 baseline; GridWorld beats its M2 bar; GridWorld-pixels reproduces M3
   (live baseline measured in the run, trained mean clearly above it, goal rate ≥ 80%).
3. **Zero Python changed between runs** — `git diff --stat` is empty across the two
   training commands. The command line is the *only* difference.

> **Verify:** run the swap check; it prints PASS with each profile's numbers and the
> proof that no source file moved.

### Brick 1 — `Profile` loads and validates
**File:** `tests/test_profile.py` → `src/gametrainer/profile.py`
- **🔴 Test first:** a known-good YAML loads to the expected field values; an unknown
  `ground:` raises with a message naming the legal options; a missing required field
  raises; a `perception: pixels` on CartPole raises (CartPole has no `rgb_array`
  Ground we've built — say so at load time, not 40 seconds in).
- A dataclass with named fields, not a bare `dict`. `profile.step_cost` should fail
  fast on a typo; `profile["step_kost"]` fails at 3am.
- **Do not** reuse Track B's `ConfigLoader` — it swallows errors and returns `{}`,
  which is the opposite of what we need.

> **Verify:** `pytest tests/test_profile.py` green; every failure message tells you
> which file and which key.

### Brick 2 — `RewardCalculator`
**File:** `tests/test_rewards.py` → `src/gametrainer/rewards.py`
- **🔴 Test first:** given "not on the goal" it returns `step_cost`; given "on the
  goal" it returns `goal_reward`; the numbers come from the profile, not from
  constants baked into the class.
- Then move `GridWorldEnv`'s reward decision to call it. **The env's behaviour must
  not change** — the existing M2/M3 tests are the proof, and they must stay green
  without being edited. If a test needs editing to pass, the refactor is wrong.
- CartPole's profile declares `reward: builtin` and no calculator is used. State that
  in the YAML comment so the asymmetry is documented where it's read, not hidden.

> **Verify:** `pytest tests/ -q` fully green with **no test file modified** except the
> new one. That's the whole safety net for this brick.

### Brick 3 — `make_env(profile)`
**File:** `tests/test_make_env.py` → `src/gametrainer/factory.py`
- **🔴 Test first:** for each of the three profiles, `make_env` returns an env that
  `check_env` accepts and whose `observation_space` is what the profile implies —
  `Box(2,)` for numeric GridWorld, `Box(0,255,(224,224,3))` for pixels, CartPole's
  own `Box(4,)` for CartPole.
- One function, one `if`-chain over known names. No dynamic `importlib`, no registry
  class, no entry points. If it's more than ~30 lines, it's doing too much.
- Wrapper order is already settled by M3 and must not drift: task/`RandomStart`
  **inside**, `PixelObservation` **outside**.

> **Verify:** the test is fast (seconds, no training) and covers all three profiles.

### Brick 4 — The three profiles
**Files:** `profiles/cartpole.yaml`, `profiles/gridworld.yaml`, `profiles/gridworld_pixels.yaml`
- Each carries: `ground`, `perception`, reward settings, PPO hyperparameters, total
  timesteps, and the **pass bar** for that profile.
- Copy the numbers from the existing scripts *exactly*. M4 is a plumbing change; if a
  hyperparameter changes here, the comparison to M3 is worthless.
- Comment the non-obvious ones in the YAML itself (why `n_epochs: 4` for pixels —
  it's the CPU cost lever, per `train_gridworld_vit.py`).

> **Verify:** all three load through `Profile` with no error, and the values match the
> old scripts line for line. Diff them by hand once; it's five minutes and it's the
> thing that makes the M3 comparison honest.

### Brick 5 — The one runner (the experiment)
**File:** `scripts/train_from_profile.py`
- `--profile profiles/gridworld_pixels.yaml` and nothing else required.
- Structure mirrors `train_gridworld_vit.py`: measure the live baseline → train →
  greedy evaluation → print the verdict, the wall-clock time, and the profile path.
- **Print the resolved profile at the top of every run.** A run whose settings you
  can't reconstruct from its own output is not a result (DOC_STANDARD rule 3).
- `--smoke` runs a few hundred steps for wiring checks; the real numbers come from a
  full run. Expect ~19 min for the pixels profile on CPU, per M3.

> **Verify (this IS the milestone "Done when"):** two full runs, two profiles, one
> unedited codebase, both printing PASS.

### Brick 6 — Behavioural test, before closeout
**File:** `scripts/check_swap.py` (or `train_from_profile.py --smoke`)

M3's lesson was that a green number can mean nothing — a "learning" agent was
actually blind. The M4 version of that trap: **a runner that looks configurable but
is really still hardcoded.** So the behavioural check needs a *negative control*, not
just a happy path:

1. **The swap is real.** Load two profiles; assert the built envs genuinely differ
   (observation space, action space, reward on an identical step). If swapping
   `perception: numeric` → `pixels` doesn't change the observation space, the profile
   isn't driving anything.
2. **The numbers are real.** Change `step_cost` in a temp profile and assert the
   reward returned by an identical step changes to match. This is the control that
   catches "the YAML is decorative and the constant is still in the class."
3. **The contract survived all of it.** `reset()`/`step()` shapes checked on every
   profile — the one promise that can never move.
4. **The suite is green** — `pytest tests/ -q`, including every M0–M3 test, unedited.
5. **The TUI runs by hand** — launch it, pick the M4 entry, watch it go. No test; it
   fails loudly.
6. **The no-edit proof** — `git status` clean between the CartPole run and the
   GridWorld run.

> **Verify:** the script prints a single PASS/FAIL, and 1–3 fail loudly if the config
> path is fake. This is the brick that earns the right to close the milestone.

### Brick 7 — TUI + close the docs
- TUI: one entry that asks which profile, then launches the runner. The old M1–M3
  entries stay (they're the record).
- `docs/m4/M4_Review.md` — results table meeting DOC_STANDARD rule 3 (number,
  baseline measured in the same run, hardware, wall-clock, seed, timesteps, command).
- `docs/CHANGELOG.md` — the M4 entry.
- Bump **Last verified** on every doc M4 changed: `PRD.md` (M4 row), `ONBOARDING.md`
  (new modules + the Track A/B profile collision), `README.md`, `CONTEXT.md`
  (its "Profile" glossary entry currently describes Track B only).
- Re-read DOC_STANDARD rule 2: no two docs may answer the same question. The new
  profile format gets exactly one home.

> **Verify:** DOC_STANDARD rule 7's four checkboxes, ticked honestly.

---

## The risk to watch

**Over-abstraction.** M4 is the milestone where "make it swappable" invites a plugin
architecture: a registry, dynamic imports, a base class per component, a schema
validator library. That would be more code than the thing it configures, and
CLAUDE.md §2 says no.

The honest size of M4: one dataclass, one small calculator, one factory function,
one runner, three YAML files. Roughly 250–350 lines total, most of it comments.
**If it passes 500, stop and delete something.**

The second risk, subtler: **a config layer that isn't really wired**. The runner
reads the YAML, prints it proudly, and then uses a hardcoded constant anyway. It
looks right and every test passes. That is exactly the M3 blind-agent failure wearing
a different hat, and Brick 6's negative control is aimed straight at it.

---

## How CLAUDE.md's working agreement applies here

The standing rules (one brick at a time, teach before coding, don't move the
finish line mid-milestone, etc.) live in `CLAUDE.md` — not repeated here. What's
M4-specific about applying them:

- **Test the promises, not the plumbing** → here: the contract per profile, profile
  validation, and reward numbers that must not drift.
- **Tests vs. experiments** → building an env is a test; training is a script.
- **Never break the Gymnasium contract** → every M0–M3 test stays green, unedited,
  the entire way through.
- **DOC_STANDARD is in force from this milestone** — every result carries its
  baseline, hardware, and wall-clock time, or it isn't a result.
