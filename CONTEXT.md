# GameTrainer Context

## Glossary

### Profile
A self-contained directory that defines how the system interacts with a specific game. It includes configuration files (e.g., `regions.yaml`), trained model checkpoints, and game-specific logic "hooks" (such as reward calculation scripts) that the core RL Engine loads dynamically.

### Global Frame
The downsampled (e.g., 224x224) RGB image of the entire game window. This serves as the primary input for the Vision Transformer (ViT) in the Agent's Observation Space.

### UI Region
A specific coordinate-based area on the screen defined in a Profile. These are used by the Reward Engine to extract specific metrics (like health or energy) to calculate Reward Signals, but are generally not provided directly to the Agent as separate inputs.

### Input Controller (Python)
The high-level behavioral layer responsible for "humanizing" the agent's actions. It orchestrates timings, adds stochastic jitter to movements, and manages the logic of complex inputs (like long-pressing or double-clicking) by coordinating calls to the C++ Extension.

### C++ Extension (Native)
The low-level injection layer that interfaces directly with the Windows API (SendInput). Its primary responsibility is technical reliability—ensuring that games using hardware scan codes (DirectInput) correctly register key presses and mouse movements. It provides raw "down" and "up" primitives to the Python layer.
