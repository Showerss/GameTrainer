"""
Unit tests for the M5 referee in scripts/check_hands.py.

Mirrors tests/test_m4_verdict.py:
Tests all 4 controls and decide_verdict() with pure logic and synthetic
Measurements, ensuring the referee is trustworthy and fails loudly if any
condition drifts.
"""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.check_hands import (
    Measurements,
    decide_frozen_frame,
    decide_keys_live,
    decide_null_input,
    decide_reset,
    decide_verdict,
)

PASSING_MEASUREMENTS = Measurements(
    target_cell=(1, 2),
    live_cells_changed=1,
    live_changed_cell=(1, 2),
    live_pixels_changed=237,
    null_cells_changed=0,
    null_pixels_changed=0,
    frozen_obs_cells_changed=0,
    live_obs_cells_changed=1,
    resets_attempted=20,
    resets_clean=20,
    reset_mouse_clicks=0,
)


def test_all_controls_passing_gives_pass_verdict():
    passed, results = decide_verdict(PASSING_MEASUREMENTS)
    assert passed is True
    assert len(results) == 4
    assert all(r.passed for r in results)


def test_keys_live_passes_when_target_matches_exactly():
    res = decide_keys_live(PASSING_MEASUREMENTS)
    assert res.passed is True
    assert res.number == 1


def test_keys_live_fails_if_no_cells_or_too_many_change():
    m_zero = Measurements(
        **{**PASSING_MEASUREMENTS.__dict__, "live_cells_changed": 0, "live_changed_cell": None}
    )
    assert decide_keys_live(m_zero).passed is False

    m_two = Measurements(
        **{**PASSING_MEASUREMENTS.__dict__, "live_cells_changed": 2, "live_changed_cell": (1, 2)}
    )
    assert decide_keys_live(m_two).passed is False


def test_keys_live_fails_if_wrong_cell_changes():
    m_wrong = Measurements(
        **{**PASSING_MEASUREMENTS.__dict__, "live_changed_cell": (0, 0)}
    )
    assert decide_keys_live(m_wrong).passed is False


def test_null_input_passes_only_with_zero_changes():
    res = decide_null_input(PASSING_MEASUREMENTS)
    assert res.passed is True
    assert res.number == 2

    m_drift = Measurements(
        **{**PASSING_MEASUREMENTS.__dict__, "null_cells_changed": 1}
    )
    assert decide_null_input(m_drift).passed is False


def test_frozen_frame_passes_when_live_moves_and_frozen_stays():
    res = decide_frozen_frame(PASSING_MEASUREMENTS)
    assert res.passed is True
    assert res.number == 3

    # Frozen observation drifted
    m_frozen_drift = Measurements(
        **{**PASSING_MEASUREMENTS.__dict__, "frozen_obs_cells_changed": 1}
    )
    assert decide_frozen_frame(m_frozen_drift).passed is False

    # Live observation didn't change on screen
    m_live_stale = Measurements(
        **{**PASSING_MEASUREMENTS.__dict__, "live_obs_cells_changed": 0}
    )
    assert decide_frozen_frame(m_live_stale).passed is False


def test_reset_passes_with_twenty_clean_trials():
    res = decide_reset(PASSING_MEASUREMENTS)
    assert res.passed is True
    assert res.number == 4

    # Fewer than 20 trials
    m_fewer = Measurements(
        **{**PASSING_MEASUREMENTS.__dict__, "resets_attempted": 19, "resets_clean": 19}
    )
    assert decide_reset(m_fewer).passed is False

    # One failed reset
    m_dirty = Measurements(
        **{**PASSING_MEASUREMENTS.__dict__, "resets_clean": 19}
    )
    assert decide_reset(m_dirty).passed is False
