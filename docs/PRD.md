## Commands

```bash
# Install core dependencies (also compiles the C++ input extension)
pip install -e .

# Install RL stack (torch, stable-baselines3, gymnasium, timm, tensorboard)
pip install -e ".[rl]"

# Install dev tools (pytest, black, mypy)
pip install -e ".[dev]"

# Run the retro TUI menu (interactive launcher)
python main.py

# Train directly (routes to scripts/train.py with no size arg = small ViT)
python main.py train

# Train with options
python scripts/train.py small              # recommended
python scripts/train.py tiny               # fast/low VRAM
python scripts/train.py base               # max capability
python scripts/train.py small --freeze     # freeze ViT backbone
python scripts/train.py small --steps 50000

# Play / inference
python main.py play
python scripts/play.py

# Tests
pytest

# Format / type-check
black .
mypy .

# Interactive input sanity check (requires Stardew Valley open)
python tests/test_input.py
```

## Architecture

### Pipeline overview

```
Screen (mss) → StardewViTEnv → PPO (SB3) ← ViTFeaturesExtractor (timm)
                    ↓
              InputController → C++ clib (Windows SendInput)
```

**Entry point** — `main.py` parses one optional argument (`train` / `play`) and delegates to `scripts/train.py` or `scripts/play.py`. No args launches the `rich`-based TUI in `src/gametrainer/tui.py`.

### Gym environment — `src/gametrainer/env_vit.py`

`StardewViTEnv` is the RL environment. Key design decisions:
- **Observation**: `(3, 224, 224)` uint8 channel-first RGB — matches ViT's native input size so positional embeddings need no interpolation.
- **Action space**: `Discrete(12)` — WASD, left/right click, 4-direction mouse aim, ESC, NO-OP.
- **Reward** is computed in `_calculate_reward()` — this is the primary "teaching surface". It currently uses pixel-diff for movement, click-interaction, loot notification detection (bottom-left region), energy bar tracking via HSV, and escalating penalties for passive/repetitive actions.
- `InterfaceManager` is called every 30 steps (not every frame) to locate UI templates via OpenCV template matching.

### ViT feature extractor — `src/gametrainer/vit_extractor.py`

Wraps a `timm` ViT model as an SB3 `BaseFeaturesExtractor`. Three concrete classes: `ViTFeaturesExtractor` (base, 768-dim), `ViTSmallFeaturesExtractor` (384-dim), `ViTTinyFeaturesExtractor` (192-dim). SB3's `CnnPolicy` is used with `policy_kwargs` pointing to these classes — the "Cnn" name is misleading, it just denotes the policy type that accepts custom feature extractors.

ImageNet normalization is applied in `forward()` before the ViT processes the frame.

### Training script — `scripts/train.py`

Auto-detects and resumes the latest checkpoint in `models/ppo_stardew_vit/`. Checkpoint naming: `stardew_vit_<N>_steps.zip`; final saves: `final_model.zip` / `interrupted_model.zip`. TensorBoard logs go to `logs/vit/`.

### Input — `src/gametrainer/input.py` + `src/cpp/clib.cpp`

**Windows-only.** The C++ extension (`clib`) calls the Windows `SendInput` API directly. It must be compiled before any actions reach the game — `pip install -e .` handles this via `setup.py`. The extension is imported as `src.gametrainer.clib`. Screen capture (`src/gametrainer/screen.py`) uses `mss` and locks to the game window by title.

### UI detection — `src/gametrainer/interface.py`

`InterfaceManager` loads PNG templates from `src/gametrainer/templates/` at startup and runs OpenCV `matchTemplate` to locate UI elements (e.g. `energy_icon.png`). The templates directory may not exist yet; the manager just warns and continues. Coordinates are cached in `self.locations` between scans.

### Config / profiles — `src/gametrainer/config.py`

`ConfigLoader` loads YAML profile files from `profiles/<game>/`. **Not yet connected to training** — `StardewViTEnv` still hardcodes `"Stardew Valley"` as the window title. Profile wiring is in-progress work.

### Package structure note

The package is `src.gametrainer` (not bare `gametrainer`). Scripts manually insert the project root into `sys.path` so imports work when run from the repo root. Always run scripts from the project root, not from inside `scripts/`.
