# Architecture Decision Records (ADRs)

> **Covers:** the big design choices, one short file each.
> **Status:** current. **Last verified:** 2026-10-17.
> **Authority:** each ADR owns the *why* of one decision.

An **ADR** is a short note: the problem, the choice, and what it cost. *Why keep them:* code shows *what* we built; ADRs show *why*, so nobody re-argues settled choices.

| # | Decision | When |
| :--- | :--- | :--- |
| [0001](0001-factory-not-gameenvironment.md) | Build games with a factory function, not a wrapper class | M4 |
| [0002](0002-measure-baselines-live.md) | Measure the random baseline live, every run | M3 |
| [0003](0003-judge-by-cells-not-pixels.md) | Judge Minesweeper by cell states, not pixels | M5 |
| [0004](0004-python-ctypes-hands.md) | Python `ctypes` hands, no C++ | M5 |
| [0005](0005-one-class-per-os.md) | One class per operating system | R1 |

**Format:** Status · Context (the problem) · Decision (the choice) · Consequences (good and bad).
**Rule:** never edit an old decision. If it changes, write a new ADR that replaces it.
