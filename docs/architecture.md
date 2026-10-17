# Architecture

> **Covers:** how the code is organised, and which design ideas it uses.
> **Status:** current. **Last verified:** 2026-10-17 (after the R1 cleanup).
> **Authority:** this file explains the *structure in words*. The diagrams are in [`UML_FULL.md`](UML_FULL.md). The reasons behind big choices are in [`adr/`](adr/README.md). Known weak spots are in [`r1/R1_Review.md`](r1/R1_Review.md).

## 1. The one rule everything follows

Every game is a **Gymnasium environment**: it has `reset()` and `step()` ([concepts §3](concepts.md#3-the-contract-reset-and-step)). The learner only ever calls those two. So the learner never needs to know which game it's playing.

## 2. How a run is put together

```
profiles/gridworld.yaml          a text file naming the game + settings
        │
        ▼
Profile.from_yaml()              reads and checks the file; stops on mistakes
        │
        ▼
make_env(profile)                the ONE place a name becomes a game object
        │
        ▼
a Gymnasium env  ──▶  PPO trains on it  ──▶  the referee judges PASS / FAIL
```

*Why one place:* to add a game you change one function, not ten files. ([ADR 0001](adr/0001-factory-not-gameenvironment.md))

## 3. The code map

| File | Job | Main pieces |
| :--- | :--- | :--- |
| `src/gametrainer/gridworld.py` | Our 5×5 game | `GridWorldEnv`, `RandomStart`, `make_vision_task()` |
| `src/gametrainer/minesweeper.py` | Plugs LibreMines into Gymnasium | `MinesweeperEnv`, `MinesweeperAction` |
| `src/gametrainer/perception.py` | Turns the observation into a picture | `PixelObservation` |
| `src/gametrainer/vit_extractor.py` | The ViT eyes for PPO | `ViTTinyFeaturesExtractor` |
| `src/gametrainer/minesweeper_vision.py` | Reads the Minesweeper board from a screenshot | `read_board()`, `CellState` |
| `src/gametrainer/screen.py` | Finds and screenshots a window | `GameWindow` + Windows / Mac versions |
| `src/gametrainer/input.py` | Presses real keys | `InputController`, `NullInput`, `KeyboardInput` + Windows / Mac versions |
| `src/gametrainer/rewards.py` | Scoring | `RewardCalculator` (GridWorld), `MinesweeperRewardCalculator` |
| `src/gametrainer/profile.py` | Reads profile files | `Profile` |
| `src/gametrainer/factory.py` | Builds the game a profile names | `make_env()` |
| `src/gametrainer/referee.py` | Baselines and PASS / FAIL | `measure_random_baseline()`, `evaluate_greedy()`, `decide_verdict()` |
| `src/gametrainer/training.py` | Shared PPO settings for M1 / M2 | `CLASSIC_PPO_SETTINGS` |
| `src/gametrainer/tui.py` | The menu you get from `python main.py` | `MenuItem`, `MENU_ITEMS` |
| `scripts/train_from_profile.py` | Trains any profile | `main()`, `source_fingerprint()` |
| `scripts/check_hands.py` | M5's live proof | four controls, `Measurements` |

## 4. Design patterns used

A **design pattern** is a named, reusable solution to a common design problem. *Why name them:* engineers can say one word instead of a paragraph.

| Pattern | In one sentence | Where | Why here |
| :--- | :--- | :--- | :--- |
| **Adapter** | Make something fit a standard plug | `MinesweeperEnv` | A desktop game becomes a Gymnasium env |
| **Decorator** (wrapper) | Wrap an object to add one job, keeping its shape | `PixelObservation(TimeLimit(RandomStart(GridWorldEnv())))` | Add features without editing the game |
| **Factory** | One function decides which object to build | `make_env()`, `keyboard_for_this_os()` | Callers don't need to know the details |
| **Template Method** | The parent writes the steps; children fill the blanks | `KeyboardInput.focus()` | Shared logic once, per-OS details separate |
| **Null Object** | A stand-in that safely does nothing | `NullInput` | No `if hands is not None` checks anywhere |
| **Dependency Injection** | Hand an object what it needs, instead of it building it | `MinesweeperEnv(hands=, window=)` | Tests can pass in fakes |
| **Value Object** | Small data that can't be changed after creation | `Profile`, reward calculators (`frozen=True`) | Settings can't change mid-run by accident |

**Honest note:** the two reward calculators are *not* the Strategy pattern, though older docs said so. Strategy means swappable classes with one shared interface, and these two have different method signatures. See [R1_Review item 6](r1/R1_Review.md).

## 5. Where the operating system shows up

Only two functions ask "which OS?": `keyboard_for_this_os()` and `game_window_for_this_os()`. Everything else just calls `hands.move_down()` or `window.grab()`. *Why:* adding Linux later means adding new classes, not editing old ones.

## 6. History: Track A and Track B

- **Track B** (retired 2026-08-04): the first attempt, which started straight on Stardew Valley. Too many unknowns at once. The code is in git history only.
- **Track A** (today): start tiny, prove each piece, then grow. M0 → M6.

*Lesson:* when something fails, you want only one possible cause.
