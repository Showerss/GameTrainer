# Milestone 1 Review — CartPole + Borrowed Brain (PPO)

**Date:** 2026-06-22
**Reviewer:** Claude (code + PRD audit)
**Branch:** `M1-Implementation`
**Scope:** Confirm M1 can be checked off, confirm M0 → M1 flows cleanly, log anything awry, give forward-looking design notes.

---

## TL;DR

> **M1 PASSES. You can check it off.** ✅

I ran both milestone scripts end-to-end on your machine (Python 3.14.5, CPU torch):

- **M0** (`scripts/run_cartpole.py`): ran 100 steps with random actions, no crash, mean reward ≈ **25/episode**.
- **M1** (`scripts/train_cartpole.py`): PPO trained for 25k steps, eval reward climbed **22 → 500** (CartPole's ceiling) and the script printed `✅ PASS`.

The PRD's M1 "Done when…" is: *"PPO trains on CartPole through your runner; average reward clearly rises vs. the random baseline."* That is satisfied with room to spare (500 vs a ~22 baseline, threshold was 44).

Nothing below is an M1 blocker. The issues are about **onboarding, docs, and seams that will bite at later milestones** — worth logging now while they're cheap.

---

## What "checking off M1" rests on (the evidence)

| Check | Result |
| :--- | :--- |
| Gymnasium link works | ✅ `gym.make("CartPole-v1")` reset/step loop runs |
| Borrowed brain plugs in | ✅ SB3 `PPO("MlpPolicy", ...)` trains, no code written for the algorithm |
| Reward clearly rises vs random | ✅ 500 vs ~22 baseline (threshold 44) |
| Runs through *your* runner | ✅ `train_cartpole.py` orchestrates train + eval + verdict |
| M0 baseline is documented for comparison | ✅ both scripts reference the random baseline |
| Architecture stays visible | ✅ `NullInput` is wired in even though CartPole doesn't need it |

Environment confirmed present and working: `gymnasium 1.3.0`, `stable-baselines3 2.9.0`, `torch 2.12.1+cpu`, `numpy 2.5.0`, `pygame`, `tensorboard`.

---

## M0 → M1 flow: does it connect?

**Yes, the spine is clean.** Both scripts share the same shape: add project root to `sys.path`, import `NullInput`, run the `observe → act → reward` loop, report a reward number you can compare. A learner moving from M0 to M1 sees the *same* loop with only the decision-maker swapped (random → PPO). That's exactly the teaching point of M1, and it lands.

One small seam to be aware of (not a bug — see Issue #6): the M0 script computes its baseline live (~25 this run, it varies with the random seed), while the M1 script hard-codes `22` as the baseline constant. They agree closely enough that the verdict is never in doubt.

---

## Issues found (ranked; none block M1)

### 🟡 #1 — `pip install -e .` forces a C++ compile that M1 doesn't need
**Where:** `setup.py` (lines 14–25), `README.md` install section.
**What:** On Windows, `setup.py` adds a C++ extension (`src/cpp/clib.cpp`) to the build. So `pip install -e .` tries to invoke the MSVC compiler. Two problems for a fresh setup:
  1. It needs Visual C++ Build Tools installed — a heavy, easy-to-miss prerequisite.
  2. `include_dirs=["include"]` points at an `include/` folder that **does not exist** in the repo.

**Why it matters:** M0 and M1 use *zero* C++ (the input "hands" are stubbed by `NullInput`). A learner could hit a compiler error during install and conclude the project is broken — before ever reaching the part M1 actually needs. The C++ build is M5 work intruding on M1 onboarding.
**Suggested fix (later):** Make the C++ build opt-in (e.g. an env flag or a separate extra), and document an "RL-only" path: `pip install gymnasium[classic-control] stable-baselines3 torch tensorboard`. Your current `.venv` clearly was set up this way (deps are present, but the compiled `.pyd` is stale — see #2), which is why M1 runs fine.

### 🟡 #2 — Stale prebuilt extension prints a scary warning on every M1 run
**Where:** `src/gametrainer/input.py` (lines 15–26); artifact `src/gametrainer/clib.cp311-win_amd64.pyd`.
**What:** The committed binary is tagged `cp311` (Python 3.11). Your venv is **Python 3.14**, so that file can't load. The import falls back to `MockClib` and prints:
`WARNING: C++ extension not found. Input simulation will not work.`
You can see it at the top of every `run_cartpole.py` / `train_cartpole.py` run.
**Why it matters:** It's *harmless* for M0/M1 (NullInput overrides every input method, so nothing tries to use `clib`). But the message reads like something failed, which is confusing during exactly the milestones where input doesn't matter. Also: `.gitignore` ignores `*.pyd`, so this stale binary probably shouldn't be tracked at all.
**Suggested fix (later):** Either downgrade the warning to something honest for early phases ("C++ input extension not loaded — fine for CartPole/GridWorld; needed at M5"), or suppress it unless a real `KeyboardInput` is requested. Consider removing the tracked `.pyd`.

### 🟡 #3 — The "recommended" entry point skips M1 entirely
**Where:** `README.md` Quickstart (`python main.py` is labeled *recommended*); `main.py` → `src/gametrainer/tui.py`.
**What:** The TUI's "Train" option launches `scripts/train.py` (the ViT + Stardew path, M3+), not the M1 CartPole scripts. There is no CartPole option in the menu. So the *documented first thing a beginner does* drops them into the most advanced, not-yet-ready path.
**Why it matters:** At M1, the real surface is `scripts/run_cartpole.py` and `scripts/train_cartpole.py`. The TUI points the other way. Mild beginner trap, and it slightly contradicts the PRD's "build in order, don't jump ahead" rule.
**Suggested fix (later):** Add a "Verify setup (CartPole)" + "Train CartPole" pair to the menu, or in the README mark `python main.py` as "advanced / later milestones" and keep the CartPole scripts as the M0–M1 quickstart.

### 🟢 #4 — `CONTEXT.md` contradicts the PRD
**Where:** `CONTEXT.md` vs `docs/PRD.md` §3.
**What:** `CONTEXT.md` describes a "C++ Extension (Native)" and an input "humanizing" layer as core architecture. The PRD lists **"No C++ in v1"** as an explicit non-goal and frames everything in the Ground/AI/Link metaphor. `CONTEXT.md` reads like leftover context from the project you absorbed.
**Why it matters:** You've told me the PRD is the source of truth. An AI assistant (or future-you) reading `CONTEXT.md` could re-introduce assumptions the PRD deliberately cut. Two sources of truth that disagree is a slow-acting trap.
**Suggested fix (later):** Either delete/trim `CONTEXT.md` to match the PRD, or add a one-line header: "Historical/absorbed context — `docs/PRD.md` overrides this."

### 🟢 #5 — `pytest` is documented but not installed
**Where:** `README.md` Dev tools; `tests/test_input.py`, `tests/test_logger.py`.
**What:** README says `pytest` runs the tests, but `pytest` isn't in the venv (`No module named pytest`). Not part of M1's done-criteria, just a doc/tooling gap.
**Suggested fix (later):** `pip install -e ".[dev]"` (it's already declared as an extra) or drop the line until tests are wired into the milestone flow.

### 🟢 #6 — M0 baseline is live; M1 baseline is hard-coded
**Where:** `run_cartpole.py` (computes mean ≈ 25) vs `train_cartpole.py` (`M0_RANDOM_BASELINE = 22.0`).
**What:** Two numbers for "the random baseline." They're close and 22 is a conservative choice, so the verdict is never wrong. Logging it only so you know it's intentional, not a mismatch to chase.
**Suggested fix:** None needed. (Optional: have M1 read the value M0 prints, but that's more plumbing than it's worth right now.)

### 🟢 #7 — Imports rely on `src` being an implicit namespace package
**Where:** all scripts: `sys.path.insert(0, root)` + `from src.gametrainer... import ...`; no `src/__init__.py`.
**What:** This works today (Python treats `src` as a namespace package, and we verified M1 runs). It's slightly fragile — it depends on scripts always injecting the project root and on the `src.` prefix. Fine for now; just don't be surprised if an import breaks when run from an unusual working directory or after a real editable install.

---

## Design thoughts & things I see coming

These are forward-looking — not problems today, but seams worth keeping clean so later milestones stay easy.

### 1. ⚠️ The PRD documents the *wrong* contract signature (this one's important)
The PRD §4 contract says:
```python
observation, reward, done, info = env.step(action)   # 4 values (old "gym")
```
But you're on **`gymnasium`**, whose contract is **5 values**:
```python
observation, reward, terminated, truncated, info = env.step(action)
```
Your `run_cartpole.py` already does this correctly. The risk is **M2**: when you build your own `GridWorld` "Ground", you must implement the *5-value* gymnasium API. If you follow the PRD snippet literally you'll write the old 4-value shape, SB3 will reject it, and — per the PRD's own rule #1 ("never break the contract") — you'd be breaking the one thing that matters without realizing it. **Recommendation:** fix the PRD snippet to the 5-tuple before starting M2. `terminated` (the pole fell / you reached the goal) and `truncated` (ran out of time) are different things and SB3 needs both.

### 2. `tap_key(action)` is a no-op now, but it's semantically crossed wires
Both scripts call `hands.tap_key(action)` where `action` is the gym action index (`0`/`1`). But `tap_key` is designed to take a **Windows virtual-key code** (e.g. `0x57` for W). For `NullInput` it does nothing, so it's harmless — but it quietly passes the wrong *kind* of number. When you reach **M5** (real `KeyboardInput`), you'll need a translation layer: *action index → key code*. That layer is exactly what the PRD's **`Profile.key_map`** is for. Flagging now so the seam is obvious: the runner should never hand a raw gym action to the hands; a profile should map it first.

### 3. The CartPole runner is hard-wired to one environment
`make_train_env()` hard-codes `gym.make("CartPole-v1")`. That's correct for M1. But M4's whole thesis is *"switching environments is config-only, no code edits."* When you get there, the cleanest path is a tiny **env factory** ("give me the env named in the profile") so the *same* runner drives CartPole, GridWorld, and beyond. Keeping `train_cartpole.py` simple now is right — just know that "generalize the runner" is a real future step, not something to retrofit awkwardly.

### 4. GPU plan for the Eyes (M3) needs an AMD-on-Windows answer
`hardware.py` detects `cuda` and `mps` (Apple). Your card is an **AMD RX 9070 XT on Windows**. Neither CUDA nor MPS applies there — the usual Windows-AMD path is **`torch-directml`** (or ROCm on Linux), which `hardware.py` doesn't currently handle. Not a problem until M3 (the ViT), and the PRD already says CPU is fine until then. Just don't let M3 day be the first time you discover the AMD/Windows torch story — it's the fiddliest piece in the whole plan. CartPole/GridWorld won't care.

### 5. What's solid and worth keeping
- Separate **eval environment** from the training environment — correct RL hygiene (you measure on an env the agent didn't train on).
- **Deterministic eval** reaching a clean 500 — that's a genuinely well-behaved result, not a fluke.
- Standard, sensible **PPO hyperparameters** for CartPole; no cargo-culting.
- The `__init__.py` decision to **not eager-import** heavy submodules — this is the single reason an M0 script can reach `NullInput` without dragging in torch/mss/timm. Good instinct; keep it.
- Teacher-note docstrings in the CartPole scripts are genuinely good for the "learn brick by brick" goal.

---

## What I did NOT touch

This was a review. I changed **no code** and created only this file. The fixes above are suggestions for when you choose to act on them — happy to do any of them on request. The M3+ code you absorbed (`env_vit.py`, `vit_extractor.py`, `screen.py`, `interface.py`, `train.py`, `play.py`, `transfer_learning.py`) was treated as intentionally-ahead and only skimmed for whether it could break the M0→M1 path. It can't — those modules aren't imported anywhere on the CartPole route.
