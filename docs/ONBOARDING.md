# GameTrainer — Onboarding for a Junior Engineer

> **Covers:** orientation for someone new to this repo — what it is, why it looks
> this way, what every technology is for, and which code is current.
> **Status:** current.
> **Last verified:** 2026-09-19 (M5 closed — §5's Track A file table, §6's input
> stack description, §7's tree, §8's status table and summary, and §12's links all
> updated to match; see each section for what changed).
> **Authority:** `docs/PRD.md` owns *what gets built*; this file is the tour.
> Written to `docs/DOC_STANDARD.md`.

> **Read this first.** It explains what this project is, why it looks the way it
> does, what every technology in it is for, and — importantly — which parts of the
> code are *current* and which are *leftovers from an older plan*.
>
> Companion file: [`docs/UML_FULL.md`](UML_FULL.md) — the diagrams.

---

## 1. What is this project, in one paragraph?

GameTrainer teaches a computer to play a game by **watching, acting, and being
scored** — over and over, thousands of times, until it gets good. That's it.
The AI is never told the rules. It tries things, gets points or loses points, and
gradually keeps whatever earns points.

**But the real product is not the AI.** The real product is the **plumbing**: a
clean, standard connector between *any game* and *any AI*. If that connector is
right, you can swap the game without touching the AI, and swap the AI without
touching the game. That swappability is the entire point of the codebase.

---\n\n## 2. The mental model (learn these 3 words and you can read everything)

The project uses a fixed vocabulary. Every doc, comment, and commit uses it.

| Word | What it means | In normal terms |
| :--- | :--- | :--- |
| **Ground** | The game world | The thing being played |
| **AI** | The player | The thing doing the playing |
| **Link** | The Gymnasium API | The standard plug between them |

The **AI** is itself three separable pieces:

| Piece | Nickname | Job | What provides it |
| :--- | :--- | :--- | :--- |
| **Eyes** | Perception | Turn pixels into a summary | A Vision Transformer (ViT) or CV classifier |
| **Brain** | Agent | Decide what to do | PPO, from stable-baselines3 |
| **Hands** | InputController | Actually press the keys | A Python/Win32/Quartz input layer |

And the whole system is one loop that never changes:

```
observe  →  act  →  reward  →  repeat
```

**Build vs. borrow** — this distinction explains most design choices:

- ✅ **We build** the Ground (game worlds) and the Link (the socket + config).
- 🔄 **We borrow** the Brain (PPO) and the Eyes backbone (a pretrained ViT).

We deliberately do *not* write our own learning algorithm. That's a solved
problem; re-solving it would teach nothing and take months.

---\n\n## 3. The one contract that must never break

Everything hangs off a single interface, defined by a library called
**Gymnasium**. Every "Ground" must expose exactly these two methods:

```python
observation, info = env.reset()
observation, reward, terminated, truncated, info = env.step(action)
```

Reading that out loud:

- `reset()` — "start a fresh attempt, and show me the opening state."
- `step(action)` — "I do *this*; tell me what happened, how many points I got,
  and whether the attempt is over."
- `terminated` — the attempt ended **naturally** (goal reached, pole fell over).
- `truncated` — the attempt was **cut short** (ran out of time / step budget).

That distinction matters to the learning maths: "I lost" and "the clock ran out"
must not be treated the same.

**The rule:** if you are ever tempted to change the *shape* of `reset()` or
`step()` to make something work — don't. The moment the shape drifts, the
swappability (the whole thesis) is gone. Find another way.

---\n\n## 4. Why the project starts with toys instead of a real game

The end goal is a complex farming game (Stardew Valley). We deliberately do
**not** start there, because a real game has:

- no clean score to learn from,
- a messy screen where reading "how am I doing?" from pixels is unreliable,
- long, slow episodes that make every experiment take hours.

If you start there, you can never tell whether a failure is your plumbing, your
reward design, or your AI. So the project **earns its way up** through
milestones, each of which changes exactly one thing:

| # | Milestone | What's new | Done when… |
| :--- | :--- | :--- | :--- |
| **M0** | Setup | Prove the Link runs at all | CartPole runs 100 random steps without crashing |
| **M1** | Borrow the Brain | Random → PPO | Trained reward clearly beats the random baseline |
| **M2** | Build our own Ground | Borrowed game → our GridWorld | PPO learns to reach the goal in our own world |
| **M3** | Add the Eyes | Numbers → a *picture* + ViT | PPO still learns (slower is fine) |
| **M4** | Make it swappable | Hard-coded → config-driven | Switching games is **config-only**, no code edits |
| **M5** | Add the Hands | Fake input → real key presses | The loop drives a real game window (**VERIFIED LIVE**) |
| **M6** | *(Stretch)* Stardew | It's "just another profile" | The agent does something sensible on screen |

