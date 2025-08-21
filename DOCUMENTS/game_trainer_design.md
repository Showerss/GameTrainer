# GameTrainer Design Document (Revised)

> **Scope note (ethics & legality):** This project is intended for **local, single‑player games** (e.g., Stardew Valley–like titles) and **offline** experimentation on processes **you own and control**. Do **not** use, distribute, or adapt this for multiplayer or anti‑cheat–protected titles. Avoid any circumvention techniques aimed at defeating third‑party protections. This design purposefully excludes such material.

---

## 1. Overview

### 1.1 Purpose
Define a clean, maintainable architecture for **GameTrainer**, a hybrid C/Python application that:
- Reads well‑defined regions of a target process’s memory to observe game state.
- Automates benign actions via simulated input and pixel cues.
- Provides a GUI to configure profiles, bot behaviors, and safety limits.

### 1.2 Goals
- **Reliability:** predictable behavior, defensive error handling, no resource leaks.
- **Maintainability:** SOLID-aligned modularity, typed Python, documented C API.
- **Testability:** unit + integration tests with a dummy target process.
- **Portability (Windows-first):** WinAPI-backed C library with narrow, stable surface.

### 1.3 Out of Scope
- Kernel‑mode drivers, stealth/evasion, thread hijacking, manual mapping, SEH abuse, DKOM. (Removed for ethics, safety, and portfolio fitness.)

---

## 2. User Stories & Requirements

### 2.1 User Stories
- **US-01:** As a user, I can attach to a local process by name or PID and confirm attachment with clear status.
- **US-02:** As a user, I can define **profiles** (pointer chains, AOB patterns, pixel regions, keybinds, timings) and save/load them.
- **US-03:** As a user, I can start/stop **automation behaviors** that read memory and/or watch pixels, then act via input with humanized timing.
- **US-04:** As a user, I can set **safety limits** (pause on input, idle/logout timers, max clicks per minute, max runtime).
- **US-05:** As a user, I can view **logs** and a **live dashboard** (target FPS, last read latency, event counts).

### 2.2 Functional Requirements
1. **Process Management:** list processes; attach/detach by PID/name; validate 64‑bit vs 32‑bit target.
2. **Memory Access (Read/Optional Write):** ReadProcessMemory wrapper; optional writes gated by explicit user consent per profile item.
3. **Address Discovery (aux tooling):** pointer-chain evaluation; AOB scanning; static base + offsets.
4. **Input Simulation:** SendInput‑based mouse/keyboard with jitter/curvature; configurable humanization; pause/resume hotkeys.
5. **Pixel Monitoring:** capture window/region; thresholded template/pixel matching; FPS and latency budget.
6. **Configuration:** JSON/YAML profiles with schema validation; per‑profile randomization bounds.
7. **Observability:** structured logging, rotating files; metrics exposed to GUI; error dialog surfacing.

### 2.3 Non‑Functional Requirements
- **Performance:** typical memory read ≤ 5 ms; pixel capture ≥ 20 FPS sustained per region; input latency ≤ 50 ms.
- **Security:** principle of least privilege; sanity‑check all pointers/sizes; bounds checking; avoid PROCESS_ALL_ACCESS.
- **Accessibility:** keyboard navigation, color‑blind friendly highlighting in GUI.

---

## 3. Architecture

### 3.1 Layered View
1. **GUI Layer (Python, PySide6 / PyQt5):** windows, profile editor, logs/metrics panel, start/stop controls.
2. **Core Layer (Python):** orchestration, scheduling, state machine/behavior tree for automation, adapter to C API.
3. **Native Layer (C, shared library):** narrow WinAPI wrappers for process/memory/input; no injection or stealth.
4. **OS/Runtime:** Windows memory APIs, Desktop Duplication or GDI for capture, SendInput.

### 3.2 Component Diagram (C4 C2-ish)
- **GameTrainerGUI** → **TrainerCore** → **libgametrainer** → WinAPI.
- **PixelDetector** feeds events → **TrainerCore**.
- **Behavior Engine** consumes Memory + Pixel signals → emits Input commands.

### 3.3 Key Abstractions
- **IProcessClient** (Python): attach/detach/status, read(addr, size), write(addr, bytes?)
- **IMemoryAddress**: direct address, base+offset chain, AOB signature resolver.
- **IInputBus**: mouse_move(x,y,opts), mouse_click(opts), key(vk,down/up,opts).
- **IPixelSource**: capture(region) → frame; **IPixelDetector**: on(frame) → events.
- **Behavior**: finite‑state machine or behavior tree node with `tick(ctx)`.

