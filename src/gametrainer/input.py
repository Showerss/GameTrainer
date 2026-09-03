"""
InputController - Handles keyboard and mouse simulation

Teacher Note: This module wraps our C++ extension to provide high-level
input commands. We use C++ for the actual injection because it's more
reliable for games than Python libraries like pyautogui.
"""


import ctypes
import sys
import time

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

    # LibreMines (M5). All four verified by hand in the pre-flight spike:
    # O reveals, P flags, Ctrl+R restarts. See docs/m5/M5_ToDo.md.
    VK_O = 0x4F  # Reveal
    VK_P = 0x50  # Flag
    VK_R = 0x52
    VK_CONTROL = 0x11

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

    def tap_chord(self, modifier_code: int, key_code: int):
        """
        Hold a modifier down, tap a key, let go. Real hands only.

        A second primitive is needed because tap_key cannot express a chord:
        Ctrl+R means the Ctrl key is still down when R goes down. The C++
        clib this base class wraps only knows single keys, so the base has
        nothing to delegate to - see KeyboardInput.
        """
        raise NotImplementedError(
            "tap_chord needs real hands - see KeyboardInput."
        )

    # Minesweeper keys (M5). These are deliberately written in terms of
    # tap_key/tap_chord and nothing else, so any subclass that overrides those
    # two primitives gets all three verbs for free - which is exactly how
    # NullInput stays a perfect stand-in for the real hands (control 2).
    def reveal(self): self.tap_key(self.VK_O)
    def flag(self): self.tap_key(self.VK_P)
    def restart(self): self.tap_chord(self.VK_CONTROL, self.VK_R)

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

    def tap_chord(self, modifier_code: int, key_code: int):
        """No-op chord. reveal(), flag() and restart() route through this and
        tap_key, so they need no override of their own and cannot drift."""
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


# ===========================================================================
# The real hands - M5 Brick 3.
#
# Teacher Note: what SendInput actually is
# =======================================
# Windows keeps one queue of input events, and every program reads from it.
# Pressing a key on the keyboard puts an event on that queue; SendInput puts
# an identical event on the same queue. Nothing downstream can tell the two
# apart - which is the whole reason a Python program can play a game it did
# not write and cannot see inside. The pre-flight spike proved LibreMines
# accepts these: W moved the cursor and changed 3,248 pixels, D changed
# exactly 6,496 - twice as many, because it cleared one cell and lit another.
#
# It also explains the one rule that follows: the queue delivers to whichever
# window has focus, not to whichever window we meant. So these hands are
# bound to one window handle and refuse to type when that window is not in
# front. Typing our moves into the user's editor is the failure this guard
# exists to prevent.
# ===========================================================================

_WORD = ctypes.c_ushort
_DWORD = ctypes.c_ulong
_LONG = ctypes.c_long
# ULONG_PTR is pointer-sized - 8 bytes on x64, 4 on x86. c_size_t is the
# ctypes type that matches it exactly, and it is load-bearing: get this wrong
# and INPUT below comes out the wrong size.
_ULONG_PTR = ctypes.c_size_t

_INPUT_KEYBOARD = 1
_KEYEVENTF_KEYUP = 0x0002


