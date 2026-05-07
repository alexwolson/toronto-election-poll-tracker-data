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
        "mayoral_alignment": "unaligned",
        "endorsements": "",
        "last_updated": "2026-01-01",
    }
    base.update(overrides)
    return base


def test_validate_challengers_accepts_empty_endorsements():
    """Empty endorsements string is valid — candidate has no known endorsers."""
    df = pd.DataFrame([_base_challengers_row(endorsements="")])
    validate_challengers(df)


def test_validate_challengers_accepts_single_endorser():
    """A single named endorser is valid."""
    df = pd.DataFrame([_base_challengers_row(endorsements="Josh Matlow")])
    validate_challengers(df)


def test_validate_challengers_accepts_pipe_separated_endorsers():
    """Multiple endorsers separated by pipes are valid."""
    df = pd.DataFrame([_base_challengers_row(endorsements="Josh Matlow|CUPE Local 79")])
    validate_challengers(df)


def test_validate_challengers_rejects_missing_endorsements_column():
    """Missing endorsements column must raise ValidationError."""
    df = pd.DataFrame([{
        "ward": 1,
        "candidate_name": "Test Candidate",
        "name_recognition_tier": "known",
        "mayoral_alignment": "unaligned",
        "last_updated": "2026-01-01",
    }])
    with pytest.raises(ValidationError, match="endorsements"):
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


def test_validate_registered_mayors_rejects_empty_status():
    df = pd.DataFrame([_base_mayor_row(status="")])
    with pytest.raises(ValidationError, match="Missing status"):
        validate_registered_mayors(df)


def test_validate_registered_councillors_rejects_null_name():
    df = pd.DataFrame([_base_councillor_row(last_name=None)])
    with pytest.raises(ValidationError, match="last_name"):
        validate_registered_councillors(df)


def test_validate_registered_councillors_rejects_empty_status():
    df = pd.DataFrame([_base_councillor_row(status="")])
    with pytest.raises(ValidationError, match="Missing status"):
        validate_registered_councillors(df)
