#!/usr/bin/env python3
"""Build the Council v1 race-card snapshot (ADR 0043).

Assembles the 25 descriptive race cards and writes
data/processed/council_race_cards.json for the frontend. Descriptive only — no
forecast — and independent of the mayoral pipeline (ADR 0014).

Run: uv run scripts/build_council_snapshot.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.council_biography import load_council_results
from backend.model.council_hints import (
    load_officeholding_history,
    load_supported_hints,
)
from backend.model.council_race import load_registered_field, load_ward_incumbency
from backend.model.council_race_card import load_ward_poll_readings
from backend.model.council_snapshot import build_council_snapshot, load_ward_names

RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "council_race_cards.json"


def main() -> None:
    canonical = RAW / "canonical" / "election_results.csv"
    snapshot = build_council_snapshot(
        load_ward_incumbency(RAW / "defeatability" / "ward_defeatability.csv"),
        load_registered_field(RAW / "candidates" / "councillor_registered.csv"),
        load_council_results(canonical),
        load_ward_poll_readings(RAW / "polls" / "ward_poll_readings.csv"),
        ward_names=load_ward_names(RAW / "defeatability" / "data-qT4Kx.csv"),
        officeholding=load_officeholding_history(canonical),
        supported_hints=load_supported_hints(
            RAW / "hints" / "supported_historical_hints.csv"
        ),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, allow_nan=False, indent=None)

    wards = snapshot["wards"]
    open_seats = [w for w, c in wards.items() if c["is_open_seat"]]
    polled = [w for w, c in wards.items() if c["ward_polls"]]
    print(f"Council race cards written to {OUT}")
    print(
        f"  {len(wards)} wards | open seats: {sorted(open_seats, key=int)} "
        f"| with ward polls: {sorted(polled, key=int)}"
    )


if __name__ == "__main__":
    main()
