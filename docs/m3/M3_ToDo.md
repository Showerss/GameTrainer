# M3 — Add the Eyes (GridWorld through a ViT)

> **Milestone goal (from PRD):** `VisionPerception` feeds a *picture* of GridWorld
> to the ViT; PPO still learns (slower is fine).
>
> **Done when…** PPO, seeing **only pixels** through the pretrained ViT, beats the
> random baseline and reaches the goal consistently — and `reset()` / `step()` still
> return the exact same shapes they did in M2. Captured as the **Brick 0 guardrail
> printing PASS**.

M2 gave PPO two numbers: `(row, col)`. M3 gives it a **picture** of the same world
and nothing else. The agent must now *look* at the grid to find itself.

The point of this milestone is the swap. Same Ground, same Brain, same contract —
we only change the **sense organ** in between. If we have to touch PPO to make this
work, we did it wrong.

---

## Scope discipline (what M3 is NOT)

- ❌ No screen capture, no real game window. We draw GridWorld ourselves.
- ❌ No `Profile` / `RewardCalculator` (still M4). Reward logic stays inside the env.
- ❌ No C++, no real key presses (M5).
- ❌ No fine-tuning the ViT. We **borrow** the eyes pretrained and frozen.
- ❌ No changes to `GridWorldEnv` beyond teaching it to draw itself.

---

## The design (proposed — confirm before Brick 1)

| Setting | Choice | Why |
| :--- | :--- | :--- |
| **How the picture is made** | `GridWorldEnv.render_mode="rgb_array"` returns a `(224, 224, 3)` uint8 image | The standard Gymnasium way to make an env drawable |
| **How it becomes the observation** | A **wrapper** (`PixelObservation`) swaps the obs from `(row,col)` to the image | Leaves `GridWorldEnv` untouched — the contract swap is the lesson |
| **Image size** | 224×224 (the 5×5 grid upscaled, blocky on purpose) | Pretrained ViTs expect exactly 224×224 |
| **ViT model** | `vit_tiny_patch16_224`, pretrained | ~5.7M params. ViT-Base (86M) is ~10× slower and we're on CPU |
| **Backbone** | **Frozen** (`freeze_backbone=True`) | Borrowed eyes stay borrowed. Only the policy head learns — far faster on CPU |
| **Hardware** | **CPU** | `torch` here is CPU-only; AMD+Windows GPU support is a fight worth skipping |

> **The one decision to confirm:** frozen ViT-Tiny on CPU. It's the difference
> between a milestone that finishes in an evening and one that runs for days.
> If training still proves too slow, the fallback is a smaller image, not a bigger model.

**Why a wrapper and not a new env:** a wrapper sits *around* `GridWorldEnv` and
changes only what comes out of `reset()`/`step()`. `GridWorldEnv` doesn't know it
exists. That's the cleanest possible demonstration of the project's whole thesis —
and it means M2's tests keep passing untouched.

---

## How we build M3: testing policy

Follows **CLAUDE.md §5**. In short:

1. **Brick 0 writes the finish line down first** — the bar M3 must clear, as a
   script that prints PASS/FAIL. Training is slow and random, so it's an
   **experiment**, not a `pytest` test.
2. **Bricks with a right answer open with a narrow red test** — image shape, the
   observation space, the feature vector's size. These are promises other code
   depends on.
3. **Glue gets no test, on purpose** — TUI wiring, print statements, `timm` install.

The tests to care about here are the **boundary** ones: what shape comes out of the
wrapper, and what shape goes into PPO. That boundary is where M3 can break silently.

---

## The to-do list

| # | Brick | File(s) | Done when… |
| :--- | :--- | :--- | :--- |
| **0** | **Guardrail — write this first** | `scripts/train_gridworld_vit.py` verdict | The pixels-only run prints **PASS**: beats the random baseline and reaches the goal |
| 1 | 🔴 test → GridWorld can draw itself | `tests/test_gridworld_pixels.py` → `src/gametrainer/gridworld.py` | `render_mode="rgb_array"` returns `(224,224,3)` uint8; agent moves ⇒ image changes |
| 2 | 🔴 test → the pixel wrapper | `tests/test_pixel_observation.py` → `src/gametrainer/perception.py` | obs is now the image; `reset()`→2-tuple, `step()`→5-tuple, `check_env` clean |
| 3 | 🔴 test → the ViT extractor fits | `tests/test_vit_extractor.py` → `src/gametrainer/vit_extractor.py` | Feeding one observation returns a feature vector of the promised width |
| 4 | Train on pixels (the experiment) | `scripts/train_gridworld_vit.py` | Runs end-to-end and prints the verdict → **Brick 0 goes PASS** |
| 5 | Wire into TUI + changelog | `tui.py`, `docs/CHANGELOG.md` | New menu item launches the script |

