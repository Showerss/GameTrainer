# ADR 0001: Build games with a factory function, not a wrapper class

**Status:** Accepted (M4). Replaces the original PRD design.

## Context
The first plan was one big class, `GameEnvironment`, holding the eyes, hands, scorer and profile for every game. A class that knows everything is called a **God object**. *Why that's bad:* every change touches it.

```
Planned (never built)              Built
GameEnvironment                    make_env(profile)
 ├─ Perception                       ├─ "cartpole"    → gym.make("CartPole-v1")
 ├─ InputController                  ├─ "gridworld"   → GridWorldEnv(...)
 ├─ RewardCalculator                 └─ "minesweeper" → MinesweeperEnv(...)
 └─ Profile
```

## Decision
One function, `make_env(profile)`, reads the profile and returns a normal Gymnasium env. Each game is its own self-contained env class.

## Consequences
- **Good:** no extra layer, so PPO gets a plain Gymnasium env and Gymnasium's own wrappers just work.
- **Good:** one place to look when adding a game.
- **Cost:** `make_env` is an `if`-chain. With many games it should become a lookup table (a **registry**). Planned for M6; see [R1_Review item 7](../r1/R1_Review.md).
