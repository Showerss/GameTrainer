"""
Profile - Milestone M4, Brick 1.

A Profile is one flat .yaml file that names a Ground, a perception mode, and
the reward + PPO numbers to train it with. Loading one is the only thing this
file does -- turning that Ground into an env is Brick 3 (factory.py), and
turning the reward numbers into a score is Brick 2 (rewards.py).

Track A (M4, current). Previously named to avoid collision with Track B's
ConfigLoader (src/gametrainer/config.py), which loaded profiles/<game>/regions.yaml
for the old Stardew screen-scraping prototype. Track B was retired (deleted)
2026-08-04 -- this is now the only "profile" in the repo. See
docs/m4/M4_ToDo.md, "The name collision".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import yaml

GROUNDS = ("cartpole", "gridworld")
PERCEPTIONS = ("numeric", "pixels")
REWARDS = ("builtin", "gridworld")

# Grounds with no pixel Ground built yet (see M4_ToDo.md, scope discipline).
_NO_PIXELS_BUILT_FOR = {"cartpole"}

_REQUIRED_FIELDS = (
    "ground",
    "perception",
    "reward",
    "total_timesteps",
    "learning_rate",
    "n_steps",
    "batch_size",
    "n_epochs",
    "gamma",
    "gae_lambda",
    "clip_range",
    "ent_coef",
    "margin_over_baseline",
)


@dataclass(frozen=True)
class Profile:
    """A validated Ground + reward + PPO description, loaded from one YAML file.

    A dataclass, not a dict: profile.step_cost fails fast (AttributeError) on
    a typo; profile["step_kost"] would fail 3am into a run instead.
    """

    ground: str
    perception: str
    reward: str
    total_timesteps: int
    learning_rate: float
    n_steps: int
    batch_size: int
    n_epochs: int
    gamma: float
    gae_lambda: float
    clip_range: float
    ent_coef: float
    margin_over_baseline: float
    step_cost: Optional[float] = None
    goal_reward: Optional[float] = None
    min_goal_rate: Optional[float] = None

    @classmethod
    def from_yaml(cls, path: str) -> "Profile":
        """Load and validate a profile. Raises ValueError, loudly, at load time."""
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ValueError(
                f"{path}: profile must be a YAML mapping, got {type(raw).__name__}"
            )

        missing = [key for key in _REQUIRED_FIELDS if key not in raw]
        if missing:
            raise ValueError(f"{path}: missing required field(s): {', '.join(missing)}")

        ground = raw["ground"]
        if ground not in GROUNDS:
            raise ValueError(
                f"{path}: unknown ground '{ground}' — legal options: {', '.join(GROUNDS)}"
            )

        perception = raw["perception"]
        if perception not in PERCEPTIONS:
            raise ValueError(
                f"{path}: unknown perception '{perception}' — legal options: "
                f"{', '.join(PERCEPTIONS)}"
            )

        if perception == "pixels" and ground in _NO_PIXELS_BUILT_FOR:
            raise ValueError(
                f"{path}: perception 'pixels' is not supported for ground "
                f"'{ground}' — no pixel Ground has been built for it"
            )

        reward = raw["reward"]
        if reward not in REWARDS:
            raise ValueError(
                f"{path}: unknown reward '{reward}' — legal options: {', '.join(REWARDS)}"
            )

        if reward == "gridworld":
            reward_missing = [k for k in ("step_cost", "goal_reward") if k not in raw]
            if reward_missing:
                raise ValueError(
                    f"{path}: reward 'gridworld' requires field(s): "
                    f"{', '.join(reward_missing)}"
                )

        return cls(
            ground=ground,
            perception=perception,
            reward=reward,
            total_timesteps=raw["total_timesteps"],
            learning_rate=raw["learning_rate"],
            n_steps=raw["n_steps"],
            batch_size=raw["batch_size"],
            n_epochs=raw["n_epochs"],
            gamma=raw["gamma"],
            gae_lambda=raw["gae_lambda"],
            clip_range=raw["clip_range"],
            ent_coef=raw["ent_coef"],
            margin_over_baseline=raw["margin_over_baseline"],
            step_cost=raw.get("step_cost"),
            goal_reward=raw.get("goal_reward"),
            min_goal_rate=raw.get("min_goal_rate"),
        )
