"""
InputController - Handles keyboard and mouse simulation

Teacher Note: This module wraps our C++ extension to provide high-level
input commands. We use C++ for the actual injection because it's more
reliable for games than Python libraries like pyautogui.
"""

import time
import random
from typing import Tuple

# Import our custom C++ "hands" extension (only built at M5; see setup.py).
try:
    import src.gametrainer.clib as clib
except ImportError:
    # No compiled extension found. Expected for M0–M2 (CartPole/GridWorld).
    import warnings
    warnings.warn(
        "[input] C++ input extension not loaded (fine for CartPole/GridWorld; needed at M5).",
        RuntimeWarning,
        stacklevel=2,
    )
    class MockClib:
        def send_key(self, code): pass
        def send_mouse_move(self, x, y): pass
        def jitter_move(self, x, y): pass
        def send_mouse_click(self): pass
        def send_mouse_right_click(self): pass
    clib = MockClib()


class InputController:
    """
    High-level interface for game input.

    Provides methods to simulate keyboard and mouse actions for game automation.
    Uses Windows SendInput via C++ extension for reliable game input.
    """

    # Virtual Key Codes (Windows)
    # https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
    VK_W = 0x57
    VK_A = 0x41
    VK_S = 0x53
    VK_D = 0x44
    VK_C = 0x43  # Tool
    VK_X = 0x58  # Check/Action
    VK_E = 0x45  # Menu
    VK_ESC = 0x1B

    def __init__(self):
        pass

    def tap_key(self, key_code: int, duration: float = 0.1):
        """
        Press and release a key.
        Time complexity: O(1) - single system call.
        """
        try:
            clib.send_key(key_code)
        except Exception as e:
            print(f"ERROR: Failed to send key {key_code}: {e}")

    # Movement keys
    def move_up(self): self.tap_key(self.VK_W)
    def move_down(self): self.tap_key(self.VK_S)
    def move_left(self): self.tap_key(self.VK_A)
    def move_right(self): self.tap_key(self.VK_D)

    # Action keys
    def use_tool(self): self.tap_key(self.VK_C)
    def action(self): self.tap_key(self.VK_X)
    def menu(self): self.tap_key(self.VK_E)
    def escape(self): self.tap_key(self.VK_ESC)

    def mouse_move(self, dx: int, dy: int):
        """
        Move mouse relative to current position.
        Time complexity: O(1) - single system call.
        """
        clib.send_mouse_move(dx, dy)

    def mouse_click(self):
        """
        Send a left mouse button click.
        Time complexity: O(1) - single system call.
        """
        try:
            clib.send_mouse_click()
        except Exception as e:
            print(f"ERROR: Failed to send mouse click: {e}")

    def mouse_right_click(self):
        """
        Send a right mouse button click.
        Time complexity: O(1) - single system call.
        """
        try:
            clib.send_mouse_right_click()
        except Exception as e:
            print(f"ERROR: Failed to send right mouse click: {e}")

class NullInput(InputController):
    """
    A no-op InputController for programmatic environments.

    Per PRD §4-5: InputController is subclassed by NullInput and KeyboardInput.
    NullInput is ideal for environments like CartPole where no real game input
    is needed — every action method silently does nothing.
    """

    def tap_key(self, key_code: int, duration: float = 0.1):
        """No-op key press."""
        pass

    def move_up(self): pass
    def move_down(self): pass
    def move_left(self): pass
    def move_right(self): pass
    def use_tool(self): pass
    def action(self): pass
    def menu(self): pass
    def escape(self): pass

    def mouse_move(self, dx: int, dy: int):
        """No-op mouse move."""
        pass

    def mouse_click(self):
        """No-op left mouse click."""
        pass

    def mouse_right_click(self):
        """No-op right mouse click."""
        pass
