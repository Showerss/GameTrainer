# 2. trainer.py is a high level loop that polls information coming from memory_controller.py every 0.5s and compares the energy, health, etc to the 
# thresholds set in the trainer GUI.  If the thresholds are met, the trainer will use the input simulator to perform the actions needed to 
# reach the thresholds, it will also load a C .dll that use windows actions to perform the actions needed to reach the thresholds


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