"""
Brick 0 (M4): lock the referee before there is a game to referee.

M4's claim is "switching games is config-only." The referee is what makes that
claim checkable, and it has exactly two pieces of logic worth pinning down:

  - decide_verdict() -- the function that says PASS. If it is wrong, the
    milestone lies, and it lies quietly: a verdict that always returns True
    looks identical to one that earned it. Pure logic, numbers in, PASS/FAIL
    out, so it costs seconds to test and never flakes.
  - source_fingerprint() -- the "no Python was edited" proof. If this returned
    something unstable (a timestamp, a set iteration order), two honest runs
    would print different fingerprints and the swap proof would be worthless.
    If it returned a constant, it would prove nothing at all and never say so.

Deliberately NOT tested here (a skip is a decision, per CLAUDE.md §5):

  - print_finish_line() and the report lines -- print statements that fail
    loudly the first time a human reads them.
  - check_contract_shapes() -- it is exercised for real against three separate
    profiles in Brick 3's test, on actual envs. Testing it here against a fake
    env would only prove the fake matches the fake.
"""

import os
import re
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

import pytest

from scripts.train_from_profile import decide_verdict, source_fingerprint


# ---------------------------------------------------------------------------
# decide_verdict -- the three M4 conditions
#
# Teacher Note: the bar is always "beat the baseline we measured in THIS run by
# a stated margin." M1 said "2x the baseline" and M2 said "at least +0.5"; both
# are the same idea written differently, and one shape is what lets a single
# referee grade CartPole and GridWorld side by side.
# ---------------------------------------------------------------------------

# A clearly-passing GridWorld-pixels run, in the M3 shape. Individual tests
# below change ONE field, so the reason a verdict flips is never ambiguous.
PASSING = dict(
    trained_mean_reward=0.99,
    live_baseline=0.48,
    margin_over_baseline=0.40,
    shapes_ok=True,
    goal_rate=1.0,
    min_goal_rate=0.80,
)


def test_all_conditions_met_passes():
    passed, _lines = decide_verdict(**PASSING)
    assert passed


def test_reward_below_baseline_plus_margin_fails():
    """0.87 beats the baseline, but not by the margin the profile demanded."""
    passed, _lines = decide_verdict(**{**PASSING, "trained_mean_reward": 0.87})
    assert not passed


def test_reward_exactly_at_the_bar_passes():
    """The bar is 'at least', not 'more than' -- 0.48 + 0.40 = 0.88 passes."""
    passed, _lines = decide_verdict(**{**PASSING, "trained_mean_reward": 0.88})
    assert passed


def test_goal_rate_below_bar_fails():
    passed, _lines = decide_verdict(**{**PASSING, "goal_rate": 0.55})
    assert not passed


def test_broken_contract_shapes_fail_everything():
    """The one condition no reward number can buy its way out of."""
    passed, _lines = decide_verdict(**{**PASSING, "shapes_ok": False})
    assert not passed


def test_profile_without_a_goal_rate_is_graded_on_reward_alone():
    """CartPole has no 'goal' to reach -- only the reward bar applies.

    Teacher Note: this is the asymmetry M4 has to be honest about. GridWorld is
    ours and we can ask "did it reach the goal?"; CartPole is borrowed and the
    question has no meaning there. Not applicable must mean not applicable --
    never a silent free pass, and never a silent failure.
    """
    passed, _lines = decide_verdict(
        trained_mean_reward=61.0,
        live_baseline=22.0,
        margin_over_baseline=22.0,
        shapes_ok=True,
        goal_rate=None,
        min_goal_rate=None,
    )
    assert passed


def test_profile_demanding_a_goal_rate_it_cannot_measure_is_an_error():
    """A YAML typo, caught loudly instead of graded as a pass.

    Nothing stops someone adding min_goal_rate to cartpole.yaml. If that were
    quietly ignored, the profile would claim a check that never ran.
    """
    with pytest.raises(ValueError):
        decide_verdict(
            trained_mean_reward=61.0,
            live_baseline=22.0,
            margin_over_baseline=22.0,
            shapes_ok=True,
            goal_rate=None,
            min_goal_rate=0.80,
        )


def test_report_lines_name_every_condition():
    """The verdict has to be readable, not just correct.

    A printed FAIL that does not say WHICH condition failed sends you reading
    code instead of reading output.
    """
    _passed, lines = decide_verdict(**{**PASSING, "goal_rate": 0.55})
    report = "\n".join(lines)
    assert "FAIL" in report          # the failing condition is marked
    assert "0.48" in report          # the baseline it was judged against
    assert "55" in report            # the goal rate it actually got


# ---------------------------------------------------------------------------
# source_fingerprint -- the "no Python was edited between runs" proof
# ---------------------------------------------------------------------------

def test_fingerprint_is_stable_across_calls():
    """Same unedited source, same fingerprint. Without this the proof is noise."""
    assert source_fingerprint() == source_fingerprint()


def test_fingerprint_looks_like_a_sha256():
    assert re.fullmatch(r"[0-9a-f]{64}", source_fingerprint())


def test_fingerprint_covers_uncommitted_files():
    """A new .py file changes the fingerprint even before it is committed.

    Teacher Note: this is the hole this test exists to keep shut. `git ls-files`
    on its own lists only files git already TRACKS, so a brand new file — or an
    edit to one — would leave the fingerprint unchanged, and two runs of
    different code would claim to be the same code. That is a false PASS on the
    one condition M4 is actually about, so it is worth ten lines to pin down.
    """
    before = source_fingerprint()
    scratch = os.path.join(_project_root, "_fingerprint_probe.py")
    try:
        with open(scratch, "w", encoding="utf-8") as f:
            f.write("# temporary file written by test_m4_verdict.py\n")
        assert source_fingerprint() != before
    finally:
        os.remove(scratch)

    # And it goes back to what it was once the file is gone.
    assert source_fingerprint() == before
