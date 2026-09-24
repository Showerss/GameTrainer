# GameTrainer — Full UML & Diagrams

> **Covers:** diagrams of the system — the mental model, the class layout, the
> execution flows, and the milestone roadmap.
> **Status:** current.
> **Last verified:** 2026-09-24 (M0–M5 complete and verified live on macOS & Windows 11;
> fully updated to reflect the completed Milestone 5 architecture: `MinesweeperEnv`,
> `GameWindow`, `KeyboardInput`, `read_board`, `MinesweeperRewardCalculator`, `Profile`,
> and `make_env`).
> **Authority:** this file owns the *diagrams* and architectural relationships across
> all milestones. For textual onboarding, see [`docs/ONBOARDING.md`](ONBOARDING.md);
> for the comprehensive architectural guide, see [`docs/MASTER_GUIDE.md`](MASTER_GUIDE.md).
> Written to `docs/DOC_STANDARD.md`.

> Companion to [`docs/ONBOARDING.md`](ONBOARDING.md) and [`docs/MASTER_GUIDE.md`](MASTER_GUIDE.md).
> Every diagram here is **Mermaid** — GitHub, VS Code (with the Markdown Preview
> Mermaid extension), and most Markdown viewers render it directly.
>
> **Legend used throughout:**
> - **Solid arrow `-->` / `..>`** — "uses / calls / depends on"
> - **Hollow triangle `<|--`** — "is a kind of" (inheritance)
> - **Filled diamond `*--`** — "owns one of these" (composition)
> - ✅ built and live &nbsp;&nbsp; ⏳ planned, next milestone

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
        G["Ground<br/>GridWorldEnv, MinesweeperEnv"]
        L["Link wiring<br/>factory make_env(), Profile"]
        R["Reward design<br/>RewardCalculator, MinesweeperRewardCalculator"]
        V["Vision & Screen<br/>read_board, GameWindow, PixelObservation"]
        H["Hands<br/>KeyboardInput, NullInput"]
    end

    subgraph WEBORROW["🔁 WE BORROW — solved problems"]
        P["PPO<br/><i>stable-baselines3</i>"]
        VT["ViT backbone<br/><i>timm, ImageNet-pretrained</i>"]
        GY["Gymnasium<br/><i>the contract itself</i>"]
        T["PyTorch<br/><i>runs the maths</i>"]
        OS["OS Input / Capture<br/><i>Win32 SendInput / macOS Quartz / mss</i>"]
    end

    G --> GY
    L --> GY
    P --> T
    VT --> T
    P -- "trains on" --> G
    VT -- "feeds features to" --> P
    R -- "scores moves for" --> G
    V -- "extracts state for" --> G
    H -- "drives window for" --> G
    H --> OS
    V --> OS

    style WEBUILD fill:#e9f7ef,stroke:#3d9970,stroke-width:2px
    style WEBORROW fill:#f4f4f4,stroke:#999999,stroke-dasharray:4 3
