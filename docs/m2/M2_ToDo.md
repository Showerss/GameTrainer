# M2 — Build Your Own Ground (GridWorld)

> **Milestone goal (from PRD):** A `GridWorld` env obeys the Gymnasium contract;
> a random agent runs, then PPO learns to reach the goal.
>
> **Done when…** Mean reward clearly beats the random baseline and the agent
> reaches the goal consistently.

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

## The to-do list

| # | Brick | File | Done when… |
| :--- | :--- | :--- | :--- |
| 1 | Build the GridWorld env | `src/gametrainer/gridworld.py` | `check_env` passes; reset→2-tuple, step→5-tuple |
| 2 | Lock the contract with tests | `tests/test_gridworld.py` | `pytest` green (reset/step shapes, goal terminates, cap truncates) |
| 3 | Random-agent runner (baseline) | `scripts/run_gridworld.py` | Runs, prints a low/negative baseline score |
| 4 | PPO learns to reach the goal | `scripts/train_gridworld.py` | Mean reward clearly beats baseline → **M2 "Done when"** |
| 5 | Wire into TUI + changelog | `tui.py`, `docs/CHANGELOG.md` | New menu items launch the scripts |

Bricks 1–4 are the real work; Brick 5 is polish to match how CartPole is wired.

---

## Brick details & verify checks

### Brick 1 — Build the GridWorld environment
**File:** `src/gametrainer/gridworld.py`
- Subclass `gymnasium.Env`.
- Action space `Discrete(4)`; observation space `Box` holding agent `(row, col)`.
- `reset()` → agent to start, return `(observation, info)`.
- `step(action)` → move, compute reward, return `(observation, reward, terminated, truncated, info)`.
- Reward: `-0.01` per step, `+1.0` on goal.
- Ends: goal → `terminated=True`; step cap → `truncated=True`.
- `render()` → simple text print of the grid (good enough for M2).

> **Verify:** `from stable_baselines3.common.env_checker import check_env; check_env(env)`
> passes; `reset()` returns a 2-tuple and `step()` returns a 5-tuple.

### Brick 2 — Lock the contract with tests
**File:** `tests/test_gridworld.py` (mirrors `tests/test_logger.py`)
- `reset()` returns `(obs, info)`; `obs` is inside `observation_space`.
- `step()` always returns the 5-tuple.
- Walking onto the goal sets `terminated=True` and gives the goal reward.
- Exceeding the step cap sets `truncated=True`.
- `check_env` runs clean.

> **Verify:** `pytest tests/test_gridworld.py` is green.

### Brick 3 — Random-agent runner (the baseline)
**File:** `scripts/run_gridworld.py` (mirrors `scripts/run_cartpole.py`)
- Run random actions for some episodes; print **mean reward / episode** = the baseline.
- Use `NullInput` to keep the architecture visible (consistent with CartPole).

> **Verify:** runs without crashing and prints a baseline number
> (expected low/negative — random walking rarely finds the goal).

### Brick 4 — PPO learns to reach the goal
**File:** `scripts/train_gridworld.py` (mirrors `scripts/train_cartpole.py`)
- PPO with `MlpPolicy` (numbers in → small network, same as CartPole).
- Checkpoints + `EvalCallback` + a printed **PASS/FAIL verdict** vs the Brick 3 baseline.

> **Verify (this IS the milestone "Done when"):** mean reward clearly beats the
> random baseline and the agent reaches the goal consistently.

### Brick 5 — Wire it in & document
- Add GridWorld run/train options to the TUI menu (`src/gametrainer/tui.py`).
- Add an M2 entry to `docs/CHANGELOG.md`.

> **Verify:** the new menu items launch the two scripts.

---

## Rules we're keeping (from CLAUDE.md)

- **One brick at a time.** Smallest next step only; stop at each checkpoint.
- **Teach before coding.** Plain-English what & why first, then the code.
- **Never break the Gymnasium contract** (`reset()` / `step()` shapes) — it's the
  entire point of the project.
