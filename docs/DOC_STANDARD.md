# Documentation Standard

> **Covers:** every `.md` file in this repository.
> **Status:** current. **Last verified:** 2026-08-14 (rule 6 gained a style
> rule for `M<N>_Log.md`/`M<N>_Review.md` — half the words, plain English —
> applied retroactively to M4's own files by explicit request; rest of the
> file re-read and still accurate).
> **Authority:** this file wins on *how* docs are written. `docs/PRD.md` wins on
> *what* gets built.

---

## Why this exists

This repo is evidence of how I work, not just a place code lives. The bar is a
**lab notebook**, not a brochure: a reader should be able to open any file, know
immediately whether to trust it, and reconstruct how every number in it was
produced.

The failure mode this standard exists to prevent is **a well-written document
that is no longer true**. That is worse than a plain one that is right, because
once a reader catches one stale claim they stop trusting all the others.

---

## The seven rules

### 1. Every doc opens with a status header

No exceptions, including this file.

```markdown
> **Covers:** what this document is responsible for.
> **Status:** current | superseded by <file> | archived — historical reference.
> **Last verified:** YYYY-MM-DD (what was true at that moment).
```

"Last verified" means *someone actually checked*, not *someone last edited*.
Bumping the date is a claim. Don't make it idly.

### 2. One authority per question

Two documents may not answer the same question. If they overlap, one of them
links to the other instead of repeating it.

| Question | The one file that answers it |
| :--- | :--- |
| What are we building, and in what order? | `docs/PRD.md` |
| How is a doc written? | `docs/DOC_STANDARD.md` (this file) |
| What happened, and when? | `docs/CHANGELOG.md` |
| How do I get oriented as a newcomer? | `docs/ONBOARDING.md` |
| What does the current milestone require? | `docs/m<N>/M<N>_ToDo.md` |
| How do I work with Phillip? | `CLAUDE.md` |
| What does an RL/project term mean? | `docs/ONBOARDING.md` §13 (RL vocabulary) — `CONTEXT.md` only for implementation-specific terms not covered there |

When two files disagree, that is a **bug**, and it gets fixed at the same
priority as a broken test.

### 3. A result is a number plus its conditions

Never "it worked" or "training improved". A reported result carries everything
needed to challenge or repeat it:

- the **number**, and the **baseline it beat** — measured in the same run, not
  quoted from memory,
- **hardware** (CPU/GPU) and **wall-clock time**,
- **seed** and **timestep count** where they apply,
- the **command** that produced it.

> **Worked example (M3, the standard to match):** live random baseline `+0.48`,
> trained `+0.99`, goal reached in 100% of greedy episodes, `reset()`/`step()`
> shapes unchanged, 19.2 min on CPU.
>
> M2 hardcoded its baseline as `-0.3` and the real figure was `+0.13`. That is
> exactly the mistake this rule exists to stop.

### 4. Negative and surprising results stay in the record

A result that turned out to be wrong is **corrected in place with a dated note**,
never deleted and never quietly rewritten.

This is not humility for its own sake — a corrected result is stronger evidence
than one that was right first time, because it shows the check happened at all.
The M3 "GridWorld was solvable blind" entry is the model: what was claimed, how
it was caught, what it actually meant, what changed.

### 5. Current and historical code are labelled, always

This repo's history and archived documentation describe two generations of code
(see `docs/ONBOARDING.md` §5), although Track B's implementation was deleted on
2026-08-04. Any historical reference to a file states which generation it belongs to:

- **Track A** — the current milestone path. Live, tested, trustworthy.
- **Track B** — the retired Stardew-first prototype. Historical reference only; its implementation remains in git history.

An unlabelled reference is assumed Track A, so labelling Track B is mandatory.

### 6. Milestone folders have a fixed shape

```
docs/m<N>/
├── M<N>_ToDo.md      # written FIRST — scope, design, bricks, "Done when…"
├── M<N>_Log.md       # written DURING — one entry per brick, the day it closes
├── M<N>_Review.md    # written LAST — what happened, results table, what I'd redo
└── *.pdf             # generated retrospectives, kept as the historical record
```

`M<N>_ToDo.md` is the plan and must exist before the first brick.
`M<N>_Log.md` is the lab notebook and is filled in **as the work happens**, not
reconstructed afterwards — it holds the run numbers, the decisions and the
surprises that the review is later assembled from. `M<N>_Review.md` is the
retrospective and must exist before the milestone closes.

The three do not overlap (rule 2): the ToDo owns *the plan*, the Log owns *the
record of doing it*, the Review owns *what it meant*.

> **Added 2026-07-30 (M4).** M0–M3 have no `M<N>_Log.md` and are not expected to
> grow one — per the scope note below, a new standard applies to the next
> milestone, never retroactively.

> **Added 2026-08-14 (M4 close).** `M<N>_Log.md` and `M<N>_Review.md` are
> **half the words, plain English.** A few short sentences per heading, not a
> full technical write-up — cover what changed, the one thing that surprised
> you, and the number that proves it. Rule 3 (number + baseline + hardware +
> wall-clock + seed + command) is unchanged and still required in full; this
> rule is about narrative, not evidence. Don't list every test case in prose —
> say how many and what they cover. Don't repeat a decision here if it's
> already a row in the Decisions log table — that table is its one authority
> (rule 2). CS terms are fine; define a new one in one plain clause the first
> time it appears (CLAUDE.md's "no jargon dumps" rule, restated here because
> logs get skimmed, not studied).
>
> Applied retroactively to `M4_Log.md`/`M4_Review.md` themselves by explicit
> request — normally a new standard applies to the next milestone only, per
> the scope note below, but the files you're reading now are already in the
> new style rather than the one that produced them.

**Reviews are markdown in the repo.** PDFs are kept alongside as generated
artefacts — markdown is what diffs, greps, and renders on GitHub.

### 7. A milestone is not closed until its docs are

Extending `CLAUDE.md` §5 "Closing a milestone". Contract tests green and the
experiment script printing PASS are necessary but no longer sufficient. Also
required:

- [ ] `M<N>_Review.md` exists, with a results table meeting rule 3
- [ ] `docs/CHANGELOG.md` has the milestone entry
- [ ] every doc whose claims the milestone changed has a bumped **Last verified**
- [ ] no two docs contradict each other (rule 2)

---

## Scope note

This standard governs **how the record is kept**. It does not change the build
order, the milestone plan, or the testing policy — `docs/PRD.md` and `CLAUDE.md`
§5 still own those.

Per `CLAUDE.md` §5, a new standard applies to the **next** milestone and is not
applied retroactively to finished work. M0–M3 are closed under the rules that
existed at the time; where they are factually stale, they get a dated correction
(rule 4), not a rewrite.

**This standard takes effect at M4.**
