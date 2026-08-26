"""
screen.py - M5 Brick 1. The eyes for a window we do not own.

Two jobs, and nothing else: find a window by its title, and return the pixels
inside it as a numpy array. No game knowledge lives here - reading a
Minesweeper board out of those pixels is Brick 2's job.

Teacher Note: the DPI trap (the one that cost the spike a day)
=============================================================
Windows can lie about where a window is. On a high-DPI display it reports
"logical" coordinates - a made-up smaller coordinate system kept around so old
programs don't render at postage-stamp size - while a screen grabber like mss
works in real, physical pixels. Ask for a window at logical (1371, 223) and
grab physical (1371, 223) and you capture something else entirely. During the
pre-flight spike that meant capturing a browser window one monitor over, while
every pixel-difference number looked plausible and meant nothing.

The fix is one call, `SetProcessDpiAwarenessContext`, which tells Windows to
stop translating and give this process real pixels. It must happen **before
any window call**, so this module makes it at import time. It is not optional
and it is not a "nice to have": without it the captures are silently wrong,
which is the worst way for anything to be wrong.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

import mss
import numpy as np

# use_last_error=True is what makes ctypes.get_last_error() below report the
# real Windows error code instead of a stale one.
_user32 = ctypes.WinDLL("user32", use_last_error=True)

# DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2. A magic constant from the Windows
# headers; -4 means "give me real pixels, per monitor, and keep up if the user
# drags the window to a display with different scaling."
_DPI_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)

# Windows error code returned when DPI awareness is already set for this
# process. Setting it twice is a legitimate no-op, not a failure.
_ERROR_ACCESS_DENIED = 5


class WindowNotFound(Exception):
    """No visible window matched the title we were told to look for."""


def set_dpi_awareness() -> None:
    """Ask Windows for real pixel coordinates. Call before any window call.

    Raises if the call fails for any reason other than "already set", because
    a silent failure here produces captures that are aligned to nothing.
    """
    if _user32.SetProcessDpiAwarenessContext(_DPI_PER_MONITOR_AWARE_V2):
        return

    error = ctypes.get_last_error()
    if error != _ERROR_ACCESS_DENIED:
        raise OSError(
            f"SetProcessDpiAwarenessContext failed (error {error}). Window "
            "coordinates would be misaligned with screen pixels; refusing to "
            "capture. See the DPI trap in docs/m5/M5_ToDo.md."
        )


# Set it now, at import, before anything in this process can ask about a
# window. Import order is load-bearing here, which is exactly why it is not
# left to a caller to remember.
set_dpi_awareness()


_EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _window_title(hwnd: int) -> str:
    """Read one window's title bar text."""
    length = _user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    _user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def find_window(title_contains: str) -> int:
    """Return the handle of the first visible window whose title contains this.

    A substring match, not an exact one: a game is free to append its
    difficulty or a filename to its own title bar, and we would rather still
    find it. Raises WindowNotFound rather than returning a falsy handle, so a
    missing game fails here instead of somewhere further downstream.
    """
    matches: list[int] = []

    def visit(hwnd, _lparam):
        if _user32.IsWindowVisible(hwnd) and title_contains in _window_title(hwnd):
            matches.append(hwnd)
        return True

    _user32.EnumWindows(_EnumWindowsProc(visit), 0)

    if not matches:
        raise WindowNotFound(
            f"No visible window with {title_contains!r} in its title. "
            "Is the game running?"
        )
    return matches[0]


def window_rect(hwnd: int) -> dict[str, int]:
    """Where the window is on screen, as the box mss wants to grab."""
    rect = wintypes.RECT()
    if not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise OSError(f"GetWindowRect failed for window {hwnd}")

    box = {
        "left": rect.left,
        "top": rect.top,
        "width": rect.right - rect.left,
        "height": rect.bottom - rect.top,
    }
    if box["width"] <= 0 or box["height"] <= 0:
        raise OSError(
            f"Window {hwnd} has no area ({box['width']}x{box['height']}). "
            "It is probably minimised."
        )
    return box


class GameWindow:
    """A live view of one window's pixels.

    Teacher Note: the rect is re-read on every grab, not cached. The spike
    found window geometry is not stable - LibreMines reopened on a different
    monitor at a different size, and `MoveWindow` reported success while the
    window sat somewhere else. Re-reading costs almost nothing and removes a
    whole class of "the numbers looked fine but the capture was stale" bug.
    """

    def __init__(self, title_contains: str = "LibreMines"):
        self.title_contains = title_contains
        self.hwnd = find_window(title_contains)
        self._sct = mss.mss()

    @property
    def rect(self) -> dict[str, int]:
        """Current position and size of the window, in real screen pixels."""
        return window_rect(self.hwnd)

    def grab(self) -> np.ndarray:
        """Capture the window right now.

        Returns a (height, width, 3) uint8 array in BGR order - the order
        OpenCV expects, since Brick 2 reads these tiles with cv2.
        """
        shot = self._sct.grab(self.rect)
        return np.array(shot)[:, :, :3]

    def close(self) -> None:
        self._sct.close()

    def __enter__(self) -> "GameWindow":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
