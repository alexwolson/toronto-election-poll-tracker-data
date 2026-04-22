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
