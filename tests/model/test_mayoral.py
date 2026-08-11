"""Tests for the v2 mayoral evidence contract."""

from datetime import UTC, datetime

import pandas as pd
import pytest

from backend.model.mayoral import (
    build_approval_slice,
    build_challenger_lane,
    build_evidence_slice,
    poll_use_breakdown,
    validate_approval_data,
)
from backend.model.mayoral_config import TARGET_FIELD


def _processed(name: str) -> pd.DataFrame:
    return pd.read_csv(f"data/processed/{name}.csv")


def test_current_fixture_poll_partition_is_exhaustive() -> None:
    breakdown = poll_use_breakdown(_processed("polls"))
    assert breakdown == {
        "current_average": 2,
        "head_to_head": 7,
        "different_candidate_field": 13,
        "other": 0,
        "total": 22,
    }
    assert sum(value for key, value in breakdown.items() if key != "total") == 22


def test_current_field_preserves_reported_residual() -> None:
    evidence = build_evidence_slice(
        _processed("polls"), TARGET_FIELD, datetime(2026, 8, 10, tzinfo=UTC)
    )
    total = sum(evidence["candidates"].values()) + evidence["residual"]["share"]
    assert evidence["poll_count"] == 2
    assert evidence["firm_count"] == 2
    assert total == pytest.approx(1.0, abs=0.001)
    assert evidence["denominator"] == "poll_reported_vote_intention"


def test_lane_split_is_descriptive_and_trend_requires_enough_evidence() -> None:
    evidence = build_evidence_slice(_processed("polls"), TARGET_FIELD)
    lane = build_challenger_lane(evidence)
    assert lane["combined_share"] == pytest.approx(
        evidence["candidates"]["bradford"] + evidence["candidates"]["alexander"],
        abs=0.0001,
    )
    assert sum(lane["named_split"].values()) == pytest.approx(1.0, abs=0.0001)
    assert lane["trend"]["status"] == "insufficient_data"


def test_approval_validation_rejects_invalid_and_duplicate_records() -> None:
    bad = pd.DataFrame(
        [
            {"date": "not-a-date", "source": "Firm", "approve": 0.5, "disapprove": 0.4, "not_sure": 0.1},
        ]
    )
    with pytest.raises(ValueError, match="invalid date"):
        validate_approval_data(bad)

    duplicate = pd.DataFrame(
        [
            {"date": "2026-01-01", "source": "Firm", "approve": 0.5, "disapprove": 0.4, "not_sure": 0.1},
            {"date": "2026-01-01", "source": "Firm", "approve": 0.5, "disapprove": 0.4, "not_sure": 0.1},
        ]
    )
    with pytest.raises(ValueError, match="unique"):
        validate_approval_data(duplicate)


def test_approval_slice_reports_raw_and_effective_reading_counts() -> None:
    approval = _processed("approval_ratings")
    result = build_approval_slice(approval, datetime(2026, 8, 10, tzinfo=UTC))
    assert result["reading_count"] == len(approval)
    assert 1.0 <= result["effective_reading_count"] <= result["reading_count"]
    total = sum(result[key] for key in ("approve", "disapprove", "not_sure", "unreported"))
    assert total == pytest.approx(1.0, abs=0.001)

