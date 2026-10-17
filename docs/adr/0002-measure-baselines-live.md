# ADR 0002: Measure the random baseline live, every run

**Status:** Accepted (M3).

## Context
To prove learning, the agent must beat a random player (the **baseline**). M2 typed in a remembered number, −0.3. It was a small, noisy sample, and the 6,000-game value is −0.09 ([RESULTS](../RESULTS.md#note-the-m2-baseline-corrected-2026-10-17)).

## Decision
Every experiment measures the baseline itself, on the exact same game, at the start of the run. The bar is "beat the live baseline by a stated margin".

## Consequences
- **Good:** if the game changes, the bar changes with it. No stale numbers.
- **Good:** one bar shape works for every profile (M4 relies on this).
- **Cost:** a few extra seconds per run. Small samples still wobble, so we use 50 episodes.
