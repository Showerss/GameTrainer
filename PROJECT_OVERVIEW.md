# GameTrainer — Project Overview

This document describes what GameTrainer is, how it works, and how it’s built. It’s written so that both humans (e.g. a CS student) and AI assistants can follow the full picture in one place.

---

## What GameTrainer Is

GameTrainer is a **local Reinforcement Learning (RL)** system for game automation. You run it on your own machine (and GPU); it learns to play a game by looking at the screen and sending keyboard/mouse input—no cloud, no memory reading, no game modification.

**Current target:** Stardew Valley. The agent is trained with a **Vision Transformer (ViT)** and **PPO** so it improves over time from trial and error instead of following hand-written rules.

**Design choices (Jan 2026 and onward):**
- **Pixels in, actions out:** The agent sees the same screen you do (captured and downscaled) and learns from that. No manual coordinate or color definitions.
- **Local only:** All training and playing happens on your hardware (e.g. a 9070xt-class GPU). No data is sent to the cloud.
- **Learning, not scripting:** The goal is an agent that gets better with experience (RL), not a fixed bot that only does what you programmed.

## Architecture

The pipeline is three steps: capture the game window, run the neural network, send input back to the game.

```
┌─────────────────┐     ┌──────────────────────────────┐     ┌─────────────────┐
│  Screen Capture │ ──► │  RL Agent (PPO + ViT on GPU)   │ ──► │ Input Simulate  │
│   (mss/opencv)  │     │   (Stable-Baselines3 + timm)  │     │ (C++ SendInput) │
└─────────────────┘     └──────────────────────────────┘     └─────────────────┘
```

## Reinforcement Learning Strategy

We use `gymnasium` and `stable-baselines3` with a custom **Vision Transformer (ViT)** feature extractor.

### 1. Perception (The Eyes)
We have moved beyond standard CNNs to use **Vision Transformers**.
- **Model:** ViT-Base or ViT-Small (via `timm`), pre-trained on ImageNet.
- **Input:** **224x224 RGB**. We do *not* convert to grayscale or aggressively downscale to 84x84. Color is vital for health/energy bars.
- **Why ViT?** Global Attention. In Stardew, the energy bar (top-right) and hotbar (bottom) are spatially distant but contextually related. ViTs connect these distinct screen regions immediately via self-attention, whereas CNNs require deep layering to find these relationships.

#### Vision Transformer (ViT) Details
| Model Variant | Parameters | VRAM | Use Case |
| :--- | :--- | :--- | :--- |
| **Tiny** | ~5.7M | ~3GB | Rapid testing; verifies pipeline works. |
| **Small** | ~22M | ~6GB | **Recommended Default.** Best balance of speed/smarts. |
| **Base** | ~86M | ~12GB+ | Maximum capability; slower training. |

**Important Note on Resolution:**
Regardless of the model size (Tiny/Small/Base), the input is **always 224x224 RGB**.
- **The "Squish":** The game's 1080p screen is downscaled to 224x224.
- **Trade-off:** We sacrifice fine text readability for **speed** and **transfer learning** (leveraging ImageNet weights). The AI sees "blobs" and "shapes" (green bar = energy) rather than reading specific numbers.

### 2. Action (The Hands)
The agent outputs **discrete actions** only. Each step it picks one of 12 actions: no-op, movement (W/A/S/D), left/right mouse click, mouse aim (up/down/left/right), and ESC. The exact mapping is in the table in "Action Space (Output)" below.

### 3. Reward (The Teacher)
We define a reward function to guide learning:
- **Positive:** Gaining XP, harvesting crops, clearing debris.
- **Negative:** Running out of energy, taking damage, wasted movement.
- **Neutral:** Existing.

### 4. Training Loop (The Brain)
- **Local & Fast:** Runs entirely on the 9070xt GPU.
- **Transfer Learning:** By using pre-trained ViT weights, the agent already understands "shapes" and "objects" before the first frame, significantly speeding up convergence compared to training a CNN from scratch on pixels.
- **Exploration:** The agent actively tries new strategies to discover optimal play.

## Environment & State

The "Knowledge" of the system is implicit within the Transformer's attention weights.

### Observation Space (Input)
- **Visual:** 224×224×3 (RGB) frames. The only observation the agent gets today.
- **Auxiliary (optional / future):** OCR or numeric gauges (e.g. energy %) could be added as an extra input later if needed.

### Action Space (Output)
The environment uses a **single discrete action space** with 12 options:

