"""
Stardew Valley Gym Environment - ViT Edition

This environment is designed for use with Vision Transformer feature extractors.
Key differences from the CNN environment:

1. RESOLUTION: 224x224 (ViT's native input size)
   - Much higher than 84x84 CNN version
   - Preserves UI details (text, icons, bars)

2. COLOR: Full RGB (not grayscale)
   - ViT was pretrained on color images
   - Color carries information (red health, green energy, item types)

3. NO FRAME STACKING: Single frame input
   - ViT processes spatial relationships well
   - Motion can be inferred from single frame context
   - (Optional: can add stacking if motion detection is poor)

Teacher Note: Why 224x224?
==========================
ViT models are trained on ImageNet at 224x224. Using this resolution means:
- The patch size (16x16) divides evenly: 224/16 = 14 patches per side
- Pre-trained positional encodings work correctly
- No interpolation artifacts from resizing

You CAN use other sizes (like 384x384 for more detail), but:
- Requires interpolating positional embeddings
- Uses more memory (196 patches → 576 patches)
- May not improve results much
"""

import time
import gymnasium as gym
import numpy as np
import cv2
from gymnasium import spaces

from src.gametrainer.screen import ScreenCapture
from src.gametrainer.input import InputController
from src.gametrainer.logger import Logger


