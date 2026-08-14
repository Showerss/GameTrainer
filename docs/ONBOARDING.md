# GameTrainer — Onboarding for a Junior Engineer

> **Covers:** orientation for someone new to this repo — what it is, why it looks
> this way, what every technology is for, and which code is current.
> **Status:** current.
> **Last verified:** 2026-08-14 (M4 closed — §5's file table, §6's "Profile"
> description, §7's tree, and §8's status table and summary all updated to
> match; see each section for what changed).
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

## 5. ⚠️ The single most confusing thing about this repo (historical — see correction)

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

### Track A — the current milestone path (M0 → M4). This is live.

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
| `src/gametrainer/profile.py` | M4: `Profile` — a validated `.yaml` → Ground + reward + PPO numbers |
| `src/gametrainer/rewards.py` | M4: `RewardCalculator` — the reward decision, pulled out of `GridWorldEnv` |
| `src/gametrainer/factory.py` | M4: `make_env(profile)` — the one place a profile's name becomes an env |
| `profiles/*.yaml` | M4: the three profiles — `cartpole`, `gridworld`, `gridworld_pixels` |
| `scripts/train_from_profile.py` | M4: one runner, any profile — replaces per-game train scripts |
| `scripts/check_swap.py` | M4: negative-control proof the config layer is really wired |
| `tests/test_profile.py`, `test_rewards.py`, `test_make_env.py`, `test_m4_verdict.py` | M4: profile validation, reward numbers, env-building, the referee |

M0–M2 here are small, numbers-only, and run on a CPU in seconds. M3 adds the ViT,
so `train_gridworld_vit.py` takes ~19 min on CPU. M4 adds no new Ground — it's a
plumbing milestone, same three runs, one shared runner. Nothing in Track A
touches your screen or your keyboard.

### Track B — the older Stardew prototype. Written, but ahead of where we are.

**(deleted 2026-08-04 — table kept for historical record, see correction above)**

| File | Role | Belongs to |
| :--- | :--- | :--- |
| `src/gametrainer/env_vit.py` | A full Stardew Gym env with pixel rewards | M5 + M6 |
| `src/gametrainer/screen.py` | Screen capture (finds the game window) | M5 |
| `src/gametrainer/interface.py` | Finds UI elements by image matching | M4/M6 |
| `src/gametrainer/config.py` | Loads per-game YAML config | M4 |
| `scripts/train.py`, `scripts/play.py` | The Stardew train/play entry points | M3+ |

**How to treat Track B:** *read it for ideas, don't trust it as current.* It
predates the milestone discipline, it isn't covered by tests, and several of its
design decisions (e.g. rewards guessed from raw pixel differences) are exactly
the fragile things the crawl-first plan exists to avoid. It gets
**rebuilt properly**, piece by piece, as each milestone arrives.

> **This has already happened once.** `vit_extractor.py` was Track B until M3.
> It was verified rather than trusted, its ViT-Base default was wrong for a CPU
> run, and it came out the other side as Track A. That's the intended lifecycle:
> Track B is a source of ideas, never a source of working code.

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

### Config and per-game data (M4 — done)

**YAML / PyYAML** — a human-friendly config file format (like JSON, but with
comments). Holds each profile's Ground, reward numbers, and PPO hyperparameters.

**Profile** — **rewritten 2026-08-14, M4 closed.** This section originally
described a *planned*, never-wired design: a folder per game holding
`profile.yaml`, screen regions, and reference images (that was Track B's
`config.py`, deleted 2026-08-04). What M4 actually built is simpler: one flat
`.yaml` file per setup (`profiles/cartpole.yaml`, `profiles/gridworld.yaml`,
`profiles/gridworld_pixels.yaml`), loaded by `src/gametrainer/profile.py` into a
validated `Profile` dataclass, turned into a Gymnasium env by
`src/gametrainer/factory.py`'s `make_env(profile)`. Adding a new *setup* of an
existing Ground means adding a `.yaml` file, not editing code — proven by
`scripts/check_swap.py`, which asserts changing a number in the YAML genuinely
changes what the agent gets scored on. Adding a whole new Ground (a new game
world) still means writing one, same as GridWorld was written for M2 — the
profile only swaps between Grounds that already exist.