| Index | Action        | Index | Action        |
| :---  | :---          | :---   | :---          |
| 0     | NO-OP         | 6      | Right Click   |
| 1     | W (up)        | 7      | Mouse Up      |
| 2     | S (down)      | 8      | Mouse Down    |
| 3     | A (left)      | 9      | Mouse Left    |
| 4     | D (right)     | 10     | Mouse Right   |
| 5     | Left Click    | 11     | ESC           |

### Where things live
- **Checkpoints and hyperparameters:** Saved `.zip` models and training settings live in the repo (e.g. `models/ppo_stardew_vit/`, `scripts/train.py`). Reward logic is in the environment code.
- **Per-game config (profiles):** See the next section.

## Game Profiles (Multi-Game Support)

The engine is designed to be game-agnostic: in theory you swap a **profile** (a folder of config and assets) to target a different game. Right now, only Stardew Valley is wired in; profile loading exists in code (`ConfigLoader`) but is not yet connected to the training or play scripts (window title and paths are hardcoded).

**How the bot actually runs:** It runs on the **trained neural network** (PPO + ViT) saved to disk. You train with `python main.py train`, then play with `python main.py play`. There is no separate “rule engine” or “decision tree” in the loop—just the policy network.

**Intended profile layout** (for when profiles are wired in):

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE ENGINE (shared)                      │
│  - Screen capture (mss)                                      │
│  - RL agent (PPO + ViT)                                      │
│  - Template matching (UI detection, e.g. energy bar)        │
│  - Input simulation (C++ SendInput)                           │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  Stardew   │  │  Game B    │  │  Game C    │
     │  Profile   │  │  Profile   │  │  Profile   │
     └────────────┘  └────────────┘  └────────────┘
```

### Profile structure (planned)

```
profiles/
└── stardew_valley/
    ├── profile.yaml          # Main config (resolution, input mappings)
    ├── templates/            # Images to match on screen (e.g. energy icon)
    │   └── *.png
    ├── regions.yaml          # UI element locations (optional override)
    └── knowledge/            # Optional wiki/strategy data (JSON)
```

| Component      | Purpose |
|----------------|---------|
| **profile.yaml** | Input mappings, resolution, game window title. |
| **templates/**   | Images used for template matching (e.g. energy bar). |
| **regions.yaml** | Where UI elements appear; used by vision/reward logic when loaded. |
| **knowledge/**   | Optional external data (e.g. calendars, crop info). |

## Changelog

- **Never overwrite the changelog.** The file `CHANGELOG.md` is append-only. When making changes that warrant a release note, add a new entry under the appropriate version or "Unreleased" section. Do not remove or rewrite existing changelog content.

## Code Style & Documentation Philosophy

**This is an educational codebase.** All code should be written as if teaching a student:

- Write comments that explain the "why", not just the "what"
- Use clear, descriptive variable names over clever abbreviations
- Include "Teacher Notes" in comments for non-obvious concepts
- Break complex operations into well-named helper functions
- Add ASCII diagrams where they aid understanding
- Reference external resources (docs, tutorials) when introducing new concepts

Example comment style:
```python
# Teacher Note: We use a separate thread here because the main thread
# is busy running the GUI. If we did our AI loop on the main thread,
# the window would freeze and become unresponsive.
```

## Build & Run

```bash
pip install -e .           # Core deps + C++ input extension
pip install -e ".[rl]"     # RL stack (gymnasium, SB3, torch, timm) — needed for train/play
python main.py train      # Train the agent
python main.py play       # Run a trained agent
pytest tests/             # Run tests
```

## Dependencies

- **Screen capture:** mss, opencv-python, numpy
- **RL stack:** gymnasium, stable-baselines3, torch, timm (see `setup.py` extras: `pip install -e ".[rl]"`)
- **Input simulation:** Custom C++ extension (`clib`) using Windows SendInput—no pyautogui/pyadirectinput
- **Config:** PyYAML for profile/region config
- **Optional / future:** A GUI (e.g. tkinter) and a proper setup/installer run for dependencies are aspirational; the current flow is CLI (`main.py train` / `main.py play`) and `pip install -e .`

## Resource Usage

```
┌─────────────────────────────────────────────────────────────────┐
│                     RESOURCE BREAKDOWN                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TRAINING PHASE (Continuous / Overnight):                       │
│  ├── Hardware ........................... GPU (9070xt) HEAVY    │
│  ├── API Costs .......................... $0 (Local only)       │
│  ├── Time ............................... Hours/Days            │
│  └── Output ............................. Trained Neural Net    │
│                                                                  │
│  INFERENCE PHASE (Playing):                                     │
│  ├── Hardware ........................... GPU (Light/Moderate)  │
│  ├── API Costs .......................... $0                    │
│  └── Latency ............................ Real-time (< 30ms)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
