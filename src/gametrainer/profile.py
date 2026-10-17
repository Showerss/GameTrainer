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
from numbers import Real

import yaml

GROUNDS = ("cartpole", "gridworld", "minesweeper")
PERCEPTIONS = ("numeric", "pixels")
REWARDS = ("builtin", "gridworld", "minesweeper")
_SUPPORTED_REWARD_BY_GROUND = {
    "cartpole": "builtin",
    "gridworld": "gridworld",
    "minesweeper": "minesweeper",
}

# Grounds with no pixel Ground built yet (see M4_ToDo.md, scope discipline).
_NO_PIXELS_BUILT_FOR = {"cartpole", "minesweeper"}

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

_OPTIONAL_FIELDS = {
    "step_cost",
    "goal_reward",
    "min_goal_rate",
    "safe_reveal_reward",
    "mine_penalty",
    "win_reward",
}

# The reward numbers each reward kind needs. "builtin" (CartPole) needs none.
_FIELDS_FOR_REWARD = {
    "gridworld": ("step_cost", "goal_reward"),
    "minesweeper": ("safe_reveal_reward", "mine_penalty", "win_reward"),
}

# The Profile fields that are handed straight to SB3's PPO, under the same names.
_PPO_FIELDS = (
    "learning_rate",
    "n_steps",
    "batch_size",
    "n_epochs",
    "gamma",
    "gae_lambda",
    "clip_range",
    "ent_coef",
)


def _require_real(path: str, raw: dict, field: str) -> float:
    """Return one numeric field, or fail loudly if YAML gave us junk."""
    value = raw[field]
    if value is None or isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{path}: '{field}' must be a number, got {value!r}")
    return float(value)


def _require_positive(path: str, raw: dict, field: str):
    """Return one field unchanged if it is a number above 0, else fail loudly."""
    value = raw[field]
    if isinstance(value, bool) or not isinstance(value, Real) or value <= 0:
        raise ValueError(f"{path}: '{field}' must be > 0, got {value!r}")
    return value


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
    step_cost: float | None = None
    goal_reward: float | None = None
    min_goal_rate: float | None = None
    safe_reveal_reward: float | None = None
    mine_penalty: float | None = None
    win_reward: float | None = None

    @classmethod
    def from_yaml(cls, path: str) -> Profile:
        """Load and validate a profile. Raises ValueError, loudly, at load time."""
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ValueError(  # noqa: TRY004 - ValueError required by profile contract & test_profile.py
                f"{path}: profile must be a YAML mapping, got {type(raw).__name__}"
            )

        allowed_fields = set(_REQUIRED_FIELDS) | _OPTIONAL_FIELDS
        unknown = sorted(set(raw) - allowed_fields)
        if unknown:
            raise ValueError(f"{path}: unknown field(s): {', '.join(unknown)}")

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

        expected_reward = _SUPPORTED_REWARD_BY_GROUND[ground]
        if reward != expected_reward:
            raise ValueError(
                f"{path}: ground '{ground}' only supports reward '{expected_reward}', "
                f"got '{reward}'"
            )

        # The reward numbers this reward kind needs; any it doesn't stay None.
        needed = _FIELDS_FOR_REWARD.get(reward, ())
        reward_missing = [k for k in needed if k not in raw]
        if reward_missing:
            raise ValueError(
                f"{path}: reward '{reward}' requires field(s): "
                f"{', '.join(reward_missing)}"
            )
        reward_numbers = {k: _require_real(path, raw, k) for k in needed}

        total_timesteps = _require_positive(path, raw, "total_timesteps")
        learning_rate = _require_positive(path, raw, "learning_rate")

        gamma = raw["gamma"]
        if (
            isinstance(gamma, bool)
            or not isinstance(gamma, Real)
            or not (0.0 < gamma <= 1.0)
        ):
            raise ValueError(
                f"{path}: 'gamma' must be between 0 (exclusive) and 1 (inclusive), got {gamma!r}"
            )

        min_goal_rate = raw.get("min_goal_rate")
        if min_goal_rate is not None:
            if ground in ("cartpole", "minesweeper"):
                raise ValueError(
                    f"{path}: 'min_goal_rate' is not supported for ground '{ground}' "
                    f"— {ground} has no discrete goal cell to measure"
                )
            min_goal_rate = _require_real(path, raw, "min_goal_rate")
            if not (0.0 <= min_goal_rate <= 1.0):
                raise ValueError(
                    f"{path}: 'min_goal_rate' must be between 0 and 1, got {min_goal_rate}"
                )

        return cls(
            ground=ground,
            perception=perception,
            reward=reward,
            total_timesteps=total_timesteps,
            learning_rate=learning_rate,
            n_steps=raw["n_steps"],
            batch_size=raw["batch_size"],
            n_epochs=raw["n_epochs"],
            gamma=gamma,
            gae_lambda=raw["gae_lambda"],
            clip_range=raw["clip_range"],
            ent_coef=raw["ent_coef"],
            margin_over_baseline=raw["margin_over_baseline"],
            min_goal_rate=min_goal_rate,
            **reward_numbers,
        )

    def ppo_settings(self) -> dict:
        """The PPO numbers from this profile, ready for PPO(..., **settings)."""
        return {name: getattr(self, name) for name in _PPO_FIELDS}
