#!/usr/bin/env python3
"""Build the frontend publication package (INT).

Emits the typed data feeds the frontend ingests, into data/processed/:
  - mayoral_polling.json   descriptive current-cycle polls + raw trend
  - manifest.json          index + live-cycle Final-Ballot state + feed versions
  - mayoral_forecast.json  (pending: the live endpoint forecast feed)
The council feed (council_race_cards.json) is produced by build_council_snapshot.py.

Run: uv run scripts/build_publication_snapshot.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.council_snapshot import COUNCIL_RACE_CARD_SCHEMA_VERSION
from backend.model.mayoral_polling_feed import (
    MAYORAL_POLLING_FEED_SCHEMA_VERSION,
    build_mayoral_polling_feed,
)
from backend.model.publication_manifest import (
    build_publication_manifest,
    load_live_cycle,
)

RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"


def _write(name: str, payload: dict) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, allow_nan=False, indent=None)
    print(f"  wrote {path.relative_to(ROOT)}")


def main() -> None:
    as_of = datetime.now(ZoneInfo("America/Toronto")).date().isoformat()

    polling = build_mayoral_polling_feed(RAW / "polls" / "polls.csv")
    _write("mayoral_polling.json", polling)

    live_cycle = load_live_cycle(RAW / "elections" / "live_cycle.json")
    manifest = build_publication_manifest(
        as_of=as_of,
        live_cycle=live_cycle,
        feed_versions={
            "mayoral_polling": MAYORAL_POLLING_FEED_SCHEMA_VERSION,
            "council_race_cards": COUNCIL_RACE_CARD_SCHEMA_VERSION,
        },
    )
    _write("manifest.json", manifest)

    print(
        f"Publication package built (as of {as_of}); "
        f"Final Ballot certified: {manifest['election']['final_ballot_certified']}"
    )


if __name__ == "__main__":
    main()
