"""
GameTrainer Setup Configuration

Teacher Note: This file tells Python how to build and install our project.
The 'ext_modules' section defines our C++ extension for input simulation.
We use C++ for input because it needs direct access to Windows APIs.
"""

import sys
from setuptools import setup, Extension

# Only compile the C++ input-injection extension on Windows.
# Per PRD v1 constraints: Python-only, CPU-first for early phases; no C++ on macOS.
_ext_modules = []
if sys.platform == "win32":
    _ext_modules = [
        Extension(
            "src.gametrainer.clib",
            sources=[
                "src/cpp/clib.cpp",
            ],
            include_dirs=["include"],
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
            "gymnasium",         # Standard API for RL environments
            "stable-baselines3", # RL algorithms (PPO, DQN, etc.)
            "torch",             # Deep learning backend
            "tensorboard",       # Training visualization
            "shimmy",            # Compatibility layer often needed for gym v0.26+
            "timm",              # PyTorch Image Models - provides ViT architectures
        ],
    },

    python_requires=">=3.9",
)
