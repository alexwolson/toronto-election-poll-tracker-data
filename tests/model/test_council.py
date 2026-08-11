from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backend.model.council import (
    build_historical_incumbent_cases,
    candidate_key,
    classify_race_evidence,
    cross_validate_retention,
    nominations_closed,
)


def _historical_results() -> pd.DataFrame:
    return pd.read_csv("data/raw/elections/historical_council_results.csv")


def test_candidate_key_matches_first_last_and_last_first_formats() -> None:
    assert candidate_key("Hall, Suzan") == candidate_key("HALL SUZAN")
    assert candidate_key("Ana Bailão") == candidate_key("Bailao Ana")


def test_historical_fixture_builds_only_stable_boundary_incumbent_cases() -> None:
    cases = build_historical_incumbent_cases(_historical_results())
    assert len(cases) == 121
    assert set(cases["election_year"]) == {2006, 2010, 2014, 2022}
    assert int((1 - cases["incumbent_won"]).sum()) == 8
    assert not cases.duplicated(["election_year", "ward"]).any()


def test_historical_model_does_not_clear_publication_baseline() -> None:
    diagnostics = cross_validate_retention(
        build_historical_incumbent_cases(_historical_results())
    )
    assert diagnostics["winner_brier"] > diagnostics["baseline_winner_brier"]
    assert diagnostics["share_log_loss"] > diagnostics["baseline_share_log_loss"]
    assert diagnostics["beats_baseline"] is False


def test_well_known_challenger_plus_exposure_is_competitive() -> None:
    status, reasons = classify_race_evidence(
        is_running=True,
        vulnerability_score=45,
        strongest_challenger_tier="well-known",
        returning_runner_up=False,
        prior_runner_up_share=None,
        direct_poll_available=False,
    )
    assert status == "competitive"
    assert "well_known_challenger" in reasons


def test_open_seat_status_never_depends_on_incumbent_forecast() -> None:
    status, reasons = classify_race_evidence(
        is_running=False,
        vulnerability_score=0,
        strongest_challenger_tier=None,
        returning_runner_up=False,
        prior_runner_up_share=None,
        direct_poll_available=False,
    )
    assert status == "open"
    assert reasons == ["no_running_incumbent"]


def test_nomination_gate_uses_fixed_close_date() -> None:
    assert nominations_closed(datetime(2026, 8, 20, tzinfo=timezone.utc)) is False
    assert nominations_closed(datetime(2026, 8, 22, tzinfo=timezone.utc)) is True


def test_calibration_artifact_matches_historical_fixture() -> None:
    artifact = Path("data/processed/council_forecast_calibration.json").read_text()
    assert '"case_count": 121' in artifact
    assert '"incumbent_losses": 8' in artifact
    assert '"status": "insufficient_data"' in artifact
