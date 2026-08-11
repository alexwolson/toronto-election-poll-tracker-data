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

from model.run import build_mayoral_products, load_processed_data, run_model
from model.snapshot import save_snapshot, _sanitize_for_json

DATA_DIR = ROOT / "data" / "processed"


def build_registered_candidates_snapshot() -> dict:
    """Load processed registered candidates and return snapshot dict."""
    mayors_path = DATA_DIR / "mayor_registered.csv"
    councillors_path = DATA_DIR / "councillor_registered.csv"

    mayors: list[dict] = []
    if mayors_path.exists():
        df = pd.read_csv(mayors_path)
        mayors = df.to_dict(orient="records")

    councillors: dict[str, list] = {}
    if councillors_path.exists():
        df = pd.read_csv(councillors_path)
        df["ward"] = df["ward"].astype(int)
        for ward_num, group in df.groupby("ward"):
            councillors[str(ward_num)] = (
                group.drop(columns=["ward"]).to_dict(orient="records")
            )

    return {"mayors": mayors, "councillors": councillors}


def build_polls_snapshot(mayoral_race: dict[str, Any]) -> dict[str, Any]:
    from model.candidates import build_candidate_status
    from model.mayoral import classify_poll_use, field_candidates
    from model.mayoral_config import SNAPSHOT_SCHEMA_VERSION

    mayor_reg_path = DATA_DIR / "mayor_registered.csv"
    mayor_records = (
        pd.read_csv(mayor_reg_path).to_dict(orient="records")
        if mayor_reg_path.exists()
        else []
    )
    candidate_status = build_candidate_status(mayor_records)

    polls_df = pd.read_csv(DATA_DIR / "polls.csv")

    def candidate_ranges(df: pd.DataFrame, status_dict: dict) -> dict:
        out: dict = {"declared": {}, "potential": {}, "declined": {}}
        for status, candidates in status_dict.items():
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
        use = classify_poll_use(row.get("field_tested"))
        history.append({
            "poll_id": str(row.get("poll_id", "")),
            "date_published": str(row.get("date_published", "")),
            "firm": str(row.get("firm", "")),
            "sample_size": int(row.get("sample_size", 0)) if pd.notna(row.get("sample_size")) else 0,
            "field_tested": str(row.get("field_tested", "")),
            "candidates": {
                candidate: round(float(row[candidate]), 4)
                for candidate in row_field
                if candidate in row and pd.notna(row[candidate])
            },
            "excluded_from_current_average": use != "current_average",
            "use": use,
        })

    registered = build_registered_candidates_snapshot()

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "mayoral_race": mayoral_race,
        "total_polls_available": int(len(polls_df)),
        "candidate_status": candidate_status,
        "candidate_ranges": candidate_ranges(polls_df, candidate_status),
        "poll_history": history,
        "registered_candidates": registered,
    }


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(_sanitize_for_json(data), f, allow_nan=False)


def main() -> None:
    load_processed_data.cache_clear()
    build_mayoral_products.cache_clear()

    mayoral_race, _ = build_mayoral_products()
    result = run_model(mayoral_race)
    model_path = save_snapshot(result)
    print(f"Model snapshot written to {model_path}")

    polls_data = build_polls_snapshot(mayoral_race)
    polls_path = DATA_DIR / "polls_snapshot.json"
    save_json(polls_data, polls_path)
    print(f"Polls snapshot written to {polls_path}")


if __name__ == "__main__":
    main()
