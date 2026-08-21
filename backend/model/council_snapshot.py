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
from backend.model.council_hints import (
    CandidacyRecord,
    FiredHint,
    PastElection,
    SignalSource,
    SupportedHint,
    candidate_features,
    fire_candidate_hints,
    past_election_history,
    resolve_person_id,
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
    parse_new_voter_margin,
    race_exposure_triggers,
)

COUNCIL_RACE_CARD_SCHEMA_VERSION = 3


def _race_candidate_hints(
    race: CouncilRace,
    history_by_person: dict[str, list[CandidacyRecord]],
    name_variants: dict[str, set[frozenset[str]]],
    hints: tuple[SupportedHint, ...],
) -> dict[str, tuple[FiredHint, ...]]:
    """Fired historical hints per candidate display name for one ward.

    Each candidate is resolved to a single upstream person_id (generous match);
    the sitting incumbent is the candidate whose person_id equals the ward
    incumbent's, so their prior council record is correctly excluded.
    """
    incumbent_pid = resolve_person_id(race.incumbent.name, "", name_variants)
    features: dict[str, object] = {}
    for candidate in race.candidates:
        person_id = resolve_person_id(candidate.display_name, "", name_variants)
        if person_id is None or person_id not in history_by_person:
            features[candidate.display_name] = None
            continue
        features[candidate.display_name] = candidate_features(
            history_by_person[person_id],
            name=candidate.display_name,
            is_sitting_incumbent=incumbent_pid is not None
            and person_id == incumbent_pid,
        )
    fired: dict[str, tuple[FiredHint, ...]] = {}
    for candidate in race.candidates:
        own = features[candidate.display_name]
        if own is None:
            fired[candidate.display_name] = ()
            continue
        opponents = [
            features[other.display_name]
            for other in race.candidates
            if other.display_name != candidate.display_name
            and features[other.display_name] is not None
        ]
        fired[candidate.display_name] = fire_candidate_hints(
            own, opponents, is_open_contest=race.is_open_seat, hints=hints
        )
    return fired


def _race_candidate_offices(
    race: CouncilRace,
    history_by_person: dict[str, list[CandidacyRecord]],
    name_variants: dict[str, set[frozenset[str]]],
) -> dict[str, tuple[PastElection, ...]]:
    """Past election history per candidate display name (ADR 0050), from the same
    generous all-offices person resolution the hints use — independent of the
    council-only biography match, so a former MP/MPP/trustee with no council
    history still gets a history."""
    offices: dict[str, tuple[PastElection, ...]] = {}
    for candidate in race.candidates:
        person_id = resolve_person_id(candidate.display_name, "", name_variants)
        if person_id is None or person_id not in history_by_person:
            offices[candidate.display_name] = ()
            continue
        offices[candidate.display_name] = past_election_history(
            history_by_person[person_id]
        )
    return offices


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
        # CDI component values, for concrete ward-fact explanations (ticket 05)
        "vote_share": incumbent.vote_share,
        "electorate_share": incumbent.electorate_share,
        "new_voter_margin": parse_new_voter_margin(incumbent.notes),
    }


def _signal_source_card(source: SignalSource) -> dict:
    return {
        "opponent_name": source.opponent_name,
        "office_type": source.office_type,
        "year": source.year,
        "district_name": source.district_name,
        "result": source.result,
        "rank": source.rank,
        "field_size": source.field_size,
        "margin": source.margin,
        "victory_count": source.victory_count,
        "qualifying_candidacy_count": source.qualifying_candidacy_count,
        "coverage": source.coverage,
    }


def _hint_card(hint: FiredHint) -> dict:
    return {
        "hint_id": hint.hint_id,
        "subject": hint.subject,
        "value": hint.value,
        "copy": hint.frontend_copy,
        "effect_pp": hint.effect_pp,
        "ci_low_pp": hint.ci_low_pp,
        "ci_high_pp": hint.ci_high_pp,
        "effect_unit": hint.effect_unit,
        "evidence_tier": hint.evidence_tier,
        "direction": hint.direction,
        "source": _signal_source_card(hint.source) if hint.source else None,
    }


def _past_election_card(election: PastElection) -> dict:
    return {
        "year": election.year,
        "election_date": election.election_date,
        "office_type": election.office_type,
        "represented_body": election.represented_body,
        "district_name": election.district_name,
        "party_name": election.party_name,
        "result": election.result,
        "vote_share": election.vote_share,
        "rank": election.rank,
        "field_size": election.field_size,
    }


def _candidate_card(
    candidate: RaceCandidate,
    hints: tuple[FiredHint, ...] = (),
    past_elections: tuple[PastElection, ...] = (),
) -> dict:
    bio = candidate.biography
    return {
        "display_name": candidate.display_name,
        "status": candidate.status,
        "candidate_id": candidate.candidate_id,
        "is_matched": candidate.is_matched,
        "is_former_councillor": bool(bio and bio.is_former_councillor),
        "council_wins": bio.council_wins if bio else 0,
        "biography": _biography_card(bio),
        "historical_hints": [_hint_card(h) for h in hints],
        "past_elections": [_past_election_card(e) for e in past_elections],
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
    candidate_hints: dict[str, tuple[FiredHint, ...]],
    candidate_offices: dict[str, tuple[PastElection, ...]],
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
        "candidates": [
            _candidate_card(
                c,
                candidate_hints.get(c.display_name, ()),
                candidate_offices.get(c.display_name, ()),
            )
            for c in race.candidates
        ],
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
    officeholding: tuple[
        dict[str, list[CandidacyRecord]], dict[str, set[frozenset[str]]]
    ]
    | None = None,
    supported_hints: tuple[SupportedHint, ...] = (),
) -> dict:
    biographies = build_all_biographies(results)
    races = build_council_races(incumbency, field, biographies)
    priors = build_prior_results(results)
    names = ward_names or {}
    history_by_person, name_variants = officeholding or ({}, {})

    def ward_hints(race: CouncilRace) -> dict[str, tuple[FiredHint, ...]]:
        if not supported_hints or not history_by_person:
            return {}
        return _race_candidate_hints(
            race, history_by_person, name_variants, supported_hints
        )

    def ward_offices(race: CouncilRace) -> dict[str, tuple[PastElection, ...]]:
        # Independent of supported_hints: past elections need only the canonical.
        if not history_by_person:
            return {}
        return _race_candidate_offices(race, history_by_person, name_variants)

    wards = {
        ward: _race_card(
            race,
            priors.get(ward),
            ward_poll_readings.get(ward, ()),
            names.get(ward),
            ward_hints(race),
            ward_offices(race),
        )
        for ward, race in races.items()
    }
    return {
        "schema_version": COUNCIL_RACE_CARD_SCHEMA_VERSION,
        "base_rate_note": COUNCIL_INCUMBENT_BASE_RATE_COPY,
        "wards": wards,
    }
