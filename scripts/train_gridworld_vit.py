"""
GridWorld-with-ViT Training Script - Milestone M3.

This file plays two roles from the M3 to-do list:
  * Brick 0 (WRITTEN FIRST, here): the *guardrail* — the finish line M3 must
    clear, written down before any of the pixel work exists.
  * Brick 4 (the experiment): training on pixels, which makes the guardrail
    print PASS. It stacks Bricks 1-3 — GridWorld draws itself, the wrapper
    makes that drawing the observation, the ViT turns it into 192 numbers.

Teacher Note: why write the referee before the game?
====================================================
A guardrail is the bar you must clear, written down *before* you start — so you
can't quietly lower it once the work gets hard. M2 made the opposite mistake: it
hardcoded the random baseline as -0.3 in train_gridworld.py, and that number was
just wrong. The real live baseline on this grid is about +0.13. If your bar is a
guess, "beating the baseline" proves nothing.

So this script's #1 job is to MEASURE the baseline live, every run, and to state
in plain code exactly what PASS means. When Brick 4 plugs in the pixel-trained
agent, it calls decide_verdict() below — the bar is already fixed.

The M3 finish line (all three must hold to PASS):
  1. The pixels-only agent's mean reward CLEARLY beats the random baseline that
     we measure live in this same run.
  2. The agent reaches the goal in MOST greedy evaluation episodes.
  3. reset() / step() still return the same shapes they did in M2
     (reset -> 2-tuple, step -> 5-tuple). Swapping in a picture must not break
     the Gymnasium contract.

Usage:
    python scripts/train_gridworld_vit.py                # default: 20,000 steps
    python scripts/train_gridworld_vit.py --steps 40000  # longer run, if it falls short
"""

import argparse
import os
import sys
import time

# Print UTF-8 so status glyphs (>=, checkmarks) don't crash on Windows consoles (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path so we can import from src/
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from src.gametrainer.gridworld import make_vision_task
from src.gametrainer.perception import PixelObservation
from src.gametrainer.vit_extractor import ViTTinyFeaturesExtractor

# ---------------------------------------------------------------------------
# The bar (named so it is impossible to miss and easy to tune later).
# ---------------------------------------------------------------------------

# Episodes to average when measuring the live random baseline. More than M2's 20
# so the number is steady — this is the value everything else is judged against.
BASELINE_EPISODES = 50

# Greedy episodes to judge the *trained* agent on.
FINAL_EVAL_EPISODES = 20

# Condition 2: "reaches the goal in MOST greedy episodes." Most = at least 80%.
GOAL_RATE_TO_PASS = 0.80

# Condition 1: "CLEARLY beats" the live baseline. Reaching the goal via a short
# path scores ~+0.93 and the live baseline is ~+0.13, so a margin of 0.40 above
# the measured baseline means the agent genuinely learned the route, not noise.
MARGIN_OVER_BASELINE = 0.40


# ---------------------------------------------------------------------------
# Training settings (Brick 4).
#
# Teacher Note: why these differ from train_gridworld.py's.
# The ViT is the expensive part, and PPO runs it once per step it collects PLUS
# once per step per training epoch. So the total picture-viewing work is roughly
#     timesteps x (1 + n_epochs)
# On this CPU the ViT handles ~150 pictures/second, which is what turns those
# numbers into minutes. Cutting n_epochs from M2's 10 to 4 roughly halves the
# wall clock; a smaller n_steps then buys back more frequent updates for free,
# because it does not change the total work at all.
# ---------------------------------------------------------------------------

DEFAULT_TIMESTEPS = 20_000
N_STEPS = 512        # steps collected before each update (M2 used 2048)
BATCH_SIZE = 64      # mini-batch size within an update (same as M2)
N_EPOCHS = 4         # passes over each batch (M2 used 10 — this is the cost lever)
LEARNING_RATE = 3e-4  # unchanged from M2: the brain is not what we are changing

MODEL_DIR = os.path.join(_project_root, "models", "ppo_gridworld_vit")


# ---------------------------------------------------------------------------
# The pixel env: Brick 1 (GridWorld draws itself) + Brick 2 (the drawing IS the
# observation), wrapped around the vision task. GridWorldEnv is not edited.
#
# Teacher Note: why the Ground had to change before this could mean anything.
# The first run of this script scored +0.905 with a completely BLIND agent. Its
# action probabilities were identical at every square — a fixed 53% DOWN / 47%
# RIGHT coin flip — and a hand-written blind agent playing that same coin flip
# scored +0.907. The old maze simply did not require eyes: from any square,
# "down or right" funnels you into the corner goal because walls stop you
# instead of costing you the run, so PPO took that cheaper path and ignored the
# ViT entirely. make_vision_task() is the fix; see gridworld.py for what it
# changes and the numbers behind each choice.
#
# Order matters: the task is INSIDE, so it places everything first; then
# PixelObservation draws the picture from where things actually landed.
# ---------------------------------------------------------------------------

