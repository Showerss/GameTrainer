"""
GameTrainer Setup Configuration
"""

import sys

from setuptools import setup

_install_requires = [
    "opencv-python",  # Image processing and computer vision
    "mss",            # Fast screen capture
    "numpy",          # Array operations (used by OpenCV)
    "pyyaml",         # YAML config file parsing
    "rich",           # Terminal formatting for the TUI menu (main.py's default path)
]

# macOS's KeyboardInput/GameWindow (M5) use Quartz and AppKit directly for
# window finding, capture and CGEventPost key injection.
if sys.platform == "darwin":
    _install_requires += [
        "pyobjc-framework-Quartz",
        "pyobjc-framework-Cocoa",
    ]


setup(
    name="gametrainer",
    version="2.0",
    description="Vision-based game automation with Reinforcement Learning",
    packages=[
        "src.gametrainer",
    ],

    # Python dependencies
    install_requires=_install_requires,

    # Optional dependencies for development
    extras_require={
        "dev": [
            "pytest",     # Testing framework
            "black",      # Code formatter
            "mypy",       # Type checker
        ],
        "rl": [
            "gymnasium[classic-control]",  # Standard API for RL envs
            "stable-baselines3",           # RL algorithms (PPO, DQN, etc.)
            "torch",                       # Deep learning backend
            "tensorboard",                 # Training visualization
            "timm",                        # PyTorch Image Models - provides ViT architectures
        ],
    },

    python_requires=">=3.9",
)
