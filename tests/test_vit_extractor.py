"""
Brick 3 (M3): lock the promise where the borrowed eyes meet the brain.

Brick 2 made the observation a 224x224x3 picture -- 150,528 numbers. PPO's
decision-making layers want a short list, not a wall of pixels. The ViT sits
between them: picture in, 192-number summary out. That summary is called a
*feature vector*, and 192 is ViT-Tiny's width.

The promises pinned here are the ones that fail silently or fail far away:

  - One observation in, exactly 192 numbers out. Get this wrong and the error
    surfaces deep inside torch, naming no file of ours.
  - features_dim (the number SB3 *reads* to size the next layer) matches the
    number the extractor actually *produces*. These are two separate values in
    the code and nothing forces them to agree.
  - Two different pictures give two different summaries. If every frame mapped
    to the same vector the agent would be blind, PPO would learn nothing, and
    no error would be raised anywhere.
  - A frozen backbone really has zero trainable parameters. Unfrozen still
    "works" -- it just trains ~30x slower on CPU, which looks like bad luck
    rather than a bug.

No training here, on purpose: one forward pass, and pretrained=False so the
test needs no download and no network. The output *width* is decided by the
architecture, not by the weights -- so untrained weights pin the same promise.
Whether the real ImageNet weights load is Brick 4's problem, and it will fail
loudly the first time it runs.
"""

import sys
from pathlib import Path

import pytest

# Project root = parent of tests/  (so `from src.gametrainer...` works)
_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))

# torch and timm live in the optional 'rl' extra. Install: pip install -e ".[rl]"
torch = pytest.importorskip("torch")
pytest.importorskip("timm")

from src.gametrainer.gridworld import GridWorldEnv
from src.gametrainer.perception import PixelObservation
from src.gametrainer.vit_extractor import ViTTinyFeaturesExtractor

# ViT-Tiny's summary width. This is the number PPO's next layer is built around.
VIT_TINY_FEATURES = 192


def make_env():
    """The Brick 2 env: GridWorld whose observation is the picture."""
    return PixelObservation(GridWorldEnv(render_mode="rgb_array"))


def make_extractor(env):
    """The extractor exactly as M3 uses it: ViT-Tiny, frozen, no download."""
    return ViTTinyFeaturesExtractor(
        env.observation_space, pretrained=False, freeze_backbone=True
    )


def as_sb3_batch(obs):
    """Turn one env observation into the tensor SB3 hands the extractor.

    SB3 does two things to an image observation before the extractor sees it:
      1. moves the colour channel to the front, (224,224,3) -> (3,224,224)
      2. divides by 255 so the values land in 0.0..1.0
    ...and it always passes a *batch*, so we add a leading 1 = "one image".
    Feeding the extractor anything else here would test a path SB3 never uses.
    """
    tensor = torch.as_tensor(obs).permute(2, 0, 1).float() / 255.0
    return tensor.unsqueeze(0)  # (3,224,224) -> (1,3,224,224)


def test_one_observation_becomes_a_192_wide_feature_vector():
    """The promise the whole brick exists for: picture in, 192 numbers out."""
    env = make_env()
    extractor = make_extractor(env)
    obs, _ = env.reset()

    with torch.no_grad():
        features = extractor(as_sb3_batch(obs))

    assert features.shape == (1, VIT_TINY_FEATURES)


def test_advertised_width_matches_the_real_output():
    """features_dim is a label; the forward pass is the truth. They must agree.

    SB3 reads features_dim once to decide how big to build the next layer. It
    never checks it against reality, so a stale label is a silent trap.
    """
    env = make_env()
    extractor = make_extractor(env)
    obs, _ = env.reset()

    with torch.no_grad():
        features = extractor(as_sb3_batch(obs))

    assert extractor.features_dim == features.shape[1]


def test_different_pictures_give_different_summaries():
    """The agent must not be blind: move, and the summary must change."""
    env = make_env()
    extractor = make_extractor(env)

    start_obs, _ = env.reset()             # agent at (0, 0)
    moved_obs, _, _, _, _ = env.step(GridWorldEnv.DOWN)  # agent at (1, 0)

    with torch.no_grad():
        start_features = extractor(as_sb3_batch(start_obs))
        moved_features = extractor(as_sb3_batch(moved_obs))

    assert not torch.allclose(start_features, moved_features)


def test_frozen_backbone_has_no_trainable_parameters():
    """Borrowed eyes stay borrowed -- and that is what makes CPU training viable."""
    env = make_env()
    extractor = make_extractor(env)

    trainable = [p for p in extractor.parameters() if p.requires_grad]

    assert trainable == []
