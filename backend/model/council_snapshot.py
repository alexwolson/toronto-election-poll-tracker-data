"""Assemble the 25 Council v1 race cards into one serializable snapshot (ADR 0043).

Pure composition: joins biographies, race assembly, prior results, CDI exposure
triggers, competitiveness facts, and raw ward polls into a JSON-ready dict for the
frontend. No model, no forecast — a descriptive race card per ward.
"""

from __future__ import annotations

import csv
from pathlib import Path

from backend.model.council_biography import (
    CandidateBiography,
    CouncilElectionResult,
    build_all_biographies,
)
from backend.model.council_race import (
    CouncilRace,
    RaceCandidate,
    WardIncumbent,
    build_council_races,
)
from backend.model.council_race_card import (
    COUNCIL_INCUMBENT_BASE_RATE_COPY,
    ExposureTrigger,
    PriorResult,
    WardPollReading,
    build_prior_results,
    derive_competitiveness_facts,
    race_exposure_triggers,
)

COUNCIL_RACE_CARD_SCHEMA_VERSION = 1


def load_ward_names(path: str | Path) -> dict[str, str]:
    """Ward number -> ward name, from Matt Elliott's CDI source (BOM-prefixed)."""
    names: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            ward = (row.get("Ward") or "").strip()
            name = (row.get("Ward Name") or "").strip().rstrip("*").strip()
            if ward and name:
                names[ward] = name
    return names


def _appearance(appearance) -> dict:
    return {
        "year": appearance.year,
        "ward": appearance.ward,
        "boundary_era": appearance.boundary_era,
        "vote_share": appearance.vote_share,
        "is_winner": appearance.is_winner,
    }


def _biography_card(bio: CandidateBiography | None) -> dict | None:
    if bio is None:
        return None
    win = bio.most_recent_win
    return {
        "council_wins": bio.council_wins,
        "is_former_councillor": bio.is_former_councillor,
        "most_recent_win": _appearance(win) if win else None,
        "appearances": [_appearance(a) for a in bio.appearances],
    }


def _incumbent_card(
    incumbent: WardIncumbent, triggers: tuple[ExposureTrigger, ...]
) -> dict:
    bio = incumbent.biography
    win = bio.most_recent_win if bio else None
    return {
        "name": incumbent.name,
        "is_byelection_incumbent": incumbent.is_byelection_incumbent,
        "defeatability_score": incumbent.defeatability_score,
        "council_wins": bio.council_wins if bio else 0,
        "most_recent_win": _appearance(win) if win else None,
        "exposure_triggers": [{"key": t.key, "copy": t.copy} for t in triggers],
    }


def _candidate_card(candidate: RaceCandidate) -> dict:
    bio = candidate.biography
    return {
        "display_name": candidate.display_name,
        "status": candidate.status,
        "candidate_id": candidate.candidate_id,
        "is_matched": candidate.is_matched,
        "is_former_councillor": bool(bio and bio.is_former_councillor),
        "council_wins": bio.council_wins if bio else 0,
        "biography": _biography_card(bio),
    }


def _prior_card(prior: PriorResult | None) -> dict | None:
    if prior is None:
        return None
    return {
        "year": prior.year,
        "winner_name": prior.winner_name,
        "winner_share": prior.winner_share,
        "winner_votes": prior.winner_votes,
        "runner_up_name": prior.runner_up_name,
        "runner_up_share": prior.runner_up_share,
        "margin_votes": prior.margin_votes,
        "margin_share": prior.margin_share,
        "field_size": prior.field_size,
    }


def _poll_card(reading: WardPollReading) -> dict:
    return {
        "poll_id": reading.poll_id,
        "firm": reading.firm,
        "date_conducted": reading.date_conducted,
        "date_published": reading.date_published,
        "sample_size": reading.sample_size,
        "methodology": reading.methodology,
        "denominator": reading.denominator,
        "ballot_status": reading.ballot_status,
        "undecided_share": reading.undecided_share,
        "candidates": [
            {
                "candidate_id": c.candidate_id,
                "candidate_name": c.candidate_name,
                "share": c.share,
                "is_incumbent": c.is_incumbent,
                "is_residual": c.is_residual,
                "registration_status": c.registration_status,
            }
            for c in reading.candidates
        ],
    }


def _race_card(
    race: CouncilRace,
    prior: PriorResult | None,
    ward_polls: tuple[WardPollReading, ...],
    ward_name: str | None,
) -> dict:
    facts = derive_competitiveness_facts(race, prior)
    triggers = race_exposure_triggers(race)
    return {
        "ward": race.ward,
        "ward_name": ward_name,
        "is_open_seat": race.is_open_seat,
        "incumbent_in_field": race.incumbent_in_field,
        "incumbency_flag_disagrees": race.incumbency_flag_disagrees,
        "incumbent": _incumbent_card(race.incumbent, triggers),
        "candidates": [_candidate_card(c) for c in race.candidates],
        "prior_result": _prior_card(prior),
        "competitiveness": {
            "field_size": facts.field_size,
            "candidates_who_won_this_ward": facts.candidates_who_won_this_ward,
            "both_won_this_ward": facts.both_won_this_ward,
            "prior_margin_votes": facts.prior_margin_votes,
            "prior_margin_share": facts.prior_margin_share,
        },
        "ward_polls": [_poll_card(r) for r in ward_polls],
    }


def build_council_snapshot(
    incumbency: dict[str, dict[str, str]],
    field: dict[str, list[dict[str, str]]],
    results: tuple[CouncilElectionResult, ...],
    ward_poll_readings: dict[str, tuple[WardPollReading, ...]],
    ward_names: dict[str, str] | None = None,
) -> dict:
    biographies = build_all_biographies(results)
    races = build_council_races(incumbency, field, biographies)
    priors = build_prior_results(results)
    names = ward_names or {}
    wards = {
        ward: _race_card(
            race, priors.get(ward), ward_poll_readings.get(ward, ()), names.get(ward)
        )
        for ward, race in races.items()
    }
    return {
        "schema_version": COUNCIL_RACE_CARD_SCHEMA_VERSION,
        "base_rate_note": COUNCIL_INCUMBENT_BASE_RATE_COPY,
        "wards": wards,
    }
