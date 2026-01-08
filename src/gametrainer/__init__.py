"""
GameTrainer - Local Reinforcement Learning for Game Automation

This package provides tools for training RL agents to play games using
visual input (screen capture) and simulated keyboard/mouse output.

Modules:
    - config: Configuration loading from YAML profiles
    - logger: Timestamped session logging
    - screen: Fast screen capture using mss
    - input: Keyboard/mouse simulation via C++ extension
    - env: Gymnasium environment for RL training
    - events: Event bus for component communication
    - dependencies: Auto-installation of optional packages
"""

__version__ = "2.0"
__author__ = "GameTrainer"

# Convenient imports for users of the package
from src.gametrainer.logger import Logger
from src.gametrainer.screen import ScreenCapture
from src.gametrainer.input import InputController
from src.gametrainer.config import ConfigLoader
from src.gametrainer.env_legacy import StardewEnv

__all__ = [
    "Logger",
    "ScreenCapture",
    "InputController",
    "ConfigLoader",
    "StardewEnv",
]
