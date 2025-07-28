# src/python/core/trainer.py
import ctypes
from pathlib import Path

class GameTrainer:
    def __init__(self):
        # Load the compiled C library
        lib_path = Path(__file__).parent.parent.parent / "build" / "libgametrainer.dll"
        self.lib = ctypes.CDLL(str(lib_path))

        # Set up function signatures
        self.lib.SendMouseMove.argtypes = [ctypes.c_int, ctypes.c_int]
        self.lib.SendMouseMove.restype = None

    def send_mouse_move(self, dx: int, dy: int):
        """Python wrapper for C function SendMouseMove"""
        self.lib.SendMouseMove(dx, dy)