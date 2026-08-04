# GameTrainer Context

## Glossary

### Profile
**Corrected 2026-08-04:** this entry described the old Stardew prototype's
directory-based profile (`profiles/<game>/regions.yaml` + `ConfigLoader`),
which was deleted along with the rest of that prototype. The current, only
Profile is `src/gametrainer/profile.py`: one flat `.yaml` file that names a
Ground (e.g. `cartpole`, `gridworld`), a perception mode, and the reward + PPO
numbers to train it with. Loading it does not touch the screen or a game
window — see `docs/m4/M4_ToDo.md`.

### Global Frame
The downsampled (e.g., 224x224) RGB image of the entire game window. This serves as the primary input for the Vision Transformer (ViT) in the Agent's Observation Space.

### UI Region
**Retired 2026-08-04:** this described the old Stardew prototype's
screen-region reward reading (`interface.py` + `regions.yaml`), which was
deleted along with the rest of that prototype. No Track A equivalent exists —
the current Profile carries reward *numbers* directly (see `RewardCalculator`
in `src/gametrainer/rewards.py`), not screen coordinates to read them from.

### Input Controller (Python)
The high-level behavioral layer responsible for "humanizing" the agent's actions. It orchestrates timings, adds stochastic jitter to movements, and manages the logic of complex inputs (like long-pressing or double-clicking) by coordinating calls to the C++ Extension.

### C++ Extension (Native)
The low-level injection layer that interfaces directly with the Windows API (SendInput). Its primary responsibility is technical reliability—ensuring that games using hardware scan codes (DirectInput) correctly register key presses and mouse movements. It provides raw "down" and "up" primitives to the Python layer.
