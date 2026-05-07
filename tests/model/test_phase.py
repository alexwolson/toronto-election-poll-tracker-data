"""Tests for phase detection logic."""
import pandas as pd
import pytest
from backend.model.phase import detect_phase


def _challengers_df(has_candidates: bool = True) -> pd.DataFrame:
    if not has_candidates:
        return pd.DataFrame(columns=["ward", "candidate_name", "name_recognition_tier",
                                      "mayoral_alignment", "endorsements"])
    return pd.DataFrame([{
        "ward": 1,
        "candidate_name": "Test Candidate",
        "name_recognition_tier": "known",
        "mayoral_alignment": "unaligned",
        "endorsements": "",
    }])


def test_detect_phase_returns_1_when_no_challengers():
    """Phase 1: no challenger data registered yet."""
    result = detect_phase(_challengers_df(has_candidates=False), has_financials=False)
    assert result["phase"] == 1


def test_detect_phase_returns_2_when_challengers_no_financials():
    """Phase 2: candidates registered but financial filings not yet available."""
    result = detect_phase(_challengers_df(), has_financials=False)
    assert result["phase"] == 2


def test_detect_phase_returns_3_when_financials_available():
    """Phase 3: full financial filing data is available."""
    result = detect_phase(_challengers_df(), has_financials=True)
    assert result["phase"] == 3
