# R1 - Docs Audit

> **Covers:** what was wrong with the docs on 2026-10-17, what was fixed, and what's still open.
> **Status:** current. **Last verified:** 2026-10-17.
> **Authority:** this file records the audit. Each fix lives in the doc it belongs to.

**Why audit docs at all?** One false claim makes a reader doubt every other claim. DOC_STANDARD calls this "a well-written document that is no longer true".

## 1. False or broken claims

| # | Problem | Fix | Status |
| :--- | :--- | :--- | :--- |
| 1 | MASTER_GUIDE "Trap 3" described an agent gaming a pixel reward. No agent was ever trained on Minesweeper. | Rewritten from the real story, in `lessons-learned.md` §3 | Done |
| 2 | Trap 4 had the wrong colours. Trap 5 said the fingerprint covers `src/` only (it covers the whole repo). Trap 7 described old code. | Fixed in `lessons-learned.md` | Done |
| 3 | `scripts/check_swap.py` is cited as M4's proof but was **never committed** (`git log --all` is empty). | Dated notes in `M4_Review.md`, `M4_Log.md`, `CHANGELOG.md` | **Open: Phillip** (see §3) |
| 4 | `docs/ARCHIVED_STARDEW_TRACK_B.md` was linked, but has never existed. | Links removed; history is in `architecture.md` §6 | Done |
| 5 | The M2 baseline was given as −0.3, −0.14 and +0.13. | Measured over 6,000 episodes: **−0.09**. All three were small samples (`RESULTS.md`) | Done |
| 6 | MASTER_GUIDE overclaims: "scan codes" (really virtual-key codes), "mss is a C-extension" (it's Python), "Strategy pattern" (it isn't). | Rewritten correctly in `concepts.md` and `architecture.md` | Done |
| 7 | PRD showed a never-built design as the architecture, and cited the deleted `src/cpp/clib.cpp`. | PRD rewritten; the old design is explained in ADR 0001 | Done |
| 8 | CHANGELOG had no R1 entry, mentioned an `escape()` that never existed, and listed a deleted `docs/README.md`. | R1 entry added; two dated corrections | Done |
| 9 | README had the wrong clone URL (`phillip/` instead of `Showerss/`) and said "Beginner" (the game says "Easy"). | README rewritten | Done |
| 10 | M4 "done when" listed Minesweeper (that was M5). | Gone with MASTER_GUIDE; correct in `RESULTS.md` | Done |

## 2. Structure changes

| Before | After | Why |
| :--- | :--- | :--- |
| `MASTER_GUIDE.md`: 800 lines, five jobs | `concepts.md`, `architecture.md`, `glossary.md`, `lessons-learned.md` | One job per file, so it's easy to find and keep true |
| Results copied in 3 places, all different | `RESULTS.md` only | One copy can't disagree with itself |
| Big decisions buried in Log tables | `docs/adr/` (5 records) | Shows *why*, not just *what* |
| PRD held a 2,200-word diary | PRD is a plan; diary moved to `r1/R1_Log.md` | A plan should be short |
| Two glossaries | `glossary.md` | Same reason as results |
| `ONBOARDING.md` (only a redirect) | Deleted; `docs/README.md` is the start page | Less clutter |
| Old m0/m1 diagrams had no status | Marked "archived" | So nobody mistakes them for today's design |
| Emoji and hype ("Holy Contract", "skyrocketed") | Plain, measured wording | Facts impress more than adjectives |
| No writing-style rule | DOC_STANDARD rule 8: write so anyone can follow | Keeps it this way |

## 3. Still open (needs Phillip)

| # | What | Why it matters |
| :--- | :--- | :--- |
| 1 | **Find `scripts/check_swap.py`** (maybe uncommitted on the Mac). Commit it, or leave the correction notes as they are. | It's M4's proof; right now it can't be re-run. |
| 2 | ~~**Choose a license**~~ **Done 2026-10-17:** MIT, in `LICENSE`. | With no license, nobody may legally reuse the code. |
| 3 | **Record a short GIF** of `check_hands.py` driving LibreMines for the README. | It's the most impressive thing the project does, and right now it's invisible. |
| 4 | ~~**Decide whether the AI rules file stays public.**~~ **Done 2026-10-17:** moved to IDE settings; mentions removed from the docs. | It's fine to share your AI workflow; just make it a choice. |
| 5 | **Add `ruff check .` to CI**, and move `setup.py` to `pyproject.toml`. *(Code/config, so not part of this docs pass.)* | The README promises a lint check that CI doesn't run. |
| 6 | **Run `check_hands.py` on macOS** to close R1. | The last R1 check still owed. |