```

**Why this split?** Writing your own RL algorithm is months of subtle, silently
wrong maths. Writing your own connector is where the actual insight is.

---

## 3. Full class diagram — the complete implemented system (M0–M5)

This diagram shows all active classes across the repository following the completion
of Milestone 5. Note the absence of a monolithic "God Object": environments are
instantiated through the factory function `make_env()` and configured via `Profile`.

```mermaid
classDiagram
    %% ============ THE CONTRACT ============
    class GymEnv {
        <<interface — gymnasium.Env>>
        +observation_space : Space
        +action_space : Space
        +reset(seed, options) tuple[obs, info]
        +step(action) tuple[obs, reward, terminated, truncated, info]
        +render()
        +close()
    }

    %% ============ GROUNDS (ENVIRONMENTS) ============
    class CartPole {
        <<borrowed — gym.make('CartPole-v1')>>
        +observation_space : Box(4,)
        +action_space : Discrete(2)
        +reset()
        +step(action)
    }

    class GridWorldEnv {
        <<live — M2/M3>>
        +SIZE : int = 5
        +START : tuple = (0, 0)
        +GOAL : tuple = (4, 4)
        +MAX_STEPS : int = 100
        +STEP_COST : float = -0.01
        +GOAL_REWARD : float = 1.0
        -agent_pos : tuple[int, int]
        -_steps : int
        +reset(seed, options)
        +step(action)
        +render()
        -_get_obs() ndarray
    }

    class MinesweeperEnv {
        <<live — M5>>
        +observation_space : Box(0, 11, (8, 8), int8)
        +action_space : Discrete(6)
        -window : GameWindow
        -hands : InputController
        -rewarder : MinesweeperRewardCalculator
        -last_grid : ndarray
        -_cursor_pos : tuple[int, int]
        +reset(seed, options)
        +step(action)
        +close()
    }

    %% ============ GYMNASIUM WRAPPERS ============
    class ObservationWrapper {
        <<gymnasium.ObservationWrapper>>
        +observation(observation)
    }
    class PixelObservation {
        <<live — M3>>
        +observation_space : Box(0, 255, (3, 224, 224), uint8)
        +observation(observation) ndarray
    }
    class RandomStart {
        <<live — M3>>
        +reset(seed, options)
    }

    %% ============ THE BRAIN (SB3) ============
    class Agent {
        <<borrowed — SB3 PPO>>
        +learn(total_timesteps, callback)
        +predict(obs, deterministic) tuple[action, state]
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
        +features_dim : int
        +forward(observations) tensor
    }
    class ViTTinyFeaturesExtractor {
        <<live — M3>>
        +features_dim : int = 192
        +model : timm.VisionTransformer
        +forward(observations) tensor
    }
    class MinesweeperVision {
        <<module — M5>>
        +find_board(frame) tuple[x, y, w, h]
        +classify_cell(cell_crop) int
        +read_board(frame) ndarray
    }

    %% ============ THE HANDS ============
    class InputController {
        <<base — input.py>>
        +tap_key(key_code)
        +tap_chord(modifier_vk, key_vk)
        +restart()
        +escape()
    }
    class NullInput {
        <<live — stub & negative control>>
        +tap_key(key_code)
        +tap_chord(modifier_vk, key_vk)
        +restart()
    }
    class KeyboardInput {
        <<live — M5 real input>>
        -_backend : str ("win32" | "quartz")
        +tap_key(key_code)
        +tap_chord(modifier_vk, key_vk)
        +restart()
        -_send_key_win32(vk)
        -_send_key_quartz(vk)
    }

    %% ============ SCREEN & WINDOW ============
    class GameWindow {
        <<live — M5 screen.py>>
        +title : str
        +window_id : int
        +sct : mss.mss
        +find_window_by_title(title)
        +grab_frame() ndarray
        +focus()
        +set_dpi_awareness()
    }

    %% ============ FACTORY & REWARDS ============
    class Profile {
        <<live — M4/M5 frozen dataclass>>
        +name : str
        +ground : str
        +perception : str
        +reward_step_cost : float
        +reward_goal : float
        +ppo_total_timesteps : int
        +from_yaml(path) Profile
    }
    class RewardCalculator {
        <<live — M4>>
        +step_cost : float
        +goal_reward : float
        +score(old_pos, new_pos, reached_goal) float
    }
    class MinesweeperRewardCalculator {
        <<live — M5>>
        +safe_reveal_reward : float = 1.0
        +mine_penalty : float = -10.0
        +win_reward : float = 10.0
        +score(prev_grid, curr_grid) tuple[float, bool, bool]
    }
    class Factory {
        <<module — factory.py>>
        +make_env(profile, render_mode) GymEnv
    }

    %% ============ RELATIONSHIPS ============
    GymEnv <|-- CartPole
    GymEnv <|-- GridWorldEnv
    GymEnv <|-- MinesweeperEnv
    GymEnv <|-- ObservationWrapper
    ObservationWrapper <|-- PixelObservation

    InputController <|-- NullInput
    InputController <|-- KeyboardInput

    BaseFeaturesExtractor <|-- ViTTinyFeaturesExtractor

    Agent ..> GymEnv : trains on (reset / step)
    Agent ..> EvalCallback : uses
    Agent ..> CheckpointCallback : uses
    Agent ..> ViTTinyFeaturesExtractor : visual policy kwargs

    MinesweeperEnv *-- GameWindow : grabs frames via mss
    MinesweeperEnv *-- InputController : injects keys
    MinesweeperEnv ..> MinesweeperVision : extracts 8x8 grid
    MinesweeperEnv *-- MinesweeperRewardCalculator : calculates move reward

    Factory ..> Profile : validates
    Factory ..> GymEnv : instantiates (CartPole, GridWorld, Minesweeper)
    Factory ..> PixelObservation : wraps when perception == "pixels"
    Factory ..> RandomStart : wraps for robust training
