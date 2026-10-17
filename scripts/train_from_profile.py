"""
Profile-driven Training Runner - Milestone M4.

This file plays two roles from the M4 to-do list:
  * Brick 0 (WRITTEN FIRST, here): the *guardrail* — the finish line M4 must
    clear, written down before any of the profile machinery exists.
  * Brick 5 (the experiment): actually training from a profile, which makes the
    guardrail print PASS. It stacks Bricks 1-4 — Profile loads the YAML,
    RewardCalculator scores the world, make_env builds the Ground.

Both roles are now built. Running this file loads the named profile, trains
PPO on whatever Ground it names, and prints the verdict the referee decides.

Teacher Note: why write the referee before the game?
====================================================
A guardrail is the bar you must clear, written down *before* you start — so you
cannot quietly lower it once the work gets hard. M3 learned this the expensive
way in the other direction: a training run scored +0.905 and looked like a win,
but the agent was blind and the bar had not been written strictly enough to
notice. The bar has to be fixed while you still cannot see how hard the work is
going to be.

The M4 finish line (all three must hold to PASS):
  1. Every profile's agent CLEARLY beats the random baseline measured live in
     that same run — by the margin that profile's own YAML demands.
  2. reset() / step() still return the same shapes they always have. Adding a
     config layer must not bend the Gymnasium contract.
  3. NO PYTHON WAS EDITED between the runs being compared. The command line is
     the only thing that differed.

Condition 3 is the whole milestone. Conditions 1 and 2 say the runs were real;
condition 3 says the *swap* was real.

Teacher Note: one bar shape for three milestones
================================================
The earlier milestones each stated their bar differently:

    M1 (CartPole)          trained >= 2 x baseline        (baseline hardcoded at 22)
    M2 (GridWorld)         trained >= +0.5                (absolute, baseline hardcoded)
    M3 (GridWorld pixels)  trained >= live baseline + 0.40, goal rate >= 80%

Three shapes cannot share one referee, so M4 uses M3's: **beat the baseline
measured live in this run by a stated margin**, plus an optional goal rate for
Grounds that have a goal. The older bars re-express exactly — CartPole's
"2 x 22 = 44" is "baseline + 22" — and they stop depending on a remembered
number, which is what DOC_STANDARD rule 3 asks for. The M1/M2/M3 scripts
themselves are untouched; closed milestones keep the rules they closed under.

Usage:
    python scripts/train_from_profile.py --profile profiles/gridworld.yaml
    python scripts/train_from_profile.py --profile profiles/cartpole.yaml --smoke
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time
from dataclasses import fields
from pathlib import Path

# Print UTF-8 so status glyphs don't crash on Windows consoles (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path so we can import from src/
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from src.gametrainer.factory import make_env
from src.gametrainer.profile import Profile
from src.gametrainer.referee import (
    check_contract_shapes,
    decide_verdict,
    evaluate_greedy,
    measure_random_baseline,
    pass_or_fail,
)
from src.gametrainer.vit_extractor import ViTTinyFeaturesExtractor

# ---------------------------------------------------------------------------
# The bar.
#
# Only the numbers that are the same for EVERY profile live here. Each
# profile's own reward bar (margin, goal rate) lives in its YAML — that is the
# point of the milestone, and hardcoding one here would quietly undo it.
# ---------------------------------------------------------------------------

# Episodes to average when measuring the live random baseline. Matches M3: more
# than M2's 20, so the number everything else is judged against is steady.
BASELINE_EPISODES = 50

# Greedy episodes to judge the trained agent on. Matches M2 and M3.
FINAL_EVAL_EPISODES = 20

# --smoke: a fast wiring check, not a milestone result. A low ceiling is
# enough to prove profile -> env -> PPO -> verdict is genuinely connected,
# without waiting for a real run (~19 min for the pixels profile on CPU).
# PPO always collects one full rollout (its own n_steps) before it can stop,
# so wall-clock stays under a minute even so.
SMOKE_TIMESTEPS = 200
SMOKE_EPISODES = 3


# ---------------------------------------------------------------------------
# Referee piece 1 — the swap proof (the genuinely new one). It is M4-only, so
# it stays here; pieces 2-4 are shared and live in src/gametrainer/referee.py.
# ---------------------------------------------------------------------------

def source_fingerprint() -> str:
    """One hash covering every git-tracked .py file in the repo.

    Teacher Note: this is how "config-only, no code edits" stops being a claim
    and becomes evidence. Every run prints this fingerprint. Two runs that
    printed the SAME fingerprint but trained on DIFFERENT games can only have
    differed in the file named on the command line — there was no other input.

    It hashes file contents rather than asking git whether the tree is clean,
    because what matters is the code that actually ran, not whether it happened
    to be committed at the time. For the same reason it asks git for tracked
    AND untracked files (-c -o), minus whatever .gitignore excludes: a brand
    new, not-yet-committed file is still code that ran, and leaving it out
    would let an edit between two runs go unnoticed — the exact failure this
    function exists to catch.
    """
    listed = subprocess.run(
        ["git", "ls-files", "-z", "-c", "-o", "--exclude-standard", "*.py"],
        cwd=_project_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\0")
    listed = [relpath for relpath in listed if relpath]

    digest = hashlib.sha256()
    for relpath in sorted(listed):
        # The name goes in as well as the bytes, so renaming or deleting a
        # tracked file changes the fingerprint just like editing one does.
        digest.update(relpath.encode("utf-8"))
        path = Path(_project_root, relpath)
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def print_finish_line(live_baseline: float | None = None) -> None:
    """Show the bar this run must clear. Called before training, not after."""
    print("The M4 finish line (all three required to PASS):")
    if live_baseline is None:
        print("  1. Trained reward >= the live baseline + the margin this profile demands")
    else:
        print(f"  1. Trained reward >= the live baseline ({live_baseline:+.2f})"
              " + the margin this profile demands")
    print("  2. reset() -> 2-tuple and step() -> 5-tuple, unchanged")
    print("  3. Source fingerprint identical across the runs being compared")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def print_resolved_profile(profile: Profile, path: str) -> None:
    """Print every field a run used.

    Teacher Note: DOC_STANDARD rule 3 — a run whose settings can't be
    reconstructed from its own printed output is not a result. This is what
    makes that true here: nothing below is guessed or looked up later, it's
    read straight off the Profile the run actually built. Looping over the
    dataclass's own fields means a field added later can never be left out.
    """
    print(f"Profile file:           {path}")
    for field in fields(profile):
        print(f"  {field.name + ':':<22}{getattr(profile, field.name)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="M4 — Train PPO on whichever Ground a profile names.",
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="Path to the profile YAML (e.g. profiles/gridworld.yaml)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Fast wiring check (a few hundred steps), not a milestone result",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 60)
    print("GAMETRAINER — M4: Make It Swappable (profile-driven run)")
    print("=" * 60)
    print()

    profile = Profile.from_yaml(args.profile)
    print_resolved_profile(profile, args.profile)
    print(f"Source fingerprint:    {source_fingerprint()}")
    print()
    if args.smoke:
        print("*** --smoke: wiring check only, NOT a milestone result ***")
        print()

    total_timesteps = SMOKE_TIMESTEPS if args.smoke else profile.total_timesteps
    baseline_episodes = SMOKE_EPISODES if args.smoke else BASELINE_EPISODES
    eval_episodes = SMOKE_EPISODES if args.smoke else FINAL_EVAL_EPISODES

    def env_factory():
        return make_env(profile)

    # Referee piece 2: contract shapes, checked before spending any training time.
    shapes_ok, detail = check_contract_shapes(env_factory())
    print(f"Contract check: {'OK' if shapes_ok else 'BROKEN'} — {detail}")
    print()

    # Referee piece 1: the live baseline, measured now — never remembered.
    print(f"Measuring live random baseline over {baseline_episodes} episodes...")
    live_baseline = measure_random_baseline(env_factory, baseline_episodes)
    print(f"  Live random baseline: {live_baseline:+.2f} reward/episode")
    print()

    print_finish_line(live_baseline)

    # The one branch left in the runner: pixels need CnnPolicy plus the
    # borrowed ViT eyes; everything else is plain numbers, so MlpPolicy.
    # make_env already made every other ground/perception decision.
    if profile.perception == "pixels":
        policy = "CnnPolicy"
        policy_kwargs = {
            "features_extractor_class": ViTTinyFeaturesExtractor,
            "features_extractor_kwargs": {"pretrained": True, "freeze_backbone": True},
        }
    else:
        policy = "MlpPolicy"
        policy_kwargs = None

    train_env = DummyVecEnv([lambda: Monitor(env_factory())])

    print(f"Training PPO ({policy}) for {total_timesteps:,} timesteps...")
    model = PPO(
        policy,
        train_env,
        verbose=1,
        **profile.ppo_settings(),
        policy_kwargs=policy_kwargs,
    )

    started = time.time()
    model.learn(total_timesteps=total_timesteps)
    elapsed = time.time() - started

    model_dir = os.path.join(_project_root, "models", f"ppo_{Path(args.profile).stem}")
    os.makedirs(model_dir, exist_ok=True)
    final_path = os.path.join(model_dir, "final_model")
    model.save(final_path)
    print(f"\nTraining complete in {elapsed / 60:.1f} min. Model saved → {final_path}.zip\n")

    print(f"Running final greedy evaluation ({eval_episodes} episodes)...")
    mean_reward, goal_rate, mean_steps = evaluate_greedy(model, env_factory, eval_episodes)
    passed, lines = decide_verdict(
        mean_reward,
        live_baseline,
        profile.margin_over_baseline,
        shapes_ok,
        goal_rate=goal_rate,
        min_goal_rate=profile.min_goal_rate,
    )

    print()
    print("=" * 60)
    print(f"M4 VERDICT ({args.profile}): {pass_or_fail(passed)}")
    print("=" * 60)
    for line in lines:
        print(line)
    print(f"  Mean steps per episode: {mean_steps:.1f}")
    print(f"  Wall-clock training:    {elapsed / 60:.1f} min for {total_timesteps:,} steps")
    print(f"  Profile:                {args.profile}")
    print("=" * 60)

    train_env.close()

    if args.smoke:
        print("\n(--smoke run: wiring check only — not a milestone result.)")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
