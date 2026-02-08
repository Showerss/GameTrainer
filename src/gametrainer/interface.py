import cv2
import numpy as np
import os
from typing import Optional, Tuple, Dict

class InterfaceManager:
    """
    Handles detection of UI elements using Template Matching.
    
    This replaces the hardcoded coordinate system. Instead of assuming
    "Energy is at 1024,700", we look for the "Energy Icon" image
    and find where it actually is.
    """
    
    def __init__(self, template_dir: str = "src/gametrainer/templates"):
        self.template_dir = template_dir
        self.templates: Dict[str, np.ndarray] = {}
        self.locations: Dict[str, Tuple[int, int, int, int]] = {}
        
        # Load all templates on startup
        self._load_templates()
        
    def _load_templates(self):
        """Load all .png files from the template directory."""
        if not os.path.exists(self.template_dir):
            print(f"[INTERFACE] Warning: Template directory not found: {self.template_dir}")
            return

        for f in os.listdir(self.template_dir):
            if f.endswith(".png"):
                path = os.path.join(self.template_dir, f)
                # Load as grayscale for faster matching
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    name = f.replace(".png", "")
                    self.templates[name] = img
                    print(f"[INTERFACE] Loaded template: {name} ({img.shape})")
                else:
                    print(f"[INTERFACE] Failed to load: {path}")

    def find_all(self, frame_bgr: np.ndarray) -> None:
        """
        Scan the frame for all loaded templates and update locations.
        Call this periodically (e.g. once per second), not every frame.
        """
        if not self.templates:
            return

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        
        for name, template in self.templates.items():
            # Match Template
            res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            # Threshold: 0.8 means 80% match
            if max_val >= 0.8:
                h, w = template.shape
                x, y = max_loc
                self.locations[name] = (x, y, w, h)
                print(f"[INTERFACE] Found {name} at ({x}, {y})")

    def get_energy_region(self, frame_bgr: np.ndarray) -> Optional[np.ndarray]:
        """
        Return the cropped energy bar region based on the 'energy_icon' location.
        """
        # 1. Try to find dynamic location
        if "energy_icon" in self.locations:
            x, y, w, h = self.locations["energy_icon"]
            
            # Assumption: Bar is strictly to the LEFT of the icon (in Stardew)
            # Or vertical? Let's assume Stardew standard layout:
            # Energy bar is a vertical strip on the right side of the screen.
            # The icon is usually at the bottom or top of it.
            
            # Let's crop a meaningful area relative to the icon.
            # E.g. 50px wide, 200px tall, positioned above the icon
            bar_w = 40
            bar_h = 200
            
            # ROI: Left of icon, moving up
            # Coordinates need tuning based on actual game UI
            roi_x = max(0, x - 10) # Roughly aligned with icon
            roi_y = max(0, y - bar_h) 
            
            return frame_bgr[roi_y:y, roi_x:roi_x+bar_w]
            
        # 2. Fallback to hardcoded (Logic derived from env_vit.py)
        h, w = frame_bgr.shape[:2]
        # env_vit.py used: frame[int(h*0.75):h, int(w*0.9):w]
        return frame_bgr[int(h*0.75):h, int(w*0.9):w]

    def get_notification_region(self, frame_bgr: np.ndarray) -> np.ndarray:
        """
        Return the notification area (bottom-left).
        Since this is usually fixed to screen corners, hardcoding is safer
        unless we have a specific anchor template.
        """
        h, w = frame_bgr.shape[:2]
        return frame_bgr[int(h*0.7):h, 0:int(w*0.3)]
