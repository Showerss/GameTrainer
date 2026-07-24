"""
Perception - the eyes' socket (M3, Brick 2).

M2's GridWorld hands the agent two numbers: (row, col). This file swaps that
for a *picture* of the same world, and changes nothing else.

It does the swap with a WRAPPER. A wrapper is a thin layer that sits around an
environment: every call passes straight through it, and it is allowed to change
exactly one thing on the way out. Here that one thing is the observation.

Why a wrapper and not a new environment:
  - GridWorldEnv is never edited and never learns this exists, so M2's tests
    keep passing untouched.
  - Same Ground, same Brain (PPO), same Gymnasium contract -- we only change the
    sense organ in between. That swappability is the entire point of the project.

The agent can no longer see (row, col) AT ALL. That is deliberate: if the
numbers were still there, we would never know whether the eyes actually work.
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces


class PixelObservation(gym.ObservationWrapper):
    """Makes an env's rendered picture the observation, instead of its numbers.

    Requires an env built with render_mode="rgb_array" -- that is what draws
    the picture in the first place.
    """

    def __init__(self, env):
        super().__init__(env)

        if env.render_mode != "rgb_array":
            raise ValueError(
                "PixelObservation needs an env that draws itself: build it with "
                f'render_mode="rgb_array" (got {env.render_mode!r}).'
            )

        # Ask the env for one frame and take its size as the promise we publish.
        # Reading the shape off a real picture beats hardcoding 224 here, where
        # it could silently drift away from what the env actually draws.
        frame = env.render()
        self.observation_space = spaces.Box(
            low=0, high=255, shape=frame.shape, dtype=np.uint8
        )

    def observation(self, observation):
        """Throw away the (row, col) numbers; hand back the current picture.

        Gymnasium calls this for us on every reset() and step(), so the tuple
        shapes those return are untouched -- only the obs inside them changed.
        """
        return self.env.render()
