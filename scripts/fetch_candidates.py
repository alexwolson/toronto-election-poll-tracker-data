#!/usr/bin/env python3
"""Fetch registered candidates from Toronto Elections API.

Downloads the city's candidate lists for the 2026 municipal election and
saves clean CSVs to data/raw/candidates/.

Outputs:
  data/raw/candidates/mayor_registered.csv
  data/raw/candidates/councillor_registered.csv

Run: uv run scripts/fetch_candidates.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

MAYOR_URL = "https://www.toronto.ca/data/elections/candidate_list/mayorCandidates_2026.json"
COUNCILLOR_URL = "https://www.toronto.ca/data/elections/candidate_list/councilorCandidates_2026.json"

OUTPUT_DIR = Path("data/raw/candidates")


def _parse_date(date_str: str) -> str:
    """Convert '01-May-2026' to '2026-05-01'."""
    try:
        return datetime.strptime(date_str, "%d-%b-%Y").strftime("%Y-%m-%d")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Unparseable dateNomination: {date_str!r}") from exc


def _parse_mayor_response(data: dict) -> list[dict]:
    """Parse city API response dict for mayor candidates."""
    return [
        {
            "first_name": c["firstName"],
            "last_name": c["lastName"],
            "status": c["status"],
            "date_nomination": _parse_date(c["dateNomination"]),
        }
        for c in data["candidates"]
    ]


def _parse_councillor_response(data: dict) -> list[dict]:
    """Parse city API response dict for councillor candidates."""
    records = []
    for ward in data["ward"]:
        ward_num = int(ward["num"])
        for c in ward["candidate"]:
            records.append(
                {
                    "ward": ward_num,
                    "first_name": c["firstName"],
                    "last_name": c["lastName"],
                    "status": c["status"],
                    "date_nomination": _parse_date(c["dateNomination"]),
                }
            )
    return records


def fetch_mayor_candidates() -> list[dict]:
    r = requests.get(MAYOR_URL, timeout=30)
    r.raise_for_status()
    return _parse_mayor_response(r.json())


def fetch_councillor_candidates() -> list[dict]:
    r = requests.get(COUNCILLOR_URL, timeout=30)
    r.raise_for_status()
    return _parse_councillor_response(r.json())


def write_with_sidecar(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    sidecar = path.with_suffix(".json")
    sidecar.write_text(
        json.dumps({"fetched_at": datetime.now(timezone.utc).isoformat()}, indent=2),
        encoding="utf-8",
    )
    print(f"  Written: {path} ({len(df)} rows)")


def main() -> None:
    print("Fetching mayor candidates...")
    mayor_records = fetch_mayor_candidates()
    if not mayor_records:
        raise RuntimeError("No mayor candidates fetched — check URL and network")
    df_mayors = pd.DataFrame(mayor_records)
    write_with_sidecar(df_mayors, OUTPUT_DIR / "mayor_registered.csv")

    print("Fetching councillor candidates...")
    councillor_records = fetch_councillor_candidates()
    if not councillor_records:
        raise RuntimeError("No councillor candidates fetched — check URL and network")
    df_councillors = pd.DataFrame(councillor_records)
    write_with_sidecar(df_councillors, OUTPUT_DIR / "councillor_registered.csv")

    print("Done.")


if __name__ == "__main__":
    main()
