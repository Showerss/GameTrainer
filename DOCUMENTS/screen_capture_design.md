# Screen Capture Design Document

> **Teacher Note:** This document explains how GameTrainer "sees" the game.
> Just like your eyes capture light and send signals to your brain, our program
> captures pixels and sends them to the decision engine. The method we choose
> dramatically affects performance and reliability.

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [Capture Methods Compared](#2-capture-methods-compared)
3. [Our Recommendation](#3-our-recommendation)
4. [Implementation Details](#4-implementation-details)
5. [Optimizing for AI Transmission](#5-optimizing-for-ai-transmission)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. The Problem

### 1.1 What We Need

GameTrainer needs to continuously see what's happening on screen to:
- Detect UI elements (health bars, stamina bars, inventory)
- Recognize game states (menu, gameplay, cutscene)
- Identify entities (enemies, items, NPCs)
- Verify that actions had the expected effect

### 1.2 Key Questions

```
┌─────────────────────────────────────────────────────────────────┐
│                  QUESTIONS TO ANSWER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. How fast do we need to capture?                            │
│     → 10 FPS is plenty for our rule-based system               │
│                                                                 │
│  2. Full screen or specific window?                            │
│     → Specific game window is ideal                            │
│                                                                 │
│  3. What if the window is partially hidden?                    │
│     → Some methods handle this, others don't                   │
│                                                                 │
│  4. How much CPU/GPU can we use?                               │
│     → As little as possible (game needs resources too!)        │
│                                                                 │
│  5. What format does our code need?                            │
│     → NumPy array for OpenCV processing                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 The "Screenshotting" Misconception

When people say "screenshot," they often think of pressing Print Screen - a slow,
blocking operation that freezes the screen momentarily. **That's not what we do.**

Modern screen capture is more like "tapping into the video feed" - we access
frames that already exist in GPU memory, often without any copying at all.

```
SLOW (Traditional Screenshot):
    Request → Wait → CPU copies every pixel → Done
    Time: 50-200ms, CPU: HIGH

FAST (Modern Capture):
    Request → GPU shares existing frame → Done
    Time: 5-20ms, CPU: LOW
```

---

## 2. Capture Methods Compared

### 2.1 Overview Table

| Method | Speed | CPU Use | Window Capture | Hidden Windows | Complexity |
|--------|-------|---------|----------------|----------------|------------|
| GDI BitBlt | Slow | High | Yes (manual crop) | ❌ No | Low |
| MSS (Python) | Medium | Medium | Yes (manual crop) | ❌ No | Very Low |
| Desktop Duplication (DXGI) | Fast | Low | No (full monitor) | ❌ No | High |
| Windows Graphics Capture | Fast | Low | Yes | ✅ Yes | Medium |

### 2.2 GDI BitBlt (The Old Way)

```
┌─────────────────────────────────────────────────────────────────┐
│  GDI BitBlt                                                     │
│  Performance: ~10-15 FPS | CPU: HIGH | Since: Windows 3.1       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  How it works:                                                  │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │  Screen │───►│   CPU   │───►│  System │───►│  Your   │      │
│  │  (GPU)  │copy│ copies  │copy│  Memory │copy│  Code   │      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
│                                                                 │
│  Problems:                                                      │
│  • Every pixel copied through CPU (millions of operations)      │
│  • GPU sits idle while CPU does all the work                   │
│  • Blocks the calling thread during copy                       │
│  • Can't capture hardware-accelerated content reliably         │
│                                                                 │
│  When to use: Never for real-time. Only for one-off captures.  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Verdict:** ❌ Don't use for GameTrainer

---

### 2.3 MSS Library (Python)

```
┌─────────────────────────────────────────────────────────────────┐
│  MSS (Multiple Screen Shots)                                    │
│  Performance: ~30-60 FPS | CPU: MEDIUM | Complexity: VERY LOW   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  What it is:                                                    │
│  A Python library that wraps the best available capture method  │
│  for your operating system. On Windows, it uses optimized       │
│  native calls under the hood.                                   │
│                                                                 │
│  How it works:                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  import mss                                              │   │
│  │                                                          │   │
│  │  with mss.mss() as sct:                                  │   │
│  │      # Define region: top-left corner, 800x600 pixels    │   │
│  │      region = {"top": 100, "left": 100,                  │   │
│  │                "width": 800, "height": 600}              │   │
│  │                                                          │   │
│  │      # Capture returns raw pixel data                    │   │
│  │      screenshot = sct.grab(region)                       │   │
│  │                                                          │   │
│  │      # Convert to numpy array for OpenCV                 │   │
│  │      frame = np.array(screenshot)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Pros:                                                          │
│  ✓ Dead simple API (3 lines of code)                           │
│  ✓ Cross-platform (Windows, Mac, Linux)                        │
│  ✓ No C++ required                                             │
│  ✓ Fast enough for 10 FPS easily                               │
│  ✓ Can capture specific regions                                │
│                                                                 │
│  Cons:                                                          │
│  ✗ Still copies through CPU                                    │
│  ✗ Can't capture hidden/minimized windows                      │
│  ✗ Not the absolute fastest option                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Verdict:** ✅ **Recommended for GameTrainer** (simplicity wins)

---

### 2.4 Desktop Duplication API (DXGI)

```
┌─────────────────────────────────────────────────────────────────┐
│  Desktop Duplication API (DXGI)                                 │
│  Performance: ~60 FPS (vsync) | CPU: LOW | Since: Windows 8     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  What it is:                                                    │
│  Microsoft's API for capturing the entire desktop efficiently.  │
│  This is what OBS, Discord, and streaming software use.         │
│                                                                 │
│  The Magic - Zero-Copy Access:                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  Traditional:                                            │   │
│  │  GPU ──copy──► CPU ──copy──► RAM ──copy──► Your Code    │   │
│  │                    (3 copies, slow)                      │   │
│  │                                                          │   │
│  │  DXGI:                                                   │   │
│  │  GPU ──share──► Your Code (on GPU) ──1 copy──► RAM      │   │
│  │                    (1 copy, only when needed)            │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Smart Feature:                                                 │
│  DXGI only returns a new frame when pixels actually changed.   │
│  If the game is paused, it uses zero resources.                │
│                                                                 │
│  Pros:                                                          │
│  ✓ Extremely efficient (shares GPU textures)                   │
│  ✓ Low CPU usage                                               │
│  ✓ Only updates when screen changes                            │
│                                                                 │
│  Cons:                                                          │
│  ✗ Captures ENTIRE monitor (must crop manually)                │
│  ✗ Must run on same GPU as display                             │
│  ✗ Complex C++ API (harder to use from Python)                 │
│  ✗ Windows 8+ only                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Verdict:** ⚠️ Consider for optimization later (overkill for 10 FPS)

---

### 2.5 Windows Graphics Capture API

```
┌─────────────────────────────────────────────────────────────────┐
│  Windows Graphics Capture (WGC)                                 │
│  Performance: ~60+ FPS | CPU: LOW | Since: Windows 10 1803      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  What it is:                                                    │
│  Microsoft's newest capture API. This is what Xbox Game Bar    │
│  uses. Designed specifically for capturing games and windows.   │
│                                                                 │
│  Key Advantage - Window Capture:                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  DXGI: "Here's everything on monitor 1"                  │   │
│  │        (You figure out where the game window is)         │   │
│  │                                                          │   │
│  │  WGC:  "Here's just the Stardew Valley window"           │   │
│  │        (Automatically tracks window position/size)       │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Special Feature - Hidden Window Capture:                       │
│  WGC can capture a window even if it's partially behind        │
│  other windows! (DXGI and MSS cannot do this)                  │
│                                                                 │
│  Pros:                                                          │
│  ✓ Efficient like DXGI                                         │
│  ✓ Can capture specific windows                                │
│  ✓ Works with partially hidden windows                         │
│  ✓ Cleaner API than DXGI                                       │
│                                                                 │
│  Cons:                                                          │
│  ✗ Windows 10 1803+ only                                       │
│  ✗ Some fullscreen exclusive games don't work                  │
│  ✗ Still requires C++ or special Python bindings               │
│                                                                 │
│  Python Library: windows-capture (Rust/Python)                  │
│  https://github.com/NiiightmareXD/windows-capture               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Verdict:** ⚠️ Best option IF you need hidden window capture

---

## 3. Our Recommendation

### 3.1 Decision Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHICH METHOD TO USE?                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  START HERE                                                     │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────────────────────────────┐                   │
│  │ Is 30+ FPS and simple code more         │                   │
│  │ important than maximum efficiency?       │                   │
│  └─────────────────┬───────────────────────┘                   │
│                    │                                            │
│          YES ◄─────┴─────► NO                                   │
│           │                 │                                   │
│           ▼                 ▼                                   │
│     ┌─────────┐    ┌─────────────────────────────┐             │
│     │   MSS   │    │ Do you need to capture      │             │
│     │  ✅ USE │    │ hidden/background windows?   │             │
│     └─────────┘    └─────────────┬───────────────┘             │
│                                  │                              │
│                        YES ◄─────┴─────► NO                     │
│                         │                 │                     │
│                         ▼                 ▼                     │
│                    ┌─────────┐      ┌─────────┐                │
│                    │   WGC   │      │  DXGI   │                │
│                    │  ✅ USE │      │  ✅ USE │                │
│                    └─────────┘      └─────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 GameTrainer Strategy

**Phase 1: Start with MSS**

We're building a 10 FPS system. MSS can easily do 30-60 FPS. It's overkill
for our needs, and the simplicity lets us focus on the AI/rules logic first.

```python
# Teacher Note: This is all we need to start. 5 lines of code.
# Don't optimize until you have a working system!

import mss
import numpy as np

def capture_game_region(region: dict) -> np.ndarray:
    """
    Capture a region of the screen.

    Args:
        region: Dict with keys: top, left, width, height

    Returns:
        NumPy array of shape (height, width, 4) in BGRA format
    """
    with mss.mss() as sct:
        screenshot = sct.grab(region)
        return np.array(screenshot)
```

**Phase 2: Optimize IF needed**

If we find MSS is too slow (unlikely), we can swap in DXGI or WGC later.
The rest of our code won't need to change - it just receives numpy arrays.

---

## 4. Implementation Details

### 4.1 ScreenCapture Class

```python
"""
Screen capture module for GameTrainer.

Teacher Note: This class abstracts away HOW we capture the screen.
The rest of our code just calls capture() and gets pixels back.
If we switch from MSS to DXGI later, only this file changes.
"""

import mss
import numpy as np
from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class CaptureRegion:
    """
    Defines a rectangular region of the screen to capture.

    Teacher Note: We use a dataclass here for clarity. It's just
    a simple container for four numbers, but giving it a name
    makes the code self-documenting.
    """
    top: int      # Y coordinate of top-left corner
    left: int     # X coordinate of top-left corner
    width: int    # Width in pixels
    height: int   # Height in pixels

    def to_mss_dict(self) -> dict:
        """Convert to the format MSS expects."""
        return {
            "top": self.top,
            "left": self.left,
            "width": self.width,
            "height": self.height
        }


class ScreenCapture:
    """
    Handles screen capture for GameTrainer.

    Usage:
        capture = ScreenCapture()
        capture.set_region(CaptureRegion(top=0, left=0, width=1920, height=1080))

        while running:
            frame = capture.capture()
            # process frame...

    Teacher Note: We keep the MSS context open between captures for
    efficiency. Creating a new context for every frame would add
    overhead.
    """

    def __init__(self):
        self._sct = mss.mss()
        self._region: Optional[CaptureRegion] = None
        self._last_capture_time: float = 0
        self._frame_count: int = 0

    def set_region(self, region: CaptureRegion) -> None:
        """
        Set the screen region to capture.

        Args:
            region: The rectangular area to capture

        Teacher Note: Call this once during setup, not every frame.
        """
        self._region = region

    def set_region_from_window(self, window_title: str) -> bool:
        """
        Automatically set the capture region to match a window.

        Args:
            window_title: The title of the window to capture

        Returns:
            True if window found, False otherwise

        Teacher Note: This uses Windows API to find the window
        position. It's a convenience method - you can also set
        the region manually if you know the coordinates.
        """
        # Import here to avoid Windows dependency at module level
        try:
            import win32gui
        except ImportError:
            print("pywin32 required for window detection. Install with: pip install pywin32")
            return False

        def callback(hwnd, results):
            if window_title.lower() in win32gui.GetWindowText(hwnd).lower():
                results.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)

        if not windows:
            return False

        hwnd = windows[0]
        rect = win32gui.GetWindowRect(hwnd)

        self._region = CaptureRegion(
            top=rect[1],
            left=rect[0],
            width=rect[2] - rect[0],
            height=rect[3] - rect[1]
        )
        return True

    def capture(self) -> np.ndarray:
        """
        Capture the current frame.

        Returns:
            NumPy array of shape (height, width, 4) in BGRA format

        Raises:
            RuntimeError: If no region has been set

        Teacher Note: The returned array is in BGRA format (Blue, Green,
        Red, Alpha). Most OpenCV functions expect BGR, so the alpha
        channel is usually ignored or stripped.
        """
        if self._region is None:
            raise RuntimeError(
                "No capture region set. Call set_region() first."
            )

        screenshot = self._sct.grab(self._region.to_mss_dict())
        frame = np.array(screenshot)

        # Track timing for debugging
        current_time = time.time()
        self._last_capture_time = current_time
        self._frame_count += 1

        return frame

    def capture_bgr(self) -> np.ndarray:
        """
        Capture and convert to BGR format (what OpenCV prefers).

        Returns:
            NumPy array of shape (height, width, 3) in BGR format

        Teacher Note: OpenCV functions like cv2.cvtColor expect BGR,
        not BGRA. This convenience method does the conversion for you.
        """
        frame = self.capture()
        # Drop the alpha channel: BGRA -> BGR
        return frame[:, :, :3]

    def get_fps_estimate(self) -> float:
        """
        Estimate current capture FPS based on recent timing.

        Teacher Note: Useful for debugging. If this drops below your
        target FPS, you might need a faster capture method.
        """
        # Simple implementation - could be improved with rolling average
        return self._frame_count / max(time.time() - self._last_capture_time, 0.001)

    def close(self) -> None:
        """
        Release resources.

        Teacher Note: Always call this when done, or use the class
        as a context manager (with statement).
        """
        self._sct.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
```

### 4.2 Usage Example

```python
"""
Example: Capture game window at 10 FPS.

Teacher Note: This demonstrates the typical capture loop pattern.
In practice, this loop would be part of the Trainer class.
"""

import time
from screen_capture import ScreenCapture, CaptureRegion

def main():
    # Target: 10 frames per second
    target_fps = 10
    frame_time = 1.0 / target_fps  # 0.1 seconds = 100ms

    capture = ScreenCapture()

    # Option 1: Set region manually
    # capture.set_region(CaptureRegion(top=0, left=0, width=1280, height=720))

    # Option 2: Find window automatically
    if not capture.set_region_from_window("Stardew Valley"):
        print("Game window not found!")
        return

    print("Starting capture loop (Ctrl+C to stop)...")

    try:
        while True:
            loop_start = time.time()

            # 1. Capture frame
            frame = capture.capture_bgr()

            # 2. Process frame (placeholder)
            # game_state = extract_state(frame)
            # action = decide(game_state)
            # execute(action)

            print(f"Captured frame: {frame.shape}")

            # 3. Sleep to maintain target FPS
            elapsed = time.time() - loop_start
            sleep_time = frame_time - elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                print(f"Warning: Frame took {elapsed*1000:.1f}ms (budget: {frame_time*1000:.1f}ms)")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        capture.close()

if __name__ == "__main__":
    main()
```

---

## 5. Optimizing for AI Transmission

### 5.1 The Problem

When we send frames to an AI (during knowledge compilation or exception analysis),
we need to consider:

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAW FRAME SIZE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1920 x 1080 resolution                                         │
│  × 4 bytes per pixel (BGRA)                                     │
│  = 8,294,400 bytes                                              │
│  = ~8 MB per frame                                              │
│                                                                 │
│  Problems:                                                      │
│  • Slow to upload (especially on slow connections)              │
│  • Expensive (AI APIs often charge by data size)                │
│  • Unnecessary (AI doesn't need every pixel)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Optimization Techniques

```python
"""
Image optimization utilities for AI transmission.

Teacher Note: These functions reduce image size before sending to
AI APIs. A 10x reduction in size means 10x faster uploads and
potentially lower costs.
"""

import cv2
import numpy as np
from typing import Tuple


def resize_for_ai(
    frame: np.ndarray,
    max_dimension: int = 1024
) -> np.ndarray:
    """
    Resize frame to reasonable size for AI processing.

    Args:
        frame: Original frame (any size)
        max_dimension: Maximum width or height

    Returns:
        Resized frame

    Teacher Note: Most vision AI models work fine with 1024px or even
    smaller images. Sending 4K screenshots is wasteful.

    Example:
        1920x1080 with max_dimension=1024:
        → Resized to 1024x576 (maintains aspect ratio)
        → ~4x fewer pixels, ~4x less data
    """
    height, width = frame.shape[:2]

    # Check if resize is needed
    if width <= max_dimension and height <= max_dimension:
        return frame

    # Calculate new dimensions maintaining aspect ratio
    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))

    return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)


