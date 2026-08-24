# Changelog


> **Covers:** every change to this project, newest first.
> **Status:** current. **Last verified:** 2026-08-14 (M4 milestone entry added;
> all earlier entries reconfirmed accurate).
> **Authority:** this file owns *what happened and when*. `docs/PRD.md` owns *what
> gets built next*. Written to `docs/DOC_STANDARD.md`.

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

**Important:** When maintaining this file, only **append** new entries. Never overwrite or remove existing changelog content.

Milestone entries are newest-first. Work predating the milestone scheme is
preserved at the **bottom** of this file under *Pre-milestone*.

---

## [M4] — Make It Swappable (`Profile` + `RewardCalculator`)

M1–M3 each proved one thing could be swapped (the brain, then the Ground, then the
sense organ). M4 proves the **whole Ground** is swappable: one runner, one
borrowed brain, and the *only* thing separating CartPole from GridWorld-through-
pixels is which `.yaml` file gets passed on the command line. This is the
milestone the PRD calls the portfolio win condition — any ground, any brain, one
socket. Full brick-by-brick record: `docs/m4/M4_Log.md`. Retrospective:
`docs/m4/M4_Review.md`.

### Added

- **`Profile` (`src/gametrainer/profile.py`):** a frozen dataclass loaded from a
  flat `.yaml` file — names a Ground (`cartpole`/`gridworld`), a perception mode
  (`numeric`/`pixels`), reward numbers, all seven PPO hyperparameters, and the
  pass bar. Validates on load and raises loudly, naming the file and the bad
  field, rather than failing silently mid-run.
- **`RewardCalculator` (`src/gametrainer/rewards.py`):** the one-line reward
  decision (`step_cost` vs. `goal_reward`) pulled out of `GridWorldEnv` so a
  `Profile` can hand it different numbers. `GridWorldEnv`'s own behaviour is
  byte-for-byte unchanged — its `STEP_COST`/`GOAL_REWARD` constants still feed the
  calculator when nothing else is passed in.
- **`make_env(profile)` (`src/gametrainer/factory.py`):** the one place a
  `Profile`'s name becomes a Gymnasium env — a single `if`-chain over the three
  `(ground, perception)` pairs the project supports, no registry, no dynamic
  imports.
- **Three profiles (`profiles/*.yaml`):** `cartpole.yaml`, `gridworld.yaml`,
  `gridworld_pixels.yaml`. Every PPO/reward number copied verbatim from the
  M1–M3 scripts; the one structural difference is `margin_over_baseline`, which
  re-expresses each script's own absolute pass bar in one shared shape (*live
  baseline + margin*) so a single referee can grade all three.
- **The runner (`scripts/train_from_profile.py`):** loads a profile, builds the
  env, measures the live random baseline, trains PPO with the profile's own
  hyperparameters, evaluates greedily, and prints a PASS/FAIL verdict — plus the
  **source fingerprint**, a SHA-256 over every tracked *and* untracked `.py` file,
  so two runs claiming "nothing but the profile changed" can actually be checked,
  not just asserted. `--smoke` runs a few hundred steps for a fast wiring check.
- **The behavioural swap check (`scripts/check_swap.py`):** four negative
  controls, run in seconds — swapping profiles genuinely changes observation
  space, action space, and reward on an identical step; changing `step_cost` in
  YAML genuinely changes the reward paid; `reset()`/`step()` contract holds on
  every shipped profile; the full test suite stays green. Exists to catch a
  config layer that *looks* wired but secretly still uses a hardcoded constant —
  the M3 "blind agent" failure wearing a different hat.
- **TUI entry (`src/gametrainer/tui.py`):** `[6] Train from profile - config-only,
  pick the game (M4)` — asks which profile, then launches the same runner above.
  Play/Changelog/Deps/Quit renumbered `7`–`10` accordingly; the M0–M3 entries
  `[1]`–`[5]` are untouched.
