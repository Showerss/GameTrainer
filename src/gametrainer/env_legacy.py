"""
Stardew Valley Gym Environment

This module adapts the Stardew Valley game into a standard Gymnasium environment
for Reinforcement Learning.

Key Concepts:
- Observation: Grayscale pixels, 84x84, 4 stacked frames (sees motion!)
- Action: Discrete keyboard inputs (WASD, mouse, ESC).
- Reward: Calculated based on game state changes.

Performance Optimizations (from Atari DQN papers):
- Grayscale: 3 channels -> 1 (3x reduction)
- Resolution: 256x256 -> 84x84 (9x reduction)
- Frame stacking: 4 frames so agent perceives motion
- Frame skipping: Repeat action 4 times (4x speedup)
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


class StardewEnv(gym.Env):
    """
    Custom Environment that follows gym interface.

    Teacher Note: We use techniques from the famous DQN Atari papers to speed up learning:
    - Grayscale reduces input by 3x (color rarely matters for game logic)
    - 84x84 is the "standard" RL resolution - smaller = faster
    - Frame stacking lets the agent see MOTION (crucial for understanding movement)
    - Frame skipping means we don't process every single frame (4x speedup)
    """
    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': 10}

    # =========================================================================
    # CONFIGURATION - Tune these for speed vs. quality tradeoff
    # =========================================================================
    FRAME_STACK = 4      # Number of frames to stack (agent sees motion)
    FRAME_SKIP = 4       # Repeat each action N times (speeds up training)
    OBS_SIZE = 84        # 84x84 is standard for Atari-style RL

    def __init__(self, render_mode=None):
        super(StardewEnv, self).__init__()

        self.logger = Logger()
        self.render_mode = render_mode

        # =====================================================================
        # LOG CONFIGURATION (So you can learn from what's happening!)
        # =====================================================================
        self.logger.log("=" * 60)
        self.logger.log("STARDEW RL ENVIRONMENT INITIALIZING")
        self.logger.log("=" * 60)
        self.logger.log("")
        self.logger.log("PERFORMANCE OPTIMIZATIONS (from Atari DQN papers):")
        self.logger.log(f"  * Frame Stacking: {self.FRAME_STACK} frames")
        self.logger.log(f"    -> Why: Agent sees MOTION, not just snapshots")
        self.logger.log(f"  * Frame Skipping: {self.FRAME_SKIP}x")
        self.logger.log(f"    -> Why: 4x faster training, actions repeated")
        self.logger.log(f"  * Resolution: {self.OBS_SIZE}x{self.OBS_SIZE} (grayscale)")
        self.logger.log(f"    -> Why: 84x84 is standard, smaller = faster CNN")
        self.logger.log("")

        # Calculate and log the data reduction
        original_size = 256 * 256 * 3  # Original RGB
        new_size = self.OBS_SIZE * self.OBS_SIZE * self.FRAME_STACK
        reduction = original_size / new_size
        self.logger.log(f"  DATA REDUCTION:")
        self.logger.log(f"    Before: 256x256x3 (RGB)     = {original_size:,} values/obs")
        self.logger.log(f"    After:  {self.OBS_SIZE}x{self.OBS_SIZE}x{self.FRAME_STACK} (Gray+Stack) = {new_size:,} values/obs")
        self.logger.log(f"    Reduction: {reduction:.1f}x smaller input!")
        self.logger.log("")

        # 1. Initialize Action Space (Discrete)
        # Movement: 0=No-op, 1=W, 2=S, 3=A, 4=D
        # Mouse clicks: 5=Left click, 6=Right click
        # Mouse movement: 7=Mouse Up, 8=Mouse Down, 9=Mouse Left, 10=Mouse Right
        # Menu dismiss: 11=ESC (critical for getting unstuck from menus!)
        self.action_space = spaces.Discrete(12)

        self.logger.log("ACTION SPACE (12 discrete actions):")
        self.logger.log("  Movement:    0=NO-OP, 1=W, 2=S, 3=A, 4=D")
        self.logger.log("  Mouse:       5=Left Click, 6=Right Click")
        self.logger.log("  Mouse Aim:   7=Up, 8=Down, 9=Left, 10=Right (30px steps)")
        self.logger.log("  Menu:        11=ESC (dismiss popups)")
        self.logger.log("")

        # 2. Initialize Observation Space (Grayscale, stacked frames)
        # Shape: (4, 84, 84) - 4 grayscale frames stacked
        # Teacher Note: We use channel-first format (C, H, W) because PyTorch CNNs expect this
        self.obs_shape = (self.FRAME_STACK, self.OBS_SIZE, self.OBS_SIZE)
        self.observation_space = spaces.Box(
            low=0, high=255, shape=self.obs_shape, dtype=np.uint8
        )

        self.logger.log(f"OBSERVATION SPACE: {self.obs_shape}")
        self.logger.log("  Format: (frames, height, width) - Channel-first for PyTorch")
        self.logger.log("")

        # Frame buffer for stacking (stores last N grayscale frames)
        self._frame_buffer = deque(maxlen=self.FRAME_STACK)

        # 3. Initialize Components
        self.cap = ScreenCapture()
        self.input = InputController()

        # Connect to game window and focus it
        found = self.cap.set_region_from_window("Stardew Valley")
        if not found:
            self.logger.log("WARNING: Stardew Valley window not found. Defaulting to full screen.")
            self.cap.set_region_fullscreen()
        else:
            # Focus the game window so it receives input
            self._focus_game_window("Stardew Valley")

        # 4. Internal State (The Referee)
        # We track these strictly for reward calculation
        self._prev_energy = 1.0
        self._prev_money_pixels = None
        self._prev_inventory_pixels = None
        self._prev_game_area = None  # For movement detection
        self._stuck_counter = 0      # How many consecutive "stuck" frames
        self._steps_alive = 0

        # Log the reward system
        self.logger.log("REWARD SYSTEM (How the agent learns):")
        self.logger.log("  +--------------------------------------------------+")
        self.logger.log("  | MOVEMENT DETECTION (compares game area frames)   |")
        self.logger.log("  |   * Movement succeeded: +0.05                    |")
        self.logger.log("  |   * Stuck (no change after WASD): -0.1 to -1.0   |")
        self.logger.log("  |     (escalates the longer agent is stuck)        |")
        self.logger.log("  +--------------------------------------------------+")
        self.logger.log("  | SURVIVAL: +0.001 per step (tiny baseline)        |")
        self.logger.log("  +--------------------------------------------------+")
        self.logger.log("  | ENERGY: -0.05 when energy decreases              |")
        self.logger.log("  +--------------------------------------------------+")
        self.logger.log("  | INVENTORY: +0.5 when inventory pixels change     |")
        self.logger.log("  +--------------------------------------------------+")
        self.logger.log("  | MONEY: +1.0 when money display changes           |")
        self.logger.log("  +--------------------------------------------------+")
        self.logger.log("  | PASS OUT: -100.0 if energy hits 0 (episode ends) |")
        self.logger.log("  +--------------------------------------------------+")
        self.logger.log("")
        self.logger.log("=" * 60)
        self.logger.log("INITIALIZATION COMPLETE - Ready to train!")
        self.logger.log("=" * 60)
        self.logger.log("")

    def step(self, action):
        """
        Execute one time step within the environment.

        Teacher Note: Frame skipping means we repeat the action N times and only
        return the final observation. This has two benefits:
        1. Training is ~4x faster (fewer forward passes through the network)
        2. Each "step" covers more meaningful game time
        """
        total_reward = 0.0
        raw_frame = None

        # =====================================================================
        # FRAME SKIPPING: Repeat action N times, accumulate rewards
        # =====================================================================
        for i in range(self.FRAME_SKIP):
            # 1. Execute Action
            self._take_action(action)

            # 2. Brief wait for game to process (shorter since we're repeating)
            time.sleep(0.025)  # 25ms x 4 = 100ms total per step

            # 3. Grab frame for reward calculation
            raw_frame = self.cap.grab()
            if raw_frame is None:
                return self._get_stacked_obs(), 0, True, False, {}

            # 4. Calculate and accumulate reward
            reward = self._calculate_reward(raw_frame, action)
            total_reward += reward

            # 5. Check for early termination (passed out, etc.)
            current_energy = self._detect_energy_level(raw_frame)
            if current_energy < 0.02:
                total_reward -= 100.0
                self.logger.log("Agent passed out! Episode End.")
                # Add final frame to buffer before returning
                self._add_frame_to_buffer(raw_frame)
                return self._get_stacked_obs(), total_reward, True, False, {"energy": current_energy}

        # =====================================================================
        # BUILD OBSERVATION (Stacked grayscale frames)
        # =====================================================================
        self._add_frame_to_buffer(raw_frame)
        obs = self._get_stacked_obs()

        # =====================================================================
        # CHECK TERMINATION CONDITIONS
        # =====================================================================
        self._steps_alive += 1
        terminated = False
        current_energy = self._detect_energy_level(raw_frame)

        # Truncate if running too long (~15 minutes with frame skip)
        # 10000 steps x 4 frame_skip x 0.025s = ~16 minutes
        if self._steps_alive > 10000:
            truncated = True
        else:
            truncated = False

        info = {"energy": current_energy, "total_reward": total_reward}

        return obs, total_reward, terminated, truncated, info

    def _calculate_reward(self, frame, action):
        """
        The "Hidden Referee" that grades the Agent's performance.

        Teacher Note: This is where the agent learns what's "good" and "bad".
        We compare frames to detect:
        - Did movement actually happen?
        - Did inventory change?
        - Did money increase?
        """
        reward = 0.0
        h, w, _ = frame.shape
        reward_reasons = []  # Track what contributed to this reward

        # Action names for logging
        action_names = [
            "NO-OP", "UP(W)", "DOWN(S)", "LEFT(A)", "RIGHT(D)",
            "LEFT_CLICK", "RIGHT_CLICK",
            "MOUSE_UP", "MOUSE_DOWN", "MOUSE_LEFT", "MOUSE_RIGHT",
            "ESC"
        ]

        # =====================================================================
        # A. MOVEMENT DETECTION (The "Am I Stuck?" Check)
        # =====================================================================
        margin_x = int(w * 0.10)
        margin_top = int(h * 0.08)
        margin_bottom = int(h * 0.12)

        game_area = frame[margin_top:h-margin_bottom, margin_x:w-margin_x]
        game_area_gray = cv2.cvtColor(game_area, cv2.COLOR_BGR2GRAY)

        is_movement_action = action in [1, 2, 3, 4]

        if self._prev_game_area is not None and is_movement_action:
            diff = cv2.absdiff(game_area_gray, self._prev_game_area)
            movement_score = diff.mean()

            STUCK_THRESHOLD = 2.0

            if movement_score < STUCK_THRESHOLD:
                self._stuck_counter += 1
                stuck_penalty = -0.1 * min(self._stuck_counter, 10)
                reward += stuck_penalty
                reward_reasons.append(f"STUCK({stuck_penalty:+.2f})")

                if self._stuck_counter % 20 == 0:
                    self.logger.log(
                        f"[PENALTY] STUCK after {action_names[action]} | "
                        f"Counter: {self._stuck_counter} | "
                        f"Penalty: {stuck_penalty:.2f} | "
                        f"Screen change: {movement_score:.2f} (threshold: {STUCK_THRESHOLD})"
                    )
            else:
                if self._stuck_counter > 0:
                    self.logger.log(
                        f"[REWARD] UNSTUCK after {self._stuck_counter} steps | "
                        f"Action: {action_names[action]} | "
                        f"Screen change: {movement_score:.2f}"
                    )
                self._stuck_counter = 0
                reward += 0.05
                reward_reasons.append("MOVED(+0.05)")

        self._prev_game_area = game_area_gray.copy()

        # =====================================================================
        # B. SURVIVAL REWARD (Tiny encouragement to exist)
        # =====================================================================
        reward += 0.001

        # =====================================================================
        # C. ENERGY MANAGEMENT
        # =====================================================================
        current_energy = self._detect_energy_level(frame)
        energy_delta = current_energy - self._prev_energy

        if energy_delta < 0:
            reward -= 0.05
            reward_reasons.append("ENERGY_LOSS(-0.05)")

        self._prev_energy = current_energy

        # =====================================================================
        # D. PRODUCTIVITY (Inventory Changes)
        # =====================================================================
        # Region: center-bottom of screen (inventory bar)
        inv_x1, inv_x2 = w // 4, (w * 3) // 4
        inv_y1, inv_y2 = h - 60, h - 10
        inv_region = frame[inv_y1:inv_y2, inv_x1:inv_x2]
        inv_gray = cv2.cvtColor(inv_region, cv2.COLOR_BGR2GRAY)

        if self._prev_inventory_pixels is not None:
            inv_diff = cv2.absdiff(inv_gray, self._prev_inventory_pixels).mean()
            INV_THRESHOLD = 5.0

            if inv_diff > INV_THRESHOLD:
                reward += 0.5
                reward_reasons.append(f"INVENTORY(+0.5)")
                self.logger.log(
                    f"[REWARD] INVENTORY CHANGED | "
                    f"Action: {action_names[action]} | "
                    f"Pixel diff: {inv_diff:.2f} (threshold: {INV_THRESHOLD}) | "
                    f"Region: x[{inv_x1}:{inv_x2}] y[{inv_y1}:{inv_y2}]"
                )

        self._prev_inventory_pixels = inv_gray

        # =====================================================================
        # E. FINANCIAL SUCCESS (Money Changes)
        # =====================================================================
        # Region: top-right corner where money is displayed
        # NOTE: The clock is ALSO in this area, so we need a higher threshold
        # to avoid false positives from time changes
        money_x1, money_x2 = w - 150, w - 10
        money_y1, money_y2 = 10, 60
        money_region = frame[money_y1:money_y2, money_x1:money_x2]
        money_gray = cv2.cvtColor(money_region, cv2.COLOR_BGR2GRAY)

        if self._prev_money_pixels is not None:
            money_diff = cv2.absdiff(money_gray, self._prev_money_pixels).mean()

            # HIGHER threshold to avoid clock changes triggering this
            # Clock ticks cause small changes (~2-5), real money changes are bigger
            MONEY_THRESHOLD = 8.0

            if money_diff > MONEY_THRESHOLD:
                reward += 1.0
                reward_reasons.append(f"MONEY(+1.0)")
                self.logger.log(
                    f"[REWARD] MONEY REGION CHANGED | "
                    f"Action: {action_names[action]} | "
                    f"Pixel diff: {money_diff:.2f} (threshold: {MONEY_THRESHOLD}) | "
                    f"Region: x[{money_x1}:{money_x2}] y[{money_y1}:{money_y2}] | "
                    f"WARNING: Could be clock change, menu, or actual money!"
                )

        self._prev_money_pixels = money_gray

        # =====================================================================
        # PERIODIC SUMMARY LOG (every 100 steps)
        # =====================================================================
        if self._steps_alive % 100 == 0 and self._steps_alive > 0:
            self.logger.log(
                f"[STEP {self._steps_alive}] Action: {action_names[action]} | "
                f"Reward: {reward:+.3f} | "
                f"Reasons: {', '.join(reward_reasons) if reward_reasons else 'survival only'}"
            )

        return reward

    def _detect_energy_level(self, frame):
        """
        Heuristic to estimate energy bar fullness.
        """
        h, w, _ = frame.shape
        if h < 500 or w < 500:
            return 1.0  # Safety for weird windows

        # For now, return a dummy 1.0 to prevent immediate panic until calibrated
        return 1.0

    def reset(self, seed=None, options=None):
        """
        Reset the state of the environment to an initial state.
        """
        super().reset(seed=seed)

        self.logger.log("Environment Reset")

        # Reset internal state trackers
        self._prev_game_area = None
        self._prev_inventory_pixels = None
        self._prev_money_pixels = None
        self._stuck_counter = 0
        self._steps_alive = 0
        self._prev_energy = 1.0

        # Clear the frame buffer and fill with initial frames
        self._frame_buffer.clear()

        # Capture initial frame and fill buffer (so we have 4 frames to stack)
        initial_frame = self.cap.grab()
        for _ in range(self.FRAME_STACK):
            self._add_frame_to_buffer(initial_frame)

        obs = self._get_stacked_obs()
        info = {}

        return obs, info

    def render(self):
        """
        Render the environment.
        Since we are capturing the screen, 'human' mode is just looking at the monitor.
        'rgb_array' returns the observation.
        """
        if self.render_mode == 'rgb_array':
            return self._get_obs()
        return None

    def close(self):
        pass

    def _focus_game_window(self, window_title: str):
        """
        Focus/activate the game window so it receives input.
        """
        try:
            import win32gui
            import win32con

            hwnd = None
            partial_lower = window_title.lower()

            def callback(window_hwnd, _):
                nonlocal hwnd
                if win32gui.IsWindowVisible(window_hwnd):
                    title = win32gui.GetWindowText(window_hwnd)
                    if partial_lower in title.lower():
                        hwnd = window_hwnd
                        return False
                return True

            win32gui.EnumWindows(callback, None)

            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                self.logger.log(f"Focused game window: {win32gui.GetWindowText(hwnd)}")
                time.sleep(0.3)
            else:
                self.logger.log(f"WARNING: Could not find window '{window_title}' to focus")
        except ImportError:
            self.logger.log("WARNING: win32gui not available - cannot focus window. Install pywin32.")
        except Exception as e:
            self.logger.log(f"WARNING: Failed to focus window: {e}")

    def _take_action(self, action):
        """
        Map discrete action index to input command.
        """
        action_names = [
            "NO-OP", "UP(W)", "DOWN(S)", "LEFT(A)", "RIGHT(D)",
            "LEFT_CLICK", "RIGHT_CLICK",
            "MOUSE_UP", "MOUSE_DOWN", "MOUSE_LEFT", "MOUSE_RIGHT",
            "ESC"
        ]

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

        if self._steps_alive % 50 == 0:
            self.logger.log(f"Action taken: {action_names[action]} (step {self._steps_alive})")

    def _add_frame_to_buffer(self, raw_frame):
        """
        Process a raw frame and add it to the frame buffer.
        """
        if raw_frame is None:
            gray = np.zeros((self.OBS_SIZE, self.OBS_SIZE), dtype=np.uint8)
        else:
            gray = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (self.OBS_SIZE, self.OBS_SIZE))

        self._frame_buffer.append(gray)

    def _get_stacked_obs(self):
        """
        Return the stacked frames as the observation.
        Shape: (4, 84, 84) - 4 grayscale images stacked.
        """
        while len(self._frame_buffer) < self.FRAME_STACK:
            self._frame_buffer.append(np.zeros((self.OBS_SIZE, self.OBS_SIZE), dtype=np.uint8))

        stacked = np.stack(list(self._frame_buffer), axis=0)
        return stacked.astype(np.uint8)

    def _get_obs(self):
        """
        Legacy method - returns stacked observation.
        """
        frame = self.cap.grab()
        self._add_frame_to_buffer(frame)
        return self._get_stacked_obs()
