"""Adapt canonical historical mayoral data to the evaluation harness.

This module is deliberately only a data seam.  It builds complete observed
outcomes and cutoff-specific evidence views; it does not choose a statistical
model, a preferred poll reading, or a publication policy.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Final
from zoneinfo import ZoneInfo

from backend.model.historical_mayoral import (
    HistoricalMayoralCorpus,
    HistoricalPollReading,
    HistoricalPollResponse,
    HistoricalPollSample,
)
from backend.model.mayoral_endpoint import MayoralEndpointEvidence
from backend.model.mayoral_evaluation import (
    ElectionCycle,
    ElectionOutcome,
    LeadTimeSnapshot,
)


_TORONTO: Final = ZoneInfo("America/Toronto")
_REVISION_SCHEMA: Final = "historical-mayoral-evidence-v4"
_INCUMBENT_BY_CYCLE: Final = {
    # Rob Ford withdrew before the 2014 Final Ballot was settled.
    "toronto_2014": None,
    "toronto_2018": "tory",
    "toronto_2022": "tory",
    # The 2023 mayoral by-election was an open contest.
    "toronto_2023": None,
}


HistoricalMayoralEvidence = MayoralEndpointEvidence


def build_historical_mayoral_evaluation_cycles(
    corpus: HistoricalMayoralCorpus,
    *,
    lead_times: Sequence[int],
    analysis_time_local: time,
) -> tuple[ElectionCycle, ...]:
    """Build whole-election evaluation cycles from the canonical corpus.

    ``lead_times`` and ``analysis_time_local`` are mandatory so the adapter
    cannot silently freeze an evaluation grid or choose a time of day.  The
    supplied time is interpreted as Toronto wall-clock time on every cutoff
    date; resulting ``analysis_cutoff`` values are offset-aware. Cutoffs before
    the corpus's conservative Final Ballot availability boundary are rejected
    because the evaluation target exposes the complete candidate universe.
    """

    fixed_lead_times = _validate_lead_times(lead_times)
    local_time = _validate_local_analysis_time(analysis_time_local)
    relationships = _validate_and_index_relationships(corpus)

    cycles: list[ElectionCycle] = []
    for election in sorted(
        corpus.elections,
        key=lambda row: (row.election_date, row.election_cycle_id),
    ):
        cycle_id = election.election_cycle_id
        if cycle_id not in _INCUMBENT_BY_CYCLE:
            raise ValueError(f"unknown historical mayoral cycle {cycle_id!r}")

        outcome_pairs = corpus.outcome_share_vector(cycle_id)
        candidate_shares = {
            candidate_id: float(share) for candidate_id, share in outcome_pairs
        }
        incumbent_id = _INCUMBENT_BY_CYCLE[cycle_id]
        if incumbent_id is not None and incumbent_id not in candidate_shares:
            raise ValueError(
                f"source-backed incumbent {incumbent_id!r} is absent from "
                f"cycle {cycle_id!r}'s Final Ballot"
            )
        outcome = ElectionOutcome(
            candidate_shares=candidate_shares,
            incumbent_candidate_id=incumbent_id,
        )

        snapshots = tuple(
            _snapshot_at_cutoff(
                cycle_id=cycle_id,
                election_date=election.election_date,
                final_ballot_evidence_available_at=(
                    election.final_ballot_evidence_available_at
                ),
                days_before_election=days_before_election,
                analysis_time_local=local_time,
                samples_by_cycle=relationships.samples_by_cycle,
                readings_by_sample=relationships.readings_by_sample,
                responses_by_reading=relationships.responses_by_reading,
            )
            for days_before_election in fixed_lead_times
        )
        cycles.append(
            ElectionCycle(
                election_cycle_id=cycle_id,
                election_type=election.election_type,
                snapshots=snapshots,
                outcome=outcome,
            )
        )
    return tuple(cycles)


@dataclass(frozen=True, slots=True)
class _Relationships:
    samples_by_cycle: dict[str, tuple[HistoricalPollSample, ...]]
    readings_by_sample: dict[str, tuple[HistoricalPollReading, ...]]
    responses_by_reading: dict[str, tuple[HistoricalPollResponse, ...]]


def _validate_and_index_relationships(
    corpus: HistoricalMayoralCorpus,
) -> _Relationships:
    elections_by_id = _unique_by_id(
        corpus.elections,
        attribute="election_cycle_id",
        label="election cycle",
    )
    unknown_cycles = sorted(set(elections_by_id) - set(_INCUMBENT_BY_CYCLE))
    if unknown_cycles:
        raise ValueError(f"unknown historical mayoral cycle(s) {unknown_cycles}")

    outcomes_by_cycle: dict[str, list[object]] = {
        cycle_id: [] for cycle_id in elections_by_id
    }
    outcome_keys: set[tuple[str, str]] = set()
    for outcome in corpus.outcomes:
        if outcome.election_cycle_id not in elections_by_id:
            raise ValueError(
                f"outcome {outcome.candidate_id!r} references unknown cycle "
                f"{outcome.election_cycle_id!r}"
            )
        key = (outcome.election_cycle_id, outcome.candidate_id)
        if key in outcome_keys:
            raise ValueError(f"duplicate historical outcome relationship {key!r}")
        outcome_keys.add(key)
        outcomes_by_cycle[outcome.election_cycle_id].append(outcome)
    cycles_without_outcomes = sorted(
        cycle_id for cycle_id, rows in outcomes_by_cycle.items() if not rows
    )
    if cycles_without_outcomes:
        raise ValueError(
            f"historical cycle(s) have no complete outcome {cycles_without_outcomes}"
        )

    samples_by_id = _unique_by_id(
        corpus.poll_samples,
        attribute="poll_sample_id",
        label="poll sample",
    )
    samples_by_cycle_lists: dict[str, list[HistoricalPollSample]] = {
        cycle_id: [] for cycle_id in elections_by_id
    }
    for sample in samples_by_id.values():
        if sample.election_cycle_id not in elections_by_id:
            raise ValueError(
                f"poll sample {sample.poll_sample_id!r} references unknown cycle "
                f"{sample.election_cycle_id!r}"
            )
        if sample.evidence_available_at.utcoffset() is None:
            raise ValueError(
                f"poll sample {sample.poll_sample_id!r} has a naive "
                "evidence_available_at"
            )
        samples_by_cycle_lists[sample.election_cycle_id].append(sample)

    readings_by_id = _unique_by_id(
        corpus.poll_readings,
        attribute="poll_reading_id",
        label="poll reading",
    )
    readings_by_sample_lists: dict[str, list[HistoricalPollReading]] = {
        sample_id: [] for sample_id in samples_by_id
    }
    for reading in readings_by_id.values():
        if reading.poll_sample_id not in samples_by_id:
            raise ValueError(
                f"poll reading {reading.poll_reading_id!r} references unknown "
                f"sample {reading.poll_sample_id!r}"
            )
        readings_by_sample_lists[reading.poll_sample_id].append(reading)

    responses_by_reading_lists: dict[str, list[HistoricalPollResponse]] = {
        reading_id: [] for reading_id in readings_by_id
    }
    response_keys: set[tuple[str, str]] = set()
    for response in corpus.poll_responses:
        if response.poll_reading_id not in readings_by_id:
            raise ValueError(
                f"poll response {response.response_option_id!r} references unknown "
                f"reading {response.poll_reading_id!r}"
            )
        key = (response.poll_reading_id, response.response_option_id)
        if key in response_keys:
            raise ValueError(f"duplicate historical poll response {key!r}")
        response_keys.add(key)
        responses_by_reading_lists[response.poll_reading_id].append(response)

    return _Relationships(
        samples_by_cycle={
            cycle_id: tuple(
                sorted(rows, key=lambda sample: sample.poll_sample_id)
            )
            for cycle_id, rows in samples_by_cycle_lists.items()
        },
        readings_by_sample={
            sample_id: tuple(
                sorted(rows, key=lambda reading: reading.poll_reading_id)
            )
            for sample_id, rows in readings_by_sample_lists.items()
        },
        responses_by_reading={
            reading_id: tuple(
                sorted(
                    rows,
                    key=lambda response: (
                        response.option_order is None,
                        response.option_order or 0,
                        response.response_option_id,
                    ),
                )
            )
            for reading_id, rows in responses_by_reading_lists.items()
        },
    )


def _snapshot_at_cutoff(
    *,
    cycle_id: str,
    election_date: date,
    final_ballot_evidence_available_at: datetime,
    days_before_election: int,
    analysis_time_local: time,
    samples_by_cycle: dict[str, tuple[HistoricalPollSample, ...]],
    readings_by_sample: dict[str, tuple[HistoricalPollReading, ...]],
    responses_by_reading: dict[str, tuple[HistoricalPollResponse, ...]],
) -> LeadTimeSnapshot:
    cutoff_date = election_date - timedelta(days=days_before_election)
    cutoff = datetime.combine(cutoff_date, analysis_time_local, tzinfo=_TORONTO)
    if cutoff < final_ballot_evidence_available_at:
        raise ValueError(
            f"cycle {cycle_id!r} cutoff {cutoff.isoformat()} precedes the "
            "conservatively knowable Final Ballot"
        )
    samples = tuple(
        sample
        for sample in samples_by_cycle[cycle_id]
        if sample.evidence_available_at <= cutoff
    )
    readings = tuple(
        reading
        for sample in samples
        for reading in readings_by_sample[sample.poll_sample_id]
    )
    responses = tuple(
        response
        for reading in readings
        for response in responses_by_reading[reading.poll_reading_id]
    )
    evidence = HistoricalMayoralEvidence(
        election_cycle_id=cycle_id,
        final_ballot_evidence_available_at=final_ballot_evidence_available_at,
        poll_samples=samples,
        poll_readings=readings,
        poll_responses=responses,
    )
    return LeadTimeSnapshot(
        days_before_election=days_before_election,
        analysis_cutoff=cutoff,
        evidence_revision=_evidence_revision(evidence),
        evidence=evidence,
    )


def _evidence_revision(evidence: HistoricalMayoralEvidence) -> str:
    payload = {
        "schema": _REVISION_SCHEMA,
        "evidence": _canonical_value(evidence),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _canonical_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, datetime):
        if value.utcoffset() is None:
            raise ValueError("cannot revise evidence containing a naive datetime")
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(
        f"unsupported canonical evidence value {type(value).__name__}"
    )


def _unique_by_id(
    rows: tuple[object, ...],
    *,
    attribute: str,
    label: str,
) -> dict[str, object]:
    result: dict[str, object] = {}
    for row in rows:
        identifier = getattr(row, attribute)
        if identifier in result:
            raise ValueError(f"duplicate {label} ID {identifier!r}")
        result[identifier] = row
    return result


def _validate_lead_times(lead_times: Sequence[int]) -> tuple[int, ...]:
    values = tuple(lead_times)
    if not values:
        raise ValueError("lead_times must not be empty")
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("lead_times must contain non-negative integers")
    if len(set(values)) != len(values):
        raise ValueError("lead_times must not contain duplicates")
    return values


def _validate_local_analysis_time(value: time) -> time:
    if not isinstance(value, time):
        raise TypeError("analysis_time_local must be a datetime.time")
    if value.tzinfo is not None:
        raise ValueError(
            "analysis_time_local must be a naive Toronto wall-clock time"
        )
    return value