> **Portfolio note:** finishing **M4** already proves the whole thesis — any
> ground, any brain, one socket. M5 bridges this plumbing to live OS windows.

---\n\n## 5. ⚠️ The single most confusing thing about this repo (historical — see correction)

> **Correction — 2026-08-04.** This section originally described two generations
> of code living side by side, with Track B kept forever as reference material.
> That plan changed: **Track B was deleted.** `env_vit.py`, `screen.py`,
> `interface.py`, `config.py`, `scripts/train.py`, `play.py`,
> `capture_templates.py`, `check_input.py`, and `transfer_learning.py` are gone
> from the repo (still in git history if you need to read them). Two files the
> table below listed under Track B were **not** deleted, because they turned out
> to be shared with the live milestone path, not Stardew-exclusive:
> `src/gametrainer/input.py` (used by every M0–M2 script) and `src/cpp/clib.cpp`
> (the opt-in M5 input extension, not Stardew-specific code). Per DOC_STANDARD
> rule 4, the rest of this section is left as originally written, below, as the
> historical record of why the split existed.

**There were two generations of code living side by side.**

The project originally started as *"build the Stardew bot right now."* A lot of
code was written for that. Then the direction changed (see the pivot log in
`docs/README.md`) to the crawl-first milestone plan above. The old code was
**never deleted** — it's kept as a reference and as the future M3/M5 material.

So when you open `src/`, you were looking at two tracks at once:

### Track A — the current milestone path (M0 → M5). This is live.

| File | Role |
| :--- | :--- |
| `scripts/run_cartpole.py` | M0: random actions on a borrowed game |
| `scripts/train_cartpole.py` | M1: PPO learns CartPole |
| `src/gametrainer/gridworld.py` | M2: **our own** 5×5 game world (+ M3: draws itself) |
| `scripts/run_gridworld.py` | M2: random baseline on our world |
| `scripts/train_gridworld.py` | M2: PPO learns our world |
| `src/gametrainer/perception.py` | M3: `PixelObservation` — swaps `(row,col)` for a picture |
| `src/gametrainer/vit_extractor.py` | M3: the frozen ViT-Tiny "eyes" |
| `scripts/train_gridworld_vit.py` | M3: PPO learns from pixels only |
| `tests/test_gridworld.py` | Locks the Gymnasium contract |
| `tests/test_gridworld_pixels.py` | M3: the rendered image's shape and behaviour |
| `tests/test_pixel_observation.py` | M3: the wrapper keeps the contract |
| `tests/test_vit_extractor.py` | M3: feature width in == feature width out |
| `tests/test_random_start.py` | M3: proves the task can't be solved blind |
| `tests/test_m2_e2e.py` | The old M2 finish line — now `skip`ped (see §8) |
| `src/gametrainer/profile.py` | M4: `Profile` — a validated .yaml → Ground + reward + PPO numbers |
| `src/gametrainer/rewards.py` | M4: `RewardCalculator` — reward decision; M5: `MinesweeperRewardCalculator` |
| `src/gametrainer/factory.py` | M4: `make_env(profile)` — the one place a profile's name becomes an env |
| `profiles/*.yaml` | M4: `cartpole`, `gridworld`, `gridworld_pixels`; M5: `minesweeper` |
| `scripts/train_from_profile.py` | M4: one runner, any profile — replaces per-game train scripts |
| `scripts/check_swap.py` | M4: negative-control proof the config layer is really wired |
| `tests/test_profile.py`, `test_rewards.py`, `test_make_env.py`, `test_m4_verdict.py` | M4: profile validation, reward numbers, env-building, the referee |
| `src/gametrainer/screen.py` | M5: `GameWindow` — DPI-aware live window capture (Windows / macOS) |
| `src/gametrainer/input.py` | M5: `KeyboardInput` — real OS key injection via SendInput / Quartz |
| `src/gametrainer/minesweeper_vision.py` | M5: `read_board` — locates board and classifies 8×8 cells |
| `src/gametrainer/minesweeper.py` | M5: `MinesweeperEnv` — Gymnasium contract wrapping LibreMines |
| `scripts/check_hands.py` | M5: the 4-control live proof runner |
| `tests/test_minesweeper_vision.py`, `test_minesweeper_rewards.py`, `test_minesweeper_env.py`, `test_check_hands.py` | M5: vision, scoring, env contract, and referee unit tests |

### Track B — the older Stardew prototype. Written, but ahead of where we are.

**(deleted 2026-08-04 — table kept for historical record, see correction above)**

