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
        # We resize the game window to 256x256 RGB for the CNN
        self.obs_shape = (256, 256, 3)
        self.observation_space = spaces.Box(
            low=0, high=255, shape=self.obs_shape, dtype=np.uint8
        )

        # 3. Initialize Components
        self.cap = ScreenCapture()
        self.input = InputController()

        # Connect to game window
        # Teacher Note: We attempt to find the window. If not found, 
        # it might default to primary monitor or fail gracefully during step.
        found = self.cap.set_region_from_window("Stardew Valley")
        if not found:
            self.logger.log("WARNING: Stardew Valley window not found. Defaulting to full screen.")
            self.cap.set_region_fullscreen()

    def step(self, action):
        """
        Execute one time step within the environment.
        """
        # 1. Execute Action
        self._take_action(action)

        # 2. Wait for game to process (10 FPS = 0.1s)
        # We can adjust this to speed up training, but the game has its own animation speed.
        time.sleep(0.1)

        # 3. Get Observation
        obs = self._get_obs()

        # 4. Calculate Reward
        # TODO: Implement complex reward function (energy change, item gain, etc.)
        # For now, small positive reward for staying alive/running.
        reward = 0.01

        # 5. Check Done
        # TODO: Check for "passed out" screen or end of day
        terminated = False
        truncated = False
        
        info = {}

        return obs, reward, terminated, truncated, info

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
