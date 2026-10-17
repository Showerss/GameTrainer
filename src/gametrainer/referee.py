"""
The referee - shared by every training script (R1, Brick 6).

These functions used to live inside scripts/train_from_profile.py, and the M3
script imported them from there - one script borrowing from another. They are
the same for every milestone, so they live in the package now, next to the
Ground and the Link.

The referee never holds the bar itself. Each script keeps its own numbers
(margin, goal rate, episode counts) and passes them in, so moving the code here
moved no PASS/FAIL decision.

Plain Python with no imports at all - no SB3, no torch - so tests can load it
cheaply. "model" is anything with a predict(obs, deterministic=True) method.
"""

from __future__ import annotations


def pass_or_fail(ok: bool) -> str:
    """The one place that turns a yes/no into the word every script prints."""
    return "PASS" if ok else "FAIL"


# ---------------------------------------------------------------------------
# The contract shapes must be unchanged.
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
# Measure the random baseline LIVE, never from memory.
# ---------------------------------------------------------------------------

def measure_random_baseline(make_env_fn, episodes: int) -> float:
    """Average reward per episode of a purely random agent on THIS env.

    Teacher Note: takes a factory (something that builds an env) rather than an
    env, because a baseline has to be measured on the very same Ground the agent
    plays. M2 hardcoded -0.3 and the true figure was +0.13; M3 measured live and
    got +0.48 on a Ground that had changed underneath it. Every profile brings
    its own Ground, so every profile brings its own baseline.
    """
    env = make_env_fn()
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
# Play the trained agent with no exploration.
# ---------------------------------------------------------------------------

def evaluate_greedy(model, make_env_fn, episodes: int):
    """Play greedy episodes; return (mean_reward, goal_rate, mean_steps).

    Teacher Note: "greedy" (deterministic=True) means the agent always takes
    the move it currently thinks is best — no random exploration mixed in.
    That is the fair way to ask "what did it actually learn?": exploration is a
    training aid, not part of the skill we are grading.

    goal_rate counts episodes that ended via terminated=True. For GridWorld
    that only ever means "reached the goal" (its one way to terminate); for
    CartPole it would mean "the pole fell," but nothing ever asks for a
    CartPole goal rate, so computing it unconditionally here is harmless.
    """
    env = make_env_fn()
    rewards, steps_list, goals = [], [], 0

    for _ in range(episodes):
        obs, _ = env.reset()
        terminated = truncated = False
        ep_reward = 0.0
        ep_steps = 0
        while not (terminated or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _info = env.step(action)
            ep_reward += reward
            ep_steps += 1
        goals += int(terminated)
        rewards.append(ep_reward)
        steps_list.append(ep_steps)

    env.close()
    return sum(rewards) / episodes, goals / episodes, sum(steps_list) / episodes


# ---------------------------------------------------------------------------
# The verdict. Pure logic: numbers in, PASS/FAIL out.
# ---------------------------------------------------------------------------

def decide_verdict(
    trained_mean_reward: float,
    live_baseline: float,
    margin_over_baseline: float,
    shapes_ok: bool,
    goal_rate: float | None = None,
    min_goal_rate: float | None = None,
) -> tuple[bool, list[str]]:
    """Apply the bar. Returns (passed, printable report lines).

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

    lines = [
        f"  Live random baseline:   {live_baseline:+.2f} reward/episode",
        f"  Trained mean reward:    {trained_mean_reward:+.2f} reward/episode",
        (
            f"  [{pass_or_fail(beats_baseline)}] beats baseline by >= {margin_over_baseline:.2f}"
            f"  (needs >= {live_baseline + margin_over_baseline:+.2f})"
        ),
    ]
    if min_goal_rate is None:
        lines.append("  [ -- ] goal rate: not applicable to this Ground")
    else:
        lines.append(
            f"  [{pass_or_fail(reaches_goal)}] reaches goal in most episodes"
            f"  ({goal_rate * 100:.0f}%, needs >= {min_goal_rate * 100:.0f}%)"
        )
    lines.append(f"  [{pass_or_fail(shapes_ok)}] reset()/step() shapes unchanged")
    return passed, lines
