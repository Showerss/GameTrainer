"""
Stardew Valley Gym Environment - Multi-Region Observation

Instead of downscaling the entire screen (losing detail), we crop specific
UI regions at higher resolution. This lets the agent actually SEE:
- What's in the hotbar (tools, seeds, items)
- Energy/health bar status (colors!)
- Time of day
- Money amount

Teacher Note: This uses stable-baselines3's Dict observation space.
The model receives multiple image inputs and learns to use each one.

┌────────────────────────────────────────────────────────────────┐
│                    OBSERVATION REGIONS                          │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐                      ┌─────────────┐         │
│   │  TIME/DATE  │                      │   MONEY     │         │
│   │  80x40 RGB  │                      │  80x32 RGB  │         │
│   └─────────────┘                      └─────────────┘         │
│                                                                 │
│          ┌─────────────────────────────────────┐               │
│          │                                     │               │
│          │           GAME AREA                 │               │
│          │          160x160 Gray               │               │
│          │     (character, objects, NPCs)      │               │
│          │                                     │               │
│          └─────────────────────────────────────┘               │
│                                                                 │
│   ┌─────────────────────────────┐      ┌─────────────┐         │
│   │         HOTBAR              │      │   ENERGY    │         │
│   │       256x48 RGB            │      │  32x128 RGB │         │
│   │  (tools, seeds, items)      │      │  (bar fill) │         │
│   └─────────────────────────────┘      └─────────────┘         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
"""

import time
import gymnasium as gym
import numpy as np
import cv2
from gymnasium import spaces
from collections import deque

from src.gametrainer.screen import ScreenCapture
from src.gametrainer.input import InputController
from src.gametrainer.logger import Logger


