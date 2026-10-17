# GameTrainer - Product Plan (PRD)

> **Covers:** what we're building, in what order, and when each step counts as done.
> **Status:** current. **Last verified:** 2026-10-17 (M0–M5 closed; R1 code done, macOS re-run owed).
> **Authority:** this file decides *what gets built*. [`DOC_STANDARD.md`](DOC_STANDARD.md) decides *how docs are written*.

> **Rewritten 2026-10-17 (R1 docs pass).** Shortened to a plan. What moved: the R1 brick diary went to [`r1/R1_Log.md`](r1/R1_Log.md) and the glossary to [`glossary.md`](glossary.md). The original, never-built `GameEnvironment` design went to [ADR 0001](adr/0001-factory-not-gameenvironment.md). The old text is in git history.

## 1. The pitch

A **PRD** (Product Requirements Document) says what to build and why. This one says:

**Teach a computer to play games by trial and error, through one standard plug, so any game works with any learner.** We don't invent the learner. We build the plug, and prove it by starting tiny and growing.

## 2. The model

| Part | Is | Job |
| :--- | :--- | :--- |
| **Ground** | the game | show what's happening, give a score |
| **AI** | the player | eyes see → brain decides → hands act |
| **Link** | Gymnasium | the standard plug (`reset()`, `step()`) |

- **We build:** the Grounds, the Link wiring, the eyes for Minesweeper, the hands.
- **We borrow:** the brain (PPO) and the picture-eyes backbone (pretrained ViT). *Why:* those are solved, hard-to-get-right problems.

Full explanation: [`concepts.md`](concepts.md).

## 3. Scope: crawl, then walk

We start tiny on purpose. *Why:* when something breaks, there's only one thing it could be.

1. **CartPole** (a built-in game): prove the plug and the brain work.
2. **GridWorld** (our own game): prove we can build a Ground.
3. **Eyes**: learn from a *picture* of the grid, not numbers.
4. **Swappable**: change games with a config file only.
5. **Hands**: drive a real desktop game with real keys.
6. **Stardew Valley**: just another profile. *(stretch)*

**Not doing (on purpose):**
- No reading game memory. *Why:* we want a method that works on any game, from the screen alone.
- No automatic control discovery. Keys are written in the profile.
- No C++ in v1 ([ADR 0004](adr/0004-python-ctypes-hands.md)). No cloud. Runs locally.

## 4. The contract

Every Ground must do this. It's the one rule that never bends:

```python
observation, info = env.reset()
observation, reward, terminated, truncated, info = env.step(action)
```

How the code meets it: [`architecture.md`](architecture.md). Diagrams: [`UML_FULL.md`](UML_FULL.md).

## 5. Milestones

Each milestone has **one job** and a "done when" written *before* starting. *Why:* so the bar can't quietly drop once the work gets hard.

| # | Milestone | Done when... | Status |
| :--- | :--- | :--- | :--- |
| **M0** | Setup | CartPole runs 100 random steps, no crash | PASS |
| **M1** | Borrow the brain | PPO clearly beats random on CartPole | PASS |
| **M2** | Build our own Ground | PPO learns GridWorld and reaches the goal | PASS |
| **M3** | Add the eyes | GridWorld learned from pictures only, on CPU | PASS |
| **M4** | Make it swappable | Swap games by YAML, zero code changes | PASS |
| **M5** | Add the hands | Drive a real game window (LibreMines) live | PASS |
| **R1** | Cleanup & OOP pass | Same behaviour, less copy-paste (see below) | code done |
| **M6** | Stardew *(stretch)* | Runs as "just another profile" | next |

Numbers for every row: [`RESULTS.md`](RESULTS.md). Pace: a few hours a week.

### R1: Cleanup & OOP pass (post-M5)

Not a feature milestone. No new features, and no PASS bar moves.

**Done when:** `pytest` and `ruff check .` pass, every experiment that passed before still prints PASS, the contract is unchanged, and `UML_FULL.md` matches the code.

| Brick | What | Date |
| :--- | :--- | :--- |
| 1 | Two real bugs: dependency check, profile printout | 2026-10-17 |
| 2 | Hands get a real abstract base class | 2026-10-17 |
| 3 | GridWorld: move table, public handles | 2026-10-17 |
| 4 | Minesweeper env, rewards, vision lose copy-paste | 2026-10-17 |
| 5 | `Profile.ppo_settings()` | 2026-10-17 |
| 6 | Referee moves into the package | 2026-10-17 |
| 7 | M1 / M2 share training setup | 2026-10-17 |
| 8 | TUI menu becomes one table | 2026-10-17 |
| 9 | `check_hands` sends one key sequence | 2026-10-17 |
| 10 | ViT extractor tidy-up | 2026-10-17 |
| 11 | One hands class per OS | 2026-10-17 |
| 12 | One screen class per OS | 2026-10-17 |
| 13 | UML catches up with the code | 2026-10-17 |
| 14 | UML truth pass + design and docs review | 2026-10-17 |
| 15 | Docs rewrite: simpler, one source per fact | 2026-10-17 |

Each brick's details and how it was checked: [`r1/R1_Log.md`](r1/R1_Log.md).
**Still owed:** a live `check_hands.py` run on macOS. Windows passed 4/4 on 2026-10-17.

### Later (v2+, out of scope for now)

- **M7:** Linux hands (`uinput` / X11 / Wayland).
- **M8:** an optional C++ input extension, if a fast game ever needs it.
- **M9:** train on several games at once.

## 6. Risks

| Risk | Plan |
| :--- | :--- |
| Stardew has no score | Define one (money, crops). That's why it's last. |
| ViT is slow on CPU | Small images (224×224), frozen backbone. |
| PPO is fussy to tune | Use defaults until everything else works. |
| Window focus is flaky | Hands refuse to type unless the game is in front. |

> **Note - 2026-09-10 (kept per DOC_STANDARD rule 4).** An earlier draft said live hands were Windows-only. On 2026-09-07 a macOS version was built and passed all four M5 checks, so hands are Windows **and** macOS. Linux is still open (M7).

## 7. For an AI coding assistant

Build in milestone order. Don't scaffold later phases early. Stop at each "done when". Never change `reset()` / `step()`.
