"""
GridWorld-with-ViT Training Script - Milestone M3.

This file plays two roles from the M3 to-do list:
  * Brick 0 (WRITTEN FIRST, here): the *guardrail* — the finish line M3 must
    clear, written down before any of the pixel work exists.
  * Brick 4 (LATER): the actual training on pixels that makes the guardrail
    print PASS. That half needs Bricks 1-3 first (teach GridWorld to draw
    itself, the pixel wrapper, the ViT extractor), so it is not wired yet.

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

Usage (today):
    python scripts/train_gridworld_vit.py
        -> measures the live baseline, checks the M2 contract shapes, prints the
           bar, then stops: "training on pixels is Brick 4, not wired yet."
"""

import os
import sys

# Print UTF-8 so status glyphs (>=, checkmarks) don't crash on Windows consoles (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path so we can import from src/
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from src.gametrainer.gridworld import GridWorldEnv

# ---------------------------------------------------------------------------
# The bar (named so it is impossible to miss and easy to tune later).
# ---------------------------------------------------------------------------

# Episodes to average when measuring the live random baseline. More than M2's 20
# so the number is steady — this is the value everything else is judged against.
BASELINE_EPISODES = 50

# Greedy episodes to judge the *trained* agent on (Brick 4 will use this).
FINAL_EVAL_EPISODES = 20

# Condition 2: "reaches the goal in MOST greedy episodes." Most = at least 80%.
GOAL_RATE_TO_PASS = 0.80

# Condition 1: "CLEARLY beats" the live baseline. Reaching the goal via a short
# path scores ~+0.93 and the live baseline is ~+0.13, so a margin of 0.40 above
# the measured baseline means the agent genuinely learned the route, not noise.
MARGIN_OVER_BASELINE = 0.40


# ---------------------------------------------------------------------------
# Referee piece 1 — measure the random baseline LIVE (the M2 hardcode, fixed).
# ---------------------------------------------------------------------------

def measure_random_baseline(episodes: int = BASELINE_EPISODES) -> float:
    """Average reward per episode of a purely random agent on GridWorld.

    Teacher Note: a random agent ignores what it sees — it just calls
    action_space.sample(). So the reward it earns is identical whether the
    observation is (row, col) numbers or a picture. That is why we can measure
    the baseline here on the plain M2 env: the number will be the same once the
    pixel wrapper (Brick 2) is added on top.
    """
    env = GridWorldEnv()
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
    print("=" * 60)
    print("GAMETRAINER — M3: Add the Eyes (guardrail)")
    print("=" * 60)
    print()

    # Referee piece 2: the contract shapes (on the M2 env — the baseline promise).
    shapes_ok, detail = check_contract_shapes(GridWorldEnv())
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
    # The pixel training that produces the trained numbers is Brick 4.
    # It needs Bricks 1-3 first. Until then, we stop here honestly instead
    # of faking a verdict.
    # -------------------------------------------------------------------
    print("-" * 60)
    print("Guardrail defined. Training on pixels is Brick 4 — not wired yet.")
    print("When Bricks 1-3 land, Brick 4 will: train the ViT agent, evaluate it,")
    print("and call decide_verdict() above to print PASS/FAIL against this bar.")
    print("=" * 60)

    # Exit codes: 0 = PASS, 1 = trained but below bar, 2 = guardrail-only (today).
    return 2


if __name__ == "__main__":
    sys.exit(main())