def make_task():
    """The Ground itself: a GridWorld that cannot be solved without looking."""
    return make_vision_task()


def make_pixel_env() -> PixelObservation:
    """GridWorld seen only as a picture — no (row, col) reaches the agent."""
    return PixelObservation(make_task())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="M3 — Train PPO on GridWorld pixels through a frozen ViT.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=DEFAULT_TIMESTEPS,
        help=f"Total training timesteps (default: {DEFAULT_TIMESTEPS:,})",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Referee piece 1 — measure the random baseline LIVE (the M2 hardcode, fixed).
# ---------------------------------------------------------------------------

def measure_random_baseline(episodes: int = BASELINE_EPISODES) -> float:
    """Average reward per episode of a purely random agent on GridWorld.

    Teacher Note: a random agent ignores what it sees — it just calls
    action_space.sample(). So the reward it earns is identical whether the
    observation is (row, col) numbers or a picture, and we can skip the pixel
    wrapper here.

    What we can NOT skip is make_task(). The baseline has to be measured on the
    very same Ground the agent plays, and the random start changed that Ground —
    starting next to the goal is much easier than starting in the far corner, so
    the bar moves with it. Measuring the bar on a different game than the one
    being graded is exactly the M2 mistake this whole guardrail exists to avoid.
    """
    env = make_task()
    total = 0.0
    for _ in range(episodes):
        env.reset()
        terminated = truncated = False
        while not (terminated or truncated):
            action = env.action_space.sample()
            _, reward, terminated, truncated, _ = env.step(action)
            total += reward
    env.close()
    return total / episodes


# ---------------------------------------------------------------------------
# Referee piece 2 — the M2 contract shapes must be unchanged.
# ---------------------------------------------------------------------------

