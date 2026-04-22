"""Phase 1 Mayoral Pool Model.

Uses all polling data regardless of field configuration or candidate status.
Characterises voter preference pools without predicting electoral outcomes.

Designed for the pre-nomination period (before August 21, 2026).
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


# Floor uses candidate-count weighting (not recency) — it is a structural property.
# Polls with fewer than 500 respondents are excluded as unreliable.
MIN_FLOOR_SAMPLE_SIZE = 500

# Minimum number of non-Chow named candidates for a poll to count as "full field."
FULL_FIELD_THRESHOLD = 3

# Candidates to track in the anti-Chow pool.
ANTI_CHOW_CANDIDATES = ["bradford"]


def _rank_weights(dates: pd.Series) -> pd.Series:
    """Harmonic recency weights: most recent poll → 1/1, next → 1/2, etc.

    Polls with equal dates receive consecutive ranks in their original order.
    NaN dates receive weight 0.
    """
    parsed = pd.to_datetime(dates, utc=True, errors="coerce")
    ranks = parsed.rank(method="first", ascending=False, na_option="bottom")
    return (1.0 / ranks).where(parsed.notna(), 0.0)


def _count_non_chow_candidates(field_tested: object) -> int:
    """Count named non-Chow, non-other candidates in a field_tested string."""
    if pd.isna(field_tested):
        return 0
    return sum(
        1 for p in str(field_tested).split(",")
        if p.strip().lower() not in ("chow", "other", "")
    )


def compute_chow_floor(polls_df: pd.DataFrame) -> float:
    """Estimate Chow's structural support floor from full-field polls.

    Uses polls with 3+ non-Chow named candidates and sample_size >= 500.
    Weights by non-Chow candidate count (more candidates = more fragmented =
    better floor estimate). Does NOT use recency weighting — the floor is a
    structural property, not a recent trend.

    Returns 0.0 if no qualifying polls exist.
    """
    if "chow" not in polls_df.columns:
        return 0.0

    df = polls_df.copy()
    df["_non_chow_count"] = df["field_tested"].apply(_count_non_chow_candidates)
    df["_n"] = pd.to_numeric(df.get("sample_size", pd.Series(dtype=float)), errors="coerce").fillna(0)

    full_field = df[(df["_non_chow_count"] >= FULL_FIELD_THRESHOLD) & (df["_n"] >= MIN_FLOOR_SAMPLE_SIZE)]
    if full_field.empty:
        return 0.0

    shares = pd.to_numeric(full_field["chow"], errors="coerce")
    valid = shares.notna()
    if not valid.any():
        return 0.0

    weights = full_field.loc[valid, "_non_chow_count"].astype(float)
    total_w = float(weights.sum())
    if total_w <= 0:
        return 0.0
    return float((shares[valid] * weights).sum() / total_w)


def compute_current_h2h_chow(
    polls_df: pd.DataFrame,
    reference_date: datetime | None = None,
) -> float | None:
    """Recency-weighted Chow share from Bradford vs Chow head-to-head polls only.

    Excludes Tory vs Chow polls (Tory has declined). Uses 12-day half-life
    so the most recent Bradford H2H poll dominates.
    Returns None if no qualifying polls exist.
    """
    if "chow" not in polls_df.columns:
        return None

    h2h = polls_df[
        polls_df["field_tested"].apply(
            lambda f: (
                "bradford" in str(f).lower()
                and "chow" in str(f).lower()
                and _count_non_chow_candidates(f) == 1
            )
        )
    ].copy()

    if h2h.empty:
        return None

    weights = _rank_weights(h2h["date_published"])
    shares = pd.to_numeric(h2h["chow"], errors="coerce")
    valid = shares.notna()
    if not valid.any():
        return None

    total_w = float(weights[valid].sum())
    if total_w <= 0:
        return None
    return float((shares[valid] * weights[valid]).sum() / total_w)


def compute_current_approval(
    approval_df: pd.DataFrame,
    reference_date: datetime | None = None,
) -> dict[str, float]:
    """Recency-weighted approve/disapprove/not_sure from approval ratings.

    Uses 30-day half-life. Returns zeroed dict if approval_df is empty.
    """
    if approval_df.empty:
        return {"approve": 0.0, "disapprove": 0.0, "not_sure": 0.0}

    required_cols = {"approve", "disapprove", "not_sure", "date"}
    if not required_cols.issubset(approval_df.columns):
        return {"approve": 0.0, "disapprove": 0.0, "not_sure": 0.0}

    weights = _rank_weights(approval_df["date"])
    total_w = float(weights.sum())
    if total_w <= 0:
        return {"approve": 0.0, "disapprove": 0.0, "not_sure": 0.0}

    return {
        col: float(
            (pd.to_numeric(approval_df[col], errors="coerce").fillna(0.0) * weights).sum()
            / total_w
        )
        for col in ("approve", "disapprove", "not_sure")
    }


def compute_candidate_capture_rates(
    polls_df: pd.DataFrame,
    anti_chow_pool: float,
    reference_date: datetime | None = None,
) -> dict[str, dict[str, float]]:
    """Recency-weighted share and anti-Chow pool capture rate for tracked candidates.

    Uses multi-candidate polls (2+ non-Chow candidates). Missing candidates
    return share=0.0, capture_rate=0.0.
    """
    multi = polls_df[
        polls_df["field_tested"].apply(_count_non_chow_candidates) >= 2
    ].copy()

    result: dict[str, dict[str, float]] = {}
    for cand in ANTI_CHOW_CANDIDATES:
        if cand not in multi.columns or multi.empty:
            result[cand] = {"share": 0.0, "capture_rate": 0.0}
            continue

        weights = _rank_weights(multi["date_published"])
        shares = pd.to_numeric(multi[cand], errors="coerce").fillna(0.0)
        total_w = float(weights.sum())
        if total_w <= 0:
            result[cand] = {"share": 0.0, "capture_rate": 0.0}
            continue

        share = float((shares * weights).sum() / total_w)
        capture_rate = share / anti_chow_pool if anti_chow_pool > 0 else 0.0
        result[cand] = {"share": round(share, 4), "capture_rate": round(capture_rate, 4)}

    return result



def compute_consolidation_trend(
    polls_df: pd.DataFrame,
    anti_chow_pool: float,
    reference_date: datetime | None = None,
) -> str:
    """Is Bradford's anti-Chow pool capture rate rising, stalling, or reversing?

    Compares Bradford's unweighted mean capture rate in multi-candidate polls
    from the past 90 days vs polls older than 90 days.
    Returns: "consolidating" | "stalling" | "reversing" | "insufficient_data"
    """
    if anti_chow_pool <= 0 or "bradford" not in polls_df.columns:
        return "insufficient_data"

    ref = reference_date or datetime.now(timezone.utc)
    multi = polls_df[
        polls_df["field_tested"].apply(_count_non_chow_candidates) >= 2
    ].copy()
    if multi.empty:
        return "insufficient_data"

    multi["_date"] = pd.to_datetime(multi["date_published"], utc=True, errors="coerce")
    multi = multi[multi["_date"].notna()]
    cutoff = ref - pd.Timedelta(days=90)

    def mean_capture(df: pd.DataFrame) -> float | None:
        if df.empty:
            return None
        shares = pd.to_numeric(df["bradford"], errors="coerce").dropna()
        if shares.empty:
            return None
        return float(shares.mean()) / anti_chow_pool

    recent_rate = mean_capture(multi[multi["_date"] >= cutoff])
    earlier_rate = mean_capture(multi[multi["_date"] < cutoff])

    if recent_rate is None or earlier_rate is None:
        return "insufficient_data"

    delta = recent_rate - earlier_rate
    if delta > 0.05:
        return "consolidating"
    if delta < -0.05:
        return "reversing"
    return "stalling"


def _safe_float(val: object) -> float:
    """Convert value to float, returning 0.0 for NaN/None/unparseable."""
    v = pd.to_numeric(val, errors="coerce")
    return float(v) if pd.notna(v) else 0.0


def _get_approval_poll_detail(
    approval_df: pd.DataFrame,
    reference_date: datetime | None = None,
) -> list[dict]:
    """Per-row approval data with weights normalised so max weight = 1.0.

    Sorted by date descending (most recent first).
    Uses 'source' column as firm name (approval_ratings.csv convention).
    """
    required = {"date", "approve", "disapprove", "not_sure"}
    if approval_df.empty or not required.issubset(approval_df.columns):
        return []
    weights = _rank_weights(approval_df["date"])
    has_source = "source" in approval_df.columns
    rows = []
    for idx, row in approval_df.iterrows():
        rows.append({
            "date": str(row["date"]),
            "firm": str(row["source"]) if has_source else "",
            "approve": round(_safe_float(row["approve"]), 4),
            "disapprove": round(_safe_float(row["disapprove"]), 4),
            "not_sure": round(_safe_float(row["not_sure"]), 4),
            "weight": round(float(weights[idx]), 4),
        })
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def _get_floor_poll_detail(polls_df: pd.DataFrame) -> list[dict]:
    """Full-field qualifying polls (3+ non-Chow candidates, n≥500) with candidate weights.

    No recency weighting — the floor is a structural property.
    Sorted by date descending.
    """
    if "chow" not in polls_df.columns or "field_tested" not in polls_df.columns:
        return []
    df = polls_df.copy()
    df["_non_chow_count"] = df["field_tested"].apply(_count_non_chow_candidates)
    df["_n"] = pd.to_numeric(
        df.get("sample_size", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    qualifying = df[
        (df["_non_chow_count"] >= FULL_FIELD_THRESHOLD) & (df["_n"] >= MIN_FLOOR_SAMPLE_SIZE)
    ]
    if qualifying.empty:
        return []
    rows = []
    for _, row in qualifying.iterrows():
        rows.append({
            "date": str(row.get("date_published", "")),
            "firm": str(row.get("firm", "")),
            "field_tested": str(row.get("field_tested", "")),
            "chow": round(_safe_float(row["chow"]), 4),
            "sample_size": int(row["_n"]),
            "candidate_weight": int(row["_non_chow_count"]),
        })
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def _get_h2h_poll_detail(
    polls_df: pd.DataFrame,
    reference_date: datetime | None = None,
) -> list[dict]:
    """Bradford vs Chow H2H polls with recency weights normalised so max weight = 1.0.

    Applies the same filter as compute_current_h2h_chow: Bradford+Chow only,
    exactly 1 non-Chow named candidate. Sorted by date descending.
    """
    if "chow" not in polls_df.columns:
        return []
    h2h = polls_df[
        polls_df["field_tested"].apply(
            lambda f: (
                "bradford" in str(f).lower()
                and "chow" in str(f).lower()
                and _count_non_chow_candidates(f) == 1
            )
        )
    ].copy()
    if h2h.empty:
        return []
    weights = _rank_weights(h2h["date_published"])
    rows = []
    for idx, row in h2h.iterrows():
        rows.append({
            "date": str(row.get("date_published", "")),
            "firm": str(row.get("firm", "")),
            "chow": round(_safe_float(row["chow"]), 4),
            "bradford": round(_safe_float(row.get("bradford", 0.0)), 4),
            "sample_size": int(_safe_float(row.get("sample_size", 0))),
            "recency_weight": round(float(weights[idx]), 4),
        })
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def _get_capture_poll_detail(
    polls_df: pd.DataFrame,
    reference_date: datetime | None = None,
) -> list[dict]:
    """Multi-candidate polls (2+ non-Chow challengers) with recency weights normalised to max=1.0.

    Used to show Bradford's anti-Chow pool capture rate per poll.
    Sorted by date descending.
    """
    multi = polls_df[
        polls_df["field_tested"].apply(_count_non_chow_candidates) >= 2
    ].copy()
    if multi.empty or "bradford" not in multi.columns:
        return []
    weights = _rank_weights(multi["date_published"])
    rows = []
    for idx, row in multi.iterrows():
        rows.append({
            "date": str(row.get("date_published", "")),
            "firm": str(row.get("firm", "")),
            "field_tested": str(row.get("field_tested", "")),
            "bradford": round(_safe_float(row.get("bradford", 0.0)), 4),
            "recency_weight": round(float(weights[idx]), 4),
        })
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def compute_pool_model(
    polls_df: pd.DataFrame,
    approval_df: pd.DataFrame,
    reference_date: datetime | None = None,
) -> dict:
    """Compute the Phase 1 pool model from all polls and approval ratings.

    Returns a dict characterising current voter preferences without predicting
    electoral outcomes. Suitable for serialisation by the FastAPI endpoint.
    """
    chow_floor = compute_chow_floor(polls_df)
    approval = compute_current_approval(approval_df, reference_date)
    anti_chow_pool = approval["disapprove"]
    chow_ceiling = approval["approve"]

    chow_h2h = compute_current_h2h_chow(polls_df, reference_date)
    current_chow = chow_h2h if chow_h2h is not None else chow_floor

    pp_activated = max(0.0, current_chow - chow_floor)
    pp_reserve = max(0.0, chow_ceiling - current_chow)

    captures = compute_candidate_capture_rates(polls_df, anti_chow_pool, reference_date)
    named_captured = sum(c["share"] for c in captures.values())
    uncaptured = max(0.0, anti_chow_pool - named_captured)

    trend = compute_consolidation_trend(polls_df, anti_chow_pool, reference_date)

    if polls_df.empty or "field_tested" not in polls_df.columns:
        full_field_count = 0
    else:
        full_field_count = int(
            (
                (polls_df["field_tested"].apply(_count_non_chow_candidates) >= FULL_FIELD_THRESHOLD)
                & (pd.to_numeric(polls_df.get("sample_size", pd.Series(dtype=float)), errors="coerce").fillna(0) >= MIN_FLOOR_SAMPLE_SIZE)
            ).sum()
        )

    return {
        "phase_mode": "pre_nomination",
        "phase_mode_context": (
            "Candidate nominations open May 1, 2026 and close August 21, 2026. "
            "The field is not yet set — any candidate could still enter or withdraw. "
            "This model characterises current voter preferences, not electoral outcomes."
        ),
        "pool": {
            "chow_floor": round(chow_floor, 4),
            "chow_ceiling": round(chow_ceiling, 4),
            "anti_chow_pool": round(anti_chow_pool, 4),
            "chow_h2h_current": round(chow_h2h, 4) if chow_h2h is not None else None,
            "protective_progressive_activated": round(pp_activated, 4),
            "protective_progressive_reserve": round(pp_reserve, 4),
        },
        "candidates": captures,
        "uncaptured_anti_chow": round(uncaptured, 4),
        "consolidation_trend": trend,
        "approval": {
            "approve": round(approval["approve"], 4),
            "disapprove": round(approval["disapprove"], 4),
            "not_sure": round(approval["not_sure"], 4),
        },
        "data_notes": {
            "full_field_poll_count": full_field_count,
            "total_polls": len(polls_df),
            "approval_data_points": len(approval_df),
            "h2h_available": chow_h2h is not None,
        },
        "poll_detail": {
            "approval_polls": _get_approval_poll_detail(approval_df, reference_date),
            "floor_polls": _get_floor_poll_detail(polls_df),
            "h2h_polls": _get_h2h_poll_detail(polls_df, reference_date),
            "capture_polls": _get_capture_poll_detail(polls_df, reference_date),
        },
    }
