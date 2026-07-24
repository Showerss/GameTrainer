"""
Brick 1 (M3): lock the promise that GridWorld can draw itself.

M2's GridWorld hands out two numbers, (row, col). M3 needs it to hand out a
*picture* instead. This file pins the promises that picture must keep, because
they are the ones that can break silently:

  - The image is exactly (224, 224, 3) uint8. Pretrained ViTs accept nothing
    else, and a wrong shape here surfaces 100 lines deep inside torch.
  - The agent's square looks different from an empty square. If it didn't, the
    agent would be invisible to its own eyes and PPO would learn nothing --
    with no error message anywhere.
  - Moving changes the picture. Same reason: a frozen image trains a blind
    agent, silently.

We are NOT changing the observation here. That is Brick 2's wrapper. So the
last test guards the other direction: the text render() M2 uses is still the
default and still returns None.
"""

import sys
from pathlib import Path

import numpy as np

# Project root = parent of tests/  (so `from src.gametrainer...` works)
_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))
from src.gametrainer.gridworld import GridWorldEnv


def cell_centre(index: int) -> int:
    """Pixel coordinate at the middle of grid row/column `index`.

    The 5 cells split 224 pixels evenly, so cell i covers roughly
    i*44.8 to (i+1)*44.8 and its middle sits at (i + 0.5) * 44.8. Sampling the
    middle keeps the test honest without copying the drawing code's exact
    boundary math.
    """
    return int((index + 0.5) * 224 / GridWorldEnv.SIZE)


def pixel_at(image, row, col):
    """The RGB colour drawn for grid square (row, col)."""
    return image[cell_centre(row), cell_centre(col)]


def test_rgb_array_render_returns_224x224x3_uint8():
    """The promise the ViT depends on: exact shape, exact dtype."""
    env = GridWorldEnv(render_mode="rgb_array")
    env.reset()

    image = env.render()

    assert isinstance(image, np.ndarray)
    assert image.shape == (224, 224, 3)
    assert image.dtype == np.uint8


def test_agent_goal_and_empty_squares_are_different_colours():
    """The agent must be visible to its own eyes -- three distinct colours."""
    env = GridWorldEnv(render_mode="rgb_array")
    env.reset()  # agent starts at START (0, 0); goal is at GOAL (4, 4)

    image = env.render()

    agent_colour = pixel_at(image, *GridWorldEnv.START)
    goal_colour = pixel_at(image, *GridWorldEnv.GOAL)
    empty_colour = pixel_at(image, 2, 2)  # middle square: neither start nor goal

    assert not np.array_equal(agent_colour, empty_colour)
    assert not np.array_equal(goal_colour, empty_colour)
    assert not np.array_equal(agent_colour, goal_colour)


def test_image_changes_after_the_agent_moves():
    """A picture that never changes would train a blind agent, silently."""
    env = GridWorldEnv(render_mode="rgb_array")
    env.reset()

    before = env.render()
    env.step(GridWorldEnv.DOWN)
    after = env.render()

    assert not np.array_equal(before, after)


def test_agent_square_follows_the_agent():
    """Stronger than 'the image changed': the agent colour moved with the agent."""
    env = GridWorldEnv(render_mode="rgb_array")
    env.reset()

    agent_colour = pixel_at(env.render(), *GridWorldEnv.START)
    env.step(GridWorldEnv.DOWN)  # (0, 0) -> (1, 0)
    image = env.render()

    assert np.array_equal(pixel_at(image, 1, 0), agent_colour)
    assert not np.array_equal(pixel_at(image, 0, 0), agent_colour)


def test_text_render_is_still_the_default():
    """M2's behaviour is untouched: no render_mode still means printed text."""
    env = GridWorldEnv()
    env.reset()

    assert env.render() is None