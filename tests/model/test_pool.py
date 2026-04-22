"""Tests for the Phase 1 mayoral pool model."""
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

_REPO_ROOT = Path(__file__).parent.parent.parent


def _load_approval() -> pd.DataFrame:
    return pd.read_csv(_REPO_ROOT / "data" / "processed" / "approval_ratings.csv")


def _load_polls() -> pd.DataFrame:
    return pd.read_csv(_REPO_ROOT / "data" / "processed" / "polls.csv")


def test_approval_csv_has_required_columns():
    df = _load_approval()
    assert {"date", "approve", "disapprove", "not_sure"}.issubset(df.columns)
    assert len(df) >= 10


def test_approval_values_are_proportions():
    df = _load_approval()
    for col in ("approve", "disapprove", "not_sure"):
        assert df[col].between(0.0, 1.0).all(), f"{col} out of [0,1]"


def test_approval_rows_sum_to_one():
    df = _load_approval()
    row_sums = df["approve"] + df["disapprove"] + df["not_sure"]
    assert row_sums.between(0.97, 1.03).all(), f"Rows do not sum to ~1.0:\n{row_sums}"


def test_compute_chow_floor_returns_value_in_range():
    """Floor from full-field polls (3+ non-Chow candidates, n≥500) should be 37-44%."""
    from backend.model.pool import compute_chow_floor
    floor = compute_chow_floor(_load_polls())
    assert 0.37 <= floor <= 0.44, f"floor={floor:.3f} — expected 0.37-0.44"


def test_compute_chow_floor_ignores_h2h_polls():
    """A dataframe containing only H2H polls returns 0.0."""
    from backend.model.pool import compute_chow_floor
    h2h_only = pd.DataFrame([{
        "date_published": "2026-03-08",
        "field_tested": "bradford,chow",
        "chow": 0.47,
        "sample_size": 735,
    }])
    assert compute_chow_floor(h2h_only) == 0.0


def test_compute_chow_floor_ignores_small_sample_polls():
    """Polls with sample_size < 500 are excluded from floor estimation."""
    from backend.model.pool import compute_chow_floor
    small_sample = pd.DataFrame([{
        "date_published": "2025-10-06",
        "field_tested": "bradford,chow,furey,tory,other",
        "chow": 0.29,
        "sample_size": 406,
    }])
    assert compute_chow_floor(small_sample) == 0.0


def test_compute_current_h2h_chow_uses_bradford_matchup_only():
    """H2H Chow share uses only Bradford vs Chow polls, not Tory vs Chow."""
    from backend.model.pool import compute_current_h2h_chow
    result = compute_current_h2h_chow(_load_polls())
    # Most recent Bradford H2H (Mar 8): Chow 47% — should dominate with 12-day half-life
    assert result is not None
    assert 0.43 <= result <= 0.49, f"h2h_chow={result:.3f} — expected 0.43-0.49"


def test_compute_current_approval_reflects_recent_data():
    """Approval weighted average should be close to most recent data (Jan 2026: 55/38/7)."""
    from backend.model.pool import compute_current_approval
    result = compute_current_approval(_load_approval())
    assert 0.50 <= result["approve"] <= 0.60, f"approve={result['approve']:.3f}"
    assert 0.33 <= result["disapprove"] <= 0.45, f"disapprove={result['disapprove']:.3f}"


def test_compute_candidate_capture_rates_has_bradford():
    from backend.model.pool import compute_candidate_capture_rates
    result = compute_candidate_capture_rates(_load_polls(), anti_chow_pool=0.38)
    assert "bradford" in result
    assert 0.0 <= result["bradford"]["share"] <= 0.60
    assert 0.0 <= result["bradford"]["capture_rate"] <= 2.0


def test_compute_pool_model_returns_all_required_keys():
    from backend.model.pool import compute_pool_model
    result = compute_pool_model(_load_polls(), _load_approval())
    assert result["phase_mode"] == "pre_nomination"
    for key in ("chow_floor", "chow_ceiling", "anti_chow_pool",
                "protective_progressive_activated", "protective_progressive_reserve"):
        assert key in result["pool"], f"Missing pool key: {key}"
    assert "bradford" in result["candidates"]
    assert "consolidation_trend" in result
    assert result["consolidation_trend"] in (
        "consolidating", "stalling", "reversing", "insufficient_data"
    )
    assert "approval" in result
    assert "data_notes" in result


def test_pool_model_floor_below_ceiling():
    from backend.model.pool import compute_pool_model
    result = compute_pool_model(_load_polls(), _load_approval())
    assert result["pool"]["chow_floor"] < result["pool"]["chow_ceiling"]


def test_pool_model_pp_components_non_negative():
    from backend.model.pool import compute_pool_model
    result = compute_pool_model(_load_polls(), _load_approval())
    assert result["pool"]["protective_progressive_activated"] >= 0.0
    assert result["pool"]["protective_progressive_reserve"] >= 0.0
    assert result["uncaptured_anti_chow"] >= 0.0


def test_pool_model_consolidation_trend_is_consolidating():
    """Bradford's capture rate has risen from ~33% (pre-Jan 2026) to ~60% (post-Jan 2026)."""
    from backend.model.pool import compute_pool_model
    result = compute_pool_model(_load_polls(), _load_approval())
    assert result["consolidation_trend"] == "consolidating"


