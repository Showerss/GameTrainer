"""
GameTrainer Setup Configuration

Teacher Note: This file tells Python how to build and install our project.
The 'ext_modules' section defines our C++ extension for input simulation.
We use C++ for input because it needs direct access to Windows APIs.
"""

import os
import sys
from setuptools import setup, Extension

# The C++ input-injection extension ("the hands") is OPT-IN — not built by default.
#
# Why: early milestones (M0-M1 CartPole, M2 GridWorld) never press real keys; they
# use the NullInput stub, so there is nothing to compile. A plain `pip install -e .`
# should not drag in the MSVC compiler just to run CartPole.
#
# When you actually need it (M5, real keyboard input), opt in by setting this
# environment variable before installing (Windows + Visual C++ Build Tools):
#     GAMETRAINER_BUILD_CPP=1
# Per PRD v1 constraints: Python-only, CPU-first for early phases; no C++ on macOS.
_ext_modules = []
if sys.platform == "win32" and os.environ.get("GAMETRAINER_BUILD_CPP") == "1":
    _ext_modules = [
        Extension(
            "src.gametrainer.clib",
            sources=[
                "src/cpp/clib.cpp",
            ],
            libraries=["user32", "kernel32"],
        )
    ]


setup(
    name="gametrainer",
    version="2.0",
    description="Vision-based game automation with Reinforcement Learning",
    packages=[
        "src.gametrainer",
    ],

    ext_modules=_ext_modules,

    # Python dependencies
    install_requires=[
        "opencv-python",  # Image processing and computer vision
        "mss",            # Fast screen capture
        "numpy",          # Array operations (used by OpenCV)
        "pydantic",       # JSON schema validation for knowledge base
        "pyyaml",         # YAML config file parsing
        "pynput",         # Global keyboard/mouse input capture
    ],

    # Optional dependencies for development
    extras_require={
        "dev": [
            "pytest",     # Testing framework
            "black",      # Code formatter
            "mypy",       # Type checker
        ],
        "ai": [
            "anthropic",  # Claude API for knowledge compilation
        ],
        "rl": [
            "gymnasium[classic-control]",  # Standard API for RL envs; extra pulls pygame for CartPole rendering
            "stable-baselines3", # RL algorithms (PPO, DQN, etc.)
            "torch",             # Deep learning backend
            "tensorboard",       # Training visualization
            "shimmy",            # Compatibility layer often needed for gym v0.26+
            "timm",              # PyTorch Image Models - provides ViT architectures
        ],
    },

    python_requires=">=3.9",
)