```

### Key Architectural Patterns

| Relationship | Architectural Meaning |
| :--- | :--- |
| `GymEnv <\|-- MinesweeperEnv` | LibreMines is adapted into a pure Gymnasium socket; SB3 algorithms treat it identically to CartPole. |
| `Factory ..> GymEnv` | `make_env(profile)` is the single point where configuration becomes an active environment. |
| `MinesweeperEnv *-- GameWindow` | Screen capture is encapsulated inside the environment, hidden from the agent. |
| `MinesweeperEnv *-- InputController` | Hands are injected into the environment; `NullInput` can be hot-swapped for tests with zero logic changes. |
| `MinesweeperEnv ..> MinesweeperVision` | Computer vision translates high-resolution pixels into a discrete 8×8 integer grid before scoring. |

---

## 4. What actually runs — files, entry points, and runners

```mermaid
flowchart TB
    USER(["👤 Developer / Operator"])
    USER --> MAIN["main.py"]
    MAIN --> TUI["src/gametrainer/tui.py<br/><i>the interactive menu</i>"]

    TUI -->|"[1]"| S1["scripts/run_cartpole.py<br/><i>M0 random baseline</i>"]
    TUI -->|"[2]"| S2["scripts/train_cartpole.py<br/><i>M1 PPO trainer</i>"]
    TUI -->|"[3]"| S3["scripts/run_gridworld.py<br/><i>M2 random baseline</i>"]
    TUI -->|"[4]"| S4["scripts/train_gridworld.py<br/><i>M2 PPO trainer</i>"]
    TUI -->|"[5]"| S5["scripts/train_gridworld_vit.py<br/><i>M3 ViT pixel training</i>"]
    TUI -->|"[6]"| S6["scripts/train_from_profile.py<br/><i>M4 universal profile runner</i>"]
    TUI -->|"[7]"| S7["scripts/check_swap.py<br/><i>M4 config swap referee</i>"]
    TUI -->|"[8]"| S8["scripts/check_hands.py<br/><i>M5 live window behavioral proof</i>"]

    S1 --> CP["CartPole-v1<br/><i>borrowed</i>"]
    S2 --> CP
    S3 --> GW["gridworld.py<br/>GridWorldEnv"]
    S4 --> GW
    S5 --> GWP["perception.py<br/>PixelObservation"] --> GW
    
    S6 --> PROF["profiles/*.yaml<br/><i>cartpole, gridworld, minesweeper</i>"]
    PROF --> FACT["factory.py<br/>make_env(profile)"]
    FACT --> CP
    FACT --> GW
    FACT --> MS["minesweeper.py<br/>MinesweeperEnv"]

    S7 --> FACT
    S8 --> MS
    MS --> GWIN["screen.py<br/>GameWindow (mss)"]
    MS --> KBD["input.py<br/>KeyboardInput (SendInput/Quartz)"]
    MS --> VIS["minesweeper_vision.py<br/>read_board()"]

    S2 --> PPO["SB3 PPO"]
    S4 --> PPO
    S5 --> PPO
    S6 --> PPO

    style S6 fill:#e7f1ff,stroke:#4a90d9,stroke-width:2px
    style S8 fill:#cff4fc,stroke:#0dcaf0,stroke-width:2px
    style FACT fill:#d4edda,stroke:#3d9970,stroke-width:2px
```

---

## 5. Sequence — one live environment step in Milestone 5

What happens under the hood when `env.step(action)` executes against the live game:

```mermaid
sequenceDiagram
    actor Agent as PPO / Script
    participant Env as MinesweeperEnv
    participant Hands as KeyboardInput
    participant Win as GameWindow
    participant CV as read_board (Vision)
    participant Calc as MinesweeperRewardCalculator
    participant OS as OS / Desktop Window

    Agent->>Env: step(action = ACTION_REVEAL)
    Note over Env: Map discrete action to key ('O')
    Env->>Hands: tap_key(VK_O)
    Hands->>OS: SendInput (Win32) / CGEventPost (macOS)
    OS-->>OS: LibreMines reveals tile under cursor
    
    Env->>Win: grab_frame()
    Win->>OS: mss screen grab
    OS-->>Win: raw BGR numpy array
    Win-->>Env: frame
    
    Env->>CV: read_board(frame)
    CV->>CV: find_board() connected components
    CV->>CV: classify 64 cells (0-8, HIDDEN, FLAGGED, MINE)
    CV-->>Env: curr_grid (8x8 ndarray)
    
    Env->>Calc: score(prev_grid, curr_grid)
    Calc-->>Env: reward (+1.0 safe, -10.0 mine), terminated, won
    
    Note over Env: Update internal observation & state
    Env-->>Agent: obs (8x8), reward, terminated, truncated, info
