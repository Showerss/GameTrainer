"""
Brick 2 (M3): lock the promises of the pixel wrapper.

Brick 1 taught GridWorld to *draw* itself. Brick 2 makes that drawing the thing
the agent actually receives. The wrapper sits around GridWorldEnv and swaps the
observation from two numbers, (row, col), to the picture -- and changes nothing
else.

The promises worth pinning here are all at the boundary, because that is where
this can break in silence:

  - The advertised observation_space really is the image box. PPO builds its
    network from this space, so if it lies, the failure surfaces deep inside
    torch with a shape error that names no file of ours.
  - reset() still returns a 2-tuple and step() still returns a 5-tuple. This is
    the Gymnasium contract -- the one promise the whole project rests on.
  - The observation is the *live* picture, not a stale first frame. A frozen
    image trains a blind agent, and nothing anywhere would raise.
  - GridWorldEnv itself is untouched. If wrapping quietly mutated the env, M2's
    swappability claim would be a lie.
"""

import sys
from pathlib import Path

import numpy as np

# Project root = parent of tests/  (so `from src.gametrainer...` works)
_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))
from src.gametrainer.gridworld import GridWorldEnv
from src.gametrainer.perception import PixelObservation


def make_env():
    """A GridWorld that draws itself, wrapped so the drawing IS the observation."""
    return PixelObservation(GridWorldEnv(render_mode="rgb_array"))


def cell_centre(index: int) -> int:
    """Pixel coordinate at the middle of grid row/column `index`."""
    return int((index + 0.5) * 224 / GridWorldEnv.SIZE)


def pixel_at(image, row, col):
    """The RGB colour drawn for grid square (row, col)."""
    return image[cell_centre(row), cell_centre(col)]


def test_observation_space_is_the_image_box():
    """The space PPO builds its network from: 0..255, (224,224,3), uint8."""
    env = make_env()

    assert env.observation_space.shape == (224, 224, 3)
    assert env.observation_space.dtype == np.uint8
    assert env.observation_space.low.min() == 0
    assert env.observation_space.high.max() == 255


def test_reset_returns_two_tuple_whose_obs_is_the_picture():
    """The M2 contract shape is unchanged -- only what's inside the obs moved."""
    env = make_env()
    result = env.reset()

    assert isinstance(result, tuple) and len(result) == 2
    obs, info = result
    assert isinstance(info, dict)
    assert obs.shape == (224, 224, 3)
    assert obs.dtype == np.uint8
    assert env.observation_space.contains(obs)


def test_step_returns_five_tuple_whose_obs_is_the_picture():
    """Same again for step(): 5-tuple in, 5-tuple out, obs is now an image."""
    env = make_env()
    env.reset()
    result = env.step(env.action_space.sample())

    assert isinstance(result, tuple) and len(result) == 5
    obs, reward, terminated, truncated, info = result
    assert env.observation_space.contains(obs)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_observation_tracks_the_agent():
    """The obs is the live picture: move down, the white square moves down.

    Weaker versions of this test ("the image changed") would still pass if the
    wrapper handed back a stale frame from the previous step. Checking that the
    agent colour landed on the new square is the promise that actually matters.
    """
    env = make_env()
    obs, _ = env.reset()  # agent at START (0, 0)

    agent_colour = pixel_at(obs, *GridWorldEnv.START)
    obs, _, _, _, _ = env.step(GridWorldEnv.DOWN)  # (0, 0) -> (1, 0)

    assert np.array_equal(pixel_at(obs, 1, 0), agent_colour)
    assert not np.array_equal(pixel_at(obs, 0, 0), agent_colour)


def test_wrapping_leaves_gridworld_untouched():
    """The whole point of a wrapper: the env underneath never learns it exists."""
    inner = GridWorldEnv(render_mode="rgb_array")
    PixelObservation(inner)

    assert inner.observation_space.shape == (2,)  # still the M2 (row, col) box


def test_wrapping_a_non_drawing_env_fails_loudly():
    """Without render_mode="rgb_array" there is no picture to hand over.

    Left unchecked, the env would quietly serve None as the observation and the
    crash would land somewhere far away with no hint of the real cause.
    """
    import pytest

    with pytest.raises(ValueError):
        PixelObservation(GridWorldEnv())  # text render mode -- draws nothing


def test_check_env_passes():
    """The official Gymnasium contract checker runs clean on the wrapped env.

    Skips automatically if stable_baselines3 isn't installed (optional 'rl'
    extra). Install with: pip install -e ".[rl]"
    """
    import pytest

    sb3_checker = pytest.importorskip("stable_baselines3.common.env_checker")
    sb3_checker.check_env(make_env())