def compress_to_jpeg(
    frame: np.ndarray,
    quality: int = 80
) -> bytes:
    """
    Compress frame to JPEG format.

    Args:
        frame: BGR or grayscale image
        quality: JPEG quality (0-100, higher = better quality, larger file)

    Returns:
        JPEG-encoded bytes

    Teacher Note: JPEG compression is lossy but achieves 10-50x
    compression ratios. Quality 80 is usually indistinguishable
    from the original for AI purposes.

    Example:
        8 MB raw frame → ~150 KB JPEG (50x smaller!)
    """
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, jpeg_bytes = cv2.imencode('.jpg', frame, encode_params)
    return jpeg_bytes.tobytes()


def compress_to_png(frame: np.ndarray) -> bytes:
    """
    Compress frame to PNG format (lossless).

    Args:
        frame: BGR or grayscale image

    Returns:
        PNG-encoded bytes

    Teacher Note: Use PNG when you need perfect quality (e.g., for
    template images). It's lossless but larger than JPEG.
    """
    _, png_bytes = cv2.imencode('.png', frame)
    return png_bytes.tobytes()


def prepare_for_ai(
    frame: np.ndarray,
    max_dimension: int = 1024,
    jpeg_quality: int = 80
) -> Tuple[bytes, dict]:
    """
    Prepare a frame for AI transmission with full optimization.

    Args:
        frame: Original captured frame
        max_dimension: Maximum dimension after resize
        jpeg_quality: JPEG compression quality

    Returns:
        Tuple of (jpeg_bytes, metadata_dict)

    Teacher Note: This is the main function to use when sending
    screenshots to AI APIs. It handles resize + compression in
    one call and returns metadata about what was done.
    """
    original_shape = frame.shape

    # Step 1: Resize
    resized = resize_for_ai(frame, max_dimension)

    # Step 2: Compress
    jpeg_bytes = compress_to_jpeg(resized, jpeg_quality)

    metadata = {
        "original_size": original_shape[:2],
        "resized_to": resized.shape[:2],
        "compressed_bytes": len(jpeg_bytes),
        "compression_ratio": (frame.nbytes / len(jpeg_bytes))
    }

    return jpeg_bytes, metadata