class StardewViTEnv(gym.Env):
    """
    Gym environment optimized for Vision Transformer processing.

    Observation: 224x224 RGB image (3 channels, uint8)
    Action: 12 discrete actions (movement, mouse, escape)
    """

    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': 10}

    # Frame skip - repeat each action N times
    # Teacher Note: Lower than CNN version because we're not stacking frames
    # The model sees more unique frames this way
    FRAME_SKIP = 2

    def __init__(self, render_mode=None):
        super().__init__()

        self.logger = Logger()
        self.render_mode = render_mode

        # =====================================================================
        # OBSERVATION SPACE: 224x224 RGB
        # =====================================================================
        # Shape: (channels, height, width) for PyTorch convention
        # Teacher Note: stable-baselines3 expects channel-first format
        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(3, 224, 224),  # RGB, 224x224
            dtype=np.uint8
        )

        # =====================================================================
        # ACTION SPACE: Same as before
        # =====================================================================
        self.action_space = spaces.Discrete(12)

        # =====================================================================
        # LOG CONFIGURATION
        # =====================================================================
        self.logger.log("=" * 70)
        self.logger.log("STARDEW VALLEY ENVIRONMENT (ViT Edition)")
        self.logger.log("=" * 70)
        self.logger.log("")
        self.logger.log("OBSERVATION SPACE:")
        self.logger.log("  Format: 224 x 224 RGB (channel-first)")
        self.logger.log("  Values: 0-255 (uint8)")
        self.logger.log(f"  Total: {3 * 224 * 224:,} values per frame")
        self.logger.log("")
        self.logger.log("  Compared to 84x84 grayscale: 7x more pixels!")
        self.logger.log("  But still 13x smaller than 1080p RGB")
        self.logger.log("")
        self.logger.log("ACTION SPACE (12 discrete actions):")
        self.logger.log("  Movement:    0=NO-OP, 1=W, 2=S, 3=A, 4=D")
        self.logger.log("  Mouse:       5=Left Click, 6=Right Click")
        self.logger.log("  Mouse Aim:   7=Up, 8=Down, 9=Left, 10=Right")
        self.logger.log("  Menu:        11=ESC")
        self.logger.log("")
        self.logger.log(f"FRAME SKIP: {self.FRAME_SKIP}")
        self.logger.log("  (Each action repeated for consistent effect)")
        self.logger.log("")

        # =====================================================================
        # INITIALIZE COMPONENTS
        # =====================================================================
        self.cap = ScreenCapture()
        self.input = InputController()

        # Find game window
        found = self.cap.set_region_from_window("Stardew Valley")
        if not found:
            self.logger.log("WARNING: Stardew Valley window not found!")
            self.logger.log("  Using full screen capture as fallback.")
            self.cap.set_region_fullscreen()
        else:
            self._focus_game_window("Stardew Valley")
            region = self.cap.region
            self.logger.log(f"WINDOW FOUND: {region['width']}x{region['height']}")

        # Internal state
        self._steps_alive = 0
        self._stuck_counter = 0
        self._prev_frame_small = None  # For movement detection
        self._prev_energy_pct = None
        self._prev_notification_region = None  # For loot/notification detection
        self._episode_reward = 0.0

        # Anti-spam tracking
        # Teacher Note: The agent will exploit any "safe" action that doesn't get
        # punished. ESC and NO-OP are perfect examples - they don't trigger stuck
        # detection or click penalties. We need to track and punish repetition.
        self._last_actions = []  # Rolling window of recent actions
        self._consecutive_passive = 0  # Count of ESC/NO-OP/mouse-aim in a row

        # Action names for logging
        self._action_names = [
            "NO-OP", "UP(W)", "DOWN(S)", "LEFT(A)", "RIGHT(D)",
            "L-CLICK", "R-CLICK", "M-UP", "M-DOWN", "M-LEFT", "M-RIGHT", "ESC"
        ]

        self.logger.log("=" * 70)
        self.logger.log("READY! Start Stardew Valley and begin training.")
        self.logger.log("=" * 70)
        self.logger.log("")

    def _preprocess_frame(self, frame):
        """
        Convert raw screen capture to 224x224 RGB.

        Teacher Note: We resize the full game window to 224x224.
        This loses some fine detail but ViT's attention mechanism
        can still learn to focus on important regions.

        If your game window is 1920x1080:
        - Horizontal: 1920 → 224 (8.6x reduction)
        - Vertical: 1080 → 224 (4.8x reduction)

        The aspect ratio changes, but ViT handles this fine.
        Games with more square layouts will look better.
        """
        if frame is None:
            return np.zeros((3, 224, 224), dtype=np.uint8)

        # Resize to 224x224
        # Teacher Note: INTER_AREA is best for shrinking (anti-aliased)
        resized = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)

        # BGR (OpenCV default) → RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # HWC → CHW (PyTorch format)
        # Teacher Note: OpenCV gives (height, width, channels)
        # PyTorch/SB3 expects (channels, height, width)
        chw = np.transpose(rgb, (2, 0, 1))

        return chw.astype(np.uint8)

    def step(self, action):
        """
        Execute one environment step.

        Returns:
            observation: 224x224 RGB image
            reward: Float reward value
            terminated: Whether episode ended (always False for now)
            truncated: Whether max steps reached
            info: Additional information dict
        """
        total_reward = 0.0
        raw_frame = None

        # Execute action multiple times (frame skipping)
        for _ in range(self.FRAME_SKIP):
            # Capture state BEFORE action for interaction checking
            # We need this to see if our click actually changed anything
            frame_before = self.cap.grab()

            self._take_action(action)
            time.sleep(0.03)  # 30ms between frames

            # Capture state AFTER action
            raw_frame = self.cap.grab()
            if raw_frame is None:
                # Window lost - return empty observation
                return np.zeros((3, 224, 224), dtype=np.uint8), 0.0, True, False, {}

            reward = self._calculate_reward(raw_frame, action, frame_before)
            total_reward += reward

        # Get processed observation
        obs = self._preprocess_frame(raw_frame)

        self._steps_alive += 1
        self._episode_reward += total_reward

        terminated = False
        truncated = self._steps_alive > 10000  # Episode length limit

        info = {
            "step": self._steps_alive,
            "reward": total_reward,
            "episode_reward": self._episode_reward,
        }

        return obs, total_reward, terminated, truncated, info

    def _calculate_reward(self, frame, action, frame_before=None):
        """
        Calculate reward based on game state.
        """
        reward = 0.0

        # -----------------------------------------------------------------
        # A. INTERACTION CHECK (Did clicking do anything?)
        # -----------------------------------------------------------------
        # Actions 5 (Left Click) and 6 (Right Click)
        if action in [5, 6] and frame_before is not None:
            interact_reward = self._calculate_interaction_reward(frame_before, frame)
            reward += interact_reward

        # -----------------------------------------------------------------
        # B. NOTIFICATION/LOOT DETECTION (Bottom-Left)
        # -----------------------------------------------------------------
        # Teacher Note: Stardew pops up "+1 Wood" or "Quest Complete" in the 
        # bottom-left. We watch this area for sudden pixel changes.
        h, w = frame.shape[:2]
        # Bottom-left 25% area
        notif_y_start = int(h * 0.7)
        notif_x_end = int(w * 0.3)
        notif_region = frame[notif_y_start:h, 0:notif_x_end]
        
        # Shrink and grayscale for robust comparison
        notif_small = cv2.resize(notif_region, (64, 64))
        notif_gray = cv2.cvtColor(notif_small, cv2.COLOR_BGR2GRAY)

        if self._prev_notification_region is not None:
            # Check for sudden appearance of text/icons
            notif_diff = cv2.absdiff(notif_gray, self._prev_notification_region).mean()
            
            # Threshold: 8.0 is enough to catch appearing text but ignore minor lighting shifts
            if notif_diff > 8.0:
                reward += 1.0
                self.logger.log(f"[LOOT/NOTIF] Detected change in bottom-left! Diff: {notif_diff:.1f}")

        self._prev_notification_region = notif_gray.copy()

        # -----------------------------------------------------------------
        # C. MOVEMENT DETECTION
        # -----------------------------------------------------------------
        # Shrink frame for fast comparison
        frame_small = cv2.resize(frame, (64, 64))
        frame_gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

        is_movement_action = action in [1, 2, 3, 4]  # WASD

        if self._prev_frame_small is not None and is_movement_action:
            diff = cv2.absdiff(frame_gray, self._prev_frame_small).mean()

            if diff < 2.0:  # Very little changed - probably stuck
                self._stuck_counter += 1
                penalty = -0.1 * min(self._stuck_counter, 10)
                reward += penalty

                if self._stuck_counter % 20 == 0:
                    self.logger.log(
                        f"[STUCK] Action: {self._action_names[action]} | "
                        f"Count: {self._stuck_counter} | Diff: {diff:.2f}"
                    )
            else:
                # Movement detected!
                if self._stuck_counter > 0:
                    self.logger.log(
                        f"[UNSTUCK] After {self._stuck_counter} steps"
                    )
                self._stuck_counter = 0
                reward += 0.05  # Small reward for successful movement

        self._prev_frame_small = frame_gray.copy()

        # -----------------------------------------------------------------
        # D. ENERGY DETECTION (approximate via green pixels in bottom-right)
        # -----------------------------------------------------------------
        h, w = frame.shape[:2]
        energy_region = frame[int(h*0.75):h, int(w*0.9):w]

        if energy_region.size > 0:
            hsv = cv2.cvtColor(energy_region, cv2.COLOR_BGR2HSV)
            # Green hue range for energy bar
            green_mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
            energy_pct = green_mask.mean() / 255.0

            if self._prev_energy_pct is not None:
                energy_change = energy_pct - self._prev_energy_pct

                if energy_change < -0.05:  # Lost significant energy
                    reward -= 0.1
                    self.logger.log(
                        f"[ENERGY] Lost: {self._prev_energy_pct:.1%} → {energy_pct:.1%}"
                    )

            self._prev_energy_pct = energy_pct

        # -----------------------------------------------------------------
        # E. SURVIVAL BASELINE
        # -----------------------------------------------------------------
        reward += 0.001  # Tiny reward for staying alive

        # -----------------------------------------------------------------
        # F. PERIODIC LOGGING
        # -----------------------------------------------------------------
        if self._steps_alive % 100 == 0:
            energy_str = f"{self._prev_energy_pct:.0%}" if self._prev_energy_pct else "?"
            self.logger.log(
                f"[STEP {self._steps_alive:5d}] "
                f"Action: {self._action_names[action]:8s} | "
                f"Reward: {reward:+.3f} | "
                f"Energy: {energy_str} | "
                f"Stuck: {self._stuck_counter}"
            )

        return reward

    def _calculate_interaction_reward(self, frame_before, frame_after):
        """
        Check if pixels around the cursor changed after a click.
        Returns positive reward if changed, small penalty if not.
        """
        try:
            import win32gui
            
            # 1. Get Global Cursor Pos
            flags, hcursor, (cx, cy) = win32gui.GetCursorInfo()
            
            # 2. Get Window Region
            region = self.cap.region
            if not region:
                return 0.0
                
            # 3. Convert to Local Coordinates relative to the frame we captured
            # Note: frame_before/after are BGR numpy arrays of the captured region
            lx = cx - region["left"]
            ly = cy - region["top"]
            
            # Check bounds
            h, w = frame_before.shape[:2]
            if lx < 0 or lx >= w or ly < 0 or ly >= h:
                return 0.0 # Cursor outside game window
                
            # 4. Define ROI (Region of Interest) around cursor
            # 40x40 box (20px radius)
            radius = 20
            x1 = max(0, lx - radius)
            y1 = max(0, ly - radius)
            x2 = min(w, lx + radius)
            y2 = min(h, ly + radius)
            
            # 5. Extract and Compare
            # Use Grayscale for simpler comparison
            roi_before = cv2.cvtColor(frame_before[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
            roi_after = cv2.cvtColor(frame_after[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
            
            diff = cv2.absdiff(roi_before, roi_after).mean()
            
            # 6. Reward Logic
            # Threshold: How much pixel change constitutes a "hit"?
            # A swinging tool animation is a large change. A menu button press is a small change.
            # 5.0 is a conservative threshold (0-255 scale).
            if diff > 5.0:
                # Significant change! We hit something or clicked a button.
                # Log it occasionally so we know it's working
                if self._steps_alive % 50 == 0:
                    self.logger.log(f"[INTERACT] Successful click! Diff: {diff:.1f}")
                return 0.5
            else:
                # No change. We clicked on static background or thin air.
                # Small penalty to discourage spamming clicks on nothing.
                return -0.05
                
        except Exception:
            # Fallback if win32gui fails or other issues
            return 0.0

    def reset(self, seed=None, options=None):
        """Reset environment for new episode."""
        super().reset(seed=seed)

        if self._steps_alive > 0:
            self.logger.log(
                f"\n[EPISODE END] Steps: {self._steps_alive} | "
                f"Total Reward: {self._episode_reward:.2f}\n"
            )

        self._steps_alive = 0
        self._stuck_counter = 0
        self._prev_frame_small = None
        self._prev_energy_pct = None
        self._prev_notification_region = None
        self._episode_reward = 0.0

        # Grab initial frame
        frame = self.cap.grab()
        obs = self._preprocess_frame(frame)

        return obs, {}

    def _take_action(self, action):
        """Execute the given action."""
        MOUSE_STEP = 30

        # Periodically refocus game window
        if self._steps_alive % 100 == 0:
            self._focus_game_window("Stardew Valley")

        if action == 0:    # NO-OP
            pass
        elif action == 1:  # UP
            self.input.move_up()
        elif action == 2:  # DOWN
            self.input.move_down()
        elif action == 3:  # LEFT
            self.input.move_left()
        elif action == 4:  # RIGHT
            self.input.move_right()
        elif action == 5:  # LEFT CLICK
            self.input.mouse_click()
        elif action == 6:  # RIGHT CLICK
            self.input.mouse_right_click()
        elif action == 7:  # MOUSE UP
            self.input.mouse_move(0, -MOUSE_STEP)
        elif action == 8:  # MOUSE DOWN
            self.input.mouse_move(0, MOUSE_STEP)
        elif action == 9:  # MOUSE LEFT
            self.input.mouse_move(-MOUSE_STEP, 0)
        elif action == 10: # MOUSE RIGHT
            self.input.mouse_move(MOUSE_STEP, 0)
        elif action == 11: # ESCAPE
            self.input.escape()

    def _focus_game_window(self, title):
        """
        Focus the game window to ensure it receives input.
        
        Teacher Note: This is critical but dangerous. If we hang here,
        training stops. We use a safe implementation that tries to find
        the window and bring it to front, but gives up easily if it fails.
        """
        try:
            import win32gui
            import win32con

            # Find the largest window with the title (same logic as ScreenCapture)
            # This avoids grabbing tooltips or hidden windows
            target_hwnd = None
            max_area = 0
            partial_lower = title.lower()

            def callback(hwnd, _):
                nonlocal target_hwnd, max_area
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if partial_lower in window_title.lower():
                        try:
                            rect = win32gui.GetWindowRect(hwnd)
                            w = rect[2] - rect[0]
                            h = rect[3] - rect[1]
                            area = w * h
                            if area > max_area:
                                max_area = area
                                target_hwnd = hwnd
                        except Exception:
                            pass
                return True

            win32gui.EnumWindows(callback, None)

            if target_hwnd:
                # If it's not the foreground window, try to switch
                if win32gui.GetForegroundWindow() != target_hwnd:
                    # Restore if minimized
                    if win32gui.IsIconic(target_hwnd):
                        win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
                    
                    # Bring to front safely
                    try:
                        win32gui.SetForegroundWindow(target_hwnd)
                    except Exception:
                        # Sometimes Windows blocks this call. That's fine.
                        # We can try a "force" via Alt key simulation if really needed,
                        # but for now let's just fail silently to keep training running.
                        pass
        except Exception:
            # Never crash the training loop just because focus failed
            pass

    def render(self):
        """Render is handled by the game itself."""
        pass

    def close(self):
        """Clean up resources."""
        pass
