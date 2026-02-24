# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GameTrainer is a **local Reinforcement Learning (RL)** system for game automation. It leverages high-end hardware (specifically the user's **9070xt GPU**) to train an autonomous agent that learns to play Stardew Valley through trial and error.

**Pivot Note (Jan 2026):** We have moved AWAY from the previous "video upload + manual pixel detection" strategy.
- **No more pixel hunting:** Manual coordinate/color definitions are unscalable and brittle. The agent uses neural networks (CNNs) to perceive the game state directly from visual input.
- **No more video uploads:** We do not send data to the cloud. Training happens locally to allow the agent to learn from unlimited gameplay steps and edge cases without API costs or latency.
- **Active Learning:** The goal is an agent that improves over time via RL, rather than a static bot that "fails safe" when confused.

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────┐     
┌─────────────────┐
│  Screen Capture │ ──► │  RL Agent (PPO/ViT on GPU)   │ ──► │ Input Simulate  │
│   (mss/opencv)  │     │   (SB3 + timm ViT-Base)      │     │   (SendInput)   │
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
The agent outputs discrete actions (e.g., `Move Up`, `Use Tool`, `Eat`) or continuous values depending on the specific task configuration.

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
- **Visual:** 224x224 x 3 (RGB) frames.
- **Auxiliary (Optional):** OCR text or critical numerical values (Energy %) can be fed as a separate vector if visual learning proves too slow for specific gauges.

### Action Space (Output)
- **Discrete:** Mapping specific indices to key presses (e.g., `0` = W, `1` = A, `2` = S, `3` = D, `4` = Use Tool).
- **MultiDiscrete:** For combining movement + action simultaneously.

### Game Profiles
Profiles now store:
- **Hyperparameters:** Learning rate, batch size, PPO/DQN settings.
- **Checkpoints:** Saved `.zip` models of the trained agent.
- **Reward Config:** Definitions of what constitutes "good" behavior for that specific game.

## Game Profiles (Multi-Game Support)

The engine is game-agnostic. Each game is defined by a **profile** - a configuration folder containing everything game-specific:

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE ENGINE (shared)                      │
│  - Screen capture                                            │
│  - Template matching system                                  │
│  - Decision tree executor                                    │
│  - Input simulation                                          │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  Stardew   │  │  Game B    │  │  Game C    │
     │  Profile   │  │  Profile   │  │  Profile   │
     └────────────┘  └────────────┘  └────────────┘
```

### Profile Structure

```
profiles/
└── stardew_valley/
    ├── profile.yaml          # Main config (resolution, input mappings)
    ├── recordings/           # Gameplay videos for training
    │   ├── raw/              # Original recorded footage
    │   │   ├── session_001.mp4
    │   │   └── session_002.mp4
    │   └── analyzed/         # Videos that have been processed
    │       └── session_001.mp4
    ├── templates/            # Images to match on screen (extracted from videos)
    │   ├── crops/
    │   │   ├── tomato_ripe.png
    │   │   └── tomato_growing.png
    │   ├── ui/
    │   │   ├── energy_bar.png
    │   │   └── inventory_full.png
    │   └── objects/
    │       └── chest.png
    ├── regions.yaml          # Where to look for UI elements (learned from videos)
    │   # date_display: {x: 1200, y: 10, w: 100, h: 30}
    │   # energy_bar: {x: 1250, y: 600, w: 50, h: 200}
    ├── knowledge/            # Wiki data, strategies (optional supplement)
    │   ├── calendar.json     # Events, festivals
    │   └── crops.json        # Growth times, prices
    └── rules/                # Decision tree definitions (generated from video analysis)
        ├── priorities.yaml   # Master priority list
        └── subtrees/
            ├── farming.yaml
            └── navigation.yaml
```

### Profile Components

| Component | Purpose | Example |
|-----------|---------|---------|
| **recordings/** | Gameplay videos for Claude to analyze | `session_001.mp4` |
| **templates/** | Images to find on screen (auto-extracted) | `tomato_ripe.png` |
| **regions.yaml** | Fixed UI element locations (learned from video) | `energy_bar: {x: 1250, y: 600}` |
| **knowledge/** | External game data (wiki, guides) - optional | `festivals.json` |
| **rules/** | Decision tree logic (generated from video analysis) | `if energy < 20 → eat` |
| **profile.yaml** | Input mappings, resolution, settings | `harvest_key: "mouse1"` |

### Creating a New Game Profile (Video-Based Workflow)

1. **Record Gameplay:** Capture 5-30 minutes of gameplay video showing various scenarios
   - Play normally, demonstrating the actions you want the bot to learn
   - Include edge cases: low health situations, inventory management, etc.

2. **Upload to Claude:** Send video clips to Claude API for analysis
   - Claude watches the video and identifies UI elements, game states, patterns
   - **This is the only paid API cost** - everything after is free

3. **Auto-Extract Training Data:** Claude generates:
   - Template images (cropped from video frames)
   - Region definitions (where UI elements are located)
   - Decision rules (when to take which actions)
   - Action mappings (what inputs achieve what)

4. **Review & Refine:** Manually review the generated rules
   - Adjust priorities, fix any misidentifications
   - Add supplementary knowledge from wikis if needed

5. **Run Locally (Free Forever):** The bot now runs using local decision trees
   - No more API calls during gameplay
   - All knowledge is stored in the profile folder

The core engine code never changes - only the profile folder is swapped.

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
pip install -e .      # Install dependencies and build C++ extensions
python main.py        # Run the application
pytest tests/         # Run tests
```

## Dependencies

- **Screen Capture & Recording:** mss, opencv-python, numpy, ffmpeg (for video encoding)
- **Video Analysis (Training):** anthropic SDK with video support
- **Input Simulation:** pyadirectinput, custom C++ SendInput wrapper
- **GUI:** tkinter

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
