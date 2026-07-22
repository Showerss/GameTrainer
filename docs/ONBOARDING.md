# GameTrainer — Onboarding for a Junior Engineer

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

---

## 2. The mental model (learn these 3 words and you can read everything)

The project uses a fixed vocabulary. Every doc, comment, and commit uses it.

| Word | What it means | In normal terms |
| :--- | :--- | :--- |
| **Ground** | The game world | The thing being played |
| **AI** | The player | The thing doing the playing |
| **Link** | The Gymnasium API | The standard plug between them |

The **AI** is itself three separable pieces:

| Piece | Nickname | Job | What provides it |
| :--- | :--- | :--- | :--- |
| **Eyes** | Perception | Turn pixels into a summary | A Vision Transformer (ViT) |
| **Brain** | Agent | Decide what to do | PPO, from stable-baselines3 |
| **Hands** | InputController | Actually press the keys | A Python/C++ input layer |

And the whole system is one loop that never changes:

```
observe  →  act  →  reward  →  repeat
```

**Build vs. borrow** — this distinction explains most design choices:

- ✅ **We build** the Ground (game worlds) and the Link (the socket + config).
- 🔁 **We borrow** the Brain (PPO) and the Eyes backbone (a pretrained ViT).

We deliberately do *not* write our own learning algorithm. That's a solved
problem; re-solving it would teach nothing and take months.

---

## 3. The one contract that must never break

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

---

## 4. Why the project starts with toys instead of a real game

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
| **M5** | Add the Hands | Fake input → real key presses | The loop drives a real game window |
| **M6** | *(Stretch)* Stardew | It's "just another profile" | The agent does something sensible on screen |

> **Portfolio note:** finishing **M4** already proves the whole thesis — any
> ground, any brain, one socket. M5/M6 are bonus.

---

## 5. ⚠️ The single most confusing thing about this repo

**There are two generations of code living side by side.**

The project originally started as *"build the Stardew bot right now."* A lot of
code was written for that. Then the direction changed (see the pivot log in
`docs/README.md`) to the crawl-first milestone plan above. The old code was
**never deleted** — it's kept as a reference and as the future M3/M5 material.

So when you open `src/`, you are looking at two tracks at once:

### Track A — the current milestone path (M0 → M2). This is live.

| File | Role |
| :--- | :--- |
| `scripts/run_cartpole.py` | M0: random actions on a borrowed game |
| `scripts/train_cartpole.py` | M1: PPO learns CartPole |
| `src/gametrainer/gridworld.py` | M2: **our own** 5×5 game world |
| `scripts/run_gridworld.py` | M2: random baseline on our world |
| `scripts/train_gridworld.py` | M2: PPO learns our world |
| `tests/test_gridworld.py` | Locks the Gymnasium contract |
| `tests/test_m2_e2e.py` | The M2 finish line (see §8) |

These files are small, numbers-only, and run on a CPU in seconds. Nothing here
touches your screen or your keyboard.

### Track B — the older Stardew prototype. Written, but ahead of where we are.

| File | Role | Belongs to |
| :--- | :--- | :--- |
| `src/gametrainer/env_vit.py` | A full Stardew Gym env with pixel rewards | M3 + M5 + M6 |
| `src/gametrainer/vit_extractor.py` | The ViT "eyes" wired into PPO | M3 |
| `src/gametrainer/screen.py` | Screen capture (finds the game window) | M3 |
| `src/gametrainer/input.py` | The "hands" (real key presses) | M5 |
| `src/gametrainer/interface.py` | Finds UI elements by image matching | M4/M6 |
| `src/gametrainer/config.py` | Loads per-game YAML config | M4 |
| `src/cpp/clib.cpp` | Native Windows key injection | M5 |
| `scripts/train.py`, `scripts/play.py` | The Stardew train/play entry points | M3+ |

