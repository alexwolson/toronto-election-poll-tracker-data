"""Tests for run.py model pipeline."""
import pandas as pd
from backend.model.run import _classify_race, _derive_endorsed_by_departing
from backend.model.simulation import SAFE_DEFEATABILITY_THRESHOLD


def _ward_data(ward: int, councillor_name: str, is_running: bool) -> pd.DataFrame:
    return pd.DataFrame([{
        "ward": ward,
        "councillor_name": councillor_name,
        "is_running": is_running,
        "defeatability_score": 20,
    }])


def test_derive_endorsed_by_departing_detects_match():
    """Challenger whose endorsements include the departing councillor's name
    should have is_endorsed_by_departing=True."""
    ward_data = _ward_data(5, "Paula Fletcher", is_running=False)
    challengers = pd.DataFrame([{
        "ward": 5,
        "candidate_name": "Challenger A",
        "endorsements": "Paula Fletcher|CUPE Local 79",
    }])

    result = _derive_endorsed_by_departing(challengers, ward_data)

    assert result.loc[0, "is_endorsed_by_departing"] is True or \
           result.loc[0, "is_endorsed_by_departing"] == True


def test_derive_endorsed_by_departing_no_match():
    """Challenger without the departing councillor in endorsements gets False."""
    ward_data = _ward_data(5, "Paula Fletcher", is_running=False)
    challengers = pd.DataFrame([{
        "ward": 5,
        "candidate_name": "Challenger A",
        "endorsements": "CUPE Local 79",
    }])

    result = _derive_endorsed_by_departing(challengers, ward_data)

    assert result.loc[0, "is_endorsed_by_departing"] == False


def test_derive_endorsed_by_departing_incumbent_ward_is_false():
    """Wards where the incumbent is running have no departing councillor;
    is_endorsed_by_departing must be False."""
    ward_data = _ward_data(3, "Mike Colle", is_running=True)
    challengers = pd.DataFrame([{
        "ward": 3,
        "candidate_name": "Challenger B",
        "endorsements": "Mike Colle",
    }])

    result = _derive_endorsed_by_departing(challengers, ward_data)

    assert result.loc[0, "is_endorsed_by_departing"] == False


def test_derive_endorsed_by_departing_empty_endorsements():
    """Empty endorsements string yields False even for open seats."""
    ward_data = _ward_data(7, "Michael Thompson", is_running=False)
    challengers = pd.DataFrame([{
        "ward": 7,
        "candidate_name": "Challenger C",
        "endorsements": "",
    }])

    result = _derive_endorsed_by_departing(challengers, ward_data)

    assert result.loc[0, "is_endorsed_by_departing"] == False


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