---

## 4. Detailed Design

### 4.1 Native C Library (`libgametrainer`)

**Headers**
```c
// process.h
#pragma once
#include <windows.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    HANDLE handle;
    DWORD  pid;
    BOOL   is64bit;
} gt_process_t;

BOOL gt_find_process_id(const char* name, DWORD* out_pid);
BOOL gt_open_process(DWORD pid, gt_process_t* out);
void gt_close_process(gt_process_t* proc);
BOOL gt_is_process_64bit(HANDLE hProc, BOOL* out);

#ifdef __cplusplus
}
#endif
```

```c
// memory.h
#pragma once
#include <windows.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

BOOL gt_read(HANDLE h, LPCVOID addr, void* buf, size_t sz);
BOOL gt_write(HANDLE h, LPVOID addr, const void* buf, size_t sz);

// Pointer chain helper (safe evaluation with bounds checks)
BOOL gt_read_ptr_chain(HANDLE h, LPCVOID base, const size_t* offsets, size_t count, void** out_addr);

#ifdef __cplusplus
}
#endif
```

```c
// input.h
#pragma once
#include <windows.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int   curvature;     // 0..100
    int   jitter_px;     // 0..N
    int   step_ms_min;   // per segment
    int   step_ms_max;
} gt_mouse_profile_t;

BOOL gt_mouse_move_curve(int x, int y, const gt_mouse_profile_t* profile);
BOOL gt_mouse_click(WORD button_vk, int down_up_both, int delay_ms);
BOOL gt_key(WORD vk, int down_up_both, int delay_ms);

#ifdef __cplusplus
}
#endif
```

**Design Notes**
- Avoid `PROCESS_ALL_ACCESS`; request only `PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION` as needed.
- Validate `sz` and pointer arguments; clamp sizes; memset output buffers on failure.
- Return `GetLastError()` via `gt_errno()` helper or thread‑local last error for Python exceptions.
- Provide `__declspec(dllexport)` on Windows and a `.def` file to keep a stable ABI.

### 4.2 Python Core

```text
trainer/
  core/
    trainer.py           # Orchestration, lifecycle
    behaviors/
      __init__.py
      fsms.py            # Finite state machine helpers
      fishing.py         # Example behavior (Stardew-like)
    io/
      process_client.py  # ctypes bindings to libgametrainer
      input_bus.py
      pixel_source.py    # mss / Desktop Duplication
      pixel_detector.py  # thresholding, template match
  gui/
    main_window.py
    profile_editor.py
    logs_panel.py
```

**TrainerCore Responsibilities**
- Manage attach/detach; runtime clock; cooperative scheduler for periodic tasks.
- Provide `Context` to behaviors: current memory snapshot, pixel events, rate limiters.
- Expose safe start/stop; propagate errors to GUI via signals.

**Behavior Engine**
- Prefer **finite‑state machines** or **behavior trees** over ad‑hoc loops.
- Each Behavior gets **tick(ctx)** at a fixed cadence (e.g., 20 Hz) with soft deadlines.
- Built‑in rate limiters/randomizers (per action min/max intervals, deviation %).

### 4.3 Pixel Path
- Use **Desktop Duplication API** (DXGI) when available for efficient capture; fall back to **GDI BitBlt**; via Python, consider `mss` with CFFI/ctypes.
- Normalize frames (format, stride); expose grayscale and downscaled versions for cheap comparisons.
- Provide region‑of‑interest (ROI) configuration in profiles; precompute masks.

### 4.4 Input Path
- Windows `SendInput` only. Expose curvature + jitter in user space; cap maximum CPS, random delay bands, occasional miss behavior only within user‑set bounds.
- Optional **global pause hotkey** and safe‑stop if user moves mouse/keyboard significantly.

### 4.5 Configuration & Profiles
- **Schema:** YAML (human friendly) or JSON with **Pydantic** validation in Python.
- **Example (YAML):**
```yaml
version: 1
profile_name: stardew_fish
process:
  name: StardewValley.exe
memory:
  pointers:
    fish_state:
      base: 0x12345678
      offsets: [0x10, 0x18, 0x30]
aob:
  reel_bar: "48 8B ?? 89 54 24 ?? 48 83 EC ??"
pixels:
  bite_roi: { x: 900, y: 540, w: 120, h: 40, threshold: 0.85 }
input:
  mouse:
    curvature: 35
    jitter_px: 2
    cps_max: 6
  safety:
    max_runtime_min: 120
    idle_logout_min: 30
```

