"""
GameTrainer Setup Configuration

Teacher Note: This file tells Python how to build and install our project.
The 'ext_modules' section defines our C++ extension for input simulation.
We use C++ for input because it needs direct access to Windows APIs.
"""

from setuptools import setup, Extension

setup(
    name="gametrainer",
    version="2.0",
    description="Vision-based game automation with Reinforcement Learning",
    packages=[
        "src.gametrainer",
    ],

    # C++ Extension for input simulation
    # Teacher Note: This compiles our C++ code into a Python-importable module.
    # The input.cpp file wraps Windows SendInput for keyboard/mouse simulation.
    ext_modules=[
        Extension(
            "src.gametrainer.clib",
            sources=[
                "src/cpp/input.cpp",
                "src/cpp/py_init.cpp",
            ],
            include_dirs=["include"],
            libraries=["user32", "kernel32"],
        )
    ],

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
