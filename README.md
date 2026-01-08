# GameTrainer

A local Reinforcement Learning (RL) agent for automating games using Computer Vision and Vision Transformers (ViT).

## Overview
GameTrainer uses **Stable-Baselines3** and **Vision Transformers** to learn how to play games (currently optimized for Stardew Valley) by looking at the screen and simulating keyboard/mouse input. It requires no memory reading or game modification.

## Features
- **ViT-Powered Vision:** Uses Vision Transformers (Tiny, Small, or Base) for superior global screen understanding.
- **Local Training:** Optimized for local GPU training (designed for 9070xt class hardware).
- **Fast Screen Capture:** Uses `mss` for high-speed frame grabbing.
- **Robust Input:** Custom C++ `SendInput` wrapper for reliable game control.
- **Window Detection:** Smart logic to lock onto the game window while ignoring tooltips.

## Installation
1. Ensure you have Python 3.10+ installed.
2. Install the package in editable mode:
   ```bash
   pip install -e .
   ```
   *Note: This will also compile the C++ input extensions.*

## Usage

### Training
To start training a new agent or resume training an existing one:
```bash
python main.py train
```
Or with specific model sizes:
```bash
python scripts/train.py small   # Recommended default
python scripts/train.py tiny    # Fast, low VRAM
python scripts/train.py base    # Most powerful, high VRAM
```

### Playing
To run the trained agent in "inference only" mode (no learning):
```bash
python main.py play
```

## Documentation
- **[CLAUDE.md](CLAUDE.md):** Detailed guide for AI assistants and technical implementation notes.
- **[docs/design.md](docs/design.md):** High-level architectural overview and philosophy.

## Safety
GameTrainer includes automatic pause-on-user-input and focuses only on the specific game window. It is intended for **single-player use only**.
