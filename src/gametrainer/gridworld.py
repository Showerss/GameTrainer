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
from gymnasium.wrappers import TimeLimit


class GridWorldEnv(gym.Env):
    """A 5x5 walk-to-the-goal world that follows the Gymnasium contract."""

    metadata = {"render_modes": ["human", "rgb_array"]}

    # World shape (fixed for M2).
    SIZE = 5                 # 5x5 grid
    START = (0, 0)           # top-left corner
    GOAL = (4, 4)            # bottom-right corner
    MAX_STEPS = 100          # truncation cap: out of moves after this many

    # Drawing numbers (M3). 224x224 is not a style choice: pretrained ViTs
    # accept exactly that size. The 5x5 board is blown up to fill it, so the
    # picture is deliberately chunky -- 45-pixel squares, no smoothing.
    IMAGE_SIZE = 224
    EMPTY_COLOR = (40, 40, 40)       # dark grey
    GOAL_COLOR = (0, 200, 0)         # green
    AGENT_COLOR = (255, 255, 255)    # white

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
        # Normalize action (SB3 may return a 1-element array) and clamp to Discrete range.
        action_arr = np.asarray(action)
        if action_arr.shape != ():
            action = action_arr.item()
        action = int(np.clip(action, 0, self.action_space.n - 1))

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
        terminated = reached_goal  # won the game
        truncated = (self._steps >= self.MAX_STEPS) and not reached_goal  # ran out of moves

        info = {"steps": self._steps}
        return self._get_obs(), reward, terminated, truncated, info

    def _render_rgb(self):
        """Draw the grid as a (224, 224, 3) uint8 picture.

        Start from an all-empty canvas, then paint the two squares that matter.
        Each grid square owns a block of pixels: square i covers columns
        i*224//5 up to (i+1)*224//5. Integer division keeps the blocks exact
        and gap-free even though 224 doesn't divide evenly by 5.
        """
        image = np.full(
            (self.IMAGE_SIZE, self.IMAGE_SIZE, 3), self.EMPTY_COLOR, dtype=np.uint8
        )
        # Goal first, agent second: when the agent lands ON the goal, it paints
        # over the green and stays visible.
        squares = ((self.GOAL, self.GOAL_COLOR), ((self.row, self.col), self.AGENT_COLOR))
        for (r, c), color in squares:
            r0, r1 = r * self.IMAGE_SIZE // self.SIZE, (r + 1) * self.IMAGE_SIZE // self.SIZE
            c0, c1 = c * self.IMAGE_SIZE // self.SIZE, (c + 1) * self.IMAGE_SIZE // self.SIZE
            image[r0:r1, c0:c1] = color
        return image

    def render(self):
        """Show the grid. Picture if render_mode="rgb_array", else printed text."""
        if self.render_mode == "rgb_array":
            return self._render_rgb()

        # Text mode (the M2 default): A = agent, G = goal, . = empty.
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


class RandomStart(gym.Wrapper):
    """Make GridWorld impossible to solve blind: random start, goal off the corner.

    Why this exists (M3, Brick 4) -- the finding that forced it.
    The first pixels-only training run scored +0.905, and the agent was totally
    BLIND. Its action probabilities were identical at every square: a fixed
    53% DOWN / 47% RIGHT coin flip. A hand-written blind agent playing that same
    coin flip scored +0.907. So the picture was never used, and the number
    proved nothing about the eyes.

    Two things made the original maze solvable blind, and BOTH have to go:

      1. The start was always (0, 0), so one memorised route always worked.
      2. The goal sat in the CORNER (4, 4). This is the sneaky one. "Always move
         down or right" funnels you into the bottom-right corner from ANY square,
         because walking into a wall just stops you rather than costing you the
         run. Randomising the start alone does not help at all -- measured, a
         blind agent still scored +0.947 with a 100% goal rate.

    Moving the goal off the corner is what actually bites. With the goal in the
    middle, overshooting is a real mistake: a blind agent drops to a 13% goal
    rate while an agent that can see its own square gets 100%. That gap is the
    room in which the eyes can prove they work.

    GridWorldEnv is not edited -- this wrapper sits around it. Setting GOAL on
    the instance shadows the class attribute, so both step() and the drawing
    pick it up. Put PixelObservation on the OUTSIDE of this one: this wrapper
    places everything first, then the picture is drawn from where things landed.
    """

    def __init__(self, env, goal=None):
        super().__init__(env)
        # Centre of the board by default -- the corner is what made blind play work.
        self.goal = goal if goal is not None else (env.unwrapped.SIZE // 2,) * 2

    def reset(self, **kwargs):
        """Start a normal episode, then place the goal and the agent."""
        _obs, info = self.env.reset(**kwargs)
        grid = self.unwrapped
        grid.GOAL = self.goal

        # Any square except the goal -- starting on it means the episode is won
        # before it begins, which teaches nothing and inflates mean reward.
        row, col = self.goal
        while (row, col) == self.goal:
            row = int(self.np_random.integers(grid.SIZE))
            col = int(self.np_random.integers(grid.SIZE))

        grid.row, grid.col = row, col
        return grid._get_obs(), info


# How many moves an episode gets in the M3 vision task.
#
# Teacher Note: why 25 and not GridWorldEnv's own 100.
# 100 moves is enough for a random walk to wander into all 25 squares, so a
# random agent reached a centre goal 94% of the time -- and a guardrail that a
# random agent passes grades nothing. Measured at a 25-move budget instead:
#   random agent  53% goal rate    blind agent 12%    agent that can see 100%
# A seeing agent needs at most 4 moves from the farthest corner, so 25 is still
# roomy. This number was chosen to make the referee DISCRIMINATE, not to make
# passing easier -- random and blind agents both fail it.
VISION_TASK_STEP_CAP = 25


def make_vision_task(render_mode="rgb_array"):
    """The Ground M3 trains on: a GridWorld that cannot be solved without looking.

    Defined here, in one place, because the training script and the tests must
    agree on it exactly. Measuring the bar on a different game than the one being
    played is the specific mistake this milestone already made once.

    Two wrapper layers (only one touches GridWorldEnv directly):
      RandomStart  -- random square each episode, goal moved off the corner
      TimeLimit    -- Gymnasium's own step-budget wrapper
    """
    return TimeLimit(
        RandomStart(GridWorldEnv(render_mode=render_mode)),
        max_episode_steps=VISION_TASK_STEP_CAP,
    )