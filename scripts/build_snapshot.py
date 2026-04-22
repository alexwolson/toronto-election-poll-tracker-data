#!/usr/bin/env python3
"""Build model snapshot for API consumption.

Run: uv run scripts/build_snapshot.py
"""

from __future__ import annotations

import json
import math
import sys
from numbers import Real
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from model.run import load_processed_data, run_model
from model.snapshot import save_snapshot, _sanitize_for_json

DATA_DIR = ROOT / "data" / "processed"
FRONTEND_DATA_DIR = ROOT / "frontend" / "public" / "data"


def build_polls_snapshot() -> dict[str, Any]:
    from model.aggregator import (
        aggregate_polls,
        exclude_polls_with_declined_candidates,
        get_latest_scenario_polls,
        get_scenario_polls,
    )
    from model.run import DEFAULT_SCENARIO, SCENARIOS
    from model.pool import compute_pool_model
    from model.candidates import CANDIDATE_STATUS, DECLINED_CANDIDATE_IDS

    def normalize_candidate(value: str) -> str:
        return str(value).strip().lower()

    def field_candidates(field: object) -> set[str]:
        if pd.isna(field):
            return set()
        return {
            normalize_candidate(c)
            for c in str(field).split(",")
            if normalize_candidate(c) and normalize_candidate(c) != "other"
        }

    polls_df = pd.read_csv(DATA_DIR / "polls.csv")
    polls_df["_field_candidates"] = polls_df["field_tested"].apply(field_candidates)
    polls_df["_contains_declined"] = polls_df["_field_candidates"].apply(
        lambda names: len(names.intersection(DECLINED_CANDIDATE_IDS)) > 0
    )

    approval_path = DATA_DIR / "approval_ratings.csv"
    approval_df = pd.read_csv(approval_path) if approval_path.exists() else pd.DataFrame()

    pool_model = compute_pool_model(polls_df, approval_df)

    scenario_candidates = SCENARIOS.get(DEFAULT_SCENARIO, [])
    eligible_polls = exclude_polls_with_declined_candidates(polls_df, DECLINED_CANDIDATE_IDS)
    scenario_polls = get_scenario_polls(eligible_polls, scenario_candidates)
    current_polls = get_latest_scenario_polls(scenario_polls)
    aggregated = aggregate_polls(current_polls, scenario_candidates)
    aggregated = {k: round(v, 4) for k, v in aggregated.items() if v > 0.001}

    trend_df = current_polls.assign(
        _parsed_date=pd.to_datetime(current_polls["date_published"], errors="coerce"),
        _date_fallback=current_polls["date_published"].astype(str),
    ).sort_values(["_parsed_date", "_date_fallback"], kind="stable")
    trend = []
    for _, row in trend_df.iterrows():
        point = {"date": str(row["date_published"])}
        for candidate in scenario_candidates:
            point[candidate] = round(float(row[candidate]), 4) if candidate in row and pd.notna(row[candidate]) else 0.0
        trend.append(point)

    def candidate_ranges(df: pd.DataFrame) -> dict:
        out: dict = {"declared": {}, "potential": {}, "declined": {}}
        for status, candidates in CANDIDATE_STATUS.items():
            for candidate in candidates:
                cid = candidate["id"]
                if cid not in df.columns:
                    out[status][cid] = None
                    continue
                series = pd.to_numeric(df[cid], errors="coerce").dropna()
                if series.empty:
                    out[status][cid] = None
                    continue
                out[status][cid] = {
                    "min": round(float(series.min()) * 100, 1),
                    "max": round(float(series.max()) * 100, 1),
                }
        return out

    history = []
    for _, row in polls_df.sort_values("date_published", ascending=False).iterrows():
        row_field = field_candidates(row.get("field_tested"))
        excluded_reason = None
        if bool(row.get("_contains_declined", False)):
            excluded_reason = "declined_candidate"
        elif len(row_field) == 2:
            excluded_reason = "head_to_head"
        history.append({
            "poll_id": str(row.get("poll_id", "")),
            "date_published": str(row.get("date_published", "")),
            "firm": str(row.get("firm", "")),
            "sample_size": int(row.get("sample_size", 0)) if pd.notna(row.get("sample_size")) else 0,
            "field_tested": str(row.get("field_tested", "")),
            "excluded_from_model": excluded_reason is not None,
            "excluded_reason": excluded_reason,
        })

    return {
        "pool_model": pool_model,
        "aggregated": aggregated,
        "polls_used": len(current_polls),
        "candidates": sorted(aggregated.keys()),
        "trend": trend,
        "total_polls_available": int(len(polls_df)),
        "excluded_declined_polls": int(polls_df["_contains_declined"].sum()),
        "candidate_status": CANDIDATE_STATUS,
        "candidate_ranges": candidate_ranges(polls_df),
        "poll_history": history,
        "chow_pressure": None,
    }


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(_sanitize_for_json(data), f, allow_nan=False)


def main() -> None:
    load_processed_data.cache_clear()
    run_model.cache_clear()

    result = run_model()
    model_path = save_snapshot(result)
    print(f"Model snapshot written to {model_path}")

    polls_data = build_polls_snapshot()
    polls_path = DATA_DIR / "polls_snapshot.json"
    save_json(polls_data, polls_path)
    print(f"Polls snapshot written to {polls_path}")

    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for src in [model_path, polls_path]:
        dest = FRONTEND_DATA_DIR / src.name
        dest.write_bytes(src.read_bytes())
        print(f"Copied {src.name} → {dest}")


if __name__ == "__main__":
    main()
