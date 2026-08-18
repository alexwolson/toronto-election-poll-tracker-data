#!/usr/bin/env python3
"""Print non-public ward polling previews from the audited source bundle."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path, PurePath


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.poll_sources import load_poll_source_bundle
from backend.model.polling_estimate import BallotCandidate
from backend.model.ward_polling import WardPollingResult, calculate_ward_polling


def _candidate_id(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return "-".join(re.findall(r"[a-z0-9]+", ascii_name.casefold()))


def _registered_ballots() -> dict[int, tuple[BallotCandidate, ...]]:
    path = ROOT / "data" / "processed" / "councillor_registered.csv"
    ballots: dict[int, list[BallotCandidate]] = {ward: [] for ward in range(1, 26)}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["status"] != "Active":
                continue
            ward = int(row["ward"])
            name = f"{row['first_name']} {row['last_name']}"
            ballots[ward].append(BallotCandidate(_candidate_id(name), name))
    return {ward: tuple(candidates) for ward, candidates in ballots.items()}


def _json_default(value: object) -> str:
    if isinstance(value, (date, datetime, Decimal, PurePath)):
        return str(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _result_payload(result: WardPollingResult) -> dict[str, object]:
    readings = []
    for view in result.readings:
        readings.append(
            {
                "poll_sample_id": view.sample.poll_sample_id,
                "poll_reading_id": view.reading.poll_reading_id,
                "pollster": view.sample.pollster,
                "fieldwork_start": view.sample.fieldwork_start,
                "fieldwork_end": view.sample.fieldwork_end,
                "age_days": view.age_days,
                "is_stale": view.is_stale,
                "is_latest_for_pollster": view.is_latest_for_pollster,
                "matches_ballot": view.matches_ballot,
                "scenario_label": view.reading.scenario_label,
                "population": view.reading.population,
                "turnout_screen": view.reading.turnout_screen,
                "denominator_type": view.reading.denominator_type,
                "denominator_text": view.reading.denominator_text,
                "source_url": view.source_document.publisher_url,
                "responses": [
                    {
                        "response_kind": response.response_kind,
                        "candidate_id": response.candidate_id,
                        "candidate_name": response.candidate_name,
                        "response_label": response.response_label,
                        "share": response.share,
                    }
                    for response in view.responses
                ],
            }
        )
    return {
        "evidence_tier": result.evidence_tier,
        "readings": readings,
        "estimate": asdict(result.estimate),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoff", type=datetime.fromisoformat, required=True)
    parser.add_argument("--ward", type=int, choices=range(1, 26), action="append")
    parser.add_argument("--certified", action="store_true")
    args = parser.parse_args()
    if args.cutoff.tzinfo is None:
        parser.error("--cutoff must include a UTC offset")

    bundle = load_poll_source_bundle(ROOT / "data" / "raw" / "polls")
    ballots = _registered_ballots()
    wards = sorted(set(args.ward or range(1, 26)))
    results = [
        {
            "ward": ward,
            **_result_payload(
                calculate_ward_polling(
                    bundle,
                    election_cycle_id="toronto-2026",
                    contest_id=f"toronto-ward-{ward}-2026",
                    analysis_cutoff=args.cutoff,
                    final_ballot=ballots[ward],
                    ballot_certified=args.certified,
                )
            ),
        }
        for ward in wards
    ]
    print(
        json.dumps(
            {
                "analysis_cutoff": args.cutoff,
                "ballot_certified": args.certified,
                "registration_source": (
                    "data/processed/councillor_registered.csv"
                ),
                "wards": results,
            },
            default=_json_default,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
