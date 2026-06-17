# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

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

---

## Who I am (this matters more than the code)
 
- **I'm here to learn, not just to ship.** This project's #1 job is that *I understand it*. A finished feature I don't understand is a failure.
- **I learn slowly and well — brick by brick.** Explain things simply. No jargon dumps. Define every new term the first time you use it, in one plain sentence.
- **I have light hours each week.** Small, finished steps beat big unfinished ones.
## How to work with me (the rules)
 
1. **One brick at a time.** Do the smallest next step only. Never scaffold future phases ahead of where we are.
2. **Teach as you go.** *Before* writing code: say in plain English what we're about to do and why. *After*: explain what it does in 2–3 simple lines.
3. **Stop at every checkpoint.** At each milestone's "Done when…", pause. Confirm I actually get it before moving on — ask me to say it back in my own words if it's a new idea.
5. **If I seem lost, slow down — don't pile on.** Switch to a metaphor or a smaller example. More detail is the wrong move; simpler is the right one.
## The shared language (use these words, they're how I think)
 
- **Ground** = the game. **AI** = eyes (ViT) + brain (PPO) + hands (input). **Link** = the Gymnasium socket.
- The loop is always: **observe → act → reward → repeat.**
- **We build** the Ground and the Link. **We borrow** the Brain (PPO) and the Eyes backbone (pretrained ViT).
## Project rules (do not bend these)
 
- **Never break the Gymnasium contract** (`reset()` / `step()`). That swappability is the entire point of the project.
- **Build in order: M0 → M6.** Don't jump ahead. Stardew is the *last* thing, not the first.
- **v1 constraints:** Python only (no C++), no memory reading, local only.
- **Hardware:** early phases run on CPU. The AMD GPU only matters at the ViT phase (M3) — don't let GPU setup block earlier steps.

## When in doubt
 
Ask me. A short question now beats a wrong assumption built into the code.
 