**Template matching** — an OpenCV technique: given a small reference image (say,
the energy icon), find where it appears in a screenshot. **Not built yet** — the
file that would have used it, `interface.py`, was Track B and was deleted
2026-08-04. Still the planned approach for M6's screen-based reward reading.

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
│   ├── gridworld.py         # M2/M3: our own game world, and it draws itself
│   ├── perception.py        # M3: the pixel wrapper (the "eyes" socket)
│   ├── vit_extractor.py     # M3: the frozen ViT eyes
│   ├── profile.py           # ★ M4: Profile — a validated .yaml → Ground + reward + PPO
│   ├── rewards.py           # ★ M4: RewardCalculator — the reward decision
│   ├── factory.py           # ★ M4: make_env(profile) — the one name→object seam
│   ├── input.py             # the Hands (+ NullInput stub)
│   ├── hardware.py          # picks CPU vs GPU
│   ├── logger.py            # timestamped logging
│   └── tui.py               # the retro menu (★ M4: profile-picker entry)
├── profiles/                 # ★ M4: cartpole.yaml, gridworld.yaml, gridworld_pixels.yaml
├── scripts/                 # runnable entry points, one per job
│   ├── train_from_profile.py # ★ M4: one runner, any profile
│   └── check_swap.py        # ★ M4: negative-control proof the config is real
├── tests/                   # pytest suite
├── docs/                    # PRD, changelog, per-milestone notes + UML
└── src/cpp/clib.cpp         # ▲ M5: native key injection, opt-in build, not yet used

