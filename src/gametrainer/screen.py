"""
screen.py - M5 Brick 1. The eyes for a window we do not own.

Two jobs, and nothing else: find a window by its title, and return the pixels
inside it as a numpy array. No game knowledge lives here - reading a Minesweeper board out of those pixels is Brick 2's job.

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
import sys
from abc import ABC, abstractmethod
from ctypes import wintypes
from typing import TYPE_CHECKING

import mss
import numpy as np

if TYPE_CHECKING:
    # Only type checkers read this; at runtime the hint stays a string thanks to
    # `from __future__ import annotations`, so Python 3.9 (no typing.Self) never
    # actually imports it.
    from typing import Self

# use_last_error=True is what makes ctypes.get_last_error() below report the
# real Windows error code instead of a stale one.
if sys.platform == "win32":
    _user32 = ctypes.WinDLL("user32", use_last_error=True)

    # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2. A magic constant from the Windows
    # headers; -4 means "give me real pixels, per monitor, and keep up if the user
    # drags the window to a display with different scaling."
    _DPI_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
    _ERROR_ACCESS_DENIED = 5
    _EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    # Declaring argument types is not decoration: a window handle is 64 bits,
    # and without argtypes ctypes would pass it as a 32-bit int and quietly
    # hand Windows a different window. (input.py declares its calls the same way.)
    _user32.SetProcessDpiAwarenessContext.argtypes = (ctypes.c_void_p,)
    _user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL
    _user32.OpenDesktopW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _user32.OpenDesktopW.restype = wintypes.HANDLE
    _user32.SetThreadDesktop.argtypes = (wintypes.HANDLE,)
    _user32.SetThreadDesktop.restype = wintypes.BOOL
    _user32.EnumWindows.argtypes = (_EnumWindowsProc, wintypes.LPARAM)
    _user32.EnumWindows.restype = wintypes.BOOL
    _user32.IsWindowVisible.argtypes = (wintypes.HWND,)
    _user32.IsWindowVisible.restype = wintypes.BOOL
    _user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
    _user32.GetWindowTextLengthW.restype = ctypes.c_int
    _user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    _user32.GetWindowTextW.restype = ctypes.c_int

    # DWM ("Desktop Window Manager") draws every window on screen, so it is the
    # one that knows where a window's *visible* edges are - see
    # WindowsGameWindow.rect for why that matters.
    _dwmapi = ctypes.WinDLL("dwmapi")
    _DWMWA_EXTENDED_FRAME_BOUNDS = 9
    _dwmapi.DwmGetWindowAttribute.argtypes = (
        wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD
    )
    _dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long  # HRESULT: 0 means success
else:
    _user32 = None
    _DPI_PER_MONITOR_AWARE_V2 = None
    _ERROR_ACCESS_DENIED = 5
    _EnumWindowsProc = None

# macOS window finding/capture (added alongside M5 Brick 1/7 so check_hands.py
# can run on this machine too - see docs/m5/M5_Log.md, "macOS backend").
#
# Teacher Note: no DPI trap here, verified by capturing a real window and
# looking at the PNG (2026-09-07). CGWindowListCopyWindowInfo reports bounds
# in points, and mss.grab() on this machine returns an image sized to match
# those points exactly - no 2x Retina doubling to correct for, unlike win32's
# SetProcessDpiAwarenessContext dance above. Measured, not assumed: Windows and
# macOS turned out to disagree about whether "window coordinates" already mean
# "screen pixels", and only running a real capture told us which one this is.
if sys.platform == "darwin":
    import Quartz

    _CG_WINDOW_LIST_OPTIONS = (
        Quartz.kCGWindowListOptionOnScreenOnly
        | Quartz.kCGWindowListExcludeDesktopElements
    )


class WindowNotFound(Exception):
    """No visible window matched the title we were told to look for."""


def set_dpi_awareness() -> None:
    """Ask Windows for real pixel coordinates. Call before any window call.

    Raises if the call fails for any reason other than "already set", because
    a silent failure here produces captures that are aligned to nothing.
    """
    if sys.platform != "win32":
        return

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
if sys.platform == "win32":
    set_dpi_awareness()


class GameWindow(ABC):
    """A live view of one window's pixels.

    Abstract: finding the window and asking where it is are per-OS, so they
    live in WindowsGameWindow and MacGameWindow below, and
    game_window_for_this_os() picks the right one. Taking the screenshot is
    the same everywhere (mss grabs a box of screen), so it lives here, once.

    Teacher Note: the rect is re-read on every grab, not cached. The spike
    found window geometry is not stable - LibreMines reopened on a different
    monitor at a different size, and `MoveWindow` reported success while the
    window sat somewhere else. Re-reading costs almost nothing and removes a
    whole class of "the numbers looked fine but the capture was stale" bug.
    """

    def __init__(self, title_contains: str = "LibreMines"):
        self.title_contains = title_contains
        self.hwnd = self._find(title_contains)
        self._sct = mss.mss()

    @abstractmethod
    def _find(self, title_contains: str) -> int:
        """Return the id of the first visible matching window, or raise WindowNotFound.

        A substring match, not an exact one: a game is free to append its
        difficulty or a filename to its own title bar, and we would rather
        still find it. Raises rather than returning a falsy id, so a missing
        game fails here instead of somewhere further downstream.
        """

    @property
    @abstractmethod
    def rect(self) -> dict[str, int]:
        """Current position and size of the window, in real screen pixels,
        as the box mss wants to grab."""

    def grab(self) -> np.ndarray:
        """Capture the window right now.

        Returns a (height, width, 3) uint8 array in BGR order - the order
        OpenCV expects, since Brick 2 reads these tiles with cv2.
        """
        shot = self._sct.grab(self.rect)
        return np.array(shot)[:, :, :3]

    def close(self) -> None:
        self._sct.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


def _require_area(box: dict[str, int], which: str) -> dict[str, int]:
    """A window with no width or height cannot be captured - fail loudly."""
    if box["width"] <= 0 or box["height"] <= 0:
        raise OSError(
            f"{which} has no area ({box['width']}x{box['height']}). "
            "It is probably minimised."
        )
    return box


class WindowsGameWindow(GameWindow):
    """GameWindow for Windows: found by title bar text, measured by HWND."""

    def _find(self, title_contains: str) -> int:
        # Attach to the interactive Default desktop if currently running on a
        # subdesktop. Both calls report failure by returning 0, never by
        # raising, so there is nothing to catch: if they fail we simply stay
        # on the desktop we were on.
        h_desk = _user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_desk:
            _user32.SetThreadDesktop(h_desk)

        matches: list[int] = []

        def visit(hwnd, _lparam):
            if _user32.IsWindowVisible(hwnd) and title_contains in self._title(hwnd):
                matches.append(hwnd)
            return True

        _user32.EnumWindows(_EnumWindowsProc(visit), 0)

        if not matches:
            raise WindowNotFound(
                f"No visible window with {title_contains!r} in its title. "
                "Is the game running?"
            )
        return matches[0]

    @staticmethod
    def _title(hwnd: int) -> str:
        """Read one window's title bar text."""
        length = _user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return ""
        buffer = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value

    @property
    def rect(self) -> dict[str, int]:
        """The window's VISIBLE frame, as DWM draws it.

        Teacher Note: the invisible border (found 2026-10-17)
        =====================================================
        Since Windows 10, every window has an invisible ~8 px resize border on
        its sides, which GetWindowRect includes. On a normal window that just
        adds a thin strip of whatever is behind it. On a MAXIMISED window,
        Windows pushes that border off the edge of the monitor (rect starts at
        -8, -8), and off-screen pixels capture as pure black. The black strip
        then merged with a board touching the left edge, the dark block was no
        longer square, and find_board raised BoardNotFound on a perfectly good
        board. DWMWA_EXTENDED_FRAME_BOUNDS is the frame without that border -
        measured on the live game: exactly 8 px in from GetWindowRect on every
        side, and exactly the monitor's area when maximised.
        """
        rect = wintypes.RECT()
        result = _dwmapi.DwmGetWindowAttribute(
            self.hwnd, _DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(rect), ctypes.sizeof(rect)
        )
        if result != 0:
            raise OSError(
                f"DwmGetWindowAttribute failed for window {self.hwnd} "
                f"(HRESULT {result & 0xFFFFFFFF:#010x})"
            )
        return _require_area(
            {
                "left": rect.left,
                "top": rect.top,
                "width": rect.right - rect.left,
                "height": rect.bottom - rect.top,
            },
            f"Window {self.hwnd}",
        )


