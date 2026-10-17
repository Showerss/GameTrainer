# ADR 0004: Python `ctypes` hands, no C++

**Status:** Accepted (M5).

## Context
Real key presses need operating-system calls (`SendInput` on Windows, Quartz on macOS). An earlier version used a C++ extension. **`ctypes`** is a built-in Python module that calls those system functions directly.

## Decision
Write the hands in pure Python with `ctypes` (Windows) and PyObjC (macOS). No compiler needed.

## Consequences
- **Good:** anyone can `pip install` and run it; nothing to compile.
- **Good:** fast enough. The 8×8 board reader (~133 ms/frame) is the slow part, not the keys.
- **Cost:** `ctypes` doesn't check struct sizes for you. A wrong size made every key silently fail during the pre-flight test, so `input.py` now checks the size when it's imported.