**How to treat Track B:** *read it for ideas, don't trust it as current.* It
predates the milestone discipline, it isn't covered by tests, and several of its
design decisions (e.g. rewards guessed from raw pixel differences) are exactly
the fragile things the crawl-first plan exists to avoid. It will be
**rebuilt properly**, piece by piece, when M3/M4/M5 arrive.

> If you only remember one thing from this document: **Track A is the project.
> Track B is a preview of the project's future, written too early.**

---

## 6. Every technology, explained

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

### The vision stack (M3)

**ViT (Vision Transformer)** — the Eyes. A neural network that reads images by
cutting them into a grid of small square **patches** (16×16 pixels each) and
letting every patch "look at" every other patch directly. Contrast with a **CNN**
(the older approach), which only looks at small neighbourhoods and needs many
layers before distant parts of the image can relate to each other. For a game UI
— where the energy bar in one corner matters to the item in the opposite corner —
that global view is genuinely useful.

**timm** — a library that hands you pretrained ViT models in one line.

**Pretrained / transfer learning** — the ViT we use was already trained on
**ImageNet** (1.2M ordinary photos). It has no idea what a game is, but it already
knows edges, colours, shapes, and layout. Starting from that is enormously faster
than starting from random noise. That's transfer learning: borrow general
knowledge, then fine-tune on your specific task.

**Why 224×224?** Because that's the size ViTs were pretrained at. 224 ÷ 16 = 14,
so the image divides into a clean 14×14 = 196 patches and the pretrained position
information stays valid. Using an odd size means fudging that, for little gain.

**OpenCV (`cv2`)** — image utilities: resize, colour-convert, compare two images.
Used to shrink a game screenshot down to 224×224.

**mss** — very fast screen capture. Grabs the game window as an image, many times
a second.

### The input stack (M5)

**InputController** — the Hands. High-level, human-ish actions: "move up",
"click". It also holds the *behaviour* (timing, jitter) so the agent doesn't
press keys with inhuman precision.

**SendInput / the C++ extension (`clib`)** — the low-level part. Some games
ignore Python-simulated key presses because they read the keyboard at a lower
level. A small C++ extension calling the Windows `SendInput` API is more
reliable. **It is not built by default** — early milestones press no real keys, so
there is nothing to compile. `src/gametrainer/input.py` falls back to a harmless
stub if the extension is missing.

**NullInput** — a deliberately do-nothing Hands implementation. CartPole and
GridWorld need no real key presses, but the scripts wire `NullInput` in anyway,
so the *seam* is visible and proven long before it carries real weight. That's a
design habit worth copying: build the empty socket early, fill it later.

### Config and per-game data (M4)

**YAML / PyYAML** — a human-friendly config file format (like JSON, but with
comments). Intended to hold each game's key mappings and settings.

**Profile** — the planned unit of "everything specific to one game": a folder
with `profile.yaml`, screen regions, and reference images. The goal of M4 is that
adding a new game means adding a folder, not editing code. **Today this is only
half-built** — `config.py` exists but is not wired into the training path.

**Template matching** — an OpenCV technique: given a small reference image (say,
the energy icon), find where it appears in a screenshot. It's how `interface.py`
locates UI elements without hard-coded coordinates.

### Developer tooling

| Tool | What it does |
| :--- | :--- |
| **pytest** | Runs the tests (`pytest` in the project root) |
| **ruff** | Lints the code — catches unused imports, bad style (`ruff check .`) |
| **TensorBoard** | A live web dashboard of training reward (`tensorboard --logdir logs/`) |
| **rich** | Draws the coloured terminal menu in `tui.py` |
| **setuptools** (`setup.py`) | Makes the project installable via `pip install -e ".[rl]"` |

---

## 7. How the code is organised

