# M3 Bricks — sprint log

One short entry per brick. Full evidence and numbers: `M3_Review.md`.
Non-brick housekeeping (repo audit, logger fix): `M3_Cleanup.md`.

**Status: 5 of 6 done. Milestone "Done when…" satisfied (Brick 4 prints PASS).**

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

### Brick 5 — Wire into TUI + changelog ⬜ not started
`src/gametrainer/tui.py` · `docs/CHANGELOG.md`

Add a "Train GridWorld with ViT eyes (M3)" menu option and an M3 changelog entry.
No test planned, on purpose: menu wiring fails loudly the first time you run it.
