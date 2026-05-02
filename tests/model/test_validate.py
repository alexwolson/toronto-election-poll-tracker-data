"""Tests for input validation functions."""
import pandas as pd
import pytest
from backend.model.validate import (
    ValidationError,
    validate_challengers,
    validate_registered_mayors,
    validate_registered_councillors,
)


def _base_challengers_row(**overrides) -> dict:
    base = {
        "ward": 1,
        "candidate_name": "Test Candidate",
        "name_recognition_tier": "known",
        "fundraising_tier": "high",
        "mayoral_alignment": "unaligned",
        "is_endorsed_by_departing": False,
        "last_updated": "2026-01-01",
    }
    base.update(overrides)
    return base


def test_validate_challengers_accepts_medium_fundraising_tier():
    """'medium' fundraising tier is handled by simulation.py but was excluded
    from the validation allowlist, causing a crash for any challenger with
    fundraising_tier='medium'.
    """
    df = pd.DataFrame([_base_challengers_row(fundraising_tier="medium")])
    # Should not raise
    validate_challengers(df)


def test_validate_challengers_still_rejects_invalid_fundraising_tier():
    """An unrecognised fundraising tier like 'very-high' must still be rejected."""
    df = pd.DataFrame([_base_challengers_row(fundraising_tier="very-high")])
    with pytest.raises(ValidationError, match="fundraising_tier"):
        validate_challengers(df)


def test_validate_challengers_accepts_high_and_low():
    """Original valid tiers must still pass."""
    for tier in ("high", "low"):
        df = pd.DataFrame([_base_challengers_row(fundraising_tier=tier)])
        validate_challengers(df)


# ---------------------------------------------------------------------------
# validate_registered_mayors
# ---------------------------------------------------------------------------

def _base_mayor_row(**overrides) -> dict:
    base = {
        "first_name": "Brad",
        "last_name": "Bradford",
        "status": "Active",
        "date_nomination": "2026-05-01",
    }
    base.update(overrides)
    return base


def test_validate_registered_mayors_accepts_valid():
    df = pd.DataFrame([_base_mayor_row(), _base_mayor_row(first_name="Lyall", last_name="Sanders")])
    validate_registered_mayors(df)  # should not raise


def test_validate_registered_mayors_rejects_missing_column():
    df = pd.DataFrame([{"first_name": "Brad", "last_name": "Bradford", "status": "Active"}])
    with pytest.raises(ValidationError, match="date_nomination"):
        validate_registered_mayors(df)


def test_validate_registered_mayors_rejects_bad_date():
    df = pd.DataFrame([_base_mayor_row(date_nomination="not-a-date")])
    with pytest.raises(ValidationError, match="date_nomination"):
        validate_registered_mayors(df)


# ---------------------------------------------------------------------------
# validate_registered_councillors
# ---------------------------------------------------------------------------

def _base_councillor_row(**overrides) -> dict:
    base = {
        "ward": 1,
        "first_name": "Gord",
        "last_name": "Perks",
        "status": "Active",
        "date_nomination": "2026-05-01",
    }
    base.update(overrides)
    return base


def test_validate_registered_councillors_accepts_valid():
    df = pd.DataFrame([_base_councillor_row(), _base_councillor_row(ward=2, first_name="Mike", last_name="Layton")])
    validate_registered_councillors(df)  # should not raise


def test_validate_registered_councillors_rejects_bad_ward():
    df = pd.DataFrame([_base_councillor_row(ward=0)])
    with pytest.raises(ValidationError, match="ward values outside"):
        validate_registered_councillors(df)


def test_validate_registered_councillors_rejects_ward_26():
    df = pd.DataFrame([_base_councillor_row(ward=26)])
    with pytest.raises(ValidationError, match="ward values outside"):
        validate_registered_councillors(df)


def test_validate_registered_councillors_rejects_bad_date():
    df = pd.DataFrame([_base_councillor_row(date_nomination="bad")])
    with pytest.raises(ValidationError, match="date_nomination"):
        validate_registered_councillors(df)


def test_validate_registered_mayors_rejects_null_name():
    df = pd.DataFrame([_base_mayor_row(first_name=None)])
    with pytest.raises(ValidationError, match="first_name"):
        validate_registered_mayors(df)


def test_validate_registered_councillors_rejects_null_name():
    df = pd.DataFrame([_base_councillor_row(last_name=None)])
    with pytest.raises(ValidationError, match="last_name"):
        validate_registered_councillors(df)


def test_validate_registered_councillors_rejects_empty_status():
    df = pd.DataFrame([_base_councillor_row(status="")])
    with pytest.raises(ValidationError, match="Missing status"):
        validate_registered_councillors(df)
