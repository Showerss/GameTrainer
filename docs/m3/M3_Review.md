# M3 Review — Add the Eyes (GridWorld through a ViT)

**Status: PASSED** — 2026-07-25
**Source document for the M3 retrospective PDF.** Every number here is copied
from a real run; the scripts that produced them are in `experiments/` and the
raw console logs are in `run-logs/`.

---

## The one-paragraph version

M3 asked whether PPO could learn GridWorld from **pixels only**, seen through a
frozen pretrained ViT. The first full run scored **+0.905** and looked like a
clean success. It wasn't: the agent was **completely blind** and had never used
the picture at all. It had memorised a single coin flip that happened to solve
the maze. Finding that took three diagnostics; fixing it meant changing the
**Ground**, not the eyes. After the fix, a genuinely sighted agent reached
**+0.99 with a 100% goal rate**, and the guardrail printed PASS.

The lesson worth carrying forward: **a rising reward curve proves the agent found
*some* winning strategy. It says nothing about whether that strategy used the
eyes.**

---

## The finish line (Brick 0, written before any pixel work existed)

All three had to hold:

1. Mean reward clearly beats the random baseline **measured live in the same run**
   (margin: +0.40).
2. The agent reaches the goal in **≥80%** of greedy evaluation episodes.
3. `reset()` / `step()` return the same shapes they did in M2.

Brick 0 was written first precisely so it couldn't be softened later. It earned
its keep twice — once by catching the blind agent, once by refusing to be moved
when the bar turned out to be harsh.

---

## Act 1 — The run that looked like a success

20,000 timesteps, frozen `vit_tiny_patch16_224`, 19.4 min on CPU.

| iteration | 1 | 5 | 10 | 12 | 20 | 30 | 40 |
|---|---|---|---|---|---|---|---|
| `ep_rew_mean` | 0.352 | 0.799 | 0.899 | 0.906 | 0.905 | 0.906 | 0.903 |
| `ep_len_mean` | 54.6 | 21.1 | 11.1 | 10.4 | 10.5 | 10.4 | 10.7 |

A textbook learning curve — until you notice it **flatlines at iteration 12 and
never improves again** for 28 more iterations. That plateau is the tell: the
agent had found everything there was to find, and it wasn't much.

Then the verdict contradicted the curve completely:

```
M3 VERDICT: FAIL
  Live random baseline:   +0.04 reward/episode
  Trained mean reward:    -1.00 reward/episode
  [FAIL] beats baseline by >= 0.40  (needs >= +0.44)
  [FAIL] reaches goal in most episodes  (0%, needs >= 80%)
  [PASS] reset()/step() shapes unchanged from M2
  Mean steps to finish:   100.0
```

**Exactly** `-1.00` reward and **exactly** 100.0 steps across all 20 episodes.
Numbers that clean are never a weak agent — a bad-but-real policy varies. That
precision is what said "measurement artefact," not "needs more training."

---

## Act 2 — The diagnosis

### 2a. The policy ignores its input entirely

Walking the trained agent through the grid and printing its action
probabilities at each square (`experiments/diagnose_greedy.py`):

```
step     pos  action  probabilities [UP DOWN LEFT RIGHT]
   0  (0, 0)  DOWN    [0.001 0.533 0.    0.466]
   1  (1, 0)  DOWN    [0.001 0.533 0.    0.466]
   2  (2, 0)  DOWN    [0.001 0.533 0.    0.466]
   3  (3, 0)  DOWN    [0.001 0.533 0.    0.466]
   4  (4, 0)  DOWN    [0.001 0.533 0.    0.466]
   5  (4, 0)  DOWN    [0.001 0.533 0.    0.466]   <- stuck against the wall
```

Identical at every position. The agent had learned a fixed **53% DOWN / 47%
RIGHT** coin flip and played it regardless of what it saw.

That also explains the exact `-1.00`: greedy evaluation takes the `argmax`, which
is always DOWN, so the agent marched to the bottom wall and ground against it for
all 100 steps. **Greedy evaluation is what exposed this.** A stochastic-only
verdict would have sampled the coin flip, reached the goal, and printed a
triumphant PASS on a blind agent.

