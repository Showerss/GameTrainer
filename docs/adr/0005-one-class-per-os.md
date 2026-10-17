# ADR 0005: One class per operating system

**Status:** Accepted (R1).

## Context
Before R1, every hands and screen method asked `if mac ... else ...` inside itself. Adding a third OS would mean editing every method.

## Decision
An abstract parent holds what all OSes share. Each OS gets its own child class. One small function picks the right child.

```
KeyboardInput (shared focus rules)        GameWindow (shared screenshot)
 ├─ WindowsKeyboardInput                   ├─ WindowsGameWindow
 └─ MacKeyboardInput                       └─ MacGameWindow
picked by keyboard_for_this_os()          picked by game_window_for_this_os()
```

## Consequences
- **Good:** "which OS?" is asked in exactly two places. Linux = new classes, no edits to old ones (the **Open/Closed principle**).
- **Cost:** two families that must be paired by hand, linked by a bare number (`hwnd`, which is a process ID on macOS). A fix is proposed in [R1_Review item 2](../r1/R1_Review.md).
