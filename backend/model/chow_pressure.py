from __future__ import annotations

import math
from datetime import datetime, timezone

import pandas as pd

RECENT_WINDOW_DAYS = 21
BASELINE_HALF_LIFE_DAYS = 21.0
MIN_HALF_LIFE_DAYS = 14.0
MAX_HALF_LIFE_DAYS = 42.0


def effective_number_of_parties(shares: list[float]) -> float:
    cleaned = [float(s) for s in shares if s is not None and s > 0]
    total = sum(cleaned)
    if total <= 0:
        return 1.0
    normalized = [s / total for s in cleaned]
    return 1.0 / sum(s * s for s in normalized)


def consolidation_factor(non_chow_shares: list[float]) -> float:
    enp = effective_number_of_parties(non_chow_shares)
    return 1.0 / math.sqrt(max(enp, 1.0))


def poll_demand(chow_share: float, non_chow_shares: list[float]) -> float:
    return max(0.0, 1.0 - max(0.0, min(1.0, float(chow_share)))) * consolidation_factor(
        non_chow_shares
    )


def adaptive_half_life_days(recent_poll_count: int, chow_std: float) -> float:
    volume_term = 1.0 - min(max(recent_poll_count, 0), 10) / 10.0
    dispersion_term = min(max(chow_std, 0.0), 0.10) / 0.10
    score = 0.6 * volume_term + 0.4 * dispersion_term
    half_life = MIN_HALF_LIFE_DAYS + (MAX_HALF_LIFE_DAYS - MIN_HALF_LIFE_DAYS) * score
    return max(MIN_HALF_LIFE_DAYS, min(MAX_HALF_LIFE_DAYS, half_life))


def adaptive_trend_horizon_days(recent_poll_count: int, chow_std: float) -> int:
    half_life = adaptive_half_life_days(recent_poll_count, chow_std)
    return int(round(max(14.0, min(56.0, half_life * 1.5))))


def trend_label(slope: float) -> str:
    if slope > 0.003:
        return "rising"
    if slope < -0.003:
        return "easing"
    return "flat"


def _pressure_band(value: float) -> str:
    if value >= 0.40:
        return "elevated"
    if value >= 0.25:
        return "moderate"
    return "low"


def _parse_field_tested(field: str | float | None) -> list[str]:
    if field is None or (isinstance(field, float) and math.isnan(field)):
        return []
    return [token.strip().lower() for token in str(field).split(",") if token.strip()]


def _non_chow_shares_from_row(row: pd.Series) -> list[float]:
    field = _parse_field_tested(row.get("field_tested"))
    shares: list[float] = []
    for candidate in field:
        if candidate == "chow":
            continue
        value = row.get(candidate, 0.0)
        if pd.isna(value):
            continue
        val = float(value)
        if val > 0:
            shares.append(val)
    if not shares:
        other_val = row.get("other", 0.0)
        if not pd.isna(other_val) and float(other_val) > 0:
            shares.append(float(other_val))
    return shares


def _safe_weighted_slope(x: list[float], y: list[float], w: list[float]) -> float:
    if len(x) < 2:
        return 0.0
    total_w = sum(w)
    if total_w <= 0:
        return 0.0
    x_mean = sum(wi * xi for wi, xi in zip(w, x, strict=False)) / total_w
    y_mean = sum(wi * yi for wi, yi in zip(w, y, strict=False)) / total_w
    cov = sum(
        wi * (xi - x_mean) * (yi - y_mean) for wi, xi, yi in zip(w, x, y, strict=False)
    )
    var = sum(wi * (xi - x_mean) ** 2 for wi, xi in zip(w, x, strict=False))
    if var <= 0:
        return 0.0
    return cov / var


def compute_chow_pressure_payload(polls_df: pd.DataFrame) -> dict:
    if polls_df.empty or "chow" not in polls_df.columns:
        return {
            "value": 0.0,
            "band": "low",
            "trend": "insufficient",
            "methodology_version": "v1-fragmentation-adjusted-demand",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "diagnostics": {
                "adaptive_half_life_days": BASELINE_HALF_LIFE_DAYS,
                "adaptive_trend_horizon_days": 28,
                "chow_share_std_recent": 0.0,
            },
        }

    df = polls_df.copy()
    df["_parsed_date"] = pd.to_datetime(df["date_published"], errors="coerce")
    df = df[df["_parsed_date"].notna()].sort_values("_parsed_date", kind="stable")
    if df.empty:
        return {
            "value": 0.0,
            "band": "low",
            "trend": "insufficient",
            "methodology_version": "v1-fragmentation-adjusted-demand",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "diagnostics": {
                "adaptive_half_life_days": BASELINE_HALF_LIFE_DAYS,
                "adaptive_trend_horizon_days": 28,
                "chow_share_std_recent": 0.0,
            },
        }

    latest = df["_parsed_date"].max()
    recent_cutoff = latest - pd.Timedelta(days=RECENT_WINDOW_DAYS)
    recent = df[df["_parsed_date"] >= recent_cutoff]

    chow_std = float(
        recent["chow"].fillna(0.0).std(ddof=0) if not recent.empty else 0.0
    )
    hl = adaptive_half_life_days(int(len(recent)), chow_std)
    horizon_days = adaptive_trend_horizon_days(int(len(recent)), chow_std)

    ages = (latest - df["_parsed_date"]).dt.total_seconds() / (24 * 3600)
    decay_lambda = math.log(2) / hl
    weights = ages.apply(lambda age: math.exp(-decay_lambda * max(0.0, float(age))))

    demands = []
    for _, row in df.iterrows():
        chow_share = float(row.get("chow", 0.0) or 0.0)
        non_chow_shares = _non_chow_shares_from_row(row)
        demands.append(poll_demand(chow_share, non_chow_shares))

    total_w = float(weights.sum())
    value = (
        float((pd.Series(demands) * weights).sum() / total_w) if total_w > 0 else 0.0
    )

    trend_cutoff = latest - pd.Timedelta(days=horizon_days)
    trend_df = df[df["_parsed_date"] >= trend_cutoff].copy()
    if len(trend_df) < 2:
        trend = "insufficient"
    else:
        trend_demands = []
        for _, row in trend_df.iterrows():
            trend_demands.append(
                poll_demand(
                    float(row.get("chow", 0.0) or 0.0), _non_chow_shares_from_row(row)
                )
            )
        trend_ages = (latest - trend_df["_parsed_date"]).dt.total_seconds() / (
            24 * 3600
        )
        trend_weights = trend_ages.apply(
            lambda age: math.exp(-math.log(2) / hl * max(0.0, float(age)))
        )
        x = [
            float(v)
            for v in trend_df["_parsed_date"].astype("int64") / 86_400_000_000_000
        ]
        y = [float(v) for v in trend_demands]
        w = [float(v) for v in trend_weights]
        slope = _safe_weighted_slope(x, y, w)
        trend = trend_label(slope)

    return {
        "value": round(value, 4),
        "band": _pressure_band(value),
        "trend": trend,
        "methodology_version": "v1-fragmentation-adjusted-demand",
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "diagnostics": {
            "adaptive_half_life_days": round(hl, 2),
            "adaptive_trend_horizon_days": horizon_days,
            "chow_share_std_recent": round(chow_std, 4),
        },
    }
