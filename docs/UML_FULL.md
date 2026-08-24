# GameTrainer — Full UML & Diagrams

> **Covers:** diagrams of the system — the mental model, the class layout, and
> the milestone roadmap.
> **Status:** partially stale. §1–2 (the loop, build-vs-borrow) are timeless and
> current. §3 and §6–8 (the full class diagram, milestone roadmap, and snapshot
> table) were drawn mid-M2 and were never refreshed for M3, M4, or the 2026-08-04
> Track B deletion — they still show Track B classes as live and M3/M4 as
> "not started." Treat those sections as a historical snapshot, not current fact.
> **Last verified:** 2026-08-08 (confirmed §1–2 still accurate; confirmed §3/§6–8
> are stale, per above — not yet redrawn).
> **Authority:** for the real current status, read `docs/ONBOARDING.md` §8 and
> `docs/CHANGELOG.md`. This file wins on *diagrams*, not on *current status*.
> Written to `docs/DOC_STANDARD.md`.

> Companion to [`docs/ONBOARDING.md`](ONBOARDING.md). Every diagram here is
> **Mermaid** — GitHub, VS Code (with the Markdown Preview Mermaid extension),
> and most Markdown viewers render it directly.
>
> **Legend used throughout:**
> - **Solid arrow `-->` / `..>`** — "uses / calls / depends on"
> - **Hollow triangle `<|--`** — "is a kind of" (inheritance)
> - **Filled diamond `*--`** — "owns one of these" (composition)
> - ✅ built and live &nbsp;&nbsp; ▲ written but ahead of schedule &nbsp;&nbsp; ⏳ planned, not written

---

## 1. The loop — the whole project in one picture

Everything else is detail. This is the system.

```mermaid
flowchart LR
    subgraph AI["🤖 AI — the player"]
        direction TB
        EYES["👁️ Eyes<br/>Perception<br/><i>pixels → summary</i>"]
        BRAIN["🧠 Brain<br/>PPO<br/><i>summary → decision</i>"]
        HANDS["✋ Hands<br/>InputController<br/><i>decision → key press</i>"]
        EYES --> BRAIN --> HANDS
    end

    subgraph GROUND["🌍 Ground — the game"]
        GAME["The world<br/><i>rules + scoring</i>"]
    end

    GAME -- "1 - observation<br/>'here is the state'" --> EYES
    HANDS -- "2 - action<br/>'press right'" --> GAME
    GAME -- "3 - reward<br/>'good: +1'" --> BRAIN

    LINK{{"🔌 The Link — Gymnasium<br/>reset · step"}}
    LINK -.->|"defines the shape of<br/>every arrow above"| GAME

    style LINK fill:#fff3cd,stroke:#d39e00,stroke-width:2px
    style AI fill:#e7f1ff,stroke:#4a90d9
    style GROUND fill:#e9f7ef,stroke:#3d9970
```

**Read it as:** the game shows a state → the eyes summarise it → the brain picks
a move → the hands perform it → the game scores it → repeat, thousands of times.
The Link (Gymnasium) is the agreement that makes every arrow a standard shape.

---

## 2. Build vs. borrow — what is actually *our* work

```mermaid
flowchart TB
    subgraph WEBUILD["✅ WE BUILD — this is the project"]
        G["Ground<br/>GridWorldEnv, future game envs"]
        L["Link wiring<br/>contract compliance, profiles"]
        R["Reward design<br/>what 'good' means"]
    end

    subgraph WEBORROW["🔁 WE BORROW — solved problems"]
        P["PPO<br/><i>stable-baselines3</i>"]
        V["ViT backbone<br/><i>timm, ImageNet-pretrained</i>"]
        GY["Gymnasium<br/><i>the contract itself</i>"]
        T["PyTorch<br/><i>runs the maths</i>"]
    end

    G --> GY
    L --> GY
    P --> T
    V --> T
    P -- "trains on" --> G
    V -- "feeds features to" --> P
    R -- "lives inside" --> G

    style WEBUILD fill:#e9f7ef,stroke:#3d9970,stroke-width:2px
    style WEBORROW fill:#f4f4f4,stroke:#999999,stroke-dasharray:4 3
```

**Why this split?** Writing your own RL algorithm is months of subtle, silently
wrong maths. Writing your own connector is where the actual insight is.

---

## 3. Full class diagram — the whole system, current state

This is the main UML. Grey dashed = planned. `▲` = code that exists but belongs
to a later milestone (see §5 of the onboarding doc).