Two possible causes were checked and one was ruled out immediately — the
observation handling was correct:

```
raw env obs shape      : (224, 224, 3)
after obs_to_tensor    : (1, 3, 224, 224)
matches manual CHW     : True
```

### 2b. Where the signal dies

Measuring how much each stage of the pipeline varies across five different agent
positions (`experiments/diagnose_features.py`):

| stage | mean magnitude | std across cells | ratio |
|---|---|---|---|
| raw pixels | 49.5998 | 17.047113 | **0.34369** |
| ViT features (192-dim) | 3.1778 | 0.123028 | **0.03871** |
| policy logits (4) | 4.1434 | 0.000019 | **0.00000** |

Pairwise cosine similarity of the ViT features across those five cells was
**0.9982 – 0.9993** — nearly parallel vectors. The pictures were plainly
different (11,748–11,883 of 150,528 pixel values changed), the ViT compressed
that difference to ~4%, and the policy head discarded what remained.

### 2c. The control that settled it

A hand-written agent that **never receives the picture**, playing that same coin
flip (`experiments/blind_control.py`, 200 episodes):

```
BLIND open-loop agent (never looks at the observation)
  mean reward : +0.907
  mean steps  : 10.2
  goal rate   : 100%

  ViT agent during training : +0.905 reward, 10.5 steps
```

A blind agent matched the "trained" agent exactly. **The +0.905 proved nothing
about the eyes.**

---

## Act 3 — The root cause was the Ground, not the eyes

The original maze had the agent start at (0,0) and the goal fixed at the **corner**
(4,4). "Always move down or right" walks you into that corner from *any* square,
because bumping a wall simply stops you instead of costing you the run. Vision was
never required to win, so PPO took the cheaper path.

Comparing a blind agent against a sighted oracle across four task designs
(`experiments/which_task_needs_eyes.py`, 300 episodes each):

| variant | blind | sighted | gap |
|---|---|---|---|
| **A** fixed start, corner goal *(the original)* | +0.906, 100% | +0.930, 100% | **+0.024** |
| **B** random start, corner goal | +0.947, 100% | +0.967, 100% | **+0.019** |
| **C** random start, **centre** goal | −0.748, 13% | +0.985, 100% | **+1.733** |
| **D** random start, random goal | −0.665, 17% | +0.976, 100% | +1.641 |

The gap between blind and sighted is the **only** thing that can prove perception
matters. In A it is +0.024 — noise.

**The most surprising result of the milestone is row B.** Randomising the start —
the obvious fix, and the one first attempted — made things *worse*: a blind agent
still scored +0.947 at a 100% goal rate. The corner is the trap, not the fixed
start. Variant **C** was chosen over D because it is the smaller step (the agent
must see *itself*; the goal stays put) and it had the larger gap.

---

## Act 4 — Calibrating the referee

Fixing the task exposed a second, independent problem: with a 100-move budget on
a 25-square grid, a random walk stumbles into a central goal **94%** of the time.
A guardrail that a random agent passes grades nothing.

The step budget was the lever (`experiments/calibrate_task.py`, 400 episodes each):

| goal | move budget | uniform random | sighted | blind | headroom | usable? |
|---|---|---|---|---|---|---|
| (2,2) | 100 | +0.640, 94% | +0.986, 100% | −0.751, 12% | +0.345 | ✗ bar unreachable |
| (2,2) | **25** | +0.361, 53% | +0.984, 100% | −0.099, 12% | **+0.624** | **✓ chosen** |
| (2,2) | 15 | +0.268, 38% | +0.985, 100% | +0.004, 14% | +0.717 | ✓ |
| (2,2) | 10 | +0.197, 28% | +0.985, 100% | +0.033, 12% | +0.788 | ✓ |
| (4,4) | 15 | +0.033, 17% | +0.968, 100% | **+0.938, 99%** | +0.935 | ✗ blind still wins |
| (2,2) | 8 | +0.182, 25% | +0.984, 100% | +0.075, 14% | +0.802 | ✓ |

