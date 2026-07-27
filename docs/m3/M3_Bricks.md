# M3 Bricks — sprint log

One short entry per brick. Full evidence and numbers: `M3_Review.md`.
Non-brick housekeeping (repo audit, logger fix): `M3_Cleanup.md`.

**Status: 6 of 6 done — M3 complete. Milestone "Done when…" satisfied (Brick 4 prints PASS).**

---

### Brick 0 — The guardrail ✅
`scripts/train_gridworld_vit.py`

Wrote the finish line *before* any pixel code existed: beat the live random
baseline by +0.40, reach the goal in ≥80% of greedy episodes, and keep M2's
`reset()`/`step()` shapes. Measures the baseline **live every run** — M2
hardcoded −0.3 and that number was simply wrong.

### Brick 1 — GridWorld draws itself ✅
`src/gametrainer/gridworld.py` → `_render_rgb()` · test `tests/test_gridworld_pixels.py`

`render_mode="rgb_array"` returns a (224, 224, 3) uint8 picture of the board,
blocky on purpose. The old text renderer still works and stays the default.

### Brick 2 — The pixel wrapper ✅
`src/gametrainer/perception.py` → `PixelObservation` · test `tests/test_pixel_observation.py`

A wrapper swaps the observation from `(row, col)` to the picture. `GridWorldEnv`
is never edited and never learns the wrapper exists, so M2's tests stay green.
The agent can no longer see its coordinates at all — that's the point.

### Brick 3 — The borrowed eyes fit ✅
`src/gametrainer/vit_extractor.py` → `ViTTinyFeaturesExtractor` · test `tests/test_vit_extractor.py`

One picture in, 192 numbers out, using a pretrained ViT-Tiny with the backbone
frozen (0 trainable parameters). Verified the width PPO reads matches the width
the extractor actually produces.

### Brick 4 — Train on pixels ✅ **PASS**
`scripts/train_gridworld_vit.py` · new test `tests/test_random_start.py`

The first run scored +0.905 and looked like a win — but the agent was **blind**.
It had memorised a single coin flip (53% DOWN / 47% RIGHT) and never used the
picture; a hand-written blind agent matched it at +0.907.

The fault was the **Ground**, not the eyes: with the goal in a corner, "down or
right" wins from any square, so vision was never required. Fixed with wrappers
only — random start, goal moved to the centre, and a 25-move budget
(`RandomStart`, `make_vision_task`). `GridWorldEnv` still unedited.

Re-run: live baseline +0.48, trained **+0.99**, **100%** goal rate, shapes
unchanged → **PASS** in 19.2 min on CPU. Three new tests assert that blind and
random agents can no longer pass, so this can't silently come back.

### Brick 5 — Wire into TUI + changelog ✅
`src/gametrainer/tui.py` · `setup.py` · `docs/CHANGELOG.md`

Gave the M3 run a front door. New menu item `[5] Train GridWorld with ViT eyes —
pixels only (M3)` launches `train_gridworld_vit.py`; the old `[5]` (the Stardew
Track B script) moved to `[6]` and lost its misleading "M3+" label, since two
items both claiming M3 is how you launch the wrong one. Play/Changelog/Deps/Quit
renumbered; Quit is now `[10]`. Added the M3 changelog section covering all six
bricks, including the blind-agent bug and its fix.

**The bug this brick found:** `rich` is imported by `tui.py` but was in **no**
dependency list and wasn't installed — so `python main.py` had been dying into
its error fallback and the TUI could not start at all. Pre-existing, unrelated to
M3, and invisible until something actually tried to launch the menu. Added `rich`
to `install_requires` (it's needed by `main.py`'s default path, so it's core, not
an `rl` extra).

No test, as planned — and it paid off exactly as the plan predicted: the wiring
failed loudly on first run. Verified by launching it: menu renders, all 8 script
paths resolve, option `[5]` reached "Contract check: OK → live baseline +0.25 →
Training PPO on pixels" before being stopped early. Suite still 41 passed /
1 skipped, `ruff` clean.
