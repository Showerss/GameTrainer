# R1 - Design Review

> **Covers:** how well the code follows object-oriented (OOP) design after the R1 cleanup: what's good, what's weak, and what to do about it.
> **Status:** current. **Last verified:** 2026-10-17. Every `file:line` was checked against the code.
> **Authority:** this file owns the design critique. Diagrams: [`UML_FULL.md`](../UML_FULL.md) §5.1. What gets built: [`PRD.md`](../PRD.md).

No code was changed to write this. Each item ends with a **verdict**:

| Verdict | Means |
| :--- | :--- |
| **Fix before M6** | Stardew will hit this. Cheaper to fix now. |
| **Fix (small)** | One brick, low risk. |
| **Wait for M6** | Real, but fixing it now is guessing. Wait for a third live game to show the real shape. |
| **Keep** | A deliberate trade-off. Leave it, keep the comment. |

---

## Part 1: What's good

| Idea (plain words) | Where | Why it's good |
| :--- | :--- | :--- |
| **Abstract class**: a parent that can't be built until its blanks are filled | `InputController` (`input.py:15`), `GameWindow` (`screen.py:137`) | A missing method fails at start-up, not mid-run. |
| **Template Method**: the parent writes the steps, children fill the blanks | `KeyboardInput.focus()` (`input.py:282`) | Tricky logic written once, not once per OS. |
| **Null Object**: a stand-in that safely does nothing | `NullInput` (`input.py:56`) | No `if hands is None` anywhere. It's also M5's negative control. |
| **Dependency injection**: hand an object its parts | `MinesweeperEnv(hands=, window=)` (`minesweeper.py:62`) | Tests pass in fakes, so no real game is needed. |
| **Value object**: data that can't change after creation | `Profile`, reward calculators (`frozen=True`) | Settings can't change mid-run by accident. |
| **Decorator**: a wrapper shaped like the thing it wraps | `PixelObservation(TimeLimit(RandomStart(GridWorldEnv())))` | Add features without editing the game. |
| **Pure functions**: numbers in, answer out, no side effects | `referee.py`, `check_hands.decide_*` | Easy to test, hard to fool. |

**R1's biggest win:** "which OS?" is now asked in exactly two places.

---

## Part 2: What to improve (most important first)

### 1. The hands know Minesweeper's keys: *Fix before M6*

**Principle:** **Interface Segregation**: don't make a class carry methods its users don't need.

`InputController` is meant to be generic hands. But it has `reveal()`, `flag()` and the LibreMines keys built in (`input.py:24-53`). Stardew's hands would inherit `flag()`.

```
Now:    InputController: tap_key, tap_chord, reveal, flag, restart ...
Better: InputController: tap_key, tap_chord           ← how to press
        MinesweeperEnv:  KEYMAP = {REVEAL: "O", ...}   ← what to press
```

**Fix:** keep only `tap_key` and `tap_chord` in the hands. Move the keymap to the game.

### 2. Two class families paired by hand: *Fix before M6*

**Principle:** **parallel hierarchies**: two families that must grow together is a warning sign.

```
GameWindow  → WindowsGameWindow,   MacGameWindow
KeyboardInput → WindowsKeyboardInput, MacKeyboardInput
```

The caller links them with a bare number: `keyboard_for_this_os(window.hwnd)` (`factory.py:68-69`). On a Mac that number is a process ID, not a window handle (`input.py:265`). The name is wrong there, which makes it a **leaky abstraction** (a hidden detail showing through).

**Fix:** pass the window *object* to the keyboard, or use one **Abstract Factory** (one maker that builds a matching pair).

### 3. A true/false flag decides who cleans up: *Fix before M6*

**Principle:** **clear ownership**: whoever creates a thing should close it.

`MinesweeperEnv` closes the window only if `owns_window=True` (`minesweeper.py:71`, `factory.py:64`). Nobody closes the hands. That's why the UML shows these as **aggregation** (`o--`, "handed one") and not **composition** (`*--`, "owns one").

**Fix:** pick one rule. Either the env always closes what it was given, or the caller always does.

### 4. A missing board gets faked silently: *Fix*

**Principle:** **fail loudly**: this project's own rule.

`MinesweeperEnv._read_obs()` (`minesweeper.py:102-114`) reads the board in one of three ways. The third invents an all-hidden board when nothing was set up. So training would run on a fake board, with no error.

**Fix:** one dependency, `board_reader`. If it's missing, raise an error.

