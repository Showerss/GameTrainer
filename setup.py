from setuptools import setup, Extension
from setuptools import setup, Extension

setup(
    name="gametrainer",
    version="1.0",
    packages=["src.python.gui", "src.python.core"],
    ext_modules=[
        Extension(
            "src.python.core.clib",
            ["src/cpp/memory_manager.cpp", "src/cpp/input.cpp", "src/cpp/py_init.cpp"],
            include_dirs=["include"],
            libraries=["user32", "kernel32"],
        )
    ],
    install_requires=[
        "opencv-python",
        "mss",
        "numpy",
        "pyadirectinput",
    ],
)