- **Results:** all three profiles PASS through the one unedited runner — CartPole
  (baseline `+20.88` → trained `+500.00`), GridWorld numeric (baseline `-0.14` →
  trained `+0.93`), GridWorld pixels (baseline `+0.46` → trained `+0.99`, 100%
  goal rate — reproduces M3's `+0.99` almost exactly). Full table with every run,
  including one FAIL, in `docs/m4/M4_Review.md`.

### Fixed

- **The swap proof didn't cover its own files.** `source_fingerprint()`'s first
  version hashed only `git ls-files` (tracked files), so brand-new, uncommitted
  code — including the runner and its own test — was invisible to the fingerprint
  it was supposed to protect. Two runs of genuinely different code could have
  printed the same hash and claimed the swap was proven. Fixed with `git ls-files
  -c -o --exclude-standard` (tracked + untracked, minus `.gitignore`); pinned by
  `test_fingerprint_covers_uncommitted_files` so it can't regress silently.
- **`float | None` syntax broke the Mac's Python 3.9 venv.** Brick 0 used PEP 604
  union syntax, which needs Python 3.10+; it ran fine on the Windows 3.14 box it
  was built on but took the entire test suite down on the Mac's 3.9.6 `.venv`
  (matching `setup.py`'s stated minimum). Fixed with `from __future__ import
  annotations`, same pattern already used in `hardware.py`/`tui.py`.

### Documentation

- `docs/m4/M4_Review.md` — **new**, the retrospective, written last.
- `docs/PRD.md` — gained a DOC_STANDARD status header (it had none — a
  pre-existing gap the milestone closeout audit caught, not an M4 regression);
  §5's UML diagram corrected in place (dated note, not a rewrite) to say the
  `GameEnvironment` wrapper class it shows was never built — `make_env(profile)`
  does that job as a function instead.
- `docs/ONBOARDING.md` — §5's Track A file table, §7's tree, and §8's results
  table gained the seven new M4 modules and M4's row; §6's "Profile" description
  (previously described the old, never-wired Track B design) rewritten to
  describe what M4 actually built.
- `CONTEXT.md`, `docs/README.md` — re-verified accurate (both already correct
  since the 2026-08-04 Track B retirement), `Last verified` bumped.

---

## 2026-08-08 — Added CI; docs audit (mid-M4, not a milestone close)

A documentation audit found several `.md` files whose "Last verified" header no
longer matched their content (`ONBOARDING.md`, `CONTEXT.md`, `UML_FULL.md`,
`README.md`, this file), plus an untracked `docs/.DS_Store`, an unlinked
`docs/m4/backpack_diagram.png`, and a stale docstring in `tests/test_m2_e2e.py`
(described the retired `xfail` scheme instead of the current
`@pytest.mark.skip`). All corrected in place per `docs/DOC_STANDARD.md` rule 4 —
see each file's own header/note for what changed.

### Added

- **`.github/workflows/tests.yml`:** runs `pytest -q` on Python 3.9 (this
  project's stated minimum) on every push/PR. Resolves the open question in
  `docs/m4/M4_Log.md` about what gate would have caught the Copilot Autofix
  syntax error that broke `main` on 2026-07-29 — a pre-push hook wouldn't have,
  since that commit was a bot-authored merge, not a local push. Deliberately
  does **not** run `ruff check .`: doing so surfaced 52 pre-existing findings
  (`I001`, `RUF059`, `BLE001`, `UP045`, and others) unrelated to this audit,
  most likely from `ruff` version drift since `ruff.toml` pins no rule set and
  no `ruff` version — `setup.py`'s `dev` extra doesn't even list `ruff` as a
  dependency, despite it being the project's actual linter (see
  `docs/README.md`'s archive note, which already corrects the outdated
  `black`/`mypy` reference). Both are real gaps, left for a future brick rather
  than fixed here.

---

## 2026-08-04 — Track B retired (mid-M4, not a milestone close)

Deleted the old Stardew-first prototype (Track B — see `docs/ONBOARDING.md` §5)
entirely, ahead of the original "decide its fate at M5/M6" plan. User's explicit
call: the crawl-first pivot happened months ago and the old code was no longer
serving as useful reference.

### Removed

- `src/gametrainer/env_vit.py`, `screen.py`, `interface.py`, `config.py`
- `scripts/train.py`, `play.py`, `capture_templates.py`, `check_input.py`, `transfer_learning.py`
- The TUI's "Train ViT agent on Stardew" menu entry (`src/gametrainer/tui.py`)

`src/gametrainer/vit_extractor.py` and `input.py` were **not** deleted — both are
shared with the live M0–M3 scripts, not Track B-exclusive. `src/cpp/clib.cpp` was
also kept — it's generic M5 input-injection scaffolding, not Stardew-specific.

### Changed

- **`main.py`:** the `train`/`play` CLI shortcuts pointed at the now-deleted
  Track B scripts, with no Track A replacement yet (that's M4 Brick 5). They now
  print a clear "not available yet" message instead of erroring on a missing file.
- **TUI (`src/gametrainer/tui.py`):** menu renumbered after removing the Track B
  entry; "Play (inference)" now says plainly that it isn't wired up yet, for the
  same reason.

### Documentation

- Corrected `docs/m4/M4_ToDo.md` (name-collision section), `docs/m4/M4_Log.md`
  (decisions log), `docs/ONBOARDING.md` §5, `docs/README.md`, and `CONTEXT.md`
  to stop describing Track B as present-tense current or "kept forever" — all
  four now carry dated corrections rather than silent rewrites, per
  `docs/DOC_STANDARD.md` rule 4.

---

## [M3] — Add the Eyes (GridWorld through a ViT)

M2 handed PPO two numbers, `(row, col)`. M3 hands it a **picture** of the same
world and nothing else. Same Ground, same borrowed brain, same Gymnasium
contract — the only thing that changed is the **sense organ** in between. PPO
was not touched.

### Added

- **GridWorld draws itself (`src/gametrainer/gridworld.py`):** `render_mode="rgb_array"` returns a `(224, 224, 3)` uint8 image of the board — the 5×5 grid upscaled, blocky on purpose, because pretrained ViTs expect exactly 224×224. The existing text renderer is unchanged and stays the default. Tests in `tests/test_gridworld_pixels.py`.
- **Pixel observation wrapper (`src/gametrainer/perception.py` → `PixelObservation`):** A `gymnasium.ObservationWrapper` that swaps the observation from `(row, col)` to the image. `GridWorldEnv` is never edited and never learns the wrapper exists, so M2's tests stayed green untouched. The agent can no longer see its coordinates **at all** — that's the point. Tests in `tests/test_pixel_observation.py`.
- **ViT feature extractor (`src/gametrainer/vit_extractor.py` → `ViTTinyFeaturesExtractor`):** One 224×224 picture in, 192 numbers out, using a pretrained `vit_tiny_patch16_224` with the backbone **frozen** (0 trainable parameters — borrowed eyes stay borrowed). Chosen over ViT-Base (86M params) because M3 runs on CPU. Test asserts the width PPO reads matches the width the extractor actually produces. Adds `timm` to the `rl` extra in `setup.py`.
- **Vision task wrappers (`src/gametrainer/gridworld.py` → `RandomStart`, `make_vision_task`):** A GridWorld that **cannot be solved without looking** — random start square, goal moved to the centre, 25-move budget. Built as wrappers only; `GridWorldEnv` itself is still unedited. Tests in `tests/test_random_start.py` assert that a blind agent and a random agent both fail here, so the flaw below cannot silently return.
- **Pixels-only training script (`scripts/train_gridworld_vit.py`):** `PPO("CnnPolicy", ...)` with `policy_kwargs` pointing at the frozen ViT. Measures the random baseline **live every run** (M2 hardcoded `-0.3`, and that number was wrong), trains, evaluates greedily, then prints a PASS/FAIL verdict plus wall-clock time. **Result: PASS** — live baseline `+0.48`, trained `+0.99`, goal reached in **100%** of greedy episodes, `reset()`/`step()` shapes unchanged, 19.2 min on CPU.

### Fixed

- **GridWorld was solvable blind.** The first pixels-only run scored `+0.905` and looked like a win, but the agent never used the picture: its action probabilities were identical on every square — a fixed 53% DOWN / 47% RIGHT coin flip — and a hand-written blind agent matched it at `+0.907`. With the goal in a corner, "down or right" wins from anywhere, because walls stop you instead of costing you the run. The fault was the **Ground**, not the eyes; fixed by `make_vision_task()` above.

  > **Citation corrected 2026-07-27.** This entry previously read "Diagnostic
  > scripts archived in `docs/m3/experiments/`". That directory no longer exists —
  > the diagnostics (a blind control agent, a blind-vs-sighted sweep across four
  > task designs, and a step-budget calibration) and the raw run logs were removed
  > in commit `fefadfb` when M3 closed. They are recoverable from `fefadfb^` if the
  > result is ever challenged. The finding itself is preserved **here**, in
  > `docs/m3/GameTrainer_5_M3_Review.pdf`, and — most durably — in
  > `tests/test_random_start.py`, which fails if the flaw ever returns.

### Changed

- **TUI menu (`src/gametrainer/tui.py`):** Added `[5] Train GridWorld with ViT eyes - pixels only (M3)`, which launches `scripts/train_gridworld_vit.py`. The old `[5] Train ViT agent` (the Stardew Track B reference script) moved to `[6]` and is relabelled so it no longer claims to be M3; Play/Changelog/Deps/Quit renumbered accordingly.

---

## [M2] — Build Your Own Ground (GridWorld)

First milestone where we **build** a Ground instead of borrowing one. GridWorld is
ours, but it obeys the exact same Gymnasium contract as CartPole, so the borrowed
PPO brain plugs in unchanged — that swappability is the whole point.

### Added

- **GridWorld environment (`src/gametrainer/gridworld.py`):** A 5×5 walk-to-the-goal `gymnasium.Env`. Start fixed at `(0,0)`, goal fixed at `(4,4)`. `Discrete(4)` actions (up/down/left/right; walking into a wall stays put), `Box` observation of the agent's `(row, col)`. Reward `-0.01` per step, `+1.0` on the goal; episodes `terminated` on the goal and `truncated` at a 100-step cap. Reward logic lives directly inside the env (no Profile/RewardCalculator abstraction yet — that's M4).
- **GridWorld contract tests (`tests/test_gridworld.py`):** Lock the Gymnasium contract — `reset()` returns `(obs, info)` with `obs` inside the observation space, `step()` returns the 5-tuple, reaching the goal sets `terminated` with the goal reward, exceeding the step cap sets `truncated`, and `stable-baselines3`'s `check_env` runs clean (skips gracefully if SB3 isn't installed).
- **GridWorld random baseline runner (`scripts/run_gridworld.py`):** Runs a random agent for 20 episodes and prints the mean reward per episode — the M2 baseline that PPO must beat (~`-0.3`; random walking wastes steps on the small grid). Wires in `NullInput` to keep the eyes→brain→hands shape visible, consistent with `run_cartpole.py`.
- **GridWorld PPO training script (`scripts/train_gridworld.py`):** Trains a `stable-baselines3` PPO agent with `MlpPolicy` on GridWorld for 25,000 timesteps (configurable via `--steps`). Uses `EvalCallback` to log mean reward every 2,000 steps and `CheckpointCallback` to save models to `models/ppo_gridworld/`. Prints a pass/fail verdict comparing the best mean reward against the random baseline (pass threshold `+0.5`) plus a greedy 20-episode goal-reach check. A `--render` flag prints the learned path step-by-step at the end. **Expected:** with sufficient training, PPO should learn the optimal 8-step path (mean reward near `+0.93`) and reach the goal consistently.

### Changed

- **TUI menu (`src/gametrainer/tui.py`):** Added two M2 options — `[3] Run GridWorld` (random baseline) and `[4] Train GridWorld` (PPO) — that launch the two scripts above. Subsequent menu items (ViT/Play/Changelog/Deps/Quit) renumbered accordingly.

---

## [M1] — Borrow the Brain

### Added

- **CartPole PPO training script (`scripts/train_cartpole.py`):** New focused training script for Milestone M1. Trains a `stable-baselines3` PPO agent with `MlpPolicy` on `CartPole-v1` for 25,000 timesteps (configurable via `--steps`). Uses `EvalCallback` to log mean reward every 2,000 steps and `CheckpointCallback` to save models to `models/ppo_cartpole/`. Prints a clear pass/fail verdict at the end by comparing the best mean reward against the M0 random baseline (~22 reward/episode). Includes a `--render` flag to watch evaluation episodes live.

### Changed

- **Baseline stats in `scripts/run_cartpole.py`:** Added per-episode reward tracking (episodes completed, mean reward per episode) to the output summary. The docstring now notes that this mean reward is the M0 random-action baseline that M1 must beat. The 100-step random loop itself is unchanged.
- **Quickstart docs (`docs/README.md`):** Added M0 and M1 quickstart sections and a TensorBoard tip for `logs/cartpole`.

---

## Pre-milestone — work before the changelog adopted milestone sections

> **Moved, not rewritten (2026-07-27).** This section was previously titled
> `[Unreleased]` and sat at the **top** of this file, above M3. That put the
> project's oldest work in front of its newest and implied the entries were
> pending rather than long since shipped. The content below is unchanged,
> word for word.
>
> **Read it with three caveats:**
>
> - Most of it describes **Track B** — the Stardew-first prototype that predates
>   the crawl-first plan (see `docs/ONBOARDING.md` §5). `StardewViTEnv`,
>   `env_vit.py` and `transfer_learning.py` are *not* on the current path.
> - **Two entries are still live:** `hardware.py` (device picker) and `tui.py`
>   (the retro menu, since extended through M3).
> - Every document named under *Documentation* — `architecture.md`, `design.md`,
>   `tasks.md`, `PROJECT_OVERVIEW.md`, `docs/AGENTS.md` — **no longer exists.**
>   These entries are a record of work done, not a guide to files you can open.

### Fixed

- **Package imports (`src/gametrainer/__init__.py`):** Replaced broken import from non-existent `env_legacy` with `env_vit`. Package now exports `StardewViTEnv` instead of `StardewEnv`. Docstring updated to list actual modules (env_vit, interface, vit_extractor, etc.).
- **Script import (`scripts/transfer_learning.py`):** Replaced import from non-existent `env` module with `src.gametrainer.env_vit.StardewViTEnv`. Added comment that transfer-learning concepts apply to ViT.
- **Test import (`tests/test_logger.py`):** Fixed incorrect path and module. Replaced `sys.path` to `src/python` and `from core.logger import Logger` with project root and `from src.gametrainer.logger import Logger` so the test runs against the actual package.

### Added

- **Action validation in `StardewViTEnv.step()`:** Actions are now validated and clamped to the valid range `[0, action_space.n - 1]` (as int) before execution. Prevents silent no-ops or errors when the policy returns an out-of-range value (e.g. from a mismatched loaded model).
- **Hardware/accelerator detection (`src/gametrainer/hardware.py`):** Added a device picker and a startup banner so training/play runs choose the best available accelerator (CUDA / MPS / CPU) without hard-requiring CUDA.
- **Retro TUI launcher (`src/gametrainer/tui.py`):** Added a retro-style menu (version/author, changelog view, Train, Play) and updated `main.py` so running `python main.py` launches the TUI by default.

### Documentation

- **Design/architecture alignment:** `architecture.md` and `design.md` were updated to describe the current RL implementation (ViT + PPO, Python screen/input, C++ input only). Original (unimplemented) design kept as a reference section. `tasks.md` was updated with an alignment note and current next steps; backlog items from the original design marked as reference only.

- **PROJECT_OVERVIEW.md overhaul:** Rewritten as the single narrative for both humans and AI (CS-student friendly). Removed all decision-tree wording and the “run using local decision trees” workflow; clarified that the bot runs on the trained PPO+ViT model only. Fixed architecture diagram (three clear boxes; core engine no longer lists “Decision tree executor”). Action space updated to match code (12 discrete actions with correct indices). Dependencies updated: removed ffmpeg; input described as C++ SendInput (`clib`), not pyadirectinput; GUI (tkinter) and setup/installer called out as aspirational. Profile section reframed: profiles are for per-game config when wired in; current run path is train → save model → play from model. Build & Run now includes `pip install -e ".[rl]"` for the RL stack.

- **Docs consolidation and glossary:** Consolidated docs into `docs/README.md` + `docs/AGENTS.md` + `docs/CHANGELOG.md` and added a glossary section defining common acronyms (RL, PPO, ViT, SB3, VRAM, etc.).
