"""
GameTrainer - Local Reinforcement Learning for Game Automation

This package provides tools for training RL agents to play games using
visual input (screen capture) and simulated keyboard/mouse output.

Modules:
    - config: Configuration loading from YAML profiles
    - logger: Timestamped session logging
    - screen: Fast screen capture using mss
    - input: Keyboard/mouse simulation via C++ extension
    - env_vit: Gymnasium environment (ViT-based) for RL training
    - interface: Template matching for UI detection
    - vit_extractor: ViT feature extractor for SB3
    - events: Event bus (placeholder)
    - dependencies: Auto-installation of optional packages
"""

__version__ = "2.0"
__author__ = "Phillip"

# NOTE: We deliberately do NOT eager-import the submodules here.
# Each submodule (screen, env_vit, ...) pulls in heavy, later-milestone
# dependencies (mss, torch, timm, win32gui). Importing them at package load
# would force an M0 script like scripts/run_cartpole.py to need M3-M5 libraries
# just to reach NullInput. Consumers import what they need from submodules
# directly, e.g. `from src.gametrainer.input import NullInput`.