# Example usage
if __name__ == "__main__":
    # Simulate a 1920x1080 frame
    fake_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

    jpeg_data, meta = prepare_for_ai(fake_frame)

    print(f"Original: {meta['original_size']}")
    print(f"Resized:  {meta['resized_to']}")
    print(f"Size:     {meta['compressed_bytes'] / 1024:.1f} KB")
    print(f"Ratio:    {meta['compression_ratio']:.1f}x smaller")
```

### 5.3 Size Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIZE COMPARISON                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Original 1920x1080 BGRA:           8,294,400 bytes  (8.0 MB)  │
│                                                                 │
│  After resize to 1024x576:          2,359,296 bytes  (2.3 MB)  │
│                                                                 │
│  After JPEG compression (q=80):        ~150,000 bytes (150 KB) │
│                                                                 │
│  Total reduction: ~55x smaller!                                │
│                                                                 │
│  Upload time (10 Mbps connection):                             │
│  • Original: 6.6 seconds                                       │
│  • Optimized: 0.12 seconds                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Troubleshooting

### 6.1 Common Issues

```
┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: Black or empty screenshots                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Possible causes:                                               │
│  1. Game running in fullscreen exclusive mode                  │
│     → Solution: Switch game to "Borderless Windowed"           │
│                                                                 │
│  2. Hardware acceleration / protected content                  │
│     → Solution: Try different capture method (WGC)             │
│                                                                 │
│  3. Wrong region coordinates                                   │
│     → Solution: Verify window position with set_region_from_   │
│       window() or check manually                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: Capture is too slow                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Check these first:                                            │
│  1. Are you capturing more pixels than needed?                 │
│     → Solution: Reduce region size                             │
│                                                                 │
│  2. Is your processing code slow, not capture?                 │
│     → Solution: Profile your code to find the real bottleneck  │
│                                                                 │
│  3. Do you actually need faster capture?                       │
│     → At 10 FPS, MSS should never be the bottleneck            │
│                                                                 │
│  If MSS is genuinely too slow:                                 │
│  → Consider DXGI (d3dshot library) or WGC (windows-capture)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROBLEM: Colors look wrong                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Cause: Format mismatch (BGRA vs RGB vs BGR)                   │
│                                                                 │
│  MSS returns: BGRA (Blue, Green, Red, Alpha)                   │
│  OpenCV expects: BGR (Blue, Green, Red)                        │
│  PIL expects: RGB (Red, Green, Blue)                           │
│  AI APIs usually expect: RGB                                   │
│                                                                 │
│  Solutions:                                                     │
│  • For OpenCV: frame[:, :, :3]  (drop alpha)                   │
│  • For RGB: cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Testing Your Capture

