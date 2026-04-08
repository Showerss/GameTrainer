# GameTrainer

A **local, vision-based Reinforcement Learning (RL)** system that learns to play games from **pixels** and sends **keyboard/mouse inputs** back to the game.

> **AI agents:** Read `AGENTS.md` first. It is the authoritative technical context, constraints, and working agreements for this repo.

---

## What this is (in one paragraph)

GameTrainer runs entirely on your machine (GPU included). It captures the game window, feeds frames into a **PPO** agent with a **Vision Transformer (ViT)** feature extractor, then injects inputs via a **C++ SendInput** wrapper. It does **not** read game memory and does **not** modify the game process.

**Current target game:** Stardew Valley (the design is intended to be game-agnostic via profiles, but profile wiring is still in progress).

---

## Safety, ethics, and scope

- **Single-player only**: intended for local, offline experimentation on games you own and control.
- **No memory reading / no game modification**: pixels-in, actions-out only.
- **User override / window focus**: the agent is designed to lock to the target window and to pause when the user takes over (see `AGENTS.md` for the authoritative behavior expectations and constraints).

---

## Quickstart

### Retro TUI (recommended)

If you run GameTrainer with no args, you’ll get a retro-style menu that can:

- show name + version + “authored by”
- show the changelog
- launch training
- launch play/inference

```bash
python main.py
```

### Installation

1. Install Python 3.10+.
2. Install in editable mode (this also builds the C++ input extension):

```bash
pip install -e .
```

3. Install RL dependencies (torch/SB3/gymnasium/timm, etc.):

```bash
pip install -e ".[rl]"
```

### Train

```bash
python main.py train
```

Or pick a ViT size:

```bash
python scripts/train.py small   # recommended default
python scripts/train.py tiny    # faster, lower VRAM
python scripts/train.py base    # strongest, higher VRAM
```

### Play (inference only)

```bash
python main.py play
```

---

## How it works (mental model)

Pipeline:

```
┌─────────────────┐     ┌──────────────────────────────┐     ┌─────────────────┐
│  Screen Capture │ ──► │  RL Agent (PPO + ViT on GPU)  │ ──► │ Input Simulate  │
│   (mss/opencv)  │     │ (SB3 + timm feature extractor)│     │ (C++ SendInput) │
└─────────────────┘     └──────────────────────────────┘     └─────────────────┘
```

### Observation (what the agent sees)

- **224×224 RGB** frames (color is preserved; it matters for UI bars and state cues).
- The downscale is a deliberate trade-off: less text readability, more speed and better transfer learning from ImageNet-pretrained ViT weights.

#### ViT model sizes (practical guidance)

| Model Variant | Parameters | VRAM | Use Case |
| :--- | :--- | :--- | :--- |
| **Tiny** | ~5.7M | ~3GB | Rapid testing; verifies pipeline works. |
| **Small** | ~22M | ~6GB | **Recommended default.** Best balance of speed/smarts. |
| **Base** | ~86M | ~12GB+ | Maximum capability; slower training. |

### Actions (what the agent can do)

The environment uses a **single discrete action space** with 12 options:

| Index | Action        | Index | Action        |
| :---  | :---          | :---  | :---          |
| 0     | NO-OP         | 6     | Right Click   |
| 1     | W (up)        | 7     | Mouse Up      |
| 2     | S (down)      | 8     | Mouse Down    |
| 3     | A (left)      | 9     | Mouse Left    |
| 4     | D (right)     | 10    | Mouse Right   |
| 5     | Left Click    | 11    | ESC           |

### Reward (what “good” means)

Reward is a multi-component signal that encourages progress (e.g., movement/interaction/positive outcomes) and discourages unproductive or harmful behavior (e.g., energy depletion, getting stuck, wasted actions). The exact shaping evolves as training lessons are learned.

---

## Design choices (the “why”)

- **Pixels-in, actions-out**: keeps the project honest (human-like perception) and avoids fragile memory hooks.
- **ViT over CNN**: global attention helps relate distant UI regions (e.g., energy bar vs hotbar) without needing deep convolutional stacking.
- **Local-first**: no cloud dependencies; you can iterate on reward shaping and policies privately.
- **C++ only for input injection**: the reliability boundary is SendInput; perception and RL stay in Python for iteration speed.

---

## Current status (what’s true today)

- The codebase is aligned around the **RL pipeline** (Gymnasium env + Stable-Baselines3 PPO + ViT extractor).
- The “original” older design (Menu/Orchestrator + C++ CV/AI engine) is **not implemented** and is treated as historical reference only.
- **Profiles / ConfigLoader exist but are not fully wired** into the env/train scripts yet (hardcoded window title/paths are still present in places).

---

## Planned: Game profiles (multi-game support)

