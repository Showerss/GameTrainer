# setup.py
from setuptools import setup, Extension

setup(
    name="gametrainer",
    version="1.0",
    packages=["src.python.gui", "src.python.core"],
    ext_modules=[
        Extension(
            "gametrainer.clib",
            ["src/c/memory_manager.c", "src/c/input.c"],
            include_dirs=["include"],
        )
    ],
)