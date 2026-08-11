"""Tests for run.py model pipeline."""
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from backend.model.council import classify_race_evidence
from backend.model.run import _derive_endorsed_by_departing


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


def test_classify_race_high_vulnerability_is_competitive_without_challenger() -> None:
    status, reasons = classify_race_evidence(
        is_running=True,
        vulnerability_score=60,
        strongest_challenger_tier=None,
        returning_runner_up=False,
        prior_runner_up_share=None,
        direct_poll_available=False,
    )
    assert status == "competitive"
    assert reasons == ["high_structural_vulnerability"]


def test_known_label_alone_does_not_make_a_low_risk_ward_competitive() -> None:
    status, reasons = classify_race_evidence(
        is_running=True,
        vulnerability_score=20,
        strongest_challenger_tier="known",
        returning_runner_up=False,
        prior_runner_up_share=None,
        direct_poll_available=False,
    )
    assert status == "safe"
    assert reasons == ["no_competitive_trigger"]


def test_v3_snapshot_separates_assessment_from_unavailable_forecast() -> None:
    snapshot = json.loads(Path("data/processed/model_snapshot.json").read_text())
    counts = Counter(ward["race_class"] for ward in snapshot["wards"])
    assert snapshot["schema_version"] == 3
    assert counts == {"safe": 14, "competitive": 9, "open": 2}
    assert sum(counts.values()) == 25
    assert snapshot["council_model"]["assessment"]["status_counts"] == {
        "safe": 14,
        "competitive": 9,
        "open": 2,
    }
    assert snapshot["council_model"]["forecast"]["status"] == "insufficient_data"
    assert snapshot["council_model"]["composition"]["status"] == "unavailable"
    for ward in snapshot["wards"]:
        assert "win_probability" not in ward
        assert "candidate_win_probabilities" not in ward
        assert "factors" not in ward
        assert ward["forecast"]["incumbent_win_probability"] is None
