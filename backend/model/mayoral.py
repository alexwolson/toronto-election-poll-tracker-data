"""Observed mayoral evidence, kept separate from the election forecast.

This module deliberately answers only questions that the underlying source
directly measures.  Approval is never converted into candidate support and a
candidate missing from a ballot is never treated as having zero support.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .aggregator import compute_poll_weights
from .mayoral_config import RESIDUAL_ID, RESIDUAL_LABEL, TARGET_FIELD

APPROVAL_HALF_LIFE_DAYS = 30.0
MIN_CROWDED_FIELD_SAMPLE = 500
MIN_CROWDED_FIELD_CHALLENGERS = 3
TREND_MIN_POLLS = 3
TREND_MIN_DAYS = 14
TREND_MIN_FIRMS = 2


def field_candidates(field_tested: object) -> set[str]:
    """Normalised named candidates, excluding catch-all responses."""
    if pd.isna(field_tested):
        return set()
    return {
        token.strip().lower()
        for token in str(field_tested).split(",")
        if token.strip().lower() not in {"", "other", "undecided", "unknown"}
    }


def exact_field_polls(polls: pd.DataFrame, candidates: Iterable[str]) -> pd.DataFrame:
    target = {str(candidate).strip().lower() for candidate in candidates}
    if polls.empty or "field_tested" not in polls.columns:
        return polls.iloc[0:0].copy()
    if not target.issubset(polls.columns):
        return polls.iloc[0:0].copy()

    valid = polls["field_tested"].apply(field_candidates) == target
    for candidate in target:
        values = pd.to_numeric(polls[candidate], errors="coerce")
        valid &= values.notna() & values.between(0.0, 1.0)
    return polls[valid].copy()


def _reference_timestamp(reference_date: datetime | None) -> pd.Timestamp:
    ref = pd.Timestamp(reference_date or datetime.now(UTC))
    return ref.tz_localize(UTC) if ref.tzinfo is None else ref.tz_convert(UTC)


def _decay_weights(
    dates: pd.Series,
    half_life_days: float,
    reference_date: datetime | None,
) -> pd.Series:
    parsed = pd.to_datetime(dates, utc=True, errors="coerce")
    ref = _reference_timestamp(reference_date)
    age = ((ref - parsed).dt.total_seconds() / 86400.0).clip(lower=0.0)
    return (0.5 ** (age / half_life_days)).where(parsed.notna(), 0.0)


def _residual_share(row: pd.Series, candidates: Iterable[str]) -> float:
    named = sum(
        float(value)
        for candidate in candidates
        if pd.notna(value := pd.to_numeric(row.get(candidate), errors="coerce"))
    )
    return max(0.0, min(1.0, 1.0 - named))


def build_evidence_slice(
    polls: pd.DataFrame,
    candidates: Iterable[str],
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    """Recency-weighted evidence for one exact ballot configuration."""
    candidate_list = list(candidates)
    exact = exact_field_polls(polls, candidate_list)
    if exact.empty:
        return {
            "availability": "unavailable",
            "denominator": "poll_reported_vote_intention",
            "candidates": {},
            "residual": {"id": RESIDUAL_ID, "label": RESIDUAL_LABEL, "share": None},
            "poll_count": 0,
            "firm_count": 0,
            "latest_date": None,
            "series": [],
        }

    weights = compute_poll_weights(exact, reference_date)
    total_weight = float(weights.sum())
    if total_weight <= 0:
        return build_evidence_slice(exact.iloc[0:0], candidate_list, reference_date)

    shares = {
        candidate: float(
            (pd.to_numeric(exact[candidate], errors="coerce") * weights).sum()
            / total_weight
        )
        for candidate in candidate_list
    }
    residuals = exact.apply(lambda row: _residual_share(row, candidate_list), axis=1)
    residual = float((residuals * weights).sum() / total_weight)

    series: list[dict[str, Any]] = []
    ordered = exact.assign(
        _date=pd.to_datetime(exact["date_published"], errors="coerce")
    ).sort_values(["_date", "poll_id"], kind="stable")
    for _, row in ordered.iterrows():
        point: dict[str, Any] = {
            "poll_id": str(row.get("poll_id", "")),
            "date": str(row.get("date_published", "")),
            "firm": str(row.get("firm", "")),
            "sample_size": (
                int(row["sample_size"]) if pd.notna(row.get("sample_size")) else None
            ),
            "residual": round(_residual_share(row, candidate_list), 4),
        }
        for candidate in candidate_list:
            point[candidate] = round(float(row[candidate]), 4)
        series.append(point)

    return {
        "availability": "available",
        "denominator": "poll_reported_vote_intention",
        "candidates": {candidate: round(value, 4) for candidate, value in shares.items()},
        "residual": {
            "id": RESIDUAL_ID,
            "label": RESIDUAL_LABEL,
            "share": round(residual, 4),
        },
        "poll_count": int(len(exact)),
        "firm_count": int(exact["firm"].dropna().astype(str).nunique()),
        "latest_date": str(exact["date_published"].max()),
        "series": series,
    }


def validate_approval_data(approval: pd.DataFrame) -> None:
    required = {"date", "source", "approve", "disapprove", "not_sure"}
    missing = required.difference(approval.columns)
    if missing:
        raise ValueError(f"Approval data missing required columns: {sorted(missing)}")
    if approval.empty:
        return

    parsed_dates = pd.to_datetime(approval["date"], errors="coerce")
    if parsed_dates.isna().any():
        raise ValueError("Approval data contains an invalid date")
    if approval["source"].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError("Approval data contains an empty source")
    if approval.duplicated(subset=["date", "source"]).any():
        raise ValueError("Approval source/date records must be unique")

    values = approval[["approve", "disapprove", "not_sure"]].apply(
        pd.to_numeric, errors="coerce"
    )
    if values.isna().any().any() or ((values < 0.0) | (values > 1.0)).any().any():
        raise ValueError("Approval values must be finite proportions in [0, 1]")
    totals = values.sum(axis=1)
    if (~totals.between(0.99, 1.01)).any():
        raise ValueError("Approval responses must sum to 1 within rounding tolerance")


def build_approval_slice(
    approval: pd.DataFrame,
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    if approval.empty:
        return {
            "availability": "unavailable",
            "approve": None,
            "disapprove": None,
            "not_sure": None,
            "unreported": None,
            "reading_count": 0,
            "effective_reading_count": 0.0,
            "firm_count": 0,
            "latest_date": None,
            "readings": [],
        }

    validate_approval_data(approval)
    weights = _decay_weights(approval["date"], APPROVAL_HALF_LIFE_DAYS, reference_date)
    total_weight = float(weights.sum())
    if total_weight <= 0:
        return build_approval_slice(approval.iloc[0:0], reference_date)

    result = {
        key: float(
            (pd.to_numeric(approval[key], errors="coerce") * weights).sum()
            / total_weight
        )
        for key in ("approve", "disapprove", "not_sure")
    }
    result["unreported"] = max(0.0, 1.0 - sum(result.values()))
    effective = (total_weight**2) / float((weights**2).sum())
    normalised = weights / float(weights.max())
    readings = []
    for idx, row in approval.assign(_weight=normalised).sort_values(
        "date", ascending=False
    ).iterrows():
        readings.append(
            {
                "date": str(row["date"]),
                "firm": str(row["source"]),
                "methodology": str(row.get("methodology", "")),
                "approve": round(float(row["approve"]), 4),
                "disapprove": round(float(row["disapprove"]), 4),
                "not_sure": round(float(row["not_sure"]), 4),
                "weight": round(float(row["_weight"]), 4),
            }
        )

    return {
        "availability": "available",
        "approve": round(result["approve"], 4),
        "disapprove": round(result["disapprove"], 4),
        "not_sure": round(result["not_sure"], 4),
        "unreported": round(result["unreported"], 4),
        "reading_count": int(len(approval)),
        "effective_reading_count": round(float(effective), 2),
        "firm_count": int(approval["source"].astype(str).nunique()),
        "latest_date": str(approval["date"].max()),
        "readings": readings,
    }


def build_challenger_lane(current_field: dict[str, Any]) -> dict[str, Any]:
    shares = current_field.get("candidates", {})
    challengers = [candidate for candidate in TARGET_FIELD if candidate != "chow"]
    combined = sum(float(shares.get(candidate, 0.0)) for candidate in challengers)
    split = {
        candidate: round(float(shares.get(candidate, 0.0)) / combined, 4)
        for candidate in challengers
    } if combined > 0 else {}

    series = current_field.get("series", [])
    trend: dict[str, Any] = {
        "status": "insufficient_data",
        "reason": "At least three comparable polls spanning 14 days and two firms are required.",
    }
    if len(series) >= TREND_MIN_POLLS:
        dates = pd.to_datetime([point["date"] for point in series], errors="coerce")
        firms = {str(point.get("firm", "")) for point in series if point.get("firm")}
        span = int((dates.max() - dates.min()).days) if not dates.isna().any() else 0
        if span >= TREND_MIN_DAYS and len(firms) >= TREND_MIN_FIRMS:
            leader = max(split, key=split.get) if split else None
            lane_values = []
            for point in series:
                total = sum(float(point.get(candidate, 0.0)) for candidate in challengers)
                lane_values.append(float(point.get(leader, 0.0)) / total if total > 0 and leader else 0.0)
            change = lane_values[-1] - lane_values[0]
            state = "stable" if abs(change) < 0.02 else ("consolidating" if change > 0 else "fragmenting")
            trend = {"status": state, "change": round(change, 4), "reason": None}

    trailing_share = min(split.values()) if len(split) > 1 else 0.0
    return {
        "availability": "available" if combined > 0 else "unavailable",
        "combined_share": round(combined, 4) if combined > 0 else None,
        "named_split": split,
        "condition": "split" if trailing_share >= 0.10 else "concentrated",
        "trend": trend,
        "poll_count": current_field.get("poll_count", 0),
        "latest_date": current_field.get("latest_date"),
    }


def build_historical_context(polls: pd.DataFrame) -> dict[str, Any]:
    if polls.empty or "chow" not in polls.columns:
        return {"availability": "unavailable", "poll_count": 0}
    candidate_counts = polls["field_tested"].apply(
        lambda field: len(field_candidates(field).difference({"chow"}))
    )
    samples = pd.to_numeric(polls.get("sample_size"), errors="coerce").fillna(0)
    chow = pd.to_numeric(polls["chow"], errors="coerce")
    qualifying = polls[
        (candidate_counts >= MIN_CROWDED_FIELD_CHALLENGERS)
        & (samples >= MIN_CROWDED_FIELD_SAMPLE)
        & chow.notna()
    ].copy()
    if qualifying.empty:
        return {"availability": "unavailable", "poll_count": 0}
    values = pd.to_numeric(qualifying["chow"], errors="coerce")
    return {
        "availability": "available",
        "definition": "Polls with at least three named challengers and sample size of at least 500.",
        "chow_crowded_field_average": round(float(values.mean()), 4),
        "range": {"low": round(float(values.min()), 4), "high": round(float(values.max()), 4)},
        "poll_count": int(len(qualifying)),
    }


def classify_poll_use(field_tested: object) -> str:
    field = field_candidates(field_tested)
    if field == set(TARGET_FIELD):
        return "current_average"
    if field == {"chow", "bradford"}:
        return "head_to_head"
    return "different_candidate_field"


def poll_use_breakdown(polls: pd.DataFrame) -> dict[str, int]:
    counts = {
        "current_average": 0,
        "head_to_head": 0,
        "different_candidate_field": 0,
        "other": 0,
        "total": int(len(polls)),
    }
    for field in polls.get("field_tested", pd.Series(dtype=object)):
        key = classify_poll_use(field)
        counts[key if key in counts else "other"] += 1
    if sum(counts[key] for key in counts if key != "total") != counts["total"]:
        raise ValueError("Poll-use categories must sum to the tracked total")
    return counts


def build_mayoral_evidence(
    polls: pd.DataFrame,
    approval: pd.DataFrame,
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    current = build_evidence_slice(polls, TARGET_FIELD, reference_date)
    latest_dates = [
        value
        for value in (current.get("latest_date"), str(approval["date"].max()) if not approval.empty else None)
        if value
    ]
    return {
        "as_of": max(latest_dates) if latest_dates else _reference_timestamp(reference_date).date().isoformat(),
        "target_field": list(TARGET_FIELD),
        "current_field": current,
        "challenger_lane": build_challenger_lane(current),
        "head_to_head": build_evidence_slice(polls, ("chow", "bradford"), reference_date),
        "approval": build_approval_slice(approval, reference_date),
        "historical_context": build_historical_context(polls),
        "poll_breakdown": poll_use_breakdown(polls),
    }

