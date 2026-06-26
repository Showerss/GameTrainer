# GameTrainer — Milestone 1 (UML)

Progress so far. One real thing changed since M0: the **`Agent` (SB3 PPO)** got connected, replacing random actions. It trains on the same CartPole contract, with two SB3 callbacks for eval and checkpoints. `NullInput` is still wired (still a no-op). Eyes, `GameEnvironment`, reward, profiles — still planned.

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
    class TrainCartpole {
        <<script: train_cartpole.py>>
        +make_train_env()
        +make_eval_env()
        +train_and_verdict(steps)
    }
    class Agent {
        <<NEW - borrowed: SB3 PPO>>
        +learn(steps)
        +predict(obs) action
        +save(path)
    }
    class EvalCallback {
        <<SB3>>
        +on_step()
    }
    class CheckpointCallback {
        <<SB3>>
        +on_step()
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

    GymEnv <|-- CartPole
    InputController <|-- NullInput
    TrainCartpole ..> Agent : creates PPO
    TrainCartpole ..> NullInput : still wired (no-op)
    Agent ..> CartPole : trains on (reset / step)
    Agent ..> EvalCallback : uses
    Agent ..> CheckpointCallback : uses

    class GameEnvironment:::planned
    class Perception:::planned
    class VisionPerception:::planned
    class ViTExtractor:::planned
    class RewardCalculator:::planned
    class KeyboardInput:::planned
    class Profile:::planned

    classDef planned fill:#f4f4f4,stroke:#bbbbbb,color:#999999,stroke-dasharray:4 3
```

**New at M1:** the `Agent` (PPO) node and its training dependency on the contract — the random policy is gone. **Result:** reward climbed 22 → 500.

**Built so far:** everything from M0, plus `Agent` (PPO) and the SB3 `EvalCallback` / `CheckpointCallback`.

**Still planned:** `GameEnvironment`, `Perception` / `VisionPerception`, `ViTExtractor`, `RewardCalculator`, `KeyboardInput` + `Clib`, `Profile`.

Note: swapping the decision-maker (random → PPO) required **no change to the contract** — which is the whole point of the architecture.