"Usable" required all four: the bar reachable at all, a random agent **failing**
the 80% goal condition, a sighted agent **passing** it, and a blind agent
**failing** it.

Two things to note for the retrospective:

- **The 25-move budget was chosen to make the referee discriminate, not to make
  passing easier.** Random and blind agents both fail it; a sighted agent needs
  at most 4 moves from the farthest corner, so 25 is still roomy.
- **Row 5 is the proof that tightening the budget alone would not have worked.**
  With the goal back in the corner and a tight 15-move budget, a blind agent
  still scored 99%. Both changes were necessary; neither was sufficient.

---

## Act 5 — The run that actually passed

Same 20,000 timesteps, same frozen ViT-Tiny, same PPO settings. Only the Ground
changed. 19.2 min on CPU.

| iteration | 1 | 7 | 13 | 19 | 22 | 27 | 32 | 40 |
|---|---|---|---|---|---|---|---|---|
| `ep_rew_mean` | 0.371 | 0.307 | 0.517 | 0.818 | 0.928 | 0.960 | 0.979 | 0.979 |
| `ep_len_mean` | 16.7 | 17.7 | 15.0 | 10.1 | 7.16 | 5.01 | 3.07 | 3.10 |

Compare this shape with Act 1. The blind run rocketed to its ceiling by iteration
12 and flatlined. This one **dips first** (0.45 → 0.307 as exploration stops
paying off), then climbs steadily for 25 more iterations and is *still improving*
at the end. That is what learning to see looks like: slower to start, and it
keeps going.

Episode length fell 16.7 → 2.85 against a theoretical optimum of ~2.5 moves.

```
M3 VERDICT: PASS
  Live random baseline:   +0.48 reward/episode
  Trained mean reward:    +0.99 reward/episode
  [PASS] beats baseline by >= 0.40  (needs >= +0.88)
  [PASS] reaches goal in most episodes  (100%, needs >= 80%)
  [PASS] reset()/step() shapes unchanged from M2
  Mean steps to finish:   2.2
  Wall-clock training:    19.2 min for 20,000 steps
```

This run set itself an unusually **harsh** bar and cleared it anyway. The live
baseline drew +0.48 against a true value of ~+0.36 (50 episodes is a noisy
sample), which put the target at +0.88 against a ceiling of ~+0.985 — roughly
0.10 of headroom. The bar was deliberately **not** adjusted mid-milestone.

---

## What changed in the code

| file | change |
|---|---|
| `src/gametrainer/gridworld.py` | Added `RandomStart` wrapper (random start square + goal moved off the corner), `VISION_TASK_STEP_CAP = 25`, and `make_vision_task()`. **`GridWorldEnv` itself is unedited.** |
| `scripts/train_gridworld_vit.py` | Trains on `make_vision_task()`; the live baseline is now measured on the **same** task the agent plays. |
| `tests/test_random_start.py` | New. 10 tests, including three that pin "this Ground cannot be solved blind." |

Everything is done with **wrappers**. `GridWorldEnv` was never edited beyond
Brick 1's drawing method, so M2's tests stayed green throughout — the M3 scope
rule held.

`make_vision_task()` deliberately lives in **one** place, imported by both the
training script and the tests. Measuring the bar on a different game than the one
being played is the specific mistake this milestone made once already.

### The tests that stop this recurring

`tests/test_random_start.py` asserts, in under a second and with no training:

- a **blind** coin-flip agent fails the 80% goal bar
- a **uniform random** agent fails it
- a **sighted** oracle passes it

If someone later moves the goal back to a corner or loosens the step budget, the
maze silently becomes blind-solvable again and these tests fail immediately. That
is the whole point — the bug that cost a 20-minute run is now caught in a second.

---

## Lessons to carry into M4

1. **A reward curve cannot tell you *what* the agent used to win.** Before
   trusting a training number on any new Ground, measure the gap between a blind
   agent and a sighted oracle on that exact task. Small gap ⇒ the task cannot
   prove anything about perception.
