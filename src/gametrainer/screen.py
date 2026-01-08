"""
ScreenCapture - The "Eyes" of GameTrainer

Teacher Note: This module handles grabbing screenshots from the screen.
We use the 'mss' library because it's fast and cross-platform.

How screen capture works:
    1. We identify a region of the screen to capture (usually a game window)
    2. We grab the pixels from that region as fast as possible
    3. We convert them to a format OpenCV can work with (BGR numpy array)

Why mss instead of PIL or pyautogui?
    - mss is significantly faster (can do 30+ FPS easily)
    - It captures directly from the screen buffer
    - Lower latency = more responsive bot

The capture region can be:
    - Full screen (monitor)
    - A specific window (by title)
    - A custom rectangle (x, y, width, height)
"""

import numpy as np
from typing import Optional, Dict, Tuple
import mss
import mss.tools

# Teacher Note: We try to import win32gui for window detection on Windows.
# This is optional - if it's not available, we just can't auto-find windows.
try:
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class ScreenCapture:
    """
    Captures screenshots from a specified screen region.

    Teacher Note: This class follows a simple lifecycle:
        1. Create instance
        2. Set the capture region (full screen, window, or custom)
        3. Call grab() repeatedly to get frames

    Example:
        capture = ScreenCapture()
        capture.set_region_fullscreen()

        while running:
            frame = capture.grab()
            # frame is a numpy array in BGR format (what OpenCV expects)
            process(frame)
    """

    def __init__(self):
        """
        Initialize the screen capture.

        Teacher Note: We create the mss instance here. mss uses a context
        manager pattern, but we keep it alive for the lifetime of this object
        to avoid the overhead of recreating it every frame.
        """
        # The mss screenshot object - our connection to the screen
        self._sct = mss.mss()

        # The region we're capturing: {"left": x, "top": y, "width": w, "height": h}
        # None means "not set yet"
        self._region: Optional[Dict[str, int]] = None

        # Cache the last frame for debugging/display purposes
        self._last_frame: Optional[np.ndarray] = None

        # Statistics
        self._capture_count = 0

    def set_region_fullscreen(self, monitor_index: int = 1) -> bool:
        """
        Set capture region to a full monitor.

        Args:
            monitor_index: Which monitor to capture (1 = primary, 2 = secondary, etc.)
                          Note: mss uses 1-based indexing, where 0 means "all monitors"

        Returns:
            True if successful, False otherwise

        Teacher Note: mss.monitors is a list where:
            - monitors[0] = bounding box of ALL monitors combined
            - monitors[1] = primary monitor
            - monitors[2] = secondary monitor (if exists)
            - etc.
        """
        monitors = self._sct.monitors

        if monitor_index < 0 or monitor_index >= len(monitors):
            print(f"Monitor {monitor_index} not found. Available: 0-{len(monitors)-1}")
            return False

        monitor = monitors[monitor_index]
        self._region = {
            "left": monitor["left"],
            "top": monitor["top"],
            "width": monitor["width"],
            "height": monitor["height"]
        }

        print(f"Capture region set to monitor {monitor_index}: {self._region}")
        return True

    def set_region_custom(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Set capture region to a custom rectangle.

        Args:
            x: Left edge of the region (pixels from left of screen)
            y: Top edge of the region (pixels from top of screen)
            width: Width of the region in pixels
            height: Height of the region in pixels

        Returns:
            True if successful, False otherwise

        Teacher Note: This is useful when you know exactly where the game
        window will be, or for capturing a specific UI element.
        """
        if width <= 0 or height <= 0:
            print(f"Invalid dimensions: {width}x{height}")
            return False

        self._region = {
            "left": x,
            "top": y,
            "width": width,
            "height": height
        }

        print(f"Capture region set to custom rect: {self._region}")
        return True

    def set_region_from_window(self, window_title: str, retry_count: int = 5) -> bool:
        """
        Set capture region to match a window by its title.

        Args:
            window_title: The title of the window to find (partial match)
            retry_count: How many times to retry if window is not found or too small

        Returns:
            True if a valid game window was found, False otherwise

        Teacher Note: We added a MIN_AREA check. If we find a window named
        "Stardew Valley" but it's tiny (like 160x28), we ignore it and retry.
        This gives the user time to open the game and ensures we don't
        accidentally capture a background process or tooltip.
        """
        if not HAS_WIN32:
            print("win32gui not available - can't find windows by title")
            return False

        # Minimum area for a window to be considered "The Game"
        # 800x600 = 480,000 pixels. Anything smaller is likely a tooltip.
        MIN_AREA = 800 * 600
        
        import time

        for attempt in range(retry_count):
            # Find the largest window
            hwnd = self._find_window_by_title(window_title)
            
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                x, y, right, bottom = rect
                width = right - x
                height = bottom - y
                area = width * height

                if area >= MIN_AREA:
                    self._region = {
                        "left": x,
                        "top": y,
                        "width": width,
                        "height": height
                    }
                    actual_title = win32gui.GetWindowText(hwnd)
                    print(f"SUCCESS: Captured '{actual_title}' ({width}x{height})")
                    return True
                else:
                    print(f"Attempt {attempt+1}: Found window, but too small ({width}x{height}). Ignoring...")
            else:
                print(f"Attempt {attempt+1}: Window '{window_title}' not found.")
            
            if attempt < retry_count - 1:
                time.sleep(1) # Wait a second before retrying

        print(f"FAILED: Could not find a valid game window for '{window_title}' after {retry_count} attempts.")
        return False

    def _find_window_by_title(self, partial_title: str) -> Optional[int]:
        """
        Find the largest window handle by partial title match.
        """
        candidates = []
        partial_lower = partial_title.lower()

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if partial_lower in title.lower():
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        width = rect[2] - rect[0]
                        height = rect[3] - rect[1]
                        area = width * height
                        if area > 0:
                            candidates.append((area, hwnd))
                    except Exception:
                        pass
            return True

        win32gui.EnumWindows(callback, None)

        if not candidates:
            return None

        # Sort by area descending and return the largest hwnd
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def grab(self) -> Optional[np.ndarray]:
        """
        Capture a screenshot of the current region.

        Returns:
            numpy array in BGR format (height, width, 3), or None if failed

        Teacher Note: This is the main method you'll call every frame.
        The returned array is in BGR format because that's what OpenCV uses.
        (Most image libraries use RGB, but OpenCV chose BGR for historical reasons)

        The conversion from mss format to numpy is fast because we're just
        reinterpreting the memory, not copying the pixels.
        """
        if self._region is None:
            print("Capture region not set! Call set_region_* first.")
            return None

        try:
            # Grab the screenshot - this is the fast part
            sct_img = self._sct.grab(self._region)

            # Convert to numpy array
            # Teacher Note: mss gives us BGRA (4 channels), but OpenCV wants BGR (3 channels)
            # We use numpy slicing to drop the alpha channel efficiently
            frame = np.array(sct_img)[:, :, :3]

            # Cache for debugging
            self._last_frame = frame
            self._capture_count += 1

            return frame

        except Exception as e:
            print(f"Screen capture failed: {e}")
            return None

    def grab_and_save(self, filename: str) -> bool:
        """
        Capture a screenshot and save it to a file.

        Args:
            filename: Path to save the image (e.g., "screenshot.png")

        Returns:
            True if successful, False otherwise

        Teacher Note: This is useful for debugging and for creating
        template images that you'll use for matching later.
        """
        frame = self.grab()
        if frame is None:
            return False

        try:
            # We need OpenCV to save, so import it here
            import cv2
            cv2.imwrite(filename, frame)
            print(f"Screenshot saved to: {filename}")
            return True
        except Exception as e:
            print(f"Failed to save screenshot: {e}")
            return False

    @property
    def region(self) -> Optional[Dict[str, int]]:
        """Get the current capture region."""
        return self._region

    @property
    def capture_count(self) -> int:
        """Get the number of frames captured so far."""
        return self._capture_count

    @property
    def last_frame(self) -> Optional[np.ndarray]:
        """Get the most recently captured frame (for debugging)."""
        return self._last_frame

    def list_windows(self) -> list:
        """
        List all visible windows on the system.

        Returns:
            List of (hwnd, title) tuples

        Teacher Note: This is a helper for finding the right window title
        to pass to set_region_from_window(). Run this to see what windows
        are available.
        """
        if not HAS_WIN32:
            print("win32gui not available")
            return []

        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:  # Skip windows with empty titles
                    windows.append((hwnd, title))
            return True

        win32gui.EnumWindows(callback, None)
        return windows
