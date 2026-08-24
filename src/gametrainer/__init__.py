"""
GameTrainer - Local Reinforcement Learning for Game Automation

This package provides tools for training RL agents to play games using
visual input (screen capture) and simulated keyboard/mouse output.

Modules:
    - logger: Timestamped session logging
    - input: Keyboard/mouse simulation via C++ extension
    - gridworld: Our own 5x5 Gymnasium environment
    - perception: PixelObservation wrapper (renders GridWorld to pixels)
    - vit_extractor: ViT feature extractor for SB3
    - profile: Loads a Profile (ground + perception + reward + PPO numbers) from YAML
    - rewards: RewardCalculator
    - hardware: CUDA/MPS/CPU device picker
    - tui: the retro menu
"""

__version__ = "2.0"
__author__ = "Phillip"

# NOTE: We deliberately do NOT eager-import the submodules here.
# Each submodule (vit_extractor, ...) pulls in heavy, later-milestone
# dependencies (torch, timm). Importing them at package load
# would force an M0 script like scripts/run_cartpole.py to need M3-M5 libraries
# just to reach NullInput. Consumers import what they need from submodules
# directly, e.g. `from src.gametrainer.input import NullInput`.
