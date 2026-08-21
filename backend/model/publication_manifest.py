"""Publication package manifest (INT).

The top-level index the frontend reads first: which feeds exist, the live cycle's
Final-Ballot state, and — once the forecast feed is produced — a per-quantity
availability summary. Pure assembly; it computes no forecast and applies no gate.
"""

from __future__ import annotations

import json
from pathlib import Path

PUBLICATION_MANIFEST_SCHEMA_VERSION = 1

_FEEDS = {
    "mayoral_forecast": "mayoral_forecast.json",
    "mayoral_polling": "mayoral_polling.json",
    "council_race_cards": "council_race_cards.json",
    "manifest": "manifest.json",
}


def load_live_cycle(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def build_publication_manifest(
    *,
    as_of: str,
    live_cycle: dict,
    feed_versions: dict[str, int],
    mayoral_publication_summary: dict | None = None,
) -> dict:
    """Assemble the manifest. ``as_of`` is an ISO date (injected, so the manifest
    is deterministic under test). The Final Ballot is certified when the maintainer
    sets the explicit ``field_certified`` flag -- never inferred from the clock, so
    the field is never treated as final while nominations are still open."""
    certified = bool(live_cycle["field_certified"])
    return {
        "schema_version": PUBLICATION_MANIFEST_SCHEMA_VERSION,
        "generated_at": as_of,
        "election": {
            "cycle_id": live_cycle["election_cycle_id"],
            "election_date": live_cycle["election_date"],
            "nomination_close_date": live_cycle["nomination_close_date"],
            "final_ballot_certified": certified,
        },
        "feeds": dict(_FEEDS),
        "feed_versions": feed_versions,
        "mayoral_publication_summary": mayoral_publication_summary,
    }
