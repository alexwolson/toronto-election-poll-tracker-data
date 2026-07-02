"""Tests for the mayoral polling aggregator."""
import pandas as pd
from backend.model.aggregator import compute_poll_weights


def _polls_with_naive_dates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date_published": ["2026-03-01", "2026-03-08"],
            "chow": [0.38, 0.40],
            "bradford": [0.20, 0.22],
        }
    )


def _polls_with_aware_dates() -> pd.DataFrame:
    """Dates that include UTC offset — triggers the tz_localize bug."""
    return pd.DataFrame(
        {
            "date_published": [
                "2026-03-01T00:00:00+00:00",
                "2026-03-08T00:00:00+00:00",
            ],
            "chow": [0.38, 0.40],
            "bradford": [0.20, 0.22],
        }
    )


def test_compute_poll_weights_accepts_tz_naive_dates():
    """Baseline: naive date strings must work."""
    df = _polls_with_naive_dates()
    weights = compute_poll_weights(df)
    assert len(weights) == 2
    assert all(0 < w <= 1.0 for w in weights)


def test_compute_poll_weights_accepts_tz_aware_dates():
    """Timezone-aware ISO strings must not raise TypeError."""
    df = _polls_with_aware_dates()
    # Must not raise: TypeError: Already tz-aware, use tz_convert to convert
    weights = compute_poll_weights(df)
    assert len(weights) == 2
    assert all(0 < w <= 1.0 for w in weights)


# --- effective_sample_size ---

from datetime import datetime, timezone

from backend.model.aggregator import effective_sample_size


def test_effective_sample_size_empty_is_zero():
    df = pd.DataFrame(columns=["date_published", "sample_size"])
    assert effective_sample_size(df) == 0.0


def test_effective_sample_size_fresh_poll_counts_fully():
    ref = datetime(2026, 7, 1, tzinfo=timezone.utc)
    df = pd.DataFrame([{"date_published": "2026-07-01", "sample_size": 1000}])
    assert abs(effective_sample_size(df, ref) - 1000.0) < 1.0


def test_effective_sample_size_decays_with_age():
    """A poll one half-life (12 days) old contributes half its sample."""
    ref = datetime(2026, 7, 1, tzinfo=timezone.utc)
    df = pd.DataFrame([{"date_published": "2026-06-19", "sample_size": 1000}])
    assert abs(effective_sample_size(df, ref) - 500.0) < 5.0


def test_effective_sample_size_sums_polls():
    ref = datetime(2026, 7, 1, tzinfo=timezone.utc)
    df = pd.DataFrame([
        {"date_published": "2026-07-01", "sample_size": 1000},
        {"date_published": "2026-06-19", "sample_size": 1000},
    ])
    assert abs(effective_sample_size(df, ref) - 1500.0) < 6.0


def test_effective_sample_size_missing_sample_size_contributes_zero():
    ref = datetime(2026, 7, 1, tzinfo=timezone.utc)
    df = pd.DataFrame([
        {"date_published": "2026-07-01", "sample_size": None},
        {"date_published": "2026-07-01", "sample_size": 600},
    ])
    assert abs(effective_sample_size(df, ref) - 600.0) < 1.0