| File | Role | Belongs to |
| :--- | :--- | :--- |
| `src/gametrainer/env_vit.py` | A full Stardew Gym env with pixel rewards | M5 + M6 |
| `src/gametrainer/screen.py` | Screen capture (finds the game window) | M5 |
| `src/gametrainer/interface.py` | Finds UI elements by image matching | M4/M6 |
| `src/gametrainer/config.py` | Loads per-game YAML config | M4 |
| `scripts/train.py`, `scripts/play.py` | The Stardew train/play entry points | M3+ |

---\n\n## 6. Every technology, explained

### The core four (needed from day one)

**Gymnasium** — the Link. A Python library that defines the standard shape of a
"game the AI can play": `reset()`, `step()`, plus an `action_space` (the list of
legal moves) and an `observation_space` (the shape of what the AI can see). It's
an *agreement*, not an engine. Anything that follows the agreement is pluggable.
It also ships some built-in toy games, which is where CartPole comes from.

**CartPole** — a built-in Gymnasium toy game: balance a pole on a moving cart.
Four numbers in, two moves out (push left / push right), +1 point per tick you
stay alive. We use it because it is the simplest possible thing that can prove
the plumbing works.

**Stable-Baselines3 (SB3)** — the borrowed Brain. A well-tested library of
ready-made learning algorithms. We use its **PPO**.

