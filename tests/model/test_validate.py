"""Tests for input validation functions."""
import pandas as pd
import pytest
from backend.model.validate import ValidationError, validate_challengers


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