class StardewMultiRegionEnv(gym.Env):
    """
    Multi-region observation environment.

    Instead of one 84x84 image, we provide multiple cropped regions
    so the agent can see UI details clearly.
    """
    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': 10}

    # =========================================================================
    # REGION DEFINITIONS (adjust these for your resolution!)
    # These are for 1920x1080. Scale proportionally for other resolutions.
    # =========================================================================

    # Format: (x, y, width, height) in screen coordinates
    # You'll need to calibrate these for Stardew Valley's UI layout

    REGIONS = {
        # Main game area (center of screen, where action happens)
        'game': {
            'crop': (384, 108, 1152, 864),  # x, y, w, h - center area
            'resize': (160, 160),            # Output size
            'color': False,                  # Grayscale (motion matters, not color)
            'stack': 4,                      # Frame stack for motion
        },
        # Hotbar (bottom center - tools, seeds, items)
        'hotbar': {
            'crop': (548, 1012, 824, 60),   # Bottom inventory bar
            'resize': (256, 48),             # Wide rectangle
            'color': True,                   # RGB (item colors matter!)
            'stack': 1,                      # No stacking needed
        },
        # Energy bar (bottom right - vertical green bar)
        'energy': {
            'crop': (1868, 852, 40, 200),   # Right side energy bar
            'resize': (32, 128),             # Tall thin rectangle
            'color': True,                   # RGB (green vs red matters!)
            'stack': 1,
        },
        # Time and date (top right)
        'time': {
            'crop': (1720, 8, 192, 60),     # Top right corner
            'resize': (96, 32),              # Small rectangle
            'color': True,                   # RGB (might help with season)
            'stack': 1,
        },
        # Money display (top right, below time)
        'money': {
            'crop': (1750, 68, 160, 40),    # Below time
            'resize': (80, 24),
            'color': False,                  # Grayscale fine for numbers
            'stack': 1,
        },
    }

    FRAME_SKIP = 4  # Repeat each action N times

    def __init__(self, render_mode=None):
        super().__init__()

        self.logger = Logger()
        self.render_mode = render_mode

        # =====================================================================
        # LOG CONFIGURATION
        # =====================================================================
        self.logger.log("=" * 70)
        self.logger.log("STARDEW MULTI-REGION ENVIRONMENT")
        self.logger.log("=" * 70)
        self.logger.log("")
        self.logger.log("OBSERVATION REGIONS:")

        total_pixels = 0
        for name, cfg in self.REGIONS.items():
            w, h = cfg['resize']
            channels = 3 if cfg['color'] else 1
            stack = cfg['stack']
            pixels = w * h * channels * stack
            total_pixels += pixels
            color_str = "RGB" if cfg['color'] else "Gray"
            self.logger.log(
                f"  • {name:8s}: {w:3d}x{h:3d} {color_str:4s} "
                f"(stack={stack}) = {pixels:,} values"
            )

        self.logger.log(f"\n  TOTAL: {total_pixels:,} values per observation")
        self.logger.log(f"  (vs 2,073,600 for full 1080p RGB - {2073600/total_pixels:.0f}x smaller!)")
        self.logger.log("")

        # =====================================================================
        # BUILD OBSERVATION SPACE (Dict of images)
        # =====================================================================
        obs_spaces = {}
        self._frame_buffers = {}

        for name, cfg in self.REGIONS.items():
            w, h = cfg['resize']
            channels = 3 if cfg['color'] else 1
            stack = cfg['stack']

            # Shape: (stack * channels, height, width) for PyTorch
            if stack > 1:
                shape = (stack * channels, h, w)
            else:
                shape = (channels, h, w)

            obs_spaces[name] = spaces.Box(
                low=0, high=255, shape=shape, dtype=np.uint8
            )

            # Create frame buffer for regions that need stacking
            if stack > 1:
                self._frame_buffers[name] = deque(maxlen=stack)

        self.observation_space = spaces.Dict(obs_spaces)

        # =====================================================================
        # ACTION SPACE (same as before)
        # =====================================================================
        self.action_space = spaces.Discrete(12)

        self.logger.log("ACTION SPACE (12 discrete actions):")
        self.logger.log("  Movement:    0=NO-OP, 1=W, 2=S, 3=A, 4=D")
        self.logger.log("  Mouse:       5=Left Click, 6=Right Click")
        self.logger.log("  Mouse Aim:   7=Up, 8=Down, 9=Left, 10=Right")
        self.logger.log("  Menu:        11=ESC")
        self.logger.log("")

        # =====================================================================
        # INITIALIZE COMPONENTS
        # =====================================================================
        self.cap = ScreenCapture()
        self.input = InputController()

        # Try to find game window
        found = self.cap.set_region_from_window("Stardew Valley")
        if not found:
            self.logger.log("WARNING: Stardew Valley not found. Using full screen.")
            self.cap.set_region_fullscreen()
        else:
            self._focus_game_window("Stardew Valley")
            # Get actual window size for region scaling
            self._calibrate_regions()

        # Internal state
        self._steps_alive = 0
        self._stuck_counter = 0
        self._prev_game_area = None
        self._prev_energy_pixels = None
        self._prev_money_pixels = None

        self.logger.log("=" * 70)
        self.logger.log("READY! Regions calibrated for game window.")
        self.logger.log("=" * 70)

    def _calibrate_regions(self):
        """
        Adjust region coordinates based on actual window size.
        The default values are for 1920x1080.
        """
        region = self.cap.region
        if region is None:
            return

        actual_w = region['width']
        actual_h = region['height']

        # Scale factor from 1920x1080 reference
        scale_x = actual_w / 1920
        scale_y = actual_h / 1080

        if scale_x != 1.0 or scale_y != 1.0:
            self.logger.log(f"Scaling regions for {actual_w}x{actual_h} (scale: {scale_x:.2f}x{scale_y:.2f})")

            for name, cfg in self.REGIONS.items():
                x, y, w, h = cfg['crop']
                cfg['crop'] = (
                    int(x * scale_x),
                    int(y * scale_y),
                    int(w * scale_x),
                    int(h * scale_y)
                )
                self.logger.log(f"  {name}: {cfg['crop']}")

    def _crop_region(self, frame, region_name):
        """
        Crop and process a specific region from the frame.
        """
        cfg = self.REGIONS[region_name]
        x, y, w, h = cfg['crop']
        target_w, target_h = cfg['resize']

        # Bounds checking
        frame_h, frame_w = frame.shape[:2]
        x = max(0, min(x, frame_w - 1))
        y = max(0, min(y, frame_h - 1))
        w = min(w, frame_w - x)
        h = min(h, frame_h - y)

        # Crop
        cropped = frame[y:y+h, x:x+w]

        # Resize
        resized = cv2.resize(cropped, (target_w, target_h))

        # Convert color if needed
        if not cfg['color']:
            if len(resized.shape) == 3:
                resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            resized = np.expand_dims(resized, axis=0)  # Add channel dim
        else:
            # BGR to RGB and channel-first
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            resized = np.transpose(resized, (2, 0, 1))  # HWC -> CHW

        return resized

    def _get_observation(self, frame):
        """
        Build the multi-region observation dictionary.
        """
        obs = {}

        for name, cfg in self.REGIONS.items():
            region_img = self._crop_region(frame, name)

            if cfg['stack'] > 1:
                # Add to frame buffer
                buffer = self._frame_buffers[name]
                buffer.append(region_img)

                # Pad if buffer not full
                while len(buffer) < cfg['stack']:
                    buffer.append(region_img)

                # Stack frames along channel dimension
                stacked = np.concatenate(list(buffer), axis=0)
                obs[name] = stacked.astype(np.uint8)
            else:
                obs[name] = region_img.astype(np.uint8)

        return obs

    def step(self, action):
        """Execute one step with frame skipping."""
        total_reward = 0.0
        raw_frame = None

        for _ in range(self.FRAME_SKIP):
            self._take_action(action)
            time.sleep(0.025)

            raw_frame = self.cap.grab()
            if raw_frame is None:
                return self._get_empty_obs(), 0, True, False, {}

            reward = self._calculate_reward(raw_frame, action)
            total_reward += reward

        obs = self._get_observation(raw_frame)

        self._steps_alive += 1
        terminated = False
        truncated = self._steps_alive > 10000

        info = {"step": self._steps_alive, "reward": total_reward}

        return obs, total_reward, terminated, truncated, info

    def _calculate_reward(self, frame, action):
        """Calculate reward based on multiple regions."""
        reward = 0.0
        action_names = [
            "NO-OP", "UP", "DOWN", "LEFT", "RIGHT",
            "LCLICK", "RCLICK", "M_UP", "M_DOWN", "M_LEFT", "M_RIGHT", "ESC"
        ]

        # A. Movement detection (using game area)
        game_cfg = self.REGIONS['game']
        x, y, w, h = game_cfg['crop']

        # Bounds check
        frame_h, frame_w = frame.shape[:2]
        x, y = max(0, x), max(0, y)
        w, h = min(w, frame_w - x), min(h, frame_h - y)

        game_area = frame[y:y+h, x:x+w]
        game_gray = cv2.cvtColor(game_area, cv2.COLOR_BGR2GRAY)
        game_gray = cv2.resize(game_gray, (80, 80))  # Smaller for comparison

        is_movement = action in [1, 2, 3, 4]

        if self._prev_game_area is not None and is_movement:
            diff = cv2.absdiff(game_gray, self._prev_game_area).mean()

            if diff < 2.0:
                self._stuck_counter += 1
                penalty = -0.1 * min(self._stuck_counter, 10)
                reward += penalty

                if self._stuck_counter % 20 == 0:
                    self.logger.log(
                        f"[STUCK] Action: {action_names[action]} | "
                        f"Count: {self._stuck_counter} | Diff: {diff:.2f}"
                    )
            else:
                if self._stuck_counter > 0:
                    self.logger.log(f"[UNSTUCK] After {self._stuck_counter} steps | Diff: {diff:.2f}")
                self._stuck_counter = 0
                reward += 0.05

        self._prev_game_area = game_gray.copy()

        # B. Energy detection (using energy region)
        energy_cfg = self.REGIONS['energy']
        ex, ey, ew, eh = energy_cfg['crop']
        ex, ey = max(0, ex), max(0, ey)
        ew, eh = min(ew, frame_w - ex), min(eh, frame_h - ey)

        if ew > 0 and eh > 0:
            energy_region = frame[ey:ey+eh, ex:ex+ew]

            # Detect green pixels (energy remaining)
            hsv = cv2.cvtColor(energy_region, cv2.COLOR_BGR2HSV)
            green_mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
            energy_pct = green_mask.mean() / 255.0

            if self._prev_energy_pixels is not None:
                energy_change = energy_pct - self._prev_energy_pixels
                if energy_change < -0.05:
                    reward -= 0.1
                    self.logger.log(
                        f"[ENERGY] Lost energy: {self._prev_energy_pixels:.1%} -> {energy_pct:.1%}"
                    )

            self._prev_energy_pixels = energy_pct

        # C. Survival baseline
        reward += 0.001

        # D. Periodic logging
        if self._steps_alive % 100 == 0:
            energy_str = f"{self._prev_energy_pixels:.0%}" if self._prev_energy_pixels else "?"
            self.logger.log(
                f"[STEP {self._steps_alive}] Action: {action_names[action]} | "
                f"Reward: {reward:+.3f} | Energy: {energy_str}"
            )

        return reward

    def reset(self, seed=None, options=None):
        """Reset environment."""
        super().reset(seed=seed)

        self.logger.log("Environment Reset")

        self._steps_alive = 0
        self._stuck_counter = 0
        self._prev_game_area = None
        self._prev_energy_pixels = None
        self._prev_money_pixels = None

        # Clear frame buffers
        for buffer in self._frame_buffers.values():
            buffer.clear()

        frame = self.cap.grab()
        if frame is None:
            return self._get_empty_obs(), {}

        # Fill buffers with initial frame
        for name, cfg in self.REGIONS.items():
            if cfg['stack'] > 1:
                region_img = self._crop_region(frame, name)
                for _ in range(cfg['stack']):
                    self._frame_buffers[name].append(region_img)

        return self._get_observation(frame), {}

    def _get_empty_obs(self):
        """Return empty observation dict."""
        obs = {}
        for name, cfg in self.REGIONS.items():
            w, h = cfg['resize']
            channels = 3 if cfg['color'] else 1
            stack = cfg['stack']
            shape = (stack * channels, h, w) if stack > 1 else (channels, h, w)
            obs[name] = np.zeros(shape, dtype=np.uint8)
        return obs

    def _take_action(self, action):
        """Execute action."""
        MOUSE_STEP = 30

        if self._steps_alive % 100 == 0:
            self._focus_game_window("Stardew Valley")

        if action == 0:
            pass
        elif action == 1:
            self.input.move_up()
        elif action == 2:
            self.input.move_down()
        elif action == 3:
            self.input.move_left()
        elif action == 4:
            self.input.move_right()
        elif action == 5:
            self.input.mouse_click()
        elif action == 6:
            self.input.mouse_right_click()
        elif action == 7:
            self.input.mouse_move(0, -MOUSE_STEP)
        elif action == 8:
            self.input.mouse_move(0, MOUSE_STEP)
        elif action == 9:
            self.input.mouse_move(-MOUSE_STEP, 0)
        elif action == 10:
            self.input.mouse_move(MOUSE_STEP, 0)
        elif action == 11:
            self.input.escape()

    def _focus_game_window(self, title):
        """Focus the game window."""
        try:
            import win32gui
            import win32con

            hwnd = None
            def callback(h, _):
                nonlocal hwnd
                if win32gui.IsWindowVisible(h):
                    if title.lower() in win32gui.GetWindowText(h).lower():
                        hwnd = h
                        return False
                return True

            win32gui.EnumWindows(callback, None)

            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
        except:
            pass

    def render(self):
        pass

    def close(self):
        pass