```mermaid
classDiagram
    %% ============ THE CONTRACT ============
    class GymEnv {
        <<interface — gymnasium>>
        +observation_space
        +action_space
        +reset(seed, options) tuple
        +step(action) tuple
        +render()
        +close()
    }

    %% ============ GROUNDS ============
    class CartPole {
        <<borrowed — gym.make>>
        +reset() obs, info
        +step(action) 5-tuple
    }

    class GridWorldEnv {
        <<OURS — M2, live>>
        +SIZE = 5
        +START = 0,0
        +GOAL = 4,4
        +MAX_STEPS = 100
        +STEP_COST = -0.01
        +GOAL_REWARD = 1.0
        -row, col
        -_steps
        +reset(seed, options) obs, info
        +step(action) 5-tuple
        +render()
        -_get_obs() ndarray
    }

    class StardewViTEnv {
        <<▲ Track B — M3/M5/M6>>
        +FRAME_SKIP = 2
        +observation_space 3x224x224
        +action_space Discrete 12
        +reset() obs, info
        +step(action) 5-tuple
        -_preprocess_frame(frame)
        -_calculate_reward(frame, action)
        -_take_action(action)
        -_focus_game_window(title)
    }

    %% ============ THE BRAIN ============
    class Agent {
        <<borrowed — SB3 PPO>>
        +learn(total_timesteps)
        +predict(obs, deterministic) action
        +save(path)
        +load(path)
    }
    class EvalCallback {
        <<SB3>>
        +on_step()
    }
    class CheckpointCallback {
        <<SB3>>
        +on_step()
    }

    %% ============ THE EYES ============
    class BaseFeaturesExtractor {
        <<interface — SB3>>
        +forward(observations) tensor
    }
    class ViTFeaturesExtractor {
        <<▲ Track B — M3>>
        +features_dim = 768
        +pretrained = True
        +freeze_backbone
        +model_name
        +forward(observations) tensor
    }

    %% ============ THE HANDS ============
    class InputController {
        <<base — the Hands>>
        +VK_W, VK_A, VK_S, VK_D, VK_ESC
        +tap_key(code, duration)
        +move_up()
        +move_down()
        +move_left()
        +move_right()
        +mouse_move(dx, dy)
        +mouse_click()
        +escape()
    }
    class NullInput {
        <<live — no-op stub>>
        +tap_key() does nothing
    }
    class Clib {
        <<▲ C++ ext — M5, opt-in build>>
        +send_key(code)
        +send_mouse_move(x, y)
        +send_mouse_click()
    }

    %% ============ SUPPORT ============
    class ScreenCapture {
        <<▲ Track B — M3>>
        +set_region_from_window(title)
        +set_region_fullscreen()
        +grab() ndarray
    }
    class InterfaceManager {
        <<▲ Track B — M4/M6>>
        +find_all(frame)
        +get_energy_region(frame)
    }
    class ConfigLoader {
        <<▲ Track B — M4, unwired>>
        +load_regions() dict
        +get_region(name)
    }
    class HardwareManager {
        <<live>>
        +pick_device() device
    }
    class Logger {
        <<live>>
        +log(msg)
    }
    class Tui {
        <<live — the menu>>
        +run_tui()
        -_run_script(path)
    }

    %% ============ PLANNED ============
    class GameEnvironment:::planned
    class Perception:::planned
    class NumericPerception:::planned
    class VisionPerception:::planned
    class RewardCalculator:::planned
    class Profile:::planned
    class KeyboardInput:::planned

    %% ============ RELATIONSHIPS ============
    GymEnv <|-- CartPole
    GymEnv <|-- GridWorldEnv
    GymEnv <|-- StardewViTEnv
    GymEnv <|-- GameEnvironment

    InputController <|-- NullInput
    InputController <|-- KeyboardInput
    BaseFeaturesExtractor <|-- ViTFeaturesExtractor
    Perception <|-- NumericPerception
    Perception <|-- VisionPerception

    Agent ..> GymEnv : trains on — reset/step
    Agent ..> EvalCallback : uses
    Agent ..> CheckpointCallback : uses
    Agent ..> ViTFeaturesExtractor : policy_kwargs

    StardewViTEnv *-- ScreenCapture
    StardewViTEnv *-- InputController
    StardewViTEnv *-- InterfaceManager
    StardewViTEnv *-- Logger
    InputController ..> Clib : sends via
    InterfaceManager ..> ConfigLoader : will read regions from

    GameEnvironment *-- Perception
    GameEnvironment *-- RewardCalculator
    GameEnvironment *-- Profile
    VisionPerception ..> ViTFeaturesExtractor : will wrap

    Tui ..> Agent : launches training scripts

    classDef planned fill:#f4f4f4,stroke:#bbbbbb,color:#999999,stroke-dasharray:4 3
```