### 5. Scoring depends on the eyes: *Fix*

**Principle:** **dependency direction**: core rules shouldn't depend on screen-reading details.

`rewards.py:18` imports `MINE` from the vision module. If the board reader is ever swapped, scoring breaks.

```
Now:    rewards.py ──▶ minesweeper_vision.py
Better: rewards.py ──▶ minesweeper_board.py ◀── minesweeper_vision.py
                       (CellState, GRID)
```

**Fix:** move `CellState` into a tiny shared file.

### 6. Reward classes: a confusing name and split rules: *Fix (small)*

**Principle:** **Strategy pattern**: swappable classes behind one shared interface.

The two calculators take different arguments (`rewards.py:34` vs `rewards.py:69`), so they can't be swapped. They aren't Strategy, and that's fine. But:
- `RewardCalculator` sounds like the parent of both. It's GridWorld-only. → Rename it `GridWorldRewardCalculator`.
- "Is the game over?" lives in the env for GridWorld (`gridworld.py:148`) but in the calculator for Minesweeper (`rewards.py:65`). → Pick one home.

### 7. A new game means editing six places: *Wait for M6*

**Principle:** **Open/Closed**: add new things without editing old code. The opposite is **shotgun surgery** (one change, many edits).

Adding a game touches four tables in `profile.py` (lines 23, 26, 33, 61), a check at `profile.py:200`, the `if`-chain in `factory.py`, and `tui.PROFILES`.

**Fix (at M6):** a **registry**: one entry per game that says what it allows and how to build it.

### 8. `Profile` carries every game's settings: *Wait for M6*

**Principle:** **make wrong states impossible**: shape the data so a bad combination can't be written.

Six reward fields are all optional (`profile.py:116-121`). So the factory has to re-check them (`factory.py:28`). And `from_yaml` is ~100 lines in one method.

**Fix (at M6):** a separate reward section per game (`GridWorldRewards`, `MinesweeperRewards`).

### 9. `RandomStart` only works on GridWorld: *Keep (for now)*

**Principle:** a wrapper should only use what it wraps.

It reaches inside to set `goal` and call `place_agent()` (`gridworld.py:230-244`).

**Fix, if it matters later:** use Gymnasium's built-in `reset(options={"goal": ...})`.

### 10. A parameter nobody uses: *Fix (small)*

**Principle:** **Liskov Substitution**: a child must keep its parent's promises.

`tap_key(key_code, duration)` promises a duration (`input.py:37`). Both real versions ignore it (`input.py:340`, `input.py:415`).

**Fix:** remove `duration`.

### 11. Three functions named `decide_verdict`: *Fix (small)*

Same name, three meanings: `referee.py:118`, `check_hands.py:276`, `train_gridworld_vit.py:153`. Hard to search, easy to mix up. Also, tests import `scripts/check_hands.py` directly, a sign that code belongs in the package.

**Fix:** rename them (`decide_m5_verdict`, `decide_m3_verdict`).

### 12. The package is named `src.gametrainer`: *Wait*

Every script edits `sys.path` to find the code. The standard layout is a package named `gametrainer` inside `src/`, installed once with `pip install -e .`.

**Fix (later):** rename and drop the path edits. The four training scripts share a skeleton, but some of that repetition is on purpose: closed milestones keep their code.

### 13. Leftovers: *Mention, don't delete yet*

| What | Where |
| :--- | :--- |
| `Logger` is used only by its own test | `logger.py` |
| `_hands = NullInput()` is never used | `train_cartpole.py:150`, `train_gridworld.py:163` |
| `HIDDEN` / `FLAGGED` / `MINE` repeat `CellState` | `minesweeper_vision.py:93-95` |
| `MinesweeperEnv.UP ... FLAG` repeat the enum | `minesweeper.py:55-60` |
| GridWorld uses plain ints, Minesweeper an enum | `gridworld.py:56` vs `minesweeper.py:36` |

### 14. Work done at start-up: *Keep*

- `ViTFeaturesExtractor` prints a banner when created (`vit_extractor.py:141`). Harmless.
- `screen.py` fixes Windows DPI the moment it's imported (`screen.py:133`). This has to happen before any window call, and the comment explains why.

---

## Part 3: Suggested order

1. Items **4, 10, 11**: small and safe.
2. Item **5**: one new file.
3. Items **1, 2, 3** together: draw the new UML first.
4. Item **6**: rename and tidy.
5. Items **7, 8**: at M6.

The contract tests stay green through all of them. They're the safety net.
