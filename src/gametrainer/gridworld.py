"""
GridWorld - our first home-built Ground (M2).

CartPole (M0/M1) was *borrowed*. GridWorld is *ours* — but it obeys the exact
same Gymnasium contract: reset() hands back a starting observation, and
step(action) moves the world forward one tick and reports back. That sameness
is the whole point of the project: anything that learned on CartPole can learn
here without changing a single line.

The world:
  - A 5x5 grid.
  - The agent starts top-left at (0, 0) and wants the goal bottom-right (4, 4).
  - Four moves: up / down / left / right. Walking into a wall just stays put.
  - Each step costs a little (-0.01) so dawdling hurts; the goal pays +1.0.
  - A game ends by winning (terminated) or by running out of moves (truncated).

The reward logic lives directly inside this class on purpose. No Profile, no
RewardCalculator abstraction yet — that's a later milestone. Numbers in,
numbers out.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces


class GridWorldEnv(gym.Env):
    """A 5x5 walk-to-the-goal world that follows the Gymnasium contract."""

    metadata = {"render_modes": ["human"]}

    # World shape (fixed for M2).
    SIZE = 5                 # 5x5 grid
    START = (0, 0)           # top-left corner
    GOAL = (4, 4)            # bottom-right corner
    MAX_STEPS = 100          # truncation cap: out of moves after this many

    # Reward numbers.
    STEP_COST = -0.01        # every step costs a little
    GOAL_REWARD = 1.0        # reaching the goal pays this

    # Action ids (this is the meaning of Discrete(4)).
    UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

    def __init__(self, render_mode=None):
        super().__init__()
        self.render_mode = render_mode

        # ACTION SPACE: four discrete moves.
        self.action_space = spaces.Discrete(4)

        # OBSERVATION SPACE: the agent's (row, col) — two numbers, each 0..SIZE-1.
        # We keep the position as plain ints internally (clean grid math), but we
        # hand it out as float32 because that's the shape a neural net reads best.
        self.observation_space = spaces.Box(
            low=0,
            high=self.SIZE - 1,
            shape=(2,),
            dtype=np.float32,
        )

        # Live state — actually set in reset(); seeded here so the object is valid.
        self.row, self.col = self.START
        self._steps = 0

    def _get_obs(self):
        """Current position as the float32 observation the contract promises."""
        return np.array([self.row, self.col], dtype=np.float32)

    def reset(self, seed=None, options=None):
        """New game: put the agent at the start. Returns (observation, info)."""
        super().reset(seed=seed)
        self.row, self.col = self.START
        self._steps = 0
        return self._get_obs(), {}

    def step(self, action):
        """One move. Returns (obs, reward, terminated, truncated, info)."""
        action = int(action)

        # Propose the move, clamped to the grid so walls simply stop us.
        if action == self.UP:
            self.row = max(0, self.row - 1)
        elif action == self.DOWN:
            self.row = min(self.SIZE - 1, self.row + 1)
        elif action == self.LEFT:
            self.col = max(0, self.col - 1)
        elif action == self.RIGHT:
            self.col = min(self.SIZE - 1, self.col + 1)

        self._steps += 1

        # Score the move and decide whether the game is over.
        reached_goal = (self.row, self.col) == self.GOAL
        reward = self.GOAL_REWARD if reached_goal else self.STEP_COST
        terminated = reached_goal                 # won the game
        truncated = self._steps >= self.MAX_STEPS  # ran out of moves

        info = {"steps": self._steps}
        return self._get_obs(), reward, terminated, truncated, info

    def render(self):
        """Print the grid as text: A = agent, G = goal, . = empty."""
        for r in range(self.SIZE):
            cells = []
            for c in range(self.SIZE):
                if (r, c) == (self.row, self.col):
                    cells.append("A")
                elif (r, c) == self.GOAL:
                    cells.append("G")
                else:
                    cells.append(".")
            print(" ".join(cells))
        print()

    def close(self):
        pass