- **Secrets/Paths:** keep per‑user paths in a separate `secrets.local.yaml` ignored by VCS.

### 4.6 Logging & Metrics
- Python `logging` with JSON formatter; rotating file handlers by size/time.
- Events: attach/detach, read/write durations, pixel FPS, input actions, behavior state changes.
- Optional lightweight metrics in memory for GUI charts (no network telemetry).

### 4.7 Error Handling
- Wrap all C calls; raise rich Python exceptions (`GtProcessError`, `GtMemoryError`).
- Provide remediation hints in GUI dialogs (32/64‑bit mismatch, access denied, window minimized, etc.).

---

## 5. Build & Packaging

### 5.1 CMake (C library)
- Minimum `cmake_minimum_required(VERSION 3.20)`.
- `set(C_STANDARD 11)`; `/W4` (MSVC) or `-Wall -Wextra -Wpedantic` (MinGW/Clang).
- Separate `gt_core` target for common code; `gametrainer` shared lib exporting a small ABI.
- Produce `.pdb` on RelWithDebInfo builds; strip symbols for Release.

### 5.2 Python Packaging
- PEP 621 `pyproject.toml` with `setuptools`.
- Wheel includes the platform‑specific DLL in `trainer/core/bin/`.
- Entry point script `gametrainer-gui`.

### 5.3 Continuous Integration
- GitHub Actions: matrix (Py 3.10–3.12; x64 Windows). Run unit tests + flake8 + mypy + C build.
- Artifact upload of wheels on tagged releases.

---

## 6. Testing Strategy

### 6.1 Unit Tests
- **C:** mockable wrappers around `ReadProcessMemory`/`WriteProcessMemory`; gtest or lightweight C harness.
- **Python:** pytest + hypothesis for pointer‑chain evaluation; pixel detector with synthetic frames.

### 6.2 Integration Tests
- **Dummy Target:** bundled sample app exposes a few read‑only counters and a writable int with guardrails.
- End‑to‑end attach → read → pixel event → input (simulated via a virtual window).

### 6.3 Performance Tests
- Frame capture FPS under various ROIs; input latency distribution; pointer resolution time for AOB vs fixed addresses.

### 6.4 Security/Safety Checks
- Ensure no writes occur unless a profile opt‑in flag is true.
- Enforce upper bounds on CPS, runtime, and pointer depths.

---

## 7. Project Structure

```
GameTrainer/
├─ src/
│  ├─ c/
│  │  ├─ process.c/.h
│  │  ├─ memory.c/.h
│  │  ├─ input.c/.h
│  │  └─ util.c/.h
│  └─ python/
│     ├─ trainer/
│     │  ├─ core/
│     │  │  ├─ trainer.py
│     │  │  ├─ behaviors/
│     │  │  ├─ io/
│     │  │  └─ utils/
│     │  └─ gui/
│     │     ├─ main_window.py
│     │     ├─ profile_editor.py
│     │     └─ logs_panel.py
├─ tests/
│  ├─ c/
│  └─ python/
├─ tools/               # small pointer/AOB helpers, profile validators
├─ examples/            # sample profiles & dummy target
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ BEHAVIORS.md
│  └─ PROFILES.md
├─ CMakeLists.txt
├─ pyproject.toml
├─ README.md
└─ LICENSE
```

---

## 8. Dependencies
- **C:** Windows SDK; optional MinGW/Clang toolchain.
- **Python:** PySide6/PyQt5, `ctypes`, `mss`, `numpy` (optional), `pydantic`, `pytest`.
- **Dev:** `black`, `ruff`/`flake8`, `mypy`.

---

## 9. Risk Management & Safety Features
- **Local‑only** operation; never network.
- **Safety caps** on actions (CPS, runtime); emergency stop hotkey.
- **Read‑first** default: encourage read‑only observation profiles.
- **Clear logs** for auditability in your demos/interviews.

---

## 10. Future Enhancements
- Plugin system for per‑game behavior packs.
- In‑GUI memory viewer (read‑only).
- Template matching with ORB/SURF (CPU‑friendly) for richer pixel cues.
- Cross‑platform capture backends.

---

## 11. Appendix: Stardew‑like Example Behavior (High Level)
- **States:** Idle → Detect Bite (pixel ROI) → Hook (click) → Reel (read `fish_state` & pixel bar) → Settle.
- **Guards:** cap reel adjustments per second; randomized micro‑delays; hard stop if user jiggles mouse.

---

*This revision strips stealth/evasion material and emphasizes safe, testable engineering with strong docs and CI. Keep the document versioned and updated as the code evolves.*

