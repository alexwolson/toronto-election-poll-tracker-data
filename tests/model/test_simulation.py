"""Tests for WardSimulation."""
import pandas as pd
import numpy as np
from backend.model.simulation import WardSimulation


def _minimal_ward_data(ward: int, is_running: bool) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ward": ward,
                "councillor_name": "Test Councillor",
                "is_running": is_running,
                "defeatability_score": 40,
                "is_byelection_incumbent": False,
            }
        ]
    )


def _minimal_mayoral_averages() -> pd.DataFrame:
    return pd.DataFrame([{"candidate": "chow", "share": 0.40}])


def _minimal_challenger(ward: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ward": ward,
                "candidate_name": "Challenger A",
                "name_recognition_tier": "known",
                "fundraising_tier": "low",
                "mayoral_alignment": "unaligned",
                "is_endorsed_by_departing": False,
            }
        ]
    )


def _empty_coattails() -> pd.DataFrame:
    """Coattails DataFrame with NO entry for the ward under test."""
    return pd.DataFrame(
        columns=["ward", "councillor_name", "alignment", "alignment_delta", "lean", "p_w", "coattail_adjustment"]
    )


def _empty_leans() -> pd.DataFrame:
    return pd.DataFrame(columns=["ward", "candidate", "lean"])


def test_open_seat_does_not_crash_when_ward_absent_from_coattails():
    """An open-seat ward missing from coattail_adjustments must not raise IndexError.

    The coattail value is irrelevant for open seats; fetching it regardless is the bug.
    """
    ward = 19

    sim = WardSimulation(
        ward_data=_minimal_ward_data(ward, is_running=False),
        mayoral_averages=_minimal_mayoral_averages(),
        coattails=_empty_coattails(),           # ward 19 absent
        challengers=_minimal_challenger(ward),
        leans=_empty_leans(),
        n_draws=10,
        seed=0,
    )

    # Must not raise IndexError
    result = sim.run()
    assert ward in result["win_probabilities"]


def test_safe_incumbent_win_probability_is_not_one():
    """Safe incumbents should win ~97% of draws, not 100%.

    SAFE_INCUMBENT_WIN_PROB = 0.97 is defined but currently unused, so safe
    incumbents win every draw. With enough draws the mean should be < 1.0.
    """
    from backend.model.simulation import SAFE_INCUMBENT_WIN_PROB

    ward = 1
    ward_data = pd.DataFrame(
        [
            {
                "ward": ward,
                "councillor_name": "Safe Councillor",
                "is_running": True,
                "defeatability_score": 10,  # well below threshold
                "is_byelection_incumbent": False,
            }
        ]
    )
    # No viable challengers → qualifies for safe incumbent shortcut
    challengers = pd.DataFrame(
        [
            {
                "ward": ward,
                "candidate_name": "Unknown Challenger",
                "name_recognition_tier": "unknown",
                "fundraising_tier": "low",
                "mayoral_alignment": "unaligned",
                "is_endorsed_by_departing": False,
            }
        ]
    )
    coattails = pd.DataFrame(
        [{"ward": ward, "alignment_delta": 0.0, "lean": 0.0, "p_w": 0.35}]
    )

    sim = WardSimulation(
        ward_data=ward_data,
        mayoral_averages=_minimal_mayoral_averages(),
        coattails=coattails,
        challengers=challengers,
        leans=_empty_leans(),
        n_draws=2000,
        seed=42,
    )
    result = sim.run()
    win_prob = result["win_probabilities"][ward]
    assert win_prob < 1.0, (
        f"Safe incumbent should not win 100% of draws (got {win_prob:.4f}). "
        f"SAFE_INCUMBENT_WIN_PROB={SAFE_INCUMBENT_WIN_PROB} may not be applied in the shortcut."
    )
    # Should be close to SAFE_INCUMBENT_WIN_PROB
    assert abs(win_prob - SAFE_INCUMBENT_WIN_PROB) < 0.03, (
        f"Expected win probability near {SAFE_INCUMBENT_WIN_PROB}, got {win_prob:.4f}"
    )


def test_incumbent_ward_simulation_produces_valid_win_probability():
    """The full incumbent simulation path (not safe incumbent, not open seat)
    produces a win probability strictly between 0 and 1.

    This covers the coat_row-dependent path refactored in the coattails fix,
    ensuring the per-draw p_w computation runs without error.
    """
    ward = 5
    ward_data = pd.DataFrame(
        [
            {
                "ward": ward,
                "councillor_name": "Incumbent",
                "is_running": True,
                "defeatability_score": 50,  # above safe threshold → full simulation runs
                "is_byelection_incumbent": False,
            }
        ]
    )
    challengers = pd.DataFrame(
        [
            {
                "ward": ward,
                "candidate_name": "Known Challenger",
                "name_recognition_tier": "known",
                "fundraising_tier": "low",
                "mayoral_alignment": "unaligned",
                "is_endorsed_by_departing": False,
            }
        ]
    )
    coattails = pd.DataFrame(
        [
            {
                "ward": ward,
                "alignment_delta": 0.1,
                "lean": 0.05,
            }
        ]
    )

    sim = WardSimulation(
        ward_data=ward_data,
        mayoral_averages=_minimal_mayoral_averages(),
        coattails=coattails,
        challengers=challengers,
        leans=_empty_leans(),
        n_draws=500,
        seed=7,
    )
    result = sim.run()

    win_prob = result["win_probabilities"][ward]
    assert 0.0 < win_prob < 1.0, (
        f"Incumbent win probability must be strictly between 0 and 1, got {win_prob}"
    )
    assert ward in result["candidate_win_probabilities"]
    assert "Incumbent" in result["candidate_win_probabilities"][ward]