The engine is intended to be game-agnostic via **profiles** (a folder of config + assets). Today, the code has a `ConfigLoader`, but profile loading is **not fully connected** into training/play yet.

Planned profile structure:

```
profiles/
└── stardew_valley/
    ├── profile.yaml          # Main config (resolution, input mappings, window title)
    ├── templates/            # Images to match on screen (e.g. energy icon)
    │   └── *.png
    ├── regions.yaml          # UI element locations (optional override)
    └── knowledge/            # Optional external data (JSON)
```

---

## Where things typically live

- **Training artifacts**: saved SB3 models/checkpoints and run logs (location depends on the training script configuration; commonly under a `models/` and/or `runs/`-style directory).
- **Reward logic**: inside the Gymnasium environment implementation (the env is the “teaching surface” in RL).
- **Per-game assets/config**: under `profiles/<game>/` once profile wiring is completed.

---

## Design pivot log (append-only, human-readable)

This section is for **high-level design pivots** (why the direction changed). For code-level change notes, see `CHANGELOG.md`.

### 2026-02 (Pivot): “Rule engine / decision tree” → RL (PPO + ViT)

- **What changed**: the project direction shifted away from a hand-authored decision engine and toward a learning agent that improves via reinforcement learning.
- **Why**: to build something that generalizes better, matches the “learning not scripting” goal, and leverages transfer learning from pretrained vision backbones.
- **Consequences**: environment/reward design became the primary “control surface”; C++ scope shrank to input injection only.

### 2026-02 (Docs): Multi-file documentation → monolithic README + dense AGENTS

- **What changed**: human-facing docs were consolidated into this `README.md`, and technical/agent-oriented context was centralized into `AGENTS.md`.
- **Why**: reduce markdown sprawl while still supporting deep, consistent AI assistance.

---

## Documentation & code philosophy (project-specific)

This is an **educational codebase**. Changes should favor clarity and “teachability”:

- Explain the **why**, not just the what.
- Prefer clear names over clever abbreviations.
- Break complex flows into well-named helpers.
- Use diagrams where they genuinely improve understanding.

---

## Dependencies (high-level)

- **Screen capture**: `mss`, `opencv-python`, `numpy`
- **RL stack**: `gymnasium`, `stable-baselines3`, `torch`, `timm` (installed via `pip install -e ".[rl]"`)
- **Input simulation**: custom C++ extension (`clib`) using Windows SendInput
- **Config**: PyYAML (profiles/regions)

---

## Resource usage (rule of thumb)

```
┌─────────────────────────────────────────────────────────────────┐
│                     RESOURCE BREAKDOWN                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TRAINING PHASE (Continuous / Overnight):                       │
│  ├── Hardware ........................... GPU HEAVY             │
│  ├── API Costs .......................... $0 (Local only)       │
│  ├── Time ............................... Hours/Days            │
│  └── Output ............................. Trained Neural Net    │
│                                                                  │
│  INFERENCE PHASE (Playing):                                     │
│  ├── Hardware ........................... GPU Light/Moderate    │
│  ├── API Costs .......................... $0                    │
│  └── Latency ............................ Real-time (< 30ms)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Glossary

- **AI**: Artificial Intelligence.
- **CNN**: Convolutional Neural Network.
- **CUDA**: NVIDIA’s GPU computing platform (used by PyTorch for acceleration).
- **Gym / Gymnasium**: The standard Python API for RL environments (observation/action spaces + `step()`/`reset()`).
- **ImageNet**: Large image dataset commonly used for pretraining vision models.
- **Inference**: Running a trained model to choose actions (no learning / no weight updates).
- **mss**: A Python library for fast screen capture.
- **OCR**: Optical Character Recognition (extracting text from pixels).
- **OpenCV**: Open Source Computer Vision Library (image processing utilities).
- **PPO**: Proximal Policy Optimization (the RL algorithm used for training the policy).
- **RL**: Reinforcement Learning (learning by trial-and-error using rewards).
- **ROI**: Region of Interest (a sub-rectangle of the screen/frame to focus processing on).
- **SB3**: Stable-Baselines3 (a widely used RL library that provides PPO and training utilities).
- **SendInput**: Windows API used for keyboard/mouse input injection (this project uses a C++ wrapper/extension).
- **Template matching**: A computer-vision technique that finds a small image (template) within a larger image (frame), often used for UI detection.
- **Transfer learning**: Starting from pretrained model weights (e.g., ImageNet) to speed up learning on a new task.
- **ViT**: Vision Transformer (a transformer architecture adapted for images, using attention over patches).
- **VRAM**: GPU memory.

---

## Where to look next

- **Humans**: you’re here in `README.md` (this is the canonical narrative).
- **AI / deep technical context**: `AGENTS.md` (authoritative constraints, repo truths, and expectations).
- **Code change notes**: `CHANGELOG.md` (append-only).