```

---

## 6. The milestone roadmap — completed state (M0–M5) & next (M6)

```mermaid
flowchart LR
    M0["M0 · Setup<br/>✅ DONE<br/><i>CartPole baseline ≈ 22</i>"]
    M1["M1 · Borrow the Brain<br/>✅ DONE<br/><i>PPO: 22 → 500</i>"]
    M2["M2 · Build our Ground<br/>✅ DONE<br/><i>GridWorld: +0.93<br/>20/20 goals</i>"]
    M3["M3 · Add the Eyes<br/>✅ DONE<br/><i>ViT-Tiny pixels: +0.99<br/>100% goals</i>"]
    M4["M4 · Make it Swappable<br/>✅ DONE<br/><i>Profile + factory<br/>4/4 check_swap PASS</i>"]
    M5["M5 · Add the Hands<br/>✅ DONE<br/><i>Live LibreMines<br/>4/4 check_hands PASS</i>"]
    M6["M6 · Stardew Valley<br/>⏳ NEXT / STRETCH<br/><i>Complex real game<br/>just another profile</i>"]

    M0 --> M1 --> M2 --> M3 --> M4 --> M5 --> M6

    style M0 fill:#d4edda,stroke:#3d9970
    style M1 fill:#d4edda,stroke:#3d9970
    style M2 fill:#d4edda,stroke:#3d9970
    style M3 fill:#d4edda,stroke:#3d9970
    style M4 fill:#d4edda,stroke:#3d9970
    style M5 fill:#d4edda,stroke:#3d9970
    style M6 fill:#fff3cd,stroke:#d39e00,stroke-width:3px
```

### The Discipline of the Milestones

| Milestone | The One Thing That Changed | Result |
| :--- | :--- | :--- |
| **M0 → M1** | Random actions → a learning brain | Reward **22 → 500** (ceiling reached on CartPole). |
| **M1 → M2** | Borrowed game → our own game | **+0.93** mean reward, **20/20** greedy goals on GridWorld. |
| **M2 → M3** | Observation is numbers → observation is a picture | **+0.99** mean reward, **100%** goals via frozen ViT-Tiny on CPU. |
| **M3 → M4** | Hard-coded wiring → config-driven wiring | 3 profiles trained via **1 unedited runner**; 4/4 swap checks PASS. |
| **M4 → M5** | Simulated in-memory env → live external desktop window | **4/4 live controls PASS** on macOS (16.8s) & Windows (22.4s); 20/20 unattended resets. |
| **M5 → M6** | Single-screen logic game → complex commercial game (Stardew) | Planned post-M5: complex multi-region visual perception profile. |

---

## 7. Component snapshot summary

| Component / Layer | Implementation | Status | Milestone |
| :--- | :--- | :--- | :--- |
| **Gymnasium Contract** | `gymnasium.Env` (`reset`, `step`) | ✅ Live | M0 |
| **Borrowed Brain** | `stable_baselines3.PPO` | ✅ Live | M1 |
| **Custom GridWorld Ground** | [`src/gametrainer/gridworld.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/gridworld.py) | ✅ Live | M2 |
| **ViT Eyes Extractor** | [`src/gametrainer/vit_extractor.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/vit_extractor.py) | ✅ Live | M3 |
| **Pixel Observation Wrapper** | [`src/gametrainer/perception.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/perception.py) | ✅ Live | M3 |
| **Profile Dataclass** | [`src/gametrainer/profile.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/profile.py) | ✅ Live | M4 |
| **Environment Factory** | [`src/gametrainer/factory.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/factory.py) | ✅ Live | M4 |
| **GridWorld Reward Calculator** | [`src/gametrainer/rewards.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/rewards.py) | ✅ Live | M4 |
| **Universal Profile Runner** | [`scripts/train_from_profile.py`](file:///Users/phillip/PycharmProjects/GameTrainer/scripts/train_from_profile.py) | ✅ Live | M4 |
| **Config Swappability Referee** | [`scripts/check_swap.py`](file:///Users/phillip/PycharmProjects/GameTrainer/scripts/check_swap.py) | ✅ Live | M4 |
| **Live Screen Capture** | [`src/gametrainer/screen.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/screen.py) (`GameWindow`) | ✅ Live | M5 |
| **Live Native Hands** | [`src/gametrainer/input.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/input.py) (`KeyboardInput`) | ✅ Live | M5 |
| **Connected Components CV** | [`src/gametrainer/minesweeper_vision.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/minesweeper_vision.py) | ✅ Live | M5 |
| **Minesweeper Reward Calculator** | [`src/gametrainer/rewards.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/rewards.py) | ✅ Live | M5 |
| **Minesweeper Gymnasium Adapter** | [`src/gametrainer/minesweeper.py`](file:///Users/phillip/PycharmProjects/GameTrainer/src/gametrainer/minesweeper.py) | ✅ Live | M5 |
| **Live Behavioral Proof** | [`scripts/check_hands.py`](file:///Users/phillip/PycharmProjects/GameTrainer/scripts/check_hands.py) | ✅ Live | M5 |
| **Stardew Valley Ground** | `profiles/stardew.yaml` | ⏳ Planned | M6 |
