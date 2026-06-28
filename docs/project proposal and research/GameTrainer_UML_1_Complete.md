# GameTrainer — Target Architecture (UML)

The complete projected design: every class, plus the training and inference flows. Everything hangs off one contract (`GymEnv`); the `Agent` is borrowed and only ever talks to that contract.

---

## Class diagram — all projected classes

```mermaid
classDiagram
    class GymEnv {
        <<interface (gymnasium)>>
        +reset() observation
        +step(action) tuple
        +render()
        +observation_space
        +action_space
    }

    class GameEnvironment {
        -Profile profile
        -Perception perception
        -InputController hands
        -RewardCalculator rewarder
        +reset() observation
        +step(action) tuple
    }

    class Perception {
        <<interface>>
        +observe(raw) observation
    }
    class NumericPerception {
        +observe(raw) observation
    }
    class VisionPerception {
        -ScreenCapture screen
        -ViTExtractor extractor
        +observe(frame) observation
    }

    class ScreenCapture {
        -region
        +grab() frame
    }
    class ViTExtractor {
        <<borrowed: pretrained ViT (timm)>>
        -model
        +extract(frame) features
    }

    class InputController {
        <<interface>>
        +send(action)
    }
    class NullInput {
        +send(action)
    }
    class KeyboardInput {
        -Clib clib
        -key_map
        +send(action)
    }
    class Clib {
        <<native C++ SendInput>>
        +key_down(vk)
        +key_up(vk)
        +move_mouse(x, y)
        +click()
    }

    class RewardCalculator {
        -components
        +score(state) float
    }
    class Profile {
        +key_map
        +settings
        +window_title
        +load(path)
    }
    class Agent {
        <<borrowed: SB3 PPO>>
        +learn(steps)
        +predict(obs) action
        +save(path)
        +load(path)
    }
    class HardwareManager {
        +pick_device() device
    }
    class Logger {
        +info(msg)
        +warn(msg)
    }

    GymEnv <|-- GameEnvironment
    Perception <|-- NumericPerception
    Perception <|-- VisionPerception
    InputController <|-- NullInput
    InputController <|-- KeyboardInput

    GameEnvironment *-- Perception
    GameEnvironment *-- InputController
    GameEnvironment *-- RewardCalculator
    GameEnvironment *-- Profile
    GameEnvironment ..> Logger

    VisionPerception --> ScreenCapture
    VisionPerception --> ViTExtractor
    KeyboardInput --> Clib

    Agent ..> GymEnv : trains on / acts in
    Agent ..> HardwareManager : picks device
```

`step()` returns the gymnasium 5-tuple: `observation, reward, terminated, truncated, info`.

---

## Training flow

The agent acts, the env grades it, the agent updates its policy. Input is the `NullInput` stub during simulated worlds (CartPole / GridWorld).

```mermaid
sequenceDiagram
    autonumber
    participant R as Runner (train.py)
    participant HW as HardwareManager
    participant A as Agent (PPO)
    participant E as GameEnvironment
    participant P as Perception
    participant I as InputController
    participant RC as RewardCalculator

    R->>HW: pick_device()
    R->>E: build(profile, perception, input, rewarder)
    R->>A: PPO("MlpPolicy", env)
    loop every training step
        A->>E: step(action)
        E->>I: send(action)
        E->>P: observe(raw)
        P-->>E: observation
        E->>RC: score(state)
        RC-->>E: reward
        E-->>A: observation, reward, terminated, truncated
        A->>A: update policy (PPO)
    end
    R->>A: save(model)
```

---

## Inference flow

Playing for real: capture the screen, decide, press keys. **No reward, no weight updates** — the model is frozen.

```mermaid
sequenceDiagram
    autonumber
    participant PL as Player (play.py)
    participant A as Agent (trained PPO)
    participant E as GameEnvironment
    participant SC as ScreenCapture
    participant P as VisionPerception
    participant I as KeyboardInput
    participant C as Clib (C++)

    PL->>A: load(model)
    loop real-time, no learning
        E->>SC: grab()
        SC-->>E: frame
        E->>P: observe(frame)
        P-->>E: observation
        PL->>A: predict(observation)
        A-->>PL: action
        PL->>E: apply(action)
        E->>I: send(action)
        I->>C: key_down / key_up / move
    end
```
