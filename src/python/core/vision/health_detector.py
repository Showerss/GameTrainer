"""
HealthDetector - Detects health/energy bar fill percentage

Teacher Note: This is our first "vision" component. It takes a screenshot (numpy array)
and a region definition, then figures out how "full" a bar is.

How bar detection works:
    1. Crop the full screenshot to just the bar region
    2. Convert to HSV color space (easier to detect colors)
    3. Create a mask of "filled" pixels (pixels that match the bar color)
    4. Count filled pixels vs total pixels = fill percentage

Why HSV instead of RGB?
    RGB mixes color and brightness together, making it hard to say "find all green pixels"
    because light green and dark green have very different RGB values.

    HSV separates:
    - H (Hue): The actual color (0-180 in OpenCV, where 0=red, 60=green, 120=blue)
    - S (Saturation): How "colorful" it is (0=gray, 255=vivid)
    - V (Value): How bright it is (0=black, 255=bright)

    So "find all green pixels" becomes "find pixels where H is 35-85" regardless of brightness.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
import cv2


class HealthDetector:
    """
    Detects the fill percentage of a health or energy bar.

    Teacher Note: This class is intentionally simple. It does ONE thing:
    look at a region and tell you what percentage is filled.

    Usage:
        detector = HealthDetector(region_config)
        percentage = detector.detect(frame)
        print(f"Health: {percentage * 100:.0f}%")
    """

    def __init__(self, region: Dict[str, Any]):
        """
        Initialize with a region definition.

        Args:
            region: Dictionary with x, y, width, height, and optionally colors config
                   Example: {"x": 1260, "y": 595, "width": 25, "height": 175}

        Teacher Note: We store the region config and precompute some values
        to avoid doing the same math every frame.
        """
        self.x = region.get("x", 0)
        self.y = region.get("y", 0)
        self.width = region.get("width", 50)
        self.height = region.get("height", 100)
        self.fill_direction = region.get("fill_direction", "bottom_to_top")

        # Color detection thresholds (HSV)
        # Teacher Note: These defaults detect any "colorful" pixel (saturation > 50)
        # that isn't too dark (value > 50). This works for most colored bars.
        colors = region.get("colors", {})

        # If specific color ranges provided, use them; otherwise use permissive defaults
        if "filled" in colors:
            c = colors["filled"]
            self.h_min = c.get("h_min", 0)
            self.h_max = c.get("h_max", 180)
            self.s_min = c.get("s_min", 50)
            self.v_min = c.get("v_min", 50)
        else:
            # Default: detect any saturated, non-dark color
            self.h_min = 0
            self.h_max = 180
            self.s_min = 50
            self.v_min = 50

        # For debugging - last detection results
        self._last_crop: Optional[np.ndarray] = None
        self._last_mask: Optional[np.ndarray] = None
        self._last_percentage: float = 0.0

    def detect(self, frame: np.ndarray) -> float:
        """
        Detect the fill percentage of the bar in the given frame.

        Args:
            frame: Full screenshot as numpy array (BGR format from screen capture)

        Returns:
            Float from 0.0 (empty) to 1.0 (full)

        Teacher Note: This is the main method. Call it every frame with the
        latest screenshot to get the current bar fill level.
        """
        # Step 1: Crop to just the bar region
        # Teacher Note: numpy array slicing is [y:y+h, x:x+w] (row, col order)
        crop = frame[self.y:self.y + self.height, self.x:self.x + self.width]

        # Sanity check - make sure we got valid data
        if crop.size == 0:
            return 0.0

        # Step 2: Convert BGR to HSV
        # Teacher Note: OpenCV uses BGR by default, but HSV is better for color detection
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        # Step 3: Create a mask of "filled" pixels
        # Teacher Note: inRange creates a binary mask where white = pixel matches,
        # black = pixel doesn't match
        lower = np.array([self.h_min, self.s_min, self.v_min])
        upper = np.array([self.h_max, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)

        # Step 4: Calculate fill percentage
        # Teacher Note: For a bar that fills bottom-to-top, we need to find
        # where the filled portion ends. We do this by looking at each row
        # and checking if it has any filled pixels.
        percentage = self._calculate_fill_percentage(mask)

        # Store for debugging
        self._last_crop = crop
        self._last_mask = mask
        self._last_percentage = percentage

        return percentage

    def _calculate_fill_percentage(self, mask: np.ndarray) -> float:
        """
        Calculate what percentage of the bar is filled.

        Args:
            mask: Binary mask where 255 = filled pixel, 0 = empty pixel

        Returns:
            Float from 0.0 to 1.0

        Teacher Note: There are two approaches here:
        1. Simple: Count all white pixels / total pixels
        2. Directional: Find where the bar "stops" based on fill direction

        We use approach 2 because bars often have gaps or decorations.
        """
        if mask.size == 0:
            return 0.0

        height, width = mask.shape

        if self.fill_direction == "bottom_to_top":
            # Scan from bottom to top, find the highest row with filled pixels
            # Teacher Note: We check each row from bottom. The first row (from top)
            # that has filled pixels tells us how "full" the bar is.

            # Count filled pixels in each row
            row_sums = np.sum(mask, axis=1)  # Sum across columns for each row

            # Find rows that have "enough" filled pixels (at least 30% of width)
            threshold = width * 255 * 0.3  # 30% of max possible sum
            filled_rows = row_sums > threshold

            if not np.any(filled_rows):
                return 0.0

            # Find the topmost filled row
            topmost_filled = np.argmax(filled_rows)

            # Calculate percentage: higher topmost = more filled
            # If topmost_filled is 0, bar is 100% full
            # If topmost_filled is height-1, bar is nearly empty
            percentage = 1.0 - (topmost_filled / height)

            return percentage

        elif self.fill_direction == "left_to_right":
            # Similar logic but scan columns instead of rows
            col_sums = np.sum(mask, axis=0)
            threshold = height * 255 * 0.3
            filled_cols = col_sums > threshold

            if not np.any(filled_cols):
                return 0.0

            # Find rightmost filled column
            rightmost_filled = len(filled_cols) - 1 - np.argmax(filled_cols[::-1])
            percentage = (rightmost_filled + 1) / width

            return percentage

        else:
            # Fallback: simple pixel count ratio
            filled_pixels = np.sum(mask > 0)
            total_pixels = mask.size
            return filled_pixels / total_pixels

    def detect_with_debug(self, frame: np.ndarray) -> Tuple[float, Dict[str, Any]]:
        """
        Detect fill percentage and return debug information.

        Args:
            frame: Full screenshot

        Returns:
            Tuple of (percentage, debug_dict)
            debug_dict contains: crop, mask, region info

        Teacher Note: Use this when setting up a new game to verify the
        detection is working correctly. The debug info can be displayed
        in a debug window.
        """
        percentage = self.detect(frame)

        debug_info = {
            "percentage": percentage,
            "region": {"x": self.x, "y": self.y, "w": self.width, "h": self.height},
            "crop": self._last_crop,
            "mask": self._last_mask,
            "fill_direction": self.fill_direction
        }

        return percentage, debug_info

    @property
    def last_percentage(self) -> float:
        """Get the last detected percentage (for polling without re-detecting)."""
        return self._last_percentage
