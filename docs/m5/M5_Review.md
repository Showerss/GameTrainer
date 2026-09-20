# M5 — Milestone Review (the sprint retrospective)

> **Covers:** what Milestone 5 proved, what failed along the way, and what we learned.
> **Status:** current. **Last verified:** 2026-09-20 (verified PASS live on both macOS and Windows; all 8 bricks complete).
> **Authority:** `docs/m5/M5_ToDo.md` owns the plan. `docs/m5/M5_Log.md` owns the lab notebook. This file owns *what it all meant*.

---

## 1. Executive Summary

Milestone 5 crossed the boundary from toy simulated environments to a **real, external, desktop game process** (`LibreMines`). We proved that GameTrainer can autonomously drive a live application through real OS window capture and native keystroke injection without human intervention.

The milestone bar was not "training improved"; it was a four-part behavioral proof (`scripts/check_hands.py`) requiring:
1. **Real effect:** Moving to cell `(1, 2)` and flagging it changes *exactly* that cell on the 8×8 grid.
2. **Negative control (hands):** Running the identical sequence with `NullInput` produces *zero* grid changes.
3. **Negative control (eyes):** A frozen-frame observation stays completely stationary while live hands mutate the screen.
4. **Unattended reset:** The agent resets the game 20 consecutive times via keyboard chord (`Ctrl+R` on Windows, `Cmd+R` on macOS), producing 20 clean boards with zero mouse clicks.

All four controls passed live on both **macOS (Apple Silicon arm64)** and **Windows 11 (x64)**.

---

## 2. Results Table (Rule 3)

Every live behavioral check and verification run recorded under identical, reproducible conditions:

| Date | Platform / Hardware | Command | Control 1 (Keys live) | Control 2 (NullInput) | Control 3 (Frozen frame) | Control 4 (Reset) | Wall-clock | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-08-26 | Windows 11 x64, Python 3.14.0 | `.venv/Scripts/python.exe scripts/check_hands.py` | Not run | Not run | Not run | Not run | < 0.1s | **NOT RUN** (Brick 0 failing guardrail) |
| 2026-09-07 | macOS 26.3.1 (Apple Silicon arm64), Python 3.14.7 | `.venv/bin/python scripts/check_hands.py` | PASS (target `(1, 2)`, exactly 1 cell changed) | PASS (0 cells changed, 0 px) | PASS (live obs changed 1, frozen obs changed 0) | PASS (20/20 clean boards, 0 mouse clicks) | 16.8s | **PASS** |
| 2026-09-15 | Windows 11 x64, Python 3.14.5 | `.venv/Scripts/python.exe scripts/check_hands.py` | PASS (target `(1, 2)`, 1 cell changed, 93,924 px) | PASS (0 cells changed, 0 px) | PASS (live obs changed 1, frozen obs changed 0) | PASS (20/20 clean boards, 0 mouse clicks) | 22.4s | **PASS** |

Current automated test suite status after the PR-review follow-up: **110 passed,
2 skipped** in 2.79s on Linux CI. The live milestone proof still remains the
macOS and Windows PASS runs recorded above.

---

## 3. What We Learned & Key Surprises

1. **Pixel counts lie; cell states don't.**
   Early spikes attempted to judge actions by pixel counts. However, a flag action changed 237 px, while an ineffective reveal on an already-revealed cell changed 342 px due to cursor redraws. Judging by the classified 8×8 grid state eliminated false positives and provided deterministic verification.

2. **The keyboard cursor highlight was an invisible state.**
   Our initial vision classifier (`classify_cell`) only recognized two background shades: hidden grey `(70, 70, 70)` and revealed dark `(26, 26, 26)`. When navigating via keyboard, LibreMines tints the active cell a third flat grey `(185, 185, 185)`. Mouse-captured fixtures never revealed this. We caught it live, added `_CURSOR_BODY` recognition, and created dedicated test fixtures.

3. **Desktop automation requires deep OS awareness.**
   - On **Windows**, background agent subshells execute in isolated virtual desktops (`exebox-...`), causing `EnumWindows` to miss top-level interactive windows. We resolved this by explicitly binding to `OpenDesktopW("Default")`. Additionally, `AttachThreadInput` was required to overcome Windows foreground focus locks, and 40-byte `INPUT` struct alignment was enforced.
   - On **macOS**, Qt translates menu shortcuts so that `Ctrl+R` becomes `Cmd+R`. Keystrokes sent via Quartz `CGEventPost` required `CGEventFlagMaskCommand` to trigger resets. Furthermore, official ad-hoc binaries required local re-signing (`codesign --deep`) to seal bundled dynamic libraries.

4. **Vision computation sets the step rate ceiling.**
   Processing a maximized 2576×1408 desktop window took ~133 ms per frame on CPU (43 ms board localization, 81 ms 64-cell classification). This establishes an upper bound of ~7 environment steps per second on CPU.

---

## 4. What We'd Redo If Starting Over

1. **Capture fixtures in active operational mode:**
   The test fixtures in Brick 2 were saved using mouse interaction, blinding us to keyboard cursor rendering until Brick 7. Always capture test fixtures in the exact control mode the agent will use.

2. **Crop immediately after board localization:**
   Scanning the entire 1440p frame on every frame grab wasted CPU cycles on blank window borders. Caching the board bounding box or cropping the ROI immediately would reduce classification time from 133 ms to ~20 ms.

3. **Account for headless / subshell execution environments early:**
   Virtual desktop station isolation on Windows was discovered during live script execution. Automated test harnesses for OS-level glue should assume non-interactive session isolation from the start.

---

## 5. DOC_STANDARD Rule 7 Closeout Checklist

### Short post-PR review follow-up

After the milestone landed, Copilot review still found four practical gaps:

- the live factory could fail quietly instead of telling us what went wrong,
- tests could accidentally touch a real LibreMines window left open on the desktop,
- the vision code still missed some real board states, and
- one negative-control script path was not truly replaying the same move list.

Those are now closed. In plain English: the game setup now fails honestly, the
tests stay in their sandbox, the board reader covers the missing `4`-`8` and
mine cases, and the control proof now compares like with like.

- [x] `docs/m5/M5_Review.md` exists, with a results table meeting Rule 3.
- [x] `docs/CHANGELOG.md` has the milestone entry.
- [x] Every doc whose claims the milestone changed has a bumped **Last verified** (`M5_Log.md`, `M5_Review.md`, `CHANGELOG.md`, `ONBOARDING.md`, `PRD.md`, `README.md`).
- [x] No two docs contradict each other (Rule 2).