**PPO (Proximal Policy Optimization)** — the specific learning recipe. Plain
version: the AI has a **policy** (its current strategy: "in this situation, do
that"). PPO plays a batch of attempts, sees which actions led to more reward, and
nudges the policy toward those actions. The "proximal" part means it deliberately
only nudges a *little* at a time — big jumps make RL training collapse. You do
not need to understand its maths to use this repo.

**PyTorch (`torch`)** — the numerical engine that actually runs and trains neural
networks. SB3 is built on it. You rarely touch it directly.

**NumPy** — fast arrays of numbers. Every observation in this repo is a NumPy
array.

### The vision stack (M3 & M5)

**ViT (Vision Transformer)** — the Eyes. A neural network that reads images by
cutting them into a grid of small square **patches** (16×16 pixels each) and
letting every patch "look at" every other patch directly.

**Connected Components & Tile Classification (M5)** — Computer vision for
structured board games. `src/gametrainer/minesweeper_vision.py` locates the
active board dynamically via square dark blob detection, and classifies cells
based on measured background tints (`_HIDDEN_BODY`, `_REVEALED_BODY`,
`_CURSOR_BODY`) and glyph ink color percentages.

**mss** — very fast screen capture. Grabs the game window as a BGR numpy array
many times a second without GDI overhead.

### The input stack (M5 — done)

**InputController & KeyboardInput** — the Hands. `src/gametrainer/input.py`
subclasses `InputController` to inject real OS keystrokes into live game windows.
On Windows, uses Win32 `SendInput` with import-time 40-byte `INPUT` struct size
assertions and `AttachThreadInput` foreground locking. On macOS, uses
`Quartz.CGEventPost` with virtual keycode translation and `Cmd+R` Qt mapping.

**NullInput** — a deliberately do-nothing Hands implementation. Used as the
negative control in M5 (`check_hands.py`) to prove that without real input, the
game screen does not mutate.

### Config and per-game data (M4 & M5 — done)

**YAML / PyYAML** — human-friendly config file format. Holds each profile's
Ground, reward numbers, and PPO hyperparameters.

**Profile** — loaded by `src/gametrainer/profile.py` into a validated `Profile`
dataclass, turned into a Gymnasium env by `src/gametrainer/factory.py`'s
`make_env(profile)`. Adding LibreMines (`profiles/minesweeper.yaml`) required zero
changes to the profile loading architecture.

---\n\n## 7. How the code is organised

```
GameTrainer/
├── main.py                  # entry point → launches the TUI menu
├── src/gametrainer/         # the library (importable code)
│   ├── gridworld.py         # M2/M3: our own game world, and it draws itself
│   ├── perception.py        # M3: the pixel wrapper (the "eyes" socket)
│   ├── vit_extractor.py     # M3: the frozen ViT eyes
│   ├── profile.py           # M4: Profile — a validated .yaml → Ground + reward + PPO
│   ├── rewards.py           # M4: RewardCalculator; M5: MinesweeperRewardCalculator
│   ├── factory.py           # M4: make_env(profile) — the one name→object seam
│   ├── screen.py            # ★ M5: GameWindow — DPI-aware live window capture
│   ├── input.py             # ★ M5: KeyboardInput — real key injection (+ NullInput stub)
│   ├── minesweeper_vision.py # ★ M5: read_board — tile classification
│   ├── minesweeper.py       # ★ M5: MinesweeperEnv — Gymnasium contract for LibreMines
│   ├── hardware.py          # picks CPU vs GPU
│   ├── logger.py            # timestamped logging
│   └── tui.py               # the retro menu
├── profiles/                # cartpole.yaml, gridworld.yaml, gridworld_pixels.yaml, minesweeper.yaml
├── scripts/                 # runnable entry points, one per job
│   ├── train_from_profile.py # M4: one runner, any profile
│   ├── check_swap.py        # M4: negative-control proof the config is real
│   └── check_hands.py       # ★ M5: 4-control proof driving a live window
├── tests/                   # pytest suite (102 passed, 1 skipped)
└── docs/                    # PRD, changelog, per-milestone notes + UML

★ = current milestone
```

---\n\n## 8. Where the project actually stands today

**Current branch:** `m5-implementation`. **Last milestone closed:** M5.

Done and working:

| # | Milestone | Result | Conditions |
| :--- | :--- | :--- | :--- |
| **M0** | Setup | CartPole runs 100 random steps, no crash. Baseline ≈ **22**/episode | CPU |
| **M1** | Borrow the Brain | Reward **22 → 500** (500 is CartPole's ceiling) | CPU, PPO `MlpPolicy`, 25k steps |
| **M2** | Build our own Ground | Trained **+0.93**, goal reached **20/20** greedy episodes | CPU, PPO `MlpPolicy`, 25k steps |
| **M3** | Add the Eyes | Live baseline **+0.48** → trained **+0.99**, goal reached **100%** of greedy episodes | CPU, frozen `vit_tiny_patch16_224`, **19.2 min** |
| **M4** | Make it swappable | All 3 profiles PASS through **one unedited runner**; 4/4 negative controls PASS (`scripts/check_swap.py`) | CPU, config-only — zero Python edits between runs |
| **M5** | Add the Hands | 4/4 controls PASS live on macOS (16.8s) and Windows (22.4s); 20/20 unattended resets clean with 0 mouse clicks (`scripts/check_hands.py`) | CPU, real desktop window (`LibreMines`) |

---\n\n## 9. How to run it

```bash
# Install
pip install -e ".[rl]"

# The menu — easiest way in
python main.py

# Milestone M5 proof — drives live LibreMines window
python scripts/check_hands.py

# Tests and lint
pytest
ruff check .
```

---\n\n## 10. Design decisions and the reasoning behind them

| Decision | Why |
| :--- | :--- |
| **Gymnasium contract is sacred** | It's the one thing that makes games and brains interchangeable. Bend it once and the project's thesis is dead. |
| **Borrow PPO, don't write it** | RL algorithms are a solved, subtle, easy-to-get-silently-wrong problem. The interesting work is the plumbing. |
| **Toys before real games** | On CartPole a failure means *your code* is broken. On Stardew a failure could be anything. Debuggability first. |
| **Pixels in, actions out** | No reading game memory, no patching the process. Keeps the AI's inputs human-like — and keeps the project honest and portable. |
| **ViT over CNN** | Global attention relates distant UI regions (energy bar ↔ hotbar) without stacking many layers. |
| **CPU-first** | CartPole and GridWorld train fine on a CPU. GPU only matters at M3. Don't let GPU driver pain block week 1. |
| **Windows SendInput & macOS Quartz** | Directly interface with OS event queues to ensure uncooperative games receive keystrokes without focus loss. |
| **Reward from state grids, not pixels (M5)** | Comparing classified 8×8 cell grids prevents pixel-noise exploit loops. |

---\n\n## 11. Known risks and honest weak spots

- **Vision computation sets the step rate ceiling.** `read_board` takes ~133 ms per frame on CPU across a maximized 1440p window (~7 steps/s). Future milestones should crop immediately to the board bounding box.
- **LibreMines reset animation timing.** Qt reset fade takes ~0.25s; stepping too quickly before the animation completes produces transient mid-fade frames.
- **Ambient desktop interaction.** Tests calling live factory auto-discovery should inject mock hands to prevent accidentally picking up active user windows.

---\n\n## 12. Where to go next

| You want… | Read |
| :--- | :--- |
| The authoritative plan | `docs/PRD.md` |
| The diagrams | [`docs/UML_FULL.md`](UML_FULL.md) |
| Milestone 5 details & retrospective | `docs/m5/M5_Log.md` and `docs/m5/M5_Review.md` |
| What has changed and when | `docs/CHANGELOG.md` |
| Per-milestone snapshots | `docs/m0/`, `docs/m1/`, `docs/m2/`, `docs/m3/`, `docs/m4/`, `docs/m5/` |
| How to work in this repo | `CLAUDE.md` (working agreements) |
| How docs must be written | `docs/DOC_STANDARD.md` |
