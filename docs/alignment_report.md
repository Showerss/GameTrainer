# Alignment Report: Milestone M0 & Architecture

This report evaluates the alignment between the current codebase of **GameTrainer** and its authoritative documentation, specifically focusing on the **M0 Milestone** and the core architectural guidelines defined in [PRD.md](file:///Users/jennayahorne/Desktop/GameTrainer/docs/PRD.md) and [CLAUDE.md](file:///Users/jennayahorne/Desktop/GameTrainer/CLAUDE.md).

---

## 1. Milestone M0 Alignment Check

The **M0 Setup** milestone in [PRD.md](file:///Users/jennayahorne/Desktop/GameTrainer/docs/PRD.md#L184) defines the success criteria as:
> **Done when:** Repo + virtualenv created, libs installed, a script runs CartPole with random actions for 100 steps without crashing.

Below is the status of the current codebase against these criteria:

| Requirement | Current Status | Alignment | Details / Issues |
| :--- | :--- | :---: | :--- |
| **Repository Created** | Created and populated with files. | ✅ **Yes** | Repository is initialized with basic folder structure (`src/`, `scripts/`, `docs/`, `tests/`). |
| **Virtual Environment** | Not present in workspace. | ❌ **No** | No local `.venv` or `venv` folder exists in the project workspace. |
| **Libraries Installed** | Packages defined in `setup.py` but not installed in environment. | ❌ **No** | Trying to run tests/scripts results in `ModuleNotFoundError: No module named 'mss'`. Furthermore, the dependency manager lists `pywin32` which fails to install on macOS. |
| **CartPole Runner Script** | Completely missing. | ❌ **No** | No scripts or modules reference or run `CartPole`. All scripts (`train.py`, `play.py`) and environments (`StardewViTEnv`) are hardcoded for Stardew Valley. |

---

## 2. Core Architectural & Platform Alignment

### A. Platform Compatibility (macOS vs. Windows)
* **Documentation Guidelines**:
  * The user is running on **macOS**.
  * [CLAUDE.md](file:///Users/jennayahorne/Desktop/GameTrainer/CLAUDE.md#L85) and [PRD.md](file:///Users/jennayahorne/Desktop/GameTrainer/docs/PRD.md#L57) state **v1 constraints: Python only (no C++), local only, CPU-first for early phases**.
* **Current Codebase Implementation**:
  * Includes a C++ input injection extension ([clib.cpp](file:///Users/jennayahorne/Desktop/GameTrainer/src/cpp/clib.cpp)) that uses Windows-specific APIs (`SendInput`, `MapVirtualKey`, `VK_*` codes) and links to Windows system libraries `user32` and `kernel32` in [setup.py](file:///Users/jennayahorne/Desktop/GameTrainer/setup.py#L29). This makes compiling the package fail entirely on macOS.
  * Uses Windows-specific imports (`win32gui`, `win32con`) inside [env_vit.py](file:///Users/jennayahorne/Desktop/GameTrainer/src/gametrainer/env_vit.py#L421) and [screen.py](file:///Users/jennayahorne/Desktop/GameTrainer/src/gametrainer/screen.py#L31), resulting in runtime failures on macOS.
  * **Alignment**: ❌ **Severe Mismatch**. The code is currently locked to Windows and relies on C++ extensions, violating the macOS runtime requirement and the "No C++ in v1" rule.

### B. Generic GameEnvironment Contract vs. Stardew Valley Hardcoding
* **Documentation Guidelines**:
  * [PRD.md Section 4 & 5](file:///Users/jennayahorne/Desktop/GameTrainer/docs/PRD.md#L62) defines a standard, game-agnostic `GameEnvironment` that interacts with swappable components via interfaces:
    * `Profile`: Configuration loading
    * `Perception` (subclassed by `NumericPerception` & `VisionPerception`)
    * `InputController` (subclassed by `NullInput` & `KeyboardInput`)
    * `RewardCalculator`
* **Current Codebase Implementation**:
  * There is no generic `GameEnvironment`, `Perception` hierarchy, `NullInput`/`KeyboardInput` subclasses, or distinct `RewardCalculator`.
  * All logic is contained in a single, monolithic class called `StardewViTEnv` in [env_vit.py](file:///Users/jennayahorne/Desktop/GameTrainer/src/gametrainer/env_vit.py).
  * Reward calculations, screen preprocessing, inputs, and UI template-matching are all hardcoded specifically for Stardew Valley.
  * **Alignment**: ❌ **No**. The modular architecture shown in the PRD's UML diagram is not implemented in the code.

### C. Profiles & Configuration Loading
* **Documentation Guidelines**:
  * Game-specific settings should reside in `profile.yaml` under a game-specific directory, allowing games to be switched via configuration changes only (M4).
* **Current Codebase Implementation**:
  * A `ConfigLoader` class exists in [config.py](file:///Users/jennayahorne/Desktop/GameTrainer/src/gametrainer/config.py), but there is no `profiles/` directory in the repository, and the loader is not integrated into `StardewViTEnv` or the training scripts.
  * **Alignment**: ❌ **No**. The profile loading is stubbed out but not wired.

---

## 3. Recommended Remediation Plan for Milestone M0

To bring the codebase into alignment with the **M0 Milestone** and prepare it for macOS execution, the following steps are required:

1. **Establish a macOS-compatible Python Environment**:
   * Create a python virtual environment (`.venv`).
   * Clean up [setup.py](file:///Users/jennayahorne/Desktop/GameTrainer/setup.py) to make the C++ extension compilation optional or conditional (disable compilation on macOS since v1 expects Python-only input hands).
   * Refactor [dependencies.py](file:///Users/jennayahorne/Desktop/GameTrainer/src/gametrainer/dependencies.py) to only load `pywin32` on Windows.
2. **Implement Platform-Agnostic Screen Capture**:
   * Modify [screen.py](file:///Users/jennayahorne/Desktop/GameTrainer/src/gametrainer/screen.py) to handle macOS window capturing or default gracefully to full-screen capture using `mss` (which is cross-platform).
3. **Implement modular InputController**:
   * Implement the `NullInput` controller class (doing nothing, which is ideal for programmatic environments like CartPole).
   * Ensure `InputController` does not crash when the Windows C++ `clib` is missing (fallback to a cross-platform Python-only input library or dummy input).
4. **Create the CartPole Script**:
   * Author a new script (e.g., `scripts/run_cartpole.py`) that initializes a standard Gymnasium `CartPole-v1` environment.
   * Run a loop for 100 steps taking random actions and rendering/updating status without crashing.
