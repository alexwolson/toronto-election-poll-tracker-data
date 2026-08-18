#!/usr/bin/env python3
"""Print a non-public Polling Estimate preview from the audited source bundle."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.candidates import build_candidate_status
from backend.model.polling_estimate import (
    BallotCandidate,
    calculate_mayoral_polling_estimate,
)
from backend.model.poll_sources import load_poll_source_bundle


def _candidate(value: str) -> BallotCandidate:
    candidate_id, separator, candidate_name = value.partition("=")
    if not separator or not candidate_id.strip() or not candidate_name.strip():
        raise argparse.ArgumentTypeError("candidate must be ID=NAME")
    return BallotCandidate(candidate_id.strip(), candidate_name.strip())


def _json_default(value: object) -> str:
    if isinstance(value, (Decimal, datetime)):
        return str(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _registered_ballot() -> tuple[BallotCandidate, ...]:
    path = ROOT / "data" / "processed" / "mayor_registered.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))
    declared = build_candidate_status(records)["declared"]
    return tuple(
        BallotCandidate(candidate["id"], candidate["name"])
        for candidate in declared
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoff", type=datetime.fromisoformat, required=True)
    parser.add_argument("--candidate", type=_candidate, action="append")
    parser.add_argument("--certified", action="store_true")
    args = parser.parse_args()

    bundle = load_poll_source_bundle(ROOT / "data" / "raw" / "polls")
    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=args.cutoff,
        final_ballot=tuple(args.candidate) if args.candidate else _registered_ballot(),
        ballot_certified=args.certified,
    )
    print(json.dumps(asdict(result), default=_json_default, indent=2))


if __name__ == "__main__":
    main()