### Reading the important relationships

| Arrow | Says |
| :--- | :--- |
| `GymEnv <\|-- GridWorldEnv` | Our world **is a** Gymnasium env. This one line is the whole architecture. |
| `Agent ..> GymEnv` | PPO talks to the **interface**, never to a specific game. That's why games are swappable. |
| `InputController <\|-- NullInput` | The Hands seam exists *now*, filled with a do-nothing stub. |
| `StardewViTEnv *-- ScreenCapture` | The old Stardew env **owns** its capture, input, and UI-detection — all hard-wired. M4 exists to break exactly that coupling apart into a `Profile`. |

---

## 4. What actually runs — files and entry points

```mermaid
flowchart TB
    USER(["👤 You"])
    USER --> MAIN["main.py"]
    MAIN --> TUI["src/gametrainer/tui.py<br/><i>the retro menu</i>"]

    TUI -->|"[1]"| S1["scripts/run_cartpole.py"]
    TUI -->|"[2]"| S2["scripts/train_cartpole.py"]
    TUI -->|"[3]"| S3["scripts/run_gridworld.py"]
    TUI -->|"[4]"| S4["scripts/train_gridworld.py"]
    TUI -->|"[5]"| S5["scripts/train.py ▲"]
    TUI -->|"[6]"| S6["scripts/play.py ▲"]

    S1 --> CP["CartPole-v1<br/><i>borrowed</i>"]
    S2 --> CP
    S3 --> GW["gridworld.py<br/>GridWorldEnv ★"]
    S4 --> GW
    S5 --> SV["env_vit.py<br/>StardewViTEnv ▲"]
    S6 --> SV

    S2 --> PPO1["SB3 PPO<br/>MlpPolicy"]
    S4 --> PPO1
    S5 --> PPO2["SB3 PPO<br/>+ ViTFeaturesExtractor ▲"]

    S1 --> NI["NullInput<br/><i>no-op hands</i>"]
    S3 --> NI
    SV --> IC["InputController ▲<br/>→ clib.cpp"]
    SV --> SC["ScreenCapture ▲<br/>→ mss"]

    PPO1 --> OUT1["models/ + logs/<br/><i>checkpoints + TensorBoard</i>"]
    PPO2 --> OUT1

    subgraph TRACKA["✅ TRACK A — current milestones M0-M2"]
        S1
        S2
        S3
        S4
        CP
        GW
        PPO1
        NI
    end

    subgraph TRACKB["▲ TRACK B — written early, rebuild at M3-M6"]
        S5
        S6
        SV
        PPO2
        IC
        SC
    end

    style TRACKA fill:#e9f7ef,stroke:#3d9970,stroke-width:2px
    style TRACKB fill:#f4f4f4,stroke:#bbbbbb,stroke-dasharray:4 3
```

**The takeaway:** menu options 1–4 are the real, tested, current project. Options
5–6 run the older Stardew prototype and need a game window, a GPU, and libraries
the early milestones deliberately avoid.

---

## 5. Sequence — one training run, start to finish

What actually happens when you run `python scripts/train_gridworld.py`:

```mermaid
sequenceDiagram
    actor You
    participant Script as train_gridworld.py
    participant PPO as PPO (SB3)
    participant Env as GridWorldEnv
    participant Disk as models/ + logs/

    You->>Script: python scripts/train_gridworld.py
    Script->>Env: GridWorldEnv()
    Note over Env: action_space  = Discrete(4)<br/>observation_space = Box(2,)
    Script->>PPO: PPO("MlpPolicy", env)

    rect rgb(232, 244, 253)
        Note over PPO,Env: THE LOOP — repeats ~25,000 times
        PPO->>Env: reset()
        Env-->>PPO: observation (row, col), info
        loop until terminated or truncated
            PPO->>PPO: policy picks an action
            PPO->>Env: step(action)
            Note over Env: move · clamp to walls · score
            Env-->>PPO: obs, reward, terminated, truncated, info
        end
        PPO->>PPO: update the policy from what scored well
    end

    PPO->>Disk: CheckpointCallback saves snapshots
    PPO->>Disk: EvalCallback logs mean reward
    Script->>PPO: predict() over 20 greedy episodes
    Script->>You: PASS / FAIL verdict vs the random baseline
```

