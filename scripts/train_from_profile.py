"""
Profile-driven Training Runner - Milestone M4.

This file plays two roles from the M4 to-do list:
  * Brick 0 (WRITTEN FIRST, here): the *guardrail* — the finish line M4 must
    clear, written down before any of the profile machinery exists.
  * Brick 5 (the experiment): actually training from a profile, which makes the
    guardrail print PASS. It stacks Bricks 1-4 — Profile loads the YAML,
    RewardCalculator scores the world, make_env builds the Ground.

Right now only the referee exists. Running this file prints the bar and then
says, honestly, that there is nothing to grade yet.

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
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

# Print UTF-8 so status glyphs don't crash on Windows consoles (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path so we can import from src/
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)


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


# ---------------------------------------------------------------------------
# Referee piece 1 — the swap proof (the genuinely new one).
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
        ["git", "ls-files", "-c", "-o", "--exclude-standard", "*.py"],
        cwd=_project_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    digest = hashlib.sha256()
    for relpath in sorted(listed):
        # The name goes in as well as the bytes, so renaming or deleting a
        # tracked file changes the fingerprint just like editing one does.
        digest.update(relpath.encode("utf-8"))
        path = Path(_project_root, relpath)
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Referee piece 2 — the contract shapes must be unchanged.
# ---------------------------------------------------------------------------

def check_contract_shapes(env) -> tuple[bool, str]:
    """Confirm reset() -> 2-tuple and step() -> 5-tuple, obs inside the space.

    Teacher Note: this is the one promise the whole project rests on, and M4
    multiplies the ways to break it — every profile is a new chance to build an
    env that is subtly not a Gymnasium env. So this runs for whichever profile
    was loaded, every run, before any training time is spent.
    """
    reset_out = env.reset()
    if not (isinstance(reset_out, tuple) and len(reset_out) == 2):
        return False, "reset() did not return a 2-tuple (obs, info)"
    obs, _info = reset_out
    if not env.observation_space.contains(obs):
        return False, "reset() obs is not inside observation_space"

    step_out = env.step(env.action_space.sample())
    if not (isinstance(step_out, tuple) and len(step_out) == 5):
        return False, "step() did not return a 5-tuple"

    return True, "reset() -> 2-tuple, step() -> 5-tuple, obs in space"


# ---------------------------------------------------------------------------
# Referee piece 3 — measure the random baseline LIVE, never from memory.
# ---------------------------------------------------------------------------

def measure_random_baseline(make_env, episodes: int = BASELINE_EPISODES) -> float:
    """Average reward per episode of a purely random agent on THIS profile's env.

    Teacher Note: takes a factory (something that builds an env) rather than an
    env, because a baseline has to be measured on the very same Ground the agent
    plays. M2 hardcoded -0.3 and the true figure was +0.13; M3 measured live and
    got +0.48 on a Ground that had changed underneath it. Every profile brings
    its own Ground, so every profile brings its own baseline.
    """
    env = make_env()
    total = 0.0
    for _ in range(episodes):
        env.reset()
        terminated = truncated = False
        while not (terminated or truncated):
            _, reward, terminated, truncated, _ = env.step(env.action_space.sample())
            total += reward
    env.close()
    return total / episodes


# ---------------------------------------------------------------------------
# Referee piece 4 — the verdict. Pure logic: numbers in, PASS/FAIL out.
# Brick 5 calls this with the trained agent's numbers.
# ---------------------------------------------------------------------------

def decide_verdict(
    trained_mean_reward: float,
    live_baseline: float,
    margin_over_baseline: float,
    shapes_ok: bool,
    goal_rate: float | None = None,
    min_goal_rate: float | None = None,
) -> tuple[bool, list[str]]:
    """Apply M4's conditions. Returns (passed, printable report lines).

    goal_rate and min_goal_rate are fractions in [0, 1], and both are optional:
    CartPole has no "goal" to reach, so that check simply does not apply there.
    Not applicable must mean not applicable — never a silent pass.
    """
    if min_goal_rate is not None and goal_rate is None:
        raise ValueError(
            "profile demands a goal rate (min_goal_rate="
            f"{min_goal_rate}) but this Ground cannot measure one"
        )

    beats_baseline = trained_mean_reward >= live_baseline + margin_over_baseline
    reaches_goal = min_goal_rate is None or goal_rate >= min_goal_rate
    passed = shapes_ok and beats_baseline and reaches_goal

    def mark(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    lines = [
        f"  Live random baseline:   {live_baseline:+.2f} reward/episode",
        f"  Trained mean reward:    {trained_mean_reward:+.2f} reward/episode",
        f"  [{mark(beats_baseline)}] beats baseline by >= {margin_over_baseline:.2f}"
        f"  (needs >= {live_baseline + margin_over_baseline:+.2f})",
    ]
    if min_goal_rate is None:
        lines.append("  [ -- ] goal rate: not applicable to this Ground")
    else:
        lines.append(
            f"  [{mark(reaches_goal)}] reaches goal in most episodes"
            f"  ({goal_rate * 100:.0f}%, needs >= {min_goal_rate * 100:.0f}%)"
        )
    lines.append(f"  [{mark(shapes_ok)}] reset()/step() shapes unchanged")
    return passed, lines


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

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="M4 — Train PPO on whichever Ground a profile names.",
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="Path to the profile YAML (e.g. profiles/gridworld.yaml)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 60)
    print("GAMETRAINER — M4: Make It Swappable (profile-driven run)")
    print("=" * 60)
    print()
    print(f"Profile requested:  {args.profile}")
    print(f"Source fingerprint: {source_fingerprint()}")
    print()

    print_finish_line()

    # Bricks 1-5 fill this in. Until then the referee exists and the game does
    # not, and saying so plainly beats a stub that pretends to run.
    print("Nothing to grade yet — the referee is built, the runner is not.")
    print("Still to come: Brick 1 (Profile), 2 (RewardCalculator), 3 (make_env),")
    print("               4 (the profile YAMLs), 5 (training).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
