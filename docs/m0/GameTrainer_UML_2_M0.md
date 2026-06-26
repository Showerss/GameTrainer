# GameTrainer — Milestone 0 (UML)

Progress so far. Only three live pieces: the **borrowed CartPole** env, a **random-action runner**, and the **`NullInput` stub** wired in early to prove the input seam exists. No brain, no eyes, no `GameEnvironment` yet.

> **Greyed, dashed boxes = planned but not yet built.**

```mermaid
classDiagram
    class GymEnv {
        <<interface (gymnasium)>>
        +reset() observation
        +step(action) tuple
    }
    class CartPole {
        <<borrowed: gym.make>>
        +reset() observation
        +step(action) tuple
    }
    class RunCartpole {
        <<script: run_cartpole.py>>
        +run(steps)
        +sample_random_action()
    }
    class InputController {
        <<interface>>
        +send(action)
    }
    class NullInput {
        +send(action)
    }
    class HardwareManager {
        +pick_device() device
    }
    class Logger {
        +info(msg)
    }

    GymEnv <|-- CartPole
    InputController <|-- NullInput
    RunCartpole ..> CartPole : reset / step loop
    RunCartpole ..> NullInput : tap_key(action) no-op

    class GameEnvironment:::planned
    class Perception:::planned
    class VisionPerception:::planned
    class ViTExtractor:::planned
    class RewardCalculator:::planned
    class KeyboardInput:::planned
    class Profile:::planned
    class Agent:::planned

    classDef planned fill:#f4f4f4,stroke:#bbbbbb,color:#999999,stroke-dasharray:4 3
```

**Built so far:** `GymEnv` contract (borrowed), `CartPole`, `RunCartpole`, `InputController` + `NullInput`, `HardwareManager`, `Logger`.

**Still planned:** `Agent`, `GameEnvironment`, `Perception` / `VisionPerception`, `ViTExtractor`, `RewardCalculator`, `KeyboardInput` + `Clib`, `Profile`.

**Proven at M0:** the loop runs (100 random steps, no crash) and the swappable-input seam is in place before it's needed.