★ = current milestone   ▲ = ahead of where we are (see §5)
(Track B — the old Stardew prototype — was deleted 2026-08-04; see §5's correction note.)
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

**Corrected 2026-08-14:** M4 closed. Live detail (per-brick status, dates,
decisions) lives in `docs/m4/M4_Log.md`; the retrospective is
`docs/m4/M4_Review.md` — this section only owns the high-level summary.

**Current branch:** `m4-implementation`. **Last milestone closed:** M4.

Done and working:

| # | Milestone | Result | Conditions |
| :--- | :--- | :--- | :--- |
| **M0** | Setup | CartPole runs 100 random steps, no crash. Baseline ≈ **22**/episode | CPU |
| **M1** | Borrow the Brain | Reward **22 → 500** (500 is CartPole's ceiling) | CPU, PPO `MlpPolicy`, 25k steps |
| **M2** | Build our own Ground | Trained **+0.93**, goal reached **20/20** greedy episodes | CPU, PPO `MlpPolicy`, 25k steps |
| **M3** | Add the Eyes | Live baseline **+0.48** → trained **+0.99**, goal reached **100%** of greedy episodes | CPU, frozen `vit_tiny_patch16_224`, **19.2 min** |
| **M4** | Make it swappable | All 3 profiles PASS through **one unedited runner**; 4/4 negative controls PASS (`scripts/check_swap.py`) | CPU, config-only — zero Python edits between runs |

M1's result *is* the proof of the architecture: nothing about the Ground changed,
only the decision-maker was swapped. M3 is the same trick one level deeper — only
the *sense organ* changed, and PPO was never touched. M4 proves the *whole
Ground* is swappable — the PRD's portfolio win condition.

**The one to actually read about is M3**, because the first run was a false
positive. It scored `+0.905` and looked like a win, but the agent's action
probabilities were identical on every square — a fixed 53% DOWN / 47% RIGHT coin
flip — and a hand-written blind agent matched it at `+0.907`. With the goal in a
corner, "down or right" wins from anywhere. The fault was the **Ground**, not the
eyes. `make_vision_task()` (random start, centre goal, 25-move budget) fixed it,
and `tests/test_random_start.py` makes sure it can't come back. Full write-up in
`docs/CHANGELOG.md` under M3.

Known gaps:

- ⏳ `tests/test_m2_e2e.py` is `@pytest.mark.skip`, not deleted. Under the current
  testing policy (`CLAUDE.md` §5) a training run is an **experiment**, not a test —
  the guardrail lives in `scripts/train_gridworld.py`'s printed verdict instead.
  **Its module docstring still describes the old `xfail` scheme and is stale.**
- ⏳ Two per-brick tests named in `docs/m2/M2_ToDo.md` were never written:
  `tests/test_run_gridworld.py` and `tests/test_train_gridworld.py`. Deliberate
  under the current policy — they'd be testing glue.
- ✅ ~~M4 has no `M4_ToDo.md` yet.~~ **Resolved 2026-08-08** — `docs/m4/M4_ToDo.md`
  and `docs/m4/M4_Log.md` exist; M4 is the first milestone written under
  `docs/DOC_STANDARD.md`, and is in progress (Bricks 0–4 done).

### How this project builds things: tests vs. experiments

**Authority: `CLAUDE.md` §5.** The short version:

A brick with a **single right answer** — an image's shape, an observation space, a
feature vector's width, a reward rule — opens with a **failing test** ("red"),
then just enough code to make it pass ("green"). The test is the spec; the code
chases it.

**Glue gets no test, on purpose.** Menu wiring, print statements and argument
parsing fail loudly the first time you run them; a test there costs more than the
bug it would catch. A skip is a decision, and the reason gets written down in the
milestone's to-do.

**A training run is never a test.** It's slow and random — it can pass today and
fail tomorrow on identical code. Those live in `scripts/` and print a PASS/FAIL
verdict you run by hand once per milestone. That distinction is why
`tests/test_m2_e2e.py` is skipped rather than maintained.

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

# M4: one runner, any profile — config-only, no code edits
python scripts/train_from_profile.py --profile profiles/cartpole.yaml
python scripts/train_from_profile.py --profile profiles/gridworld.yaml
python scripts/train_from_profile.py --profile profiles/gridworld_pixels.yaml
python scripts/check_swap.py        # M4: proves the config layer is really wired

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
- ~~**Profiles are half-built.** `config.py` exists; nothing calls it. Hard-coded
  window titles are still present in Track B. Finishing that is M4's whole job.~~
  **Resolved 2026-08-14 (M4 closed).** `config.py` was deleted with the rest of
  Track B (2026-08-04). The current `Profile` (`src/gametrainer/profile.py`) is
  fully wired: `make_env(profile)` builds the env, `scripts/check_swap.py`
  proves the numbers in the YAML genuinely drive the run, not a hardcoded
  fallback. See §6 and `docs/m4/M4_Review.md`.
- **`docs/README.md` is archived.** It describes the Stardew-first system (Track B)
  and was written before the crawl-first pivot. It is kept for its design pivot
  log and is clearly marked at the top. **`docs/PRD.md` is the authority.**
- **The ViT's features were never proven to be *good*.** M3 proves PPO can learn
  from pixels on a task that demands looking. It does not prove a frozen ImageNet
  ViT is the *right* set of eyes for blocky grids — only that it is sufficient
  here. That question is open.

---

## 12. Where to go next

| You want… | Read |
| :--- | :--- |
| The authoritative plan | `docs/PRD.md` |
| The diagrams | [`docs/UML_FULL.md`](UML_FULL.md) |
| What the last milestone required | `docs/m3/M3_ToDo.md` |
| What has changed and when | `docs/CHANGELOG.md` |
| Per-milestone snapshots | `docs/m0/`, `docs/m1/`, `docs/m2/`, `docs/m3/` |
| How to work in this repo | `CLAUDE.md` (working agreements) |
| How docs must be written | `docs/DOC_STANDARD.md` |
| The pre-pivot Stardew design (historical) | `docs/README.md` — **archived** |

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