```
GameTrainer/
├── main.py                  # entry point → launches the TUI menu
├── src/gametrainer/         # the library (importable code)
│   ├── gridworld.py         # ★ M2: our own game world
│   ├── input.py             # the Hands (+ NullInput stub)
│   ├── hardware.py          # picks CPU vs GPU
│   ├── logger.py            # timestamped logging
│   ├── tui.py               # the retro menu
│   ├── env_vit.py           # ▲ Track B: Stardew env
│   ├── vit_extractor.py     # ▲ Track B: the ViT eyes
│   ├── screen.py            # ▲ Track B: screen capture
│   ├── interface.py         # ▲ Track B: UI template matching
│   └── config.py            # ▲ Track B: YAML profile loader
├── scripts/                 # runnable entry points, one per job
├── tests/                   # pytest suite
├── docs/                    # PRD, changelog, per-milestone notes + UML
└── src/cpp/clib.cpp         # ▲ Track B: native key injection (M5, opt-in build)

★ = current milestone   ▲ = ahead of where we are (see §5)
```

**A useful pattern to notice:** `src/gametrainer/` holds *things* (classes you
import), `scripts/` holds *jobs* (files you run). A script is thin: it wires
pieces together, runs a loop, prints a verdict. Logic lives in the library.

**Another:** `src/gametrainer/__init__.py` deliberately imports **nothing**. If it
eagerly imported the submodules, running the tiny M0 CartPole script would drag
in torch, timm, mss and the Windows APIs — forcing you to install the M5 stack to
run the M0 demo. Import what you need, where you need it.

---

## 8. Where the project actually stands today

**Current branch:** `M2-Implementation`. **Current milestone:** M2.

Done and working:

- ✅ **M0** — CartPole runs with random actions. Baseline reward ≈ 22/episode.
- ✅ **M1** — PPO trains on CartPole. Reward climbed **22 → 500** (500 is the
  maximum CartPole allows). Nothing about the Ground changed to make that
  happen — only the decision-maker was swapped. That result *is* the proof of
  the architecture.
- ✅ **M2 code** — `GridWorldEnv` exists, obeys the contract, and has real
  contract tests. Both the random-baseline runner and the PPO trainer exist and
  are wired into the menu.

Not finished:

- ⏳ **The M2 finish line has not been crossed.** `tests/test_m2_e2e.py` is still
  marked `xfail` — "expected to fail, on purpose." That test is the milestone's
  definition of done: train PPO on GridWorld, then assert it beats random *and*
  reaches the goal in ≥90% of episodes. **M2 closes the day that test passes on
  its own and the `xfail` marker is deleted.**
- ⏳ Two per-brick tests named in `docs/m2/M2_ToDo.md` were never written:
  `tests/test_run_gridworld.py` and `tests/test_train_gridworld.py`.
- ⏳ There are uncommitted lint fixes in the working tree (`train.py`,
  `train_cartpole.py`, `transfer_learning.py`, `tui.py`, `vit_extractor.py`).

### How this project builds things: test-first

Every brick of work starts with a **failing test** (this is called "red"), then
just enough code to make it pass ("green"). The test is the spec; the code
chases the test. On top of that, each milestone opens with one **end-to-end
guardrail test** that describes the whole slice and is red from day one. It is
the North Star: you always know exactly what "done" means, because it's an
assertion, not an opinion.

---

## 9. How to run it

```bash
# Install (M0–M2 stack; no C++ compiler needed)
pip install -e ".[rl]"

# The menu — easiest way in
python main.py

# Or run the milestones directly:
python scripts/run_cartpole.py      # M0: random baseline
python scripts/train_cartpole.py    # M1: PPO learns CartPole
python scripts/run_gridworld.py     # M2: random baseline on our world
python scripts/train_gridworld.py   # M2: PPO learns our world

# Tests and lint
pytest
ruff check .

# Watch training live
tensorboard --logdir logs/
```

Each training script prints a **PASS/FAIL verdict** at the end, comparing the
trained reward to the random baseline. That's the milestone check, built into
the script — you don't have to eyeball a graph and guess.

---

## 10. Design decisions and the reasoning behind them