class MacGameWindow(GameWindow):
    """GameWindow for macOS: found by owning app name, measured by PID.

    The id stored in self.hwnd is that app's PID, not a window handle - there
    is no macOS equivalent of an HWND here. MacKeyboardInput takes the same
    PID, so callers never need to know the difference.
    """

    def _find(self, title_contains: str) -> int:
        """Teacher Note: matched by owning app, not title.
        CGWindowListCopyWindowInfo's kCGWindowName (the title bar text) comes
        back None for LibreMines even with every permission granted - measured,
        not assumed. kCGWindowOwnerName (the app's own name) is always there,
        so that is what gets matched instead.
        """
        for w in Quartz.CGWindowListCopyWindowInfo(_CG_WINDOW_LIST_OPTIONS, Quartz.kCGNullWindowID):
            owner = w.get("kCGWindowOwnerName") or ""
            if title_contains.lower() in owner.lower():
                return int(w["kCGWindowOwnerPID"])
        raise WindowNotFound(
            f"No visible window owned by an app matching {title_contains!r}. "
            "Is the game running?"
        )

    @property
    def rect(self) -> dict[str, int]:
        """Re-queries CGWindowListCopyWindowInfo each time rather than caching,
        for the same reason the rect is re-read on every grab: geometry can move."""
        for w in Quartz.CGWindowListCopyWindowInfo(_CG_WINDOW_LIST_OPTIONS, Quartz.kCGNullWindowID):
            if w.get("kCGWindowOwnerPID") == self.hwnd:
                bounds = w["kCGWindowBounds"]
                return _require_area(
                    {
                        "left": int(bounds["X"]),
                        "top": int(bounds["Y"]),
                        "width": int(bounds["Width"]),
                        "height": int(bounds["Height"]),
                    },
                    f"Window for pid {self.hwnd}",
                )
        raise OSError(f"No on-screen window found for pid {self.hwnd}.")


def game_window_for_this_os(title_contains: str = "LibreMines") -> GameWindow:
    """The window view for whichever OS we are running on.

    The one place that asks "which OS?" - everything after this just calls
    window.grab() and lets the subclass know how to find and measure it.
    """
    if sys.platform == "win32":
        return WindowsGameWindow(title_contains)
    if sys.platform == "darwin":
        return MacGameWindow(title_contains)
    raise RuntimeError(
        "GameWindow requires Windows or macOS. On Linux/CI, pass "
        "window=None or mock window to run headlessly."
    )
