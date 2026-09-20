# CLAUDE.md — GameTrainer

## Commands & layout

- Run tests: `pytest`  (fast, deterministic contract tests — see Testing Policy)
- Run a milestone experiment: `python scripts/experiment_m<N>.py`  → prints PASS or FAIL
  (TODO: script does not exist yet for M3 — build it as part of M3, not before)
- Watch a training run: `tensorboard --logdir runs/`  (SB3 writes here when `tensorboard_log="runs/"` is set)
- Layout: `ground/` = the game environment · `ai/` = agent (eyes + brain + hands) · `link/` = Gymnasium adapter
- Milestone summaries live in the **PRD**.

## Who I am (this matters more than the code)

- **I'm here to learn, not just to ship.** This project's #1 job is that *I understand it*. A finished feature I don't understand is a failure.
- **I learn slowly and well — brick by brick.** Explain things simply. No jargon dumps. Define every new term the first time you use it, in one plain sentence.
- **I have light hours each week.** Small, finished steps beat big unfinished ones.
- **I'm a newbie developer.** Keep every response simple enough that a beginner can follow the whole conversation.

## How to work with me

1. **One brick at a time.** Do the smallest next step only. Never scaffold future phases ahead of where we are.
2. **Teach as you go.** *Before* writing code: say in plain English what we're about to do and why. *After*: explain what it does in 2–3 simple lines.
3. **Draw it first.** When introducing a new structure, data flow, or loop, sketch it as a small ASCII or Mermaid diagram *before* explaining in words.
4. **Stop at every checkpoint.** At each milestone's "Done when…", pause. Confirm I actually get it before moving on — if it's a new idea, ask me to say it back in my own words.
5. **Log every finished brick.** When a brick is done, add a 3–5 line summary to the PRD under that milestone: what changed, why, and how to verify it. I use these for sprint retrospectives.
6. **If I seem lost, slow down — don't pile on.** Switch to a metaphor or a smaller example. More detail is the wrong move; simpler is the right one.

## The shared language (use these words, they're how I think)

- **Ground** = the game. **AI** = eyes (ViT) + brain (PPO) + hands (input). **Link** = the Gymnasium socket.
- The loop is always: **observe → act → reward → repeat.**
- **We build** the Ground and the Link. **We borrow** the brain (PPO) and the eyes backbone (pretrained ViT).

## Project rules (do not bend these)

- **NEVER run `git commit` or `git push`, never stage files, never write commit messages.** Commits are strictly Phillip's job. Leave all changed files in the working directory for review, under any circumstances.
- **Never break the Gymnasium contract** (`reset()` / `step()`). Any Ground must plug into any AI — that swappability is the entire point of the project.
- **Build in order: M0 → M6.** Don't jump ahead. Stardew is the *last* thing, not the first.
- **v1 constraints:** Python only (no C++), no memory reading, local only.
- **Hardware:** early phases run on CPU. The AMD GPU only matters at the ViT phase (M3) — don't let GPU setup block earlier steps.
- **Results are reproducible.** Never report a training result without its baseline, hardware, and wall-clock time. Never delete a wrong result — correct it with a dated note.

---

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines but it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Testing Policy

**Test the promises, not the plumbing.**

A test earns its place when something would break *silently* without it. Ask: how likely is this to break, and how bad is it if it breaks quietly? If both are low, skip the test — and say so out loud.

### Always test

- **The Gymnasium contract** (`reset()` / `step()` shapes). This is the one promise the whole project rests on: any Ground must plug into any AI. A contract test here is worth ten tests anywhere else.
- **Logic with a single right answer:** rewards, movement rules, walls, termination. Fast, deterministic, cheap to keep forever.

### Deliberately don't test

- Menu wiring, print statements, argument parsing — glue that fails loudly the first time you run it.
- Anything where writing the test costs more than the bug it would catch.

A skip is a decision, not a gap. Write the *why* next to it in the milestone to-do.

### Tests vs. experiments — keep these separate

- A **test** is fast and deterministic: same input, same answer, every time. It runs on every change via `pytest`.
- An **experiment** asks "did the agent actually learn?" It is slow and random — it can pass today and fail tomorrow on identical code. It belongs in `scripts/experiment_m<N>.py`, which **prints a PASS/FAIL verdict**, run by hand once per milestone.

Never put an experiment in the test suite. Training only gets slower from M3 on, and a test you learn to skip is worse than no test at all.

### Closing a milestone

Write the "Done when…" in one sentence **before** starting. Then:

- **Don't move it mid-milestone.** If you discover a better standard, it applies to the *next* milestone — never retroactively to finished work.
- **Closed** = contract tests green **and** the milestone's experiment script prints PASS.
- "Free of errors" is not achievable and isn't the goal. Tests buy **change confidence** — the freedom to edit without fear. A test that doesn't buy that, cut.

## When in doubt

Ask me. A short question now beats a wrong assumption built into the code.