2. **Greedy evaluation earns its keep.** Sampling hides degenerate policies;
   `argmax` exposes them. The blind agent looked fine stochastically and fell
   apart deterministically.
3. **Suspiciously clean numbers are a clue.** Exactly `-1.00` and exactly `100.0`
   pointed at a systematic cause, not a weak agent.
4. **Design the Ground so the trick doesn't work.** Corners and fixed
   start/goal positions let open-loop policies win. This will recur in richer
   environments in new shapes.
5. **Measuring the bar live saved the milestone twice.** The hardcoded baseline
   M2 used (−0.3) was wrong; the live values here ranged +0.04 to +0.48 across
   runs and tasks. Any fixed number would have been wrong for at least one of them.

### Known weakness, deliberately left alone

`BASELINE_EPISODES = 50` is noisy — it drew +0.48 against a true ~+0.36, setting
a bar 0.12 harsher than intended. Raising it would tighten the measurement, but
changing the bar mid-milestone is exactly what Brick 0 exists to prevent. **This
is an M4 change, not an M3 one.**

Also unresolved and worth naming: the frozen ImageNet ViT's features remain very
similar across positions (cosine ≥ 0.998). PPO learned to read them anyway once
it had a reason to, but the features were never the strong part of this pipeline.
If a future Ground needs finer spatial discrimination, unfreezing the last ViT
block is the documented next rung.

---

## Reproducibility note (read before quoting exact digits)

The comparison tables above are from the runs made during the milestone. The
episode **starting squares are random and unseeded**, so a re-run moves the
digits slightly. The *conclusions* are stable. A verification re-run on
2026-07-26 gave:

| quantity | during milestone | re-run | verdict |
|---|---|---|---|
| variant A gap (blind vs sighted) | +0.024 | +0.024 | unchanged — task needs no eyes |
| variant B gap | +0.019 | +0.020 | unchanged — random start fixes nothing |
| variant C gap | +1.733 | +1.727 | unchanged — eyes required |
| centre goal, 100 moves — headroom | +0.345 | +0.334 | still below the +0.40 margin |
| centre goal, 25 moves — headroom | +0.624 | +0.572 | still usable |
| centre goal, 25 moves — random goal rate | 53% | 57% | still fails the 80% bar |
| corner goal, 15 moves — blind goal rate | 99% | 99% | still blind-solvable |

Every "usable / not usable" verdict came out the same. **Quote the conclusions
and the approximate magnitudes, not the third decimal place.**

## Reproducing this

```bash
# The passing run (~20 min on CPU)
python scripts/train_gridworld_vit.py --steps 20000

# The task-quality tests (~1 second, no training)
python -m pytest tests/test_random_start.py -q

# The evidence
python docs/m3/experiments/blind_control.py        # blind agent scores +0.907
python docs/m3/experiments/which_task_needs_eyes.py # blind vs sighted, 4 variants
python docs/m3/experiments/calibrate_task.py        # step-budget calibration
```

**Not reproducible:** `diagnose_greedy.py` and `diagnose_features.py` analysed the
*blind* trained model, and `models/ppo_gridworld_vit/final_model.zip` was
overwritten by the successful run. Their outputs are preserved verbatim above and
in `run-logs/`; the scripts are kept as a record of method.

### File inventory

| path | what it is |
|---|---|
| `run-logs/m3_run_20k_FAIL.log` | The blind run, full console output |
| `run-logs/m3_run_vision_PASS.log` | The passing run, full console output |
| `experiments/diagnose_greedy.py` | Found the constant action probabilities *(historical)* |
| `experiments/diagnose_features.py` | Traced the signal decay through the pipeline *(historical)* |
| `experiments/blind_control.py` | The blind agent matching +0.907 |
| `experiments/which_task_needs_eyes.py` | Blind vs sighted across 4 task designs |
| `experiments/calibrate_task.py` | Step-budget calibration |

---

## One-line summary for the PDF

*M3 passed, but only after discovering that the milestone's own success metric
had been satisfied by an agent with its eyes shut — and that fixing it meant
redesigning the game, not the eyes.*