| Decision | Why |
| :--- | :--- |
| **Gymnasium contract is sacred** | It's the one thing that makes games and brains interchangeable. Bend it once and the project's thesis is dead. |
| **Borrow PPO, don't write it** | RL algorithms are a solved, subtle, easy-to-get-silently-wrong problem. The interesting work is the plumbing. |
| **Toys before real games** | On CartPole a failure means *your code* is broken. On Stardew a failure could be anything. Debuggability first. |
| **Pixels in, actions out** | No reading game memory, no patching the process. Keeps the AI's inputs human-like — and keeps the project honest and portable. |
| **ViT over CNN** | Global attention relates distant UI regions (energy bar ↔ hotbar) without stacking many layers. |
| **CPU-first** | CartPole and GridWorld train fine on a CPU. GPU only matters at M3. Don't let GPU driver pain block week 1. |
| **C++ only for input** | The one place Python is genuinely unreliable is low-level key injection. Everything else stays Python for iteration speed. |
| **Reward lives inside the env** | In RL, the environment *is* the teacher. Keeping the scoring next to the rules keeps that visible. It moves out to a `RewardCalculator` at M4, once there's a second game to justify the abstraction. |
| **`NullInput` exists from M0** | Build the seam before you need it, so the shape of the system is honest from day one. |
| **Small grid, fixed goal (M2)** | Learns fast, and makes the M3 contrast crisp: same world, same brain, but the input becomes a *picture* instead of coordinates. |

---

## 11. Known risks and honest weak spots

- **Reward from pixels is brittle.** Track B guesses reward from raw pixel
  differences ("did the screen change after I clicked?"). That is fragile and
  gameable — the agent will find and exploit any loophole. Expect this to be
  redesigned, not reused as-is.
- **Track B is untested.** No test covers `env_vit.py`, `screen.py`, or
  `interface.py`. Treat it as a prototype.
- **Profiles are half-built.** `config.py` exists; nothing calls it. Hard-coded
  window titles are still present in Track B. Finishing that is M4's whole job.
- **Docs describe two eras.** `docs/README.md` describes the Stardew-first system
  (Track B); `docs/PRD.md` describes the crawl-first plan (Track A). **`PRD.md` is
  the authority** when they disagree.

---

## 12. Where to go next

| You want… | Read |
| :--- | :--- |
| The diagrams | [`docs/UML_FULL.md`](UML_FULL.md) |
| The authoritative plan | `docs/PRD.md` |
| What the current milestone requires | `docs/m2/M2_ToDo.md` |
| What has changed and when | `docs/CHANGELOG.md` |
| Per-milestone snapshots | `docs/m0/`, `docs/m1/`, `docs/m2/` |
| How to work in this repo | `CLAUDE.md` (working agreements) |

---

## 13. Glossary — quick reference

| Term | Plain meaning |
| :--- | :--- |
| **Agent** | The AI that plays |
| **Environment** | The game, in code (the "Ground") |
| **Observation** | What the game shows the AI |
| **Action** | What the AI does |
| **Reward** | The score the game hands back |
| **Episode** | One full attempt, start to finish |
| **Action space** | The list of legal moves |
| **Observation space** | The shape of what the AI can see |
| **Policy** | The AI's current strategy; training = improving it |
| **RL** | Reinforcement Learning — learning by trial, error, and reward |
| **PPO** | The specific learning recipe we borrow |
| **SB3** | Stable-Baselines3, the library PPO comes from |
| **ViT** | Vision Transformer — the "eyes" |
| **CNN** | Convolutional Neural Network — the older vision approach |
| **Timestep / step** | One turn of the loop |
| **Terminated** | The episode ended naturally (won/lost) |
| **Truncated** | The episode was cut short (out of time) |
| **Exploration vs exploitation** | Try new things vs. stick with what works |
| **Transfer learning** | Start from pretrained weights instead of from scratch |
| **Fine-tuning** | Continuing to train a pretrained model on your task |
| **Inference / "play"** | Running a trained model with no further learning |
| **Baseline** | The score to beat (here: a random agent's score) |
| **Frame skip** | Repeat one action over N frames, to make its effect visible |
| **Checkpoint** | A saved snapshot of the model mid-training |