```python
"""
Quick test script to verify screen capture is working.

Run this to confirm everything is set up correctly before
integrating with the rest of GameTrainer.
"""

import mss
import numpy as np
import cv2
import time


def test_capture():
    print("Testing screen capture...")
    print("-" * 40)

    with mss.mss() as sct:
        # Test 1: List available monitors
        print(f"Found {len(sct.monitors)} monitor(s):")
        for i, monitor in enumerate(sct.monitors):
            print(f"  {i}: {monitor}")

        # Test 2: Capture a small region
        region = {"top": 0, "left": 0, "width": 100, "height": 100}

        start = time.time()
        for _ in range(10):
            frame = np.array(sct.grab(region))
        elapsed = time.time() - start

        print(f"\nCapture test (100x100 region, 10 frames):")
        print(f"  Total time: {elapsed*1000:.1f}ms")
        print(f"  Per frame: {elapsed*100:.1f}ms")
        print(f"  Potential FPS: {10/elapsed:.0f}")

        # Test 3: Full screen capture
        monitor = sct.monitors[1]  # Primary monitor

        start = time.time()
        frame = np.array(sct.grab(monitor))
        elapsed = time.time() - start

        print(f"\nFull screen capture ({monitor['width']}x{monitor['height']}):")
        print(f"  Time: {elapsed*1000:.1f}ms")
        print(f"  Frame shape: {frame.shape}")
        print(f"  Frame size: {frame.nbytes / 1024 / 1024:.1f} MB")

        # Test 4: Save a test image
        cv2.imwrite("test_capture.png", frame)
        print(f"\nSaved test image to: test_capture.png")

    print("-" * 40)
    print("All tests passed!")


if __name__ == "__main__":
    test_capture()
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    KEY TAKEAWAYS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Start with MSS                                             │
│     Simple, fast enough, cross-platform                        │
│                                                                 │
│  2. Capture only what you need                                 │
│     Smaller region = faster capture = less processing          │
│                                                                 │
│  3. Optimize images before AI transmission                     │
│     Resize + JPEG = 50x smaller, 50x faster uploads            │
│                                                                 │
│  4. Don't optimize prematurely                                 │
│     Get it working first, optimize if actually needed          │
│                                                                 │
│  5. The capture method can be swapped later                    │
│     Abstract it behind a clean interface                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## References

- [MSS Documentation](https://python-mss.readthedocs.io/)
- [Desktop Duplication API - Microsoft](https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/desktop-dup-api)
- [Windows Graphics Capture - Microsoft](https://learn.microsoft.com/en-us/windows/uwp/audio-video-camera/screen-capture)
- [windows-capture (Python/Rust)](https://github.com/NiiightmareXD/windows-capture)
- [OBS Forums - WGC vs DXGI Discussion](https://obsproject.com/forum/threads/windows-graphics-capture-vs-dxgi-desktop-duplication.149320/)

---

*Document version: 1.0*
*Last updated: December 2024*
