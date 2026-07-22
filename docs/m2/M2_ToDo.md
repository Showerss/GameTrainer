# M2 — Build Your Own Ground (GridWorld)

> **Milestone goal (from PRD):** A `GridWorld` env obeys the Gymnasium contract;
> a random agent runs, then PPO learns to reach the goal.
>
> **Done when…** Mean reward clearly beats the random baseline and the agent
> reaches the goal consistently — captured as the **Brick 0 guardrail printing
> PASS** (see "How we build M2", below).

This is the first milestone where we **build a Ground** instead of borrowing one.
CartPole (M0/M1) was borrowed; GridWorld is ours. The `reset()` / `step()` shape
stays identical to CartPole — that sameness *is* the whole point of the project.


---

## Scope discipline (what M2 is NOT)

Keep M2 lean. The following belong to later milestones — do **not** build them now:

- ❌ No `Profile` / no `RewardCalculator` abstraction (that's M4 — config-only swapping).
- ❌ No ViT / pixels / `VisionPerception` (that's M3 — "add the eyes").
- ❌ No C++, no screen capture, no real key presses (M5).

GridWorld for M2 is a plain `gymnasium.Env` with its reward logic written
**directly inside it**. Numbers in, numbers out.

---

## GridWorld spec (decided)

| Setting | Choice |
| :--- | :--- |
| **Grid** | 5×5 |
| **Start** | top-left `(0, 0)` — fixed |
| **Goal** | bottom-right `(4, 4)` — fixed |
| **Actions** | `Discrete(4)` → up / down / left / right (walking into a wall = stay put) |
| **Observation** | `Box` of the agent's `(row, col)` — two numbers |
| **Reward** | `-0.01` per step, `+1.0` on reaching the goal |
| **Ends** | on goal → `terminated`; after a step cap (100) → `truncated` |

Design choices made: **fixed goal** (agent learns one reliable path) and
**coordinate observation** (truly "numeric perception" — the cleanest contrast
for when M3 swaps in a picture + ViT).

---

## How we build M2: test-first (TDD)

**TDD (test-driven development)** = write a small test that *fails first* (we call
that **red**), then write just enough code to make it *pass* (**green**). The test
is the spec; the code chases the test.

M2 follows the project testing policy (see **CLAUDE.md §5**), which comes down to
three rules:

1. **The finish line is written down first (Brick 0).** One whole-slice check for
   the entire M2 vertical: build GridWorld → train PPO → reach the goal and beat
   the random baseline. It's the North Star — **M2 is "done" when this passes.**

2. **Bricks with a right answer open with a narrow red test.** Before touching the
   implementation, write one small failing test that pins down just *that* brick's
   job, then make it pass. Narrow = one thing (a shape, a number, a transition),
   not the whole world. This covers the env and its rules.

3. **Bricks that are glue get no test, on purpose.** Menu wiring and print
   statements fail loudly the first time you run them; a test there costs more than
   the bug it would catch. Skipping is a decision — the to-do records *why*.

> Plain version: Brick 0 says *where* we're going; the narrow tests are the
> *stepping stones*. We don't write real logic without a red test asking for it —
> but we don't perform the ritual on plumbing either.

**One important distinction.** Brick 0 trains a neural network, so it is an
**experiment**, not a test: it's slow, and it's random enough to pass one day and
fail the next on identical code. Experiments live in a **script that prints a
PASS/FAIL verdict** (`scripts/train_gridworld.py`), run by hand at the end of the
milestone — not in the `pytest` suite that runs on every change.

---

## The to-do list

| # | Brick | File(s) | Done when… |
| :--- | :--- | :--- | :--- |
| **0** | **E2E guardrail — write this first** | `scripts/train_gridworld.py` verdict | The whole-slice run prints **PASS**: mean reward clearly beats the random baseline and the agent reaches the goal. **This closes M2.** |
| 1 | 🔴 narrow test → build the env | `tests/test_gridworld.py` → `src/gametrainer/gridworld.py` | contract test written first; `check_env` passes; reset→2-tuple, step→5-tuple |
| 2 | Broaden the contract tests | `tests/test_gridworld.py` | `pytest` green (goal terminates, step-cap truncates, obs in space) |
| 3 | 🔴 narrow test → random baseline | `tests/test_run_gridworld.py` → `scripts/run_gridworld.py` | smoke test pins the runner; script prints a low/negative baseline |
| 4 | 🔴 narrow test → PPO learns the goal | `tests/test_train_gridworld.py` → `scripts/train_gridworld.py` | mean reward clearly beats baseline → **Brick 0 prints PASS** |
| 5 | Wire into TUI + changelog | `tui.py`, `docs/CHANGELOG.md` | New menu items launch the scripts |

Brick 0 is the guardrail; Bricks 1–4 are the real work; Brick 5 is polish to match
how CartPole is wired.

> **Honest note:** Brick 1's env is already committed from our first pass, so we
> write its narrow test *now* to lock it. Every brick from here on is genuinely
> test-first (red before code).

---

## Brick details & verify checks

### Brick 0 — End-to-end guardrail (write this FIRST)
**File:** `scripts/train_gridworld.py` (its printed verdict)
- One run that walks the whole M2 slice: make `GridWorldEnv` → train PPO on a
  *real* budget → evaluate → print PASS/FAIL on whether mean reward beats the
  random baseline **and** the agent reaches the goal within the step cap.
- Write the bar down *now*, before the work: that's what makes it a guardrail.
- This is the contract for the *whole milestone*, the same way `check_env` is the
  contract for a single env.

> **Why a script and not a `pytest` test:** training is slow and random, so as a
> test it would be flaky and we'd learn to skip it. As a script with a verdict, it
> stays honest — we run it deliberately, once, and read the number.

> **Verify:** run the script; it prints **PASS** with the mean reward and goal rate
> beside the baseline it had to beat.

### Brick 1 — Build the GridWorld environment
**File:** `tests/test_gridworld.py` (narrow test) → `src/gametrainer/gridworld.py`
- **🔴 Test first:** write the narrow contract test — `reset()` returns a 2-tuple
  with `obs` inside `observation_space`, `step()` returns a 5-tuple. (The env is
  already committed, so this test locks existing behavior; from Brick 3 on we
  write the test before any code exists.)
- Subclass `gymnasium.Env`.
- Action space `Discrete(4)`; observation space `Box` holding agent `(row, col)`.
- `reset()` → agent to start, return `(observation, info)`.
- `step(action)` → move, compute reward, return `(observation, reward, terminated, truncated, info)`.
- Reward: `-0.01` per step, `+1.0` on goal.
- Ends: goal → `terminated=True`; step cap → `truncated=True`.
- `render()` → simple text print of the grid (good enough for M2).

> **Verify:** `from stable_baselines3.common.env_checker import check_env; check_env(env)`
> passes; `reset()` returns a 2-tuple and `step()` returns a 5-tuple.

### Brick 2 — Broaden the contract tests
**File:** `tests/test_gridworld.py` (mirrors `tests/test_logger.py`)
Builds on Brick 1's narrow test — adds the rest of the contract:
- Walking onto the goal sets `terminated=True` and gives the goal reward.
- Exceeding the step cap sets `truncated=True`.
- `check_env` runs clean.

> **Verify:** `pytest tests/test_gridworld.py` is green.

### Brick 3 — Random-agent runner (the baseline)
**File:** `tests/test_run_gridworld.py` (narrow test) → `scripts/run_gridworld.py`
- **🔴 Test first:** write a small smoke test — calling the runner over a few
  episodes returns a single `float` mean reward (no crash, right type). Watch it
  fail (the script doesn't exist yet), then build the script to make it pass.
- Run random actions for some episodes; print **mean reward / episode** = the baseline.
- Use `NullInput` to keep the architecture visible (consistent with CartPole).

> **Verify:** runs without crashing and prints a baseline number
> (expected low/negative — random walking rarely finds the goal).

### Brick 4 — PPO learns to reach the goal
**File:** `tests/test_train_gridworld.py` (narrow test) → `scripts/train_gridworld.py`
- **🔴 Test first:** write a narrow test — a *short* PPO run returns a trained
  model plus a numeric mean reward (and a PASS/FAIL verdict object). Keep the
  training budget tiny here; this test pins the *shape* of the output, not the
  learning quality. The learning quality is what the **Brick 0 guardrail** judges.
- PPO with `MlpPolicy` (numbers in → small network, same as CartPole).
- Checkpoints + `EvalCallback` + a printed **PASS/FAIL verdict** vs the Brick 3 baseline.

> **Verify (this IS the milestone "Done when"):** mean reward clearly beats the
> random baseline and the agent reaches the goal consistently — which is exactly
> what the **Brick 0 guardrail** prints. Run it; read PASS; M2 closes.

### Brick 5 — Wire it in & document
- Add GridWorld run/train options to the TUI menu (`src/gametrainer/tui.py`).
- Add an M2 entry to `docs/CHANGELOG.md`.

> **No narrow test here (on purpose):** unit-testing TUI menu wiring is low-value
> and brittle. The Brick 0 e2e guardrail already proves the slice works; this
> brick's check is a manual one — launch the menu items and watch them run.

> **Verify:** the new menu items launch the two scripts.

---

## Rules we're keeping (from CLAUDE.md)

- **One brick at a time.** Smallest next step only; stop at each checkpoint.
- **Teach before coding.** Plain-English what & why first, then the code.
- **Red before green — where it fits.** Bricks with a right answer (env rules,
  rewards, contract shapes) start with a small failing test. Glue bricks don't;
  see CLAUDE.md §5.
- **Test the promises, not the plumbing.** The Gymnasium contract is the promise.
- **Don't move the finish line mid-milestone.** A better standard applies to the
  *next* milestone, not backwards onto finished work.
- **Never break the Gymnasium contract** (`reset()` / `step()` shapes) — it's the
  entire point of the project.
