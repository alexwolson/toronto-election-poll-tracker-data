"""Firm-balanced descriptive mayoral Polling Estimate.

This module is deliberately pure and is not connected to snapshot generation.
It describes comparable Poll Readings; it does not forecast the election.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from .poll_sources import PollReading, PollResponse, PollSample, PollSourceBundle


_TORONTO = ZoneInfo("America/Toronto")
_MAX_AGE_DAYS = 21
_DECIDED_AND_LEANING_LABELS = frozenset(
    {
        "[decided/ leaning]",
        "decided and leaning",
        "decided and leaning voters",
    }
)
_POLITICAL_SPONSOR_MARKERS = (
    " campaign",
    "candidate ",
    " political party",
    "registered third-party",
)


@dataclass(frozen=True, slots=True)
class BallotCandidate:
    candidate_id: str
    candidate_name: str


@dataclass(frozen=True, slots=True)
class CandidateEstimate:
    candidate_id: str
    candidate_name: str
    share: Decimal


@dataclass(frozen=True, slots=True)
class PollingEstimateResult:
    status: Literal["preview", "available", "unavailable"]
    reason: str
    candidates: tuple[CandidateEstimate, ...] = ()
    poll_residual_share: Decimal | None = None
    selected_poll_sample_ids: tuple[str, ...] = ()
    selected_poll_reading_ids: tuple[str, ...] = ()
    unmeasured_final_candidates: tuple[BallotCandidate, ...] = ()


@dataclass(frozen=True, slots=True)
class _EligibleReading:
    sample: PollSample
    reading: PollReading
    candidate_shares: dict[str, Decimal]
    residual_share: Decimal


def _has_political_sponsor(sample: PollSample) -> bool:
    sponsor = f" {sample.sponsor or ''} ".casefold()
    return any(marker in sponsor for marker in _POLITICAL_SPONSOR_MARKERS)


def _is_self_selected(sample: PollSample) -> bool:
    mode = sample.collection_mode.casefold()
    return "self-selected" in mode or "self_selected" in mode


def _has_basic_methodology(sample: PollSample) -> bool:
    mode = sample.collection_mode.strip().casefold()
    has_size = sample.recruited_sample_size is not None or bool(
        re.search(r"\bn\s*=\s*[\d,]+", sample.notes or "", flags=re.IGNORECASE)
    )
    return mode not in {"", "not-reported", "not_reported"} and has_size


def _turnout_class(reading: PollReading) -> str:
    if reading.turnout_screen in {"none", "not_reported"}:
        return "general_citywide_adults"
    return reading.turnout_screen


def calculate_mayoral_polling_estimate(
    bundle: PollSourceBundle,
    *,
    election_cycle_id: str,
    contest_id: str,
    analysis_cutoff: datetime,
    final_ballot: tuple[BallotCandidate, ...],
    ballot_certified: bool,
) -> PollingEstimateResult:
    """Return the current descriptive estimate or a fail-closed status."""
    if analysis_cutoff.tzinfo is None:
        raise ValueError("analysis_cutoff must be timezone-aware")
    candidate_ids = tuple(candidate.candidate_id for candidate in final_ballot)
    if not candidate_ids or len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("final_ballot must contain unique candidates")

    samples = {sample.poll_sample_id: sample for sample in bundle.poll_samples}
    documents = {
        document.source_document_id: document for document in bundle.source_documents
    }
    responses_by_reading: dict[str, list[PollResponse]] = defaultdict(list)
    for response in bundle.poll_responses:
        responses_by_reading[response.poll_reading_id].append(response)

    cutoff_local = analysis_cutoff.astimezone(_TORONTO)
    eligible: list[_EligibleReading] = []
    for reading in bundle.poll_readings:
        sample = samples[reading.poll_sample_id]
        document = documents[reading.source_document_id]
        if (
            sample.election_cycle_id != election_cycle_id
            or sample.geography_type != "citywide"
            or reading.contest_type != "mayoral"
            or reading.contest_id != contest_id
            or sample.extraction_status != "extracted"
            or document.retrieval_status != "retrieved"
            or document.visual_qa_status != "passed"
            or _has_political_sponsor(sample)
            or _is_self_selected(sample)
            or not _has_basic_methodology(sample)
            or reading.reading_purpose != "general_vote_intention"
            or reading.response_coverage != "complete"
            or sample.evidence_available_at > analysis_cutoff
        ):
            continue
        age_days = (cutoff_local.date() - sample.fieldwork_end).days
        if not 0 <= age_days <= _MAX_AGE_DAYS:
            continue
        denominator = (reading.denominator_text or "").strip().casefold()
        if (
            reading.denominator_type != "custom"
            or denominator not in _DECIDED_AND_LEANING_LABELS
        ):
            continue

        candidate_shares: dict[str, Decimal] = {}
        residuals: list[Decimal] = []
        valid = True
        for response in responses_by_reading[reading.poll_reading_id]:
            if response.share is None:
                valid = False
                break
            if response.response_kind == "candidate":
                if (
                    response.candidate_id is None
                    or response.candidate_observation_status
                    != "individually_published"
                    or response.candidate_id not in candidate_ids
                    or response.candidate_id in candidate_shares
                ):
                    valid = False
                    break
                candidate_shares[response.candidate_id] = response.share
            elif response.response_kind == "other":
                residuals.append(response.share)
            else:
                valid = False
                break
        if not valid or not candidate_shares or not residuals:
            continue
        eligible.append(
            _EligibleReading(
                sample,
                reading,
                candidate_shares,
                sum(residuals, Decimal("0")),
            )
        )

    by_field: dict[tuple[str, frozenset[str]], list[_EligibleReading]] = defaultdict(list)
    for item in eligible:
        signature = (_turnout_class(item.reading), frozenset(item.candidate_shares))
        by_field[signature].append(item)
    replicated = {
        field: items
        for field, items in by_field.items()
        if len({item.sample.pollster.casefold() for item in items}) >= 2
        and len({item.sample.poll_sample_id for item in items}) >= 2
    }
    if not replicated:
        return PollingEstimateResult("unavailable", "insufficient_replication")

    maximal_fields = [
        signature
        for signature in replicated
        if not any(
            signature[0] == other[0] and signature[1] < other[1]
            for other in by_field
        )
    ]
    if not maximal_fields:
        return PollingEstimateResult(
            "unavailable", "expanded_field_awaiting_replication"
        )
    if len(maximal_fields) != 1:
        return PollingEstimateResult("unavailable", "incomparable_fields")

    signature = maximal_fields[0]
    field = signature[1]
    latest_by_pollster: dict[str, _EligibleReading] = {}
    for item in replicated[signature]:
        pollster = item.sample.pollster.casefold()
        current = latest_by_pollster.get(pollster)
        ordering = (
            item.sample.fieldwork_end,
            item.sample.evidence_available_at,
            item.sample.poll_sample_id,
            item.reading.poll_reading_id,
        )
        if current is None or ordering > (
            current.sample.fieldwork_end,
            current.sample.evidence_available_at,
            current.sample.poll_sample_id,
            current.reading.poll_reading_id,
        ):
            latest_by_pollster[pollster] = item
    selected = tuple(
        sorted(latest_by_pollster.values(), key=lambda item: item.sample.pollster.casefold())
    )
    divisor = Decimal(len(selected))
    name_by_id = {candidate.candidate_id: candidate.candidate_name for candidate in final_ballot}
    estimates = tuple(
        CandidateEstimate(
            candidate_id,
            name_by_id[candidate_id],
            sum(
                (item.candidate_shares[candidate_id] for item in selected),
                Decimal("0"),
            )
            / divisor,
        )
        for candidate_id in candidate_ids
        if candidate_id in field
    )
    residual = sum((item.residual_share for item in selected), Decimal("0")) / divisor
    unmeasured = tuple(
        candidate for candidate in final_ballot if candidate.candidate_id not in field
    )
    return PollingEstimateResult(
        "available" if ballot_certified else "preview",
        "qualifying_evidence" if ballot_certified else "provisional_ballot",
        estimates,
        residual,
        tuple(item.sample.poll_sample_id for item in selected),
        tuple(item.reading.poll_reading_id for item in selected),
        unmeasured,
    )
