"""
Stardew Valley Gym Environment

This module adapts the Stardew Valley game into a standard Gymnasium environment
for Reinforcement Learning.

Key Concepts:
- Observation: The raw pixels of the game window (resized).
- Action: Discrete keyboard inputs (WASD, etc.).
- Reward: Calculated based on game state changes (currently simplified).
"""

import time
import gymnasium as gym
import numpy as np
import cv2
from gymnasium import spaces

from src.python.core.screen_capture import ScreenCapture
from src.python.core.input_controller import InputController
from src.python.core.logger import Logger

class StardewEnv(gym.Env):
    """
    Custom Environment that follows gym interface.
    """
    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': 10}

    def __init__(self, render_mode=None):
        super(StardewEnv, self).__init__()

        self.logger = Logger()
        self.render_mode = render_mode
        
        # 1. Initialize Action Space (Discrete)
        # 0: No-op, 1: W, 2: S, 3: A, 4: D, 5: Tool(C), 6: Action(X)
        self.action_space = spaces.Discrete(7)

        # 2. Initialize Observation Space (Visual)
        self.obs_shape = (256, 256, 3)
        self.observation_space = spaces.Box(
            low=0, high=255, shape=self.obs_shape, dtype=np.uint8
        )

        # 3. Initialize Components
        self.cap = ScreenCapture()
        self.input = InputController()

        # Connect to game window
        found = self.cap.set_region_from_window("Stardew Valley")
        if not found:
            self.logger.log("WARNING: Stardew Valley window not found. Defaulting to full screen.")
            self.cap.set_region_fullscreen()

        # 4. Internal State (The Referee)
        # We track these strictly for reward calculation
        self._prev_energy = 1.0
        self._prev_money_pixels = None
        self._prev_inventory_pixels = None
        self._steps_alive = 0

    def step(self, action):
        """
        Execute one time step within the environment.
        """
        # 1. Execute Action
        self._take_action(action)

        # 2. Wait for game to process
        time.sleep(0.1)

        # 3. Get Observation & Raw Frame
        # We need the raw frame for our "Referee" checks (Reward calculation)
        raw_frame = self.cap.grab()
        if raw_frame is None:
            return np.zeros(self.obs_shape, dtype=np.uint8), 0, True, False, {}

        # Resize for the Agent's eyes (Observation)
        frame_rgb = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
        obs = cv2.resize(frame_rgb, (self.obs_shape[1], self.obs_shape[0]))

        # 4. Calculate Reward (The Referee Logic)
        reward = self._calculate_reward(raw_frame, action)

        # 5. Check Done
        self._steps_alive += 1
        terminated = False
        
        # End episode if we pass out (Energy critical) or run too long (20 mins)
        current_energy = self._detect_energy_level(raw_frame)
        if current_energy < 0.02: # 2% energy
            reward -= 100.0 # Massive penalty for passing out
            terminated = True
            self.logger.log("Agent passed out! Episode End.")
        
        if self._steps_alive > 10000: # ~15 minutes
            truncated = True
        else:
            truncated = False
            
        info = {"energy": current_energy}

        return obs, reward, terminated, truncated, info

    def _calculate_reward(self, frame, action):
        """
        The "Hidden Referee" that grades the Agent's performance.
        """
        reward = 0.0
        
        # A. Survival Reward (Tiny encouragement to exist)
        reward += 0.001

        # B. Energy Management
        # We assume Energy bar is roughly at the bottom right.
        # Teacher Note: These coords are hardcoded for 1080p standard UI. 
        # In a real product, we'd auto-detect them.
        current_energy = self._detect_energy_level(frame)
        energy_delta = current_energy - self._prev_energy
        
        if energy_delta < 0:
            # We lost energy. Was it worth it?
            # Small penalty to discourage swinging tools at nothing
            reward -= 0.05
        
        self._prev_energy = current_energy

        # C. Productivity (Inventory Changes)
        # Check bottom row of screen where inventory usually is
        h, w, _ = frame.shape
        inv_region = frame[h-60:h-10, w//4:w//4*3] # Rough center bottom
        inv_gray = cv2.cvtColor(inv_region, cv2.COLOR_BGR2GRAY)
        
        if self._prev_inventory_pixels is not None:
            # Calculate difference
            score = cv2.absdiff(inv_gray, self._prev_inventory_pixels).mean()
            if score > 5.0: # Significant change threshold
                # Something changed in inventory! (Picked up item, selected new tool)
                # We give a reward for "interacting with the world"
                reward += 0.5
                # self.logger.log("Reward: Inventory Activity!")
        
        self._prev_inventory_pixels = inv_gray

        # D. Financial Success (Money Changes)
        # Top right corner usually
        money_region = frame[10:60, w-150:w-10] 
        money_gray = cv2.cvtColor(money_region, cv2.COLOR_BGR2GRAY)
        
        if self._prev_money_pixels is not None:
            score = cv2.absdiff(money_gray, self._prev_money_pixels).mean()
            if score > 2.0: # Digits changed
                reward += 1.0
                self.logger.log("Reward: MONEY EARNED!")
        
        self._prev_money_pixels = money_gray

        return reward

    def _detect_energy_level(self, frame):
        """
        Heuristic to estimate energy bar fullness.
        """
        # Crop the energy bar region (Bottom Right, vertical bar)
        h, w, _ = frame.shape
        # This is a Rough guess for 1080p. 
        # Ideally, we'd use template matching here.
        # Region: x=w-35, y=h-250, w=20, h=200
        if h < 500 or w < 500: return 1.0 # Safety for weird windows
        
        bar_x = w - 40
        bar_bottom = h - 20
        bar_height = 200
        
        # Scan up the bar to find where it turns from "Color" to "Grey"
        # This is simplified; assumes full bar = 1.0, empty = 0.0
        # For now, return a dummy 1.0 to prevent immediate panic until calibrated
        return 1.0 

    def reset(self, seed=None, options=None):
        """
        Reset the state of the environment to an initial state.
        """
        super().reset(seed=seed)
        
        self.logger.log("Environment Reset")
        
        # TODO: We might need to implement a macro to wake up/walk out of bed here.
        # For now, we just capture the current state.
        
        obs = self._get_obs()
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

    def _take_action(self, action):
        """Map discrete action index to input command."""
        if action == 0:
            pass # No-op
        elif action == 1:
            self.input.move_up()
        elif action == 2:
            self.input.move_down()
        elif action == 3:
            self.input.move_left()
        elif action == 4:
            self.input.move_right()
        elif action == 5:
            self.input.use_tool()
        elif action == 6:
            self.input.action()

    def _get_obs(self):
        """Capture screen and resize to observation shape."""
        frame = self.cap.grab()
        
        if frame is None:
            # Return black screen if capture fails
            return np.zeros(self.obs_shape, dtype=np.uint8)
        
        # Resize to 256x256
        # OpenCV uses BGR, but Gymnasium expects RGB usually.
        # We'll stick to what we captured (BGR) for now, but CNNs might prefer RGB.
        # Let's convert to RGB for consistency with standard ML models.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(frame_rgb, (self.obs_shape[1], self.obs_shape[0]))
        
        return resized
