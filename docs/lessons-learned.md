# Lessons Learned

> **Covers:** the traps we hit, what fooled us, and how we know the fix works.
> **Status:** current. **Last verified:** 2026-10-17. Every trap below was re-checked against the code and the milestone logs.
> **Authority:** this file owns the "what went wrong" stories. Full detail is in each milestone's Log.

> **Correction - 2026-10-17.** These traps used to live in `MASTER_GUIDE.md`, and four of them were wrong. One (an agent "gaming" a pixel reward) described something that never happened. Two others got the colours and the fingerprint scope wrong, and one described code that has since changed. They're fixed here. The old text is in git history (`docs/MASTER_GUIDE.md` before this date).

The common thread: **most of these bugs didn't crash.** They gave believable, wrong numbers. So the habit is: *measure the case where nothing should happen.*

---

## 1. The blind agent (M3)

- **What fooled us:** the first picture-trained agent scored +0.905. It looked like the eyes worked.
- **The truth:** it pressed DOWN 53% and RIGHT 47% on *every* square. A script with no eyes, playing that same coin flip, scored +0.907.
- **Why:** the goal was in the bottom-right corner. Walls just stop you, so "go down or right" always ends at the goal, without looking.
- **Fix:** random start square, goal moved to the centre (`RandomStart`). Now a blind agent reaches the goal 12% of the time; a seeing one, 100%.

## 2. Windows lies about where windows are (M5)

- **What fooled us:** screenshots looked normal, but showed the wrong window, one monitor over.
- **Why:** on high-DPI screens Windows reports *scaled* positions, while screenshots use *real* pixels.
- **Fix:** `screen.py` calls `SetProcessDpiAwarenessContext` when it's imported, before any window call.

## 3. Pixel counts can't tell a real move from a fake one (M5)

- **What fooled us:** in the pre-flight test, we judged "did the key work?" by counting changed pixels.
- **The truth:** placing a flag changed 237 pixels, while a *useless* reveal on an already-open cell changed 342. More pixels changed for the move that did nothing.
- **Fix:** judge by the 8×8 **cell grid**, not pixels. "Exactly one cell changed, and it was the one we aimed at" is a yes/no fact.

## 4. The cursor changes a cell's colour (M5)

- **What fooled us:** board-reading tests passed, then live play crashed with `UnreadableCell`.
- **Why:** with keyboard control, LibreMines tints the cell under the cursor a lighter flat grey, `(185, 185, 185)`. Our test screenshots were taken with the mouse, so they never showed it. Hidden cells are normally `(70, 70, 70)`.
- **Fix:** the reader knows three backgrounds: hidden, cursor, revealed. *Lesson:* capture test images the same way the agent will play.

## 5. The code fingerprint missed new files (M4)

- **What fooled us:** M4 proves "no code changed between runs" with a hash of the code. But a brand-new, uncommitted file was invisible to it.
- **Why:** `git ls-files` only lists files git already tracks.
- **Fix:** hash **every** `.py` in the repo, tracked *and* untracked (`git ls-files -c -o --exclude-standard`). A test locks it in.

## 6. Background shells can't see your windows (M5)

- **What fooled us:** "LibreMines not found", while it was open on screen.
- **Why:** Windows can run background programs on a separate, hidden desktop.
- **Fix:** `screen.py` attaches to the main desktop (`OpenDesktopW("Default")`) before searching.

## 7. Ctrl+R is Cmd+R on a Mac (M5)

- **What fooled us:** the reset shortcut did nothing on macOS.
- **Why:** LibreMines is a Qt app, and Qt turns "Ctrl" into the Command key on Macs.
- **Fix:** the Mac hands map the Ctrl modifier to Command (`_MAC_MODIFIER_FLAG` in `input.py`). Verified live, not assumed.

## 8. The invisible window border (R1)

- **What fooled us:** a maximised window broke board-finding.
- **Why:** Windows counts an invisible ~8 px border around windows. When maximised, that border sits off-screen and captures as black.
- **Fix:** ask the Windows window manager (DWM) for the *visible* frame instead. The fix is in; whether it fully explains the original failure is still being checked (see `docs/PRD.md` R1 notes).

## 9. Small samples make noisy baselines (M2, found in R1)

- **What fooled us:** three docs gave three GridWorld baselines: −0.3, −0.14, +0.13.
- **The truth:** all three were real 20–50 game samples. Over 6,000 games it's **−0.09**.
- **Fix:** measure baselines live, over enough games. See [RESULTS.md](RESULTS.md#note-the-m2-baseline-corrected-2026-10-17).