def check_contract_shapes(env) -> tuple[bool, str]:
    """Confirm reset() -> 2-tuple and step() -> 5-tuple, obs inside the space.

    Teacher Note: this is the one promise the whole project rests on. M3 swaps
    the *observation* from numbers to a picture, but the tuple shapes of reset()
    and step() must not move. We check the plain M2 env here; Brick 4 will run
    the exact same check on the pixel-wrapped env to prove the swap kept faith.
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
# Referee piece 3 — the verdict. Pure logic: numbers in, PASS/FAIL out.
# Brick 4 calls this with the trained agent's numbers.
# ---------------------------------------------------------------------------

def decide_verdict(
    trained_mean_reward: float,
    goal_rate: float,
    live_baseline: float,
    shapes_ok: bool,
) -> tuple[bool, list[str]]:
    """Apply the three M3 conditions. Returns (passed, printable report lines).

    goal_rate is a fraction in [0, 1] (e.g. 0.9 == reached the goal 90% of the
    greedy evaluation episodes).
    """
    beats_baseline = trained_mean_reward >= live_baseline + MARGIN_OVER_BASELINE
    reaches_goal = goal_rate >= GOAL_RATE_TO_PASS
    passed = shapes_ok and beats_baseline and reaches_goal

    def mark(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    lines = [
        f"  Live random baseline:   {live_baseline:+.2f} reward/episode",
        f"  Trained mean reward:    {trained_mean_reward:+.2f} reward/episode",
        f"  [{mark(beats_baseline)}] beats baseline by >= {MARGIN_OVER_BASELINE:.2f}"
        f"  (needs >= {live_baseline + MARGIN_OVER_BASELINE:+.2f})",
        f"  [{mark(reaches_goal)}] reaches goal in most episodes"
        f"  ({goal_rate * 100:.0f}%, needs >= {GOAL_RATE_TO_PASS * 100:.0f}%)",
        f"  [{mark(shapes_ok)}] reset()/step() shapes unchanged from M2",
    ]
    return passed, lines


def evaluate_greedy(model, episodes: int = FINAL_EVAL_EPISODES):
    """Play greedy episodes on pixels; return (mean_reward, goal_rate, mean_steps).

    Teacher Note: "greedy" (deterministic=True) means the agent always takes the
    move it currently thinks is best, with no random exploration mixed in. That
    is the fair way to ask "what did it actually learn?" — exploration is a
    training aid, not part of the skill we are grading.
    """
    env = make_pixel_env()
    rewards, steps_list, goals = [], [], 0

    for _ in range(episodes):
        obs, _ = env.reset()
        terminated = truncated = False
        ep_reward = 0.0
        while not (terminated or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            ep_reward += reward
        goals += int(terminated)  # GridWorld only terminates by reaching the goal
        rewards.append(ep_reward)
        steps_list.append(info["steps"])

    env.close()
    return sum(rewards) / episodes, goals / episodes, sum(steps_list) / episodes


def print_finish_line(live_baseline: float) -> None:
    """Show the concrete bar this run must clear, given the measured baseline."""
    print("The M3 finish line (all three required to PASS):")
    print(
        f"  1. Trained reward >= {live_baseline + MARGIN_OVER_BASELINE:+.2f}"
        f"  (live baseline {live_baseline:+.2f}  +  {MARGIN_OVER_BASELINE:.2f} margin)"
    )
    print(f"  2. Reaches the goal in >= {GOAL_RATE_TO_PASS * 100:.0f}% of "
          f"{FINAL_EVAL_EPISODES} greedy episodes")
    print("  3. reset() -> 2-tuple and step() -> 5-tuple, unchanged from M2")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()

    print("=" * 60)
    print("GAMETRAINER — M3: Add the Eyes (pixels-only GridWorld)")
    print("=" * 60)
    print()

    # Referee piece 2: the contract shapes — now checked on the PIXEL env. This
    # is the promise M3 exists to keep: the observation became a picture, but
    # reset() and step() hand back the same tuple shapes they did in M2.
    shapes_ok, detail = check_contract_shapes(make_pixel_env())
    print(f"Contract check: {'OK' if shapes_ok else 'BROKEN'} — {detail}")
    print()

    # Referee piece 1: the live baseline (never hardcoded).
    print(f"Measuring live random baseline over {BASELINE_EPISODES} episodes...")
    live_baseline = measure_random_baseline()
    print(f"  Live random baseline: {live_baseline:+.2f} reward/episode")
    print()

    # State the bar this run must clear.
    print_finish_line(live_baseline)

    # -------------------------------------------------------------------
    # Build the agent. The ONLY thing that changed from M2 is what goes in
    # the front: "CnnPolicy" tells PPO the observation is an image, and
    # policy_kwargs swaps its stock image reader for our borrowed ViT eyes.
    # The decision-making layers behind it are untouched.
    # -------------------------------------------------------------------
    # Monitor is a bookkeeping wrapper: it changes nothing about the env, it just
    # records each finished episode's reward so SB3 can print rollout/ep_rew_mean.
    # Without it a ten-minute run shows no sign of whether the agent is improving.
    train_env = DummyVecEnv([lambda: Monitor(make_pixel_env())])

    print(f"Training PPO on pixels for {args.steps:,} timesteps...")
    model = PPO(
        "CnnPolicy",
        train_env,
        verbose=1,               # SB3 prints ep_rew_mean each rollout — watch it rise
        learning_rate=LEARNING_RATE,
        n_steps=N_STEPS,
        batch_size=BATCH_SIZE,
        n_epochs=N_EPOCHS,
        policy_kwargs={
            "features_extractor_class": ViTTinyFeaturesExtractor,
            "features_extractor_kwargs": {
                "pretrained": True,       # borrowed ImageNet eyes
                "freeze_backbone": True,  # borrowed eyes stay borrowed
            },
        },
    )

    started = time.time()
    model.learn(total_timesteps=args.steps)
    elapsed = time.time() - started

    os.makedirs(MODEL_DIR, exist_ok=True)
    final_path = os.path.join(MODEL_DIR, "final_model")
    model.save(final_path)
    print(f"\nTraining complete in {elapsed / 60:.1f} min. Model saved → {final_path}.zip\n")

    # -------------------------------------------------------------------
    # The verdict, judged by the rules Brick 0 fixed before any of this existed.
    # -------------------------------------------------------------------
    print(f"Running final greedy evaluation ({FINAL_EVAL_EPISODES} episodes)...")
    mean_reward, goal_rate, mean_steps = evaluate_greedy(model)
    passed, lines = decide_verdict(mean_reward, goal_rate, live_baseline, shapes_ok)

    print()
    print("=" * 60)
    print(f"M3 VERDICT: {'PASS' if passed else 'FAIL'}")
    print("=" * 60)
    for line in lines:
        print(line)
    # "8" here used to be the corner-to-corner distance of the old fixed-start
    # maze. With a random start and a centre goal the perfect route averages
    # 2.5 moves, and any single batch of episodes can land either side of that
    # depending on which starting squares came up.
    print(f"  Mean steps to finish:   {mean_steps:.1f}  "
          f"(a perfect agent averages ~2.5 from a random start)")
    print(f"  Wall-clock training:    {elapsed / 60:.1f} min for {args.steps:,} steps")
    print("=" * 60)

    if not passed:
        print("Below the bar. The honest fixes, in order (see docs/m3/M3_ToDo.md):")
        print("  train longer (--steps 40000) -> unfreeze the last ViT block -> shrink the image.")
        print("Do NOT start editing PPO.")

    train_env.close()

    # Exit codes: 0 = PASS, 1 = trained but below the bar.
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