def test_polls_latest_includes_pool_model():
    """GET /api/polls/latest returns a pool_model key with required structure."""
    import sys
    sys.path.insert(0, str(_REPO_ROOT / "backend"))
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    response = client.get("/api/polls/latest")
    assert response.status_code == 200
    data = response.json()
    assert "pool_model" in data, "pool_model missing from response"
    pm = data["pool_model"]
    assert pm["phase_mode"] == "pre_nomination"
    assert "pool" in pm
    assert "candidates" in pm
    assert "bradford" in pm["candidates"]


# ── poll_detail ────────────────────────────────────────────────


def test_poll_detail_keys_present():
    from backend.model.pool import compute_pool_model
    result = compute_pool_model(_load_polls(), _load_approval())
    assert "poll_detail" in result
    pd_keys = {"approval_polls", "floor_polls", "h2h_polls", "capture_polls"}
    assert pd_keys == set(result["poll_detail"].keys())


def test_poll_detail_approval_polls_shape():
    from backend.model.pool import compute_pool_model
    detail = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]
    polls = detail["approval_polls"]
    assert len(polls) > 0
    for row in polls:
        assert set(row.keys()) == {"date", "firm", "approve", "disapprove", "not_sure", "weight"}
        assert 0.0 <= row["approve"] <= 1.0
        assert 0.0 <= row["disapprove"] <= 1.0
        assert 0.0 <= row["not_sure"] <= 1.0
        assert 0.0 <= row["weight"] <= 1.0


def test_poll_detail_approval_polls_weight_normalised():
    """Most recent approval poll must have weight 1.0."""
    from backend.model.pool import compute_pool_model
    polls = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]["approval_polls"]
    assert polls[0]["weight"] == 1.0, "First row (most recent) should have weight 1.0"


def test_poll_detail_approval_polls_sorted_descending():
    from backend.model.pool import compute_pool_model
    polls = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]["approval_polls"]
    dates = [r["date"] for r in polls]
    assert dates == sorted(dates, reverse=True), "approval_polls should be sorted date desc"


def test_poll_detail_floor_polls_sorted_descending():
    from backend.model.pool import compute_pool_model
    polls = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]["floor_polls"]
    if len(polls) > 1:
        dates = [r["date"] for r in polls]
        assert dates == sorted(dates, reverse=True), "floor_polls should be sorted date desc"


def test_poll_detail_h2h_polls_sorted_descending():
    from backend.model.pool import compute_pool_model
    polls = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]["h2h_polls"]
    if len(polls) > 1:
        dates = [r["date"] for r in polls]
        assert dates == sorted(dates, reverse=True), "h2h_polls should be sorted date desc"


def test_poll_detail_capture_polls_sorted_descending():
    from backend.model.pool import compute_pool_model
    polls = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]["capture_polls"]
    if len(polls) > 1:
        dates = [r["date"] for r in polls]
        assert dates == sorted(dates, reverse=True), "capture_polls should be sorted date desc"


def test_poll_detail_floor_polls_shape():
    from backend.model.pool import compute_pool_model
    detail = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]
    polls = detail["floor_polls"]
    assert len(polls) > 0
    for row in polls:
        assert set(row.keys()) == {"date", "firm", "field_tested", "chow", "sample_size", "candidate_weight"}
        assert 0.0 <= row["chow"] <= 1.0
        assert row["sample_size"] >= 500
        assert row["candidate_weight"] >= 3  # FULL_FIELD_THRESHOLD non-Chow candidates


def test_poll_detail_h2h_polls_shape():
    from backend.model.pool import compute_pool_model
    detail = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]
    polls = detail["h2h_polls"]
    assert len(polls) > 0
    for row in polls:
        assert set(row.keys()) == {"date", "firm", "chow", "bradford", "sample_size", "recency_weight"}
        assert 0.0 <= row["chow"] <= 1.0
        assert 0.0 <= row["recency_weight"] <= 1.0


def test_poll_detail_h2h_polls_weight_normalised():
    from backend.model.pool import compute_pool_model
    polls = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]["h2h_polls"]
    assert polls[0]["recency_weight"] == 1.0


def test_poll_detail_capture_polls_shape():
    from backend.model.pool import compute_pool_model
    detail = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]
    polls = detail["capture_polls"]
    assert len(polls) > 0
    for row in polls:
        assert set(row.keys()) == {"date", "firm", "field_tested", "bradford", "recency_weight"}
        assert 0.0 <= row["bradford"] <= 1.0
        assert 0.0 <= row["recency_weight"] <= 1.0


def test_poll_detail_capture_polls_weight_normalised():
    from backend.model.pool import compute_pool_model
    polls = compute_pool_model(_load_polls(), _load_approval())["poll_detail"]["capture_polls"]
    assert polls[0]["recency_weight"] == 1.0


def test_polls_latest_includes_poll_detail():
    """GET /api/polls/latest returns pool_model.poll_detail with all four lists."""
    import sys
    sys.path.insert(0, str(_REPO_ROOT / "backend"))
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    response = client.get("/api/polls/latest")
    assert response.status_code == 200
    pm = response.json()["pool_model"]
    assert "poll_detail" in pm
    for key in ("approval_polls", "floor_polls", "h2h_polls", "capture_polls"):
        assert key in pm["poll_detail"], f"Missing poll_detail.{key}"
        assert isinstance(pm["poll_detail"][key], list)


