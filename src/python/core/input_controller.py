"""
InputController - Handles keyboard and mouse simulation

Teacher Note: This module wraps our C++ extension to provide high-level
input commands. We use C++ for the actual injection because it's more
reliable for games than Python libraries like pyautogui.
"""

import time
import random
from typing import Tuple

# Import our custom C++ extension
# Note: This might fail if the extension isn't built yet
try:
    import src.python.core.clib as clib
except ImportError:
    print("WARNING: C++ extension not found. Input simulation will not work.")
    # Mock for testing/linting without build
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
        # For now, our C++ SendKey does a full press+release instantly.
        # Ideally we'd separate down/up for duration control.
        # TODO: Update C++ to support hold duration.
        try:
            clib.send_key(key_code)
        except Exception as e:
            print(f"ERROR: Failed to send key {key_code}: {e}")
        
        # If we need to simulate holding, we'd need separate down/up functions in C++.
        # For discrete RL steps, a "tap" is usually sufficient for movement.

    def move_up(self): self.tap_key(self.VK_W)
    def move_down(self): self.tap_key(self.VK_S)
    def move_left(self): self.tap_key(self.VK_A)
    def move_right(self): self.tap_key(self.VK_D)
    
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
        
        Following clean code principles: Clear, descriptive method name.
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