Brick 0 is the finish line; Bricks 1–4 are the work; Brick 5 is polish.

---

## Brick details & verify checks

### Brick 0 — The guardrail (write this FIRST)
**File:** `scripts/train_gridworld_vit.py` (its printed verdict)

Write down the bar *before* building anything:
- Mean reward must clearly beat the random baseline **measured live in the same run**
  (M2 hardcoded `-0.3` and it was wrong — the real number is ≈ `+0.13`. Don't repeat that).
- The agent must reach the goal in most greedy evaluation episodes.
- `reset()` / `step()` shapes must be unchanged from M2.

> **Verify:** run the script; it prints PASS with the reward, the goal rate, and the
> live baseline it had to beat.

### Brick 1 — Teach GridWorld to draw itself
**File:** `tests/test_gridworld_pixels.py` → `src/gametrainer/gridworld.py`
- **🔴 Test first:** `render_mode="rgb_array"` returns a `(224,224,3)` `uint8` array;
  the agent's square is a different colour from empty squares; after a move, the
  image is different.
- Keep the existing text `render()` working — the current mode stays the default.
- Blocky upscaling is correct here. It should look like a chunky 5×5 board.

> **Verify:** `pytest tests/test_gridworld_pixels.py` green, and M2's
> `tests/test_gridworld.py` still green (we didn't break the old contract).

### Brick 2 — The pixel wrapper (this is `VisionPerception`)
**File:** `tests/test_pixel_observation.py` → `src/gametrainer/perception.py`
- **🔴 Test first:** wrapping `GridWorldEnv` makes `observation_space` a
  `Box(0, 255, (224,224,3), uint8)`; `reset()` still returns a 2-tuple whose obs is
  inside that space; `step()` still returns the 5-tuple; `check_env` runs clean.
- Implement as a `gymnasium.ObservationWrapper` — override the observation only.
- The agent can no longer see `(row, col)` **at all**. That's the point.

> **Verify:** `check_env` passes on the wrapped env, and the M2 tests are untouched
> and still green.

### Brick 3 — Make the borrowed eyes fit
**File:** `tests/test_vit_extractor.py` → `src/gametrainer/vit_extractor.py`
- **🔴 Test first:** build the extractor on the wrapped env's observation space,
  push **one** observation through it, assert the output is a feature vector of the
  promised width (192 for ViT-Tiny).
- `vit_extractor.py` already exists from the old Stardew work. **Verify it, don't
  trust it** — it was written for a different observation space and defaults to
  ViT-Base. Expect to change defaults; delete what doesn't apply.
- Needs `timm` installed. Add it to the `rl` extra in `setup.py`.
- This test must not train anything — one forward pass, deterministic, fast.

> **Verify:** the test runs in seconds and the vector width matches what PPO expects.

### Brick 4 — Train on pixels (the experiment)
**File:** `scripts/train_gridworld_vit.py`
- Mirror `train_gridworld.py` so the two read as one system.
- `PPO("CnnPolicy", ...)` with `policy_kwargs` pointing at the ViT extractor.
- Measure the random baseline **live**, then train, then evaluate greedily.
- Print the PASS/FAIL verdict and the wall-clock time (we'll want it at M5).
- Expect this to be **much** slower than M2. Slower is fine; wrong is not.

> **Verify (this IS the milestone "Done when"):** the script prints PASS.

### Brick 5 — Wire it in & document
- Add a "Train GridWorld with ViT eyes (M3)" option to the TUI menu.
- Add an M3 entry to `docs/CHANGELOG.md`.

> **No test here, on purpose:** menu wiring fails loudly the first time you run it;
> a test costs more than the bug it would catch. Check: launch it and watch it go.

---

## The risk to watch

**PPO may learn slowly or not at all from pixels, even when everything is wired
correctly.** A frozen ImageNet ViT was trained on photographs, not blocky grids —
its features may not cleanly separate "agent at (2,3)" from "agent at (2,4)".

That is a *real result*, not a failure of the code. If it happens, the honest fixes
in order: train longer → unfreeze the last ViT block → shrink the image. Do **not**
start editing PPO. Note in `M3_Review` what actually happened.

---

## Rules we're keeping (from CLAUDE.md)

- **One brick at a time.** Smallest next step only; stop at each checkpoint.
- **Teach before coding.** Plain-English what & why first, then the code.
- **Test the promises, not the plumbing.** Here that means the boundaries: image
  shape out of the env, observation space out of the wrapper, feature width out of
  the extractor.
- **Tests vs. experiments.** One forward pass is a test. A training run is a script.
- **Don't move the finish line mid-milestone.** A better standard applies to M4.
- **Never break the Gymnasium contract** — M2's tests must stay green the whole way.
