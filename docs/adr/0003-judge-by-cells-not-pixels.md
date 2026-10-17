# ADR 0003: Judge Minesweeper by cell states, not pixels

**Status:** Accepted (M5).

## Context
To check "did our key press work?", the first idea was counting changed pixels. In testing, a flag changed 237 pixels, but a useless reveal changed 342. The move that did nothing scored higher.

## Decision
Read the screen into an 8×8 grid of **cell states** (0–8, hidden, flagged, mine), and judge only that grid. Pixel counts are printed as evidence but never decide anything.

## Consequences
- **Good:** "exactly one cell changed, the one we aimed at" is a clear yes/no.
- **Good:** the reward uses the same grid, so scoring can't be fooled by redraws.
- **Cost:** the board reader must be right. So it raises an error instead of guessing, and is tested on real screenshots.