class _KEYBDINPUT(ctypes.Structure):
    """One keyboard event: which key, and whether it went down or came up."""

    _fields_ = [
        ("wVk", _WORD),
        ("wScan", _WORD),
        ("dwFlags", _DWORD),
        ("time", _DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _MOUSEINPUT(ctypes.Structure):
    """Never sent. Present only to give the union below its true size.

    Teacher Note: trap #1, the one that cost the spike a day
    ========================================================
    INPUT is a union - one struct that can hold either a keyboard event or a
    mouse event - and a union is always as big as its largest member. The
    mouse member is 32 bytes; the keyboard member is only 24. Leave the mouse
    out and INPUT comes out 32 bytes instead of 40, every SendInput call fails
    with error 87 (ERROR_INVALID_PARAMETER), and *zero pixels change*.

    Which reads exactly like "this game ignores synthetic input." It does not.
    The struct was simply the wrong size, and nothing said so out loud.
    """

    _fields_ = [
        ("dx", _LONG),
        ("dy", _LONG),
        ("mouseData", _DWORD),
        ("dwFlags", _DWORD),
        ("time", _DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", _DWORD), ("union", _INPUT_UNION)]


_EXPECTED_INPUT_SIZE = 40  # x64, and v1 is x64 Windows only.

if ctypes.sizeof(_INPUT) != _EXPECTED_INPUT_SIZE:
    raise RuntimeError(
        f"INPUT is {ctypes.sizeof(_INPUT)} bytes, expected "
        f"{_EXPECTED_INPUT_SIZE}. SendInput would fail with error 87 and "
        "change nothing on screen, which looks identical to a game that "
        "ignores synthetic input. Checked here at import rather than in a "
        "test, because an import cannot be skipped."
    )


if sys.platform == "win32":
    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    # Declaring argument types is not decoration: a window handle is 64 bits,
    # and without argtypes ctypes would pass it as a 32-bit int and quietly
    # hand Windows a different window.
    _user32.SendInput.argtypes = (ctypes.c_uint, ctypes.POINTER(_INPUT), ctypes.c_int)
    _user32.SendInput.restype = ctypes.c_uint
    _user32.GetForegroundWindow.argtypes = ()
    _user32.GetForegroundWindow.restype = ctypes.c_void_p
    _user32.SetForegroundWindow.argtypes = (ctypes.c_void_p,)
    _user32.SetForegroundWindow.restype = ctypes.c_int
    _user32.GetWindowThreadProcessId.argtypes = (
        ctypes.c_void_p,
        ctypes.POINTER(_DWORD),
    )
    _user32.GetWindowThreadProcessId.restype = _DWORD
    _user32.AttachThreadInput.argtypes = (_DWORD, _DWORD, ctypes.c_int)
    _user32.AttachThreadInput.restype = ctypes.c_int
    _kernel32.GetCurrentThreadId.argtypes = ()
    _kernel32.GetCurrentThreadId.restype = _DWORD
else:
    # Not Windows. The module still has to import: NullInput is what CartPole
    # and GridWorld run with, and CI runs the suite on Linux.
    _user32 = _kernel32 = None


class WindowNotFocused(Exception):
    """The target window is not in front, so keystrokes would land elsewhere."""


class KeyboardInput(InputController):
    """Real key presses, delivered to one window by Windows itself.

    Drop-in for NullInput - same interface, same method names - which is what
    makes M5's control 2 possible: run a sequence with these hands, run the
    identical sequence with NullInput, and the difference is the proof that
    our keystrokes are what moved the board.

    Bound to a window handle, from Brick 1's finder:

        from src.gametrainer.screen import find_window
        hands = KeyboardInput(find_window("LibreMines"))
        hands.focus()
        hands.move_right()
        hands.flag()

    Failures here are loud on purpose. The base class prints and carries on;
    these hands raise. A keystroke that silently went nowhere is the most
    expensive bug in this milestone - it looks exactly like a game that cannot
    be driven, and the spike lost a day to it once already.
    """

    # A requested foreground change is not instant - Windows delivers it as a
    # message - so focus() waits for it to happen instead of assuming it did.
    _FOCUS_TIMEOUT = 0.5
    _FOCUS_POLL = 0.02

    def __init__(self, hwnd: int):
        if sys.platform != "win32":
            raise RuntimeError(
                "KeyboardInput needs Windows (SendInput). Off Windows, use "
                "NullInput - that is what CartPole and GridWorld run with."
            )
        super().__init__()
        self.hwnd = int(hwnd)

    # --- focus: who the keystrokes will actually reach ---

    def has_focus(self) -> bool:
        """Is our window the one Windows will deliver keystrokes to?"""
        return int(_user32.GetForegroundWindow() or 0) == self.hwnd

    def focus(self) -> None:
        """Bring the game to the front, and confirm that it came.

        Teacher Note: the foreground lock
        =================================
        Windows will not let a background program steal focus whenever it
        likes - otherwise every app would fight over your screen. So a plain
        SetForegroundWindow call from here is often ignored, and it reports
        success either way. The workaround is AttachThreadInput: for a moment
        we tell Windows that our thread and the game's thread share an input
        queue, which makes the request come from "inside" the game's own
        thread and be granted. Then we detach again - and because the call
        lies, we check the window really is in front before trusting it.
        """
        if self.has_focus():
            return

        our_thread = _kernel32.GetCurrentThreadId()
        game_thread = _user32.GetWindowThreadProcessId(ctypes.c_void_p(self.hwnd), None)
        attached = _user32.AttachThreadInput(our_thread, game_thread, True)
        try:
            _user32.SetForegroundWindow(ctypes.c_void_p(self.hwnd))
        finally:
            if attached:
                _user32.AttachThreadInput(our_thread, game_thread, False)

        deadline = time.monotonic() + self._FOCUS_TIMEOUT
        while not self.has_focus():
            if time.monotonic() > deadline:
                raise WindowNotFocused(
                    f"Window {self.hwnd} did not come to the foreground within "
                    f"{self._FOCUS_TIMEOUT}s. Windows refused the request (the "
                    "foreground lock), or the window is minimised. Nothing was "
                    "typed."
                )
            time.sleep(self._FOCUS_POLL)

    def _require_focus(self) -> None:
        if not self.has_focus():
            raise WindowNotFocused(
                f"Window {self.hwnd} is not in front, so this keystroke would "
                "have gone to whatever is. Call focus() first. Nothing was "
                "typed."
            )

    # --- the two primitives everything else is built from ---

    def tap_key(self, key_code: int, duration: float = 0.1):
        """Press and release one key in the game window.

        `duration` is accepted to keep the base class's signature and is
        ignored: both events go onto the queue in a single call, so there is
        no gap to hold open. LibreMines reacts to the key going down.
        """
        self._require_focus()
        self._send(self._key_event(key_code), self._key_event(key_code, up=True))

    def tap_chord(self, modifier_code: int, key_code: int):
        """Hold a modifier, tap a key, let go. Ctrl+R is M5's only chord.

        All four events go in one SendInput call, so nothing - not a real
        keypress, not another program - can interleave between them and leave
        Ctrl stuck down.
        """
        self._require_focus()
        self._send(
            self._key_event(modifier_code),
            self._key_event(key_code),
            self._key_event(key_code, up=True),
            self._key_event(modifier_code, up=True),
        )

    @staticmethod
    def _key_event(key_code: int, up: bool = False) -> _INPUT:
        """Build one keyboard event, ready to hand to Windows."""
        event = _INPUT(type=_INPUT_KEYBOARD)
        event.union.ki = _KEYBDINPUT(
            wVk=key_code,
            dwFlags=_KEYEVENTF_KEYUP if up else 0,
        )
        return event

    @staticmethod
    def _send(*events: _INPUT) -> None:
        """Put these events on the queue, and insist that all of them landed."""
        batch = (_INPUT * len(events))(*events)
        sent = _user32.SendInput(len(events), batch, ctypes.sizeof(_INPUT))
        if sent != len(events):
            raise OSError(
                f"SendInput delivered {sent} of {len(events)} events (Windows "
                f"error {ctypes.get_last_error()}). Error 87 means the INPUT "
                "struct is the wrong size; error 5 usually means a more "
                "privileged window has focus."
            )

    # --- two things these hands refuse to do ---

    def escape(self):
        """Refused. Escape is the one key that must never reach LibreMines."""
        raise RuntimeError(
            "Escape must never be sent to LibreMines: it exits keyboard mode, "
            "after which W/A/S/D/O/P do nothing at all. The loop would carry "
            "on driving a game that had stopped listening, and every reading "
            "would still look plausible. See docs/m5/M5_ToDo.md, 'Verified "
            "controls'."
        )

    def _no_mouse(self):
        raise NotImplementedError(
            "KeyboardInput sends keys only. M5 uses the mouse exactly once - "
            "to click a difficulty and start the first game - and that click "
            "belongs to the env, not to the hands (docs/m5/M5_ToDo.md, "
            "'Scope discipline')."
        )

    def mouse_move(self, dx: int, dy: int): self._no_mouse()
    def mouse_click(self): self._no_mouse()
    def mouse_right_click(self): self._no_mouse()