**The key detail:** PPO only ever calls `reset()` and `step()`. It has no idea
whether it's playing CartPole, GridWorld, or Stardew. Swap the `Env` line and
everything else is unchanged — *that* is what the project is proving.

---

## 6. The milestone roadmap — and exactly where we are

```mermaid
flowchart LR
    M0["M0 · Setup<br/>✅ DONE<br/><i>CartPole, random<br/>baseline ≈ 22</i>"]
    M1["M1 · Borrow the Brain<br/>✅ DONE<br/><i>PPO: 22 → 500</i>"]
    M2["M2 · Build our Ground<br/>⏳ IN PROGRESS<br/><i>GridWorld built;<br/>e2e test still xfail</i>"]
    M3["M3 · Add the Eyes<br/>⏳ NEXT<br/><i>picture + ViT</i>"]
    M4["M4 · Make it swappable<br/>⏳<br/><i>Profile + RewardCalculator<br/>★ thesis proven here</i>"]
    M5["M5 · Add the Hands<br/>⏳<br/><i>real key presses</i>"]
    M6["M6 · Stardew<br/>⏳ stretch<br/><i>just another profile</i>"]

    M0 --> M1 --> M2 --> M3 --> M4 --> M5 --> M6

    style M0 fill:#d4edda,stroke:#3d9970
    style M1 fill:#d4edda,stroke:#3d9970
    style M2 fill:#fff3cd,stroke:#d39e00,stroke-width:3px
    style M4 fill:#e7f1ff,stroke:#4a90d9,stroke-width:2px
```

**Each milestone changes exactly one thing.** That's the discipline: when
something breaks, there's only one candidate cause.

| Milestone | The one thing that changes |
| :--- | :--- |
| M0 → M1 | Random actions → a learning brain |
| M1 → M2 | Borrowed game → our own game |
| M2 → M3 | Observation is numbers → observation is a picture |
| M3 → M4 | Hard-coded wiring → config-driven wiring |
| M4 → M5 | Fake key presses → real ones |
| M5 → M6 | A toy window → a real commercial game |

---

## 7. How a milestone gets finished — the test-first loop

```mermaid
flowchart TB
    START(["Milestone starts"]) --> E2E["Write the end-to-end<br/>guardrail test FIRST<br/><i>marked xfail — red on purpose</i>"]
    E2E --> BRICK{"Next brick"}
    BRICK --> RED["🔴 Write one small<br/>failing test"]
    RED --> CODE["Write the minimum<br/>code to pass it"]
    CODE --> GREEN{"🟢 Green?"}
    GREEN -->|no| CODE
    GREEN -->|yes| MORE{"More bricks?"}
    MORE -->|yes| BRICK
    MORE -->|no| CHECK{"Does the e2e<br/>guardrail pass<br/>on its own?"}
    CHECK -->|no| BRICK
    CHECK -->|yes| DONE(["✅ Delete the xfail.<br/>Milestone closed."])

    style E2E fill:#f8d7da,stroke:#c82333
    style DONE fill:#d4edda,stroke:#3d9970
```

**Why work this way?** Because "done" becomes an assertion instead of an
opinion. For M2, the finish line is one specific line in
`tests/test_m2_e2e.py`: PPO must beat the random baseline **and** reach the goal
in ≥90% of episodes. Until then, M2 is open — no debate required.

---

## 8. Snapshot summary

| Component | Status | Milestone |
| :--- | :--- | :--- |
| Gymnasium contract | ✅ live | M0 |
| CartPole runner + PPO trainer | ✅ live | M0 / M1 |
| `NullInput` seam | ✅ live | M0 |
| `HardwareManager`, `Logger`, `Tui` | ✅ live | M0 |
| `GridWorldEnv` + contract tests | ✅ live | M2 |
| GridWorld runner + trainer | ✅ live | M2 |
| M2 end-to-end guardrail | ⏳ still `xfail` | **M2 — the finish line** |
| `ViTFeaturesExtractor` | ▲ written, ahead | M3 |
| `ScreenCapture` | ▲ written, ahead | M3 |
| `ConfigLoader` / profiles | ▲ written, unwired | M4 |
| `Perception` / `RewardCalculator` / `GameEnvironment` | ⏳ not written | M3 / M4 |
| `InputController` + `clib.cpp` | ▲ written, not built by default | M5 |
| `StardewViTEnv` | ▲ prototype, untested | M6 |
