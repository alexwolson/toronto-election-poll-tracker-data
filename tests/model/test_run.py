"""Tests for run.py model pipeline."""
import pandas as pd
from backend.model.run import _classify_race
from backend.model.simulation import SAFE_DEFEATABILITY_THRESHOLD


def test_classify_race_high_defeatability_no_challengers_is_not_safe():
    """A ward with high defeatability and no viable challengers must not be
    classified as 'safe'. The simulation's _is_safe_incumbent requires
    defeatability_score < SAFE_DEFEATABILITY_THRESHOLD, so _classify_race must
    agree to avoid showing 'safe' with a simulation-derived (non-safe) win prob.
    """
    row = {
        "is_running": True,
        "defeatability_score": SAFE_DEFEATABILITY_THRESHOLD + 1,  # e.g. 31
    }
    challengers = []  # no challengers at all

    result = _classify_race(row, challengers)

    assert result != "safe", (
        f"Ward with defeatability={row['defeatability_score']} (>= threshold "
        f"{SAFE_DEFEATABILITY_THRESHOLD}) should not be 'safe', got '{result}'"
    )


def test_classify_race_low_defeatability_no_challengers_is_safe():
    """A ward with low defeatability and no viable challengers is 'safe'."""
    row = {
        "is_running": True,
        "defeatability_score": SAFE_DEFEATABILITY_THRESHOLD - 1,  # e.g. 29
    }
    challengers = []

    result = _classify_race(row, challengers)
    assert result == "safe"
