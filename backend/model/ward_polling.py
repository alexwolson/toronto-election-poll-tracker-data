"""Descriptive ward polling evidence and firm-balanced estimates.

This module is deliberately pure and is not connected to snapshot generation.
Ward Poll Readings remain visible when they cannot form an estimate.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from .poll_sources import (
    PollReading,
    PollResponse,
    PollSample,
    PollSourceBundle,
    SourceDocument,
)
from .polling_estimate import (
    BallotCandidate,
    CandidateEstimate,
    PollingEstimateResult,
)


_TORONTO = ZoneInfo("America/Toronto")
_MAX_ESTIMATE_AGE_DAYS = 21
_ALLOWED_TURNOUT_SCREENS = frozenset(
    {
        "none",
        "not_reported",
        "eligible_voters",
        "registered_voters",
        "likely_voters",
    }
)
_POLL_RESIDUAL_KINDS = frozenset({"other", "combined_residual"})
_NON_EXPRESSED_KINDS = frozenset(
    {
        "undecided",
        "refusal",
        "dont_know",
        "would_not_vote",
        "none_of_the_above",
        "no_answer",
    }
)
_POLITICAL_SPONSOR_MARKERS = (
    " campaign",
    "candidate ",
    " political party",
    "registered third-party",
)


@dataclass(frozen=True, slots=True)
class WardPollReadingView:
    sample: PollSample
    reading: PollReading
    source_document: SourceDocument
    responses: tuple[PollResponse, ...]
    age_days: int
    is_stale: bool
    is_latest_for_pollster: bool
    matches_ballot: bool


@dataclass(frozen=True, slots=True)
class WardPollingResult:
    evidence_tier: Literal["C0", "C1", "C2"]
    readings: tuple[WardPollReadingView, ...]
    estimate: PollingEstimateResult


@dataclass(frozen=True, slots=True)
class _EstimateReading:
    view: WardPollReadingView
    candidate_shares: dict[str, Decimal]
    residual_share: Decimal | None


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


def _candidate_ids(responses: tuple[PollResponse, ...]) -> frozenset[str]:
    return frozenset(
        response.candidate_id
        for response in responses
        if response.response_kind == "candidate"
        and response.candidate_id is not None
        and response.candidate_observation_status == "individually_published"
        and response.share is not None
    )


def _is_expressed_preference(
    reading: PollReading, responses: tuple[PollResponse, ...]
) -> bool:
    if reading.turnout_screen not in _ALLOWED_TURNOUT_SCREENS:
        return False
    if reading.denominator_type == "all_respondents":
        return False
    if any(response.response_kind in _NON_EXPRESSED_KINDS for response in responses):
        return False
    if reading.denominator_type in {"decided_respondents", "valid_responses"}:
        return True
    wording = f"{reading.denominator_text or ''} {reading.question_text or ''}".casefold()
    return "decided" in wording or "lean" in wording


def _estimate_values(
    view: WardPollReadingView,
) -> tuple[dict[str, Decimal], Decimal | None] | None:
    if not _is_expressed_preference(view.reading, view.responses):
        return None
    candidate_shares: dict[str, Decimal] = {}
    residuals: list[Decimal] = []
    for response in view.responses:
        if response.response_kind == "candidate":
            if (
                response.candidate_id is None
                or response.candidate_observation_status
                != "individually_published"
                or response.share is None
                or response.candidate_id in candidate_shares
            ):
                return None
            candidate_shares[response.candidate_id] = response.share
        elif response.response_kind in _POLL_RESIDUAL_KINDS:
            if response.share is None:
                return None
            residuals.append(response.share)
        elif response.response_kind in _NON_EXPRESSED_KINDS:
            return None
    if not candidate_shares:
        return None
    residual = sum(residuals, Decimal("0")) if residuals else None
    return candidate_shares, residual


def calculate_ward_polling(
    bundle: PollSourceBundle,
    *,
    election_cycle_id: str,
    contest_id: str,
    analysis_cutoff: datetime,
    final_ballot: tuple[BallotCandidate, ...],
    ballot_certified: bool,
) -> WardPollingResult:
    """Return source-faithful ward readings and any qualifying estimate."""
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
    provisional_views: list[
        tuple[PollSample, PollReading, SourceDocument, tuple[PollResponse, ...], int]
    ] = []
    for reading in bundle.poll_readings:
        sample = samples[reading.poll_sample_id]
        document = documents[reading.source_document_id]
        responses = tuple(responses_by_reading[reading.poll_reading_id])
        if (
            sample.election_cycle_id != election_cycle_id
            or sample.geography_type != "ward"
            or reading.contest_type != "council"
            or reading.contest_id != contest_id
            or sample.extraction_status != "extracted"
            or document.retrieval_status != "retrieved"
            or document.visual_qa_status != "passed"
            or _has_political_sponsor(sample)
            or _is_self_selected(sample)
            or not _has_basic_methodology(sample)
            or reading.reading_purpose != "general_vote_intention"
            or sample.evidence_available_at > analysis_cutoff
            or not _candidate_ids(responses)
        ):
            continue
        age_days = (cutoff_local.date() - sample.fieldwork_end).days
        if age_days < 0:
            continue
        provisional_views.append((sample, reading, document, responses, age_days))

    latest_sample_by_pollster: dict[str, tuple[object, ...]] = {}
    for sample, _, _, _, _ in provisional_views:
        key = sample.pollster.casefold()
        ordering = (
            sample.fieldwork_end,
            sample.evidence_available_at,
            sample.poll_sample_id,
        )
        latest_sample_by_pollster[key] = max(
            ordering, latest_sample_by_pollster.get(key, ordering)
        )

    ballot_ids = frozenset(candidate_ids)
    views = tuple(
        WardPollReadingView(
            sample=sample,
            reading=reading,
            source_document=document,
            responses=responses,
            age_days=age_days,
            is_stale=age_days > _MAX_ESTIMATE_AGE_DAYS,
            is_latest_for_pollster=(
                sample.fieldwork_end,
                sample.evidence_available_at,
                sample.poll_sample_id,
            )
            == latest_sample_by_pollster[sample.pollster.casefold()],
            matches_ballot=_candidate_ids(responses) <= ballot_ids,
        )
        for sample, reading, document, responses, age_days in sorted(
            provisional_views,
            key=lambda item: (
                item[0].fieldwork_end,
                item[0].evidence_available_at,
                item[0].poll_sample_id,
                item[1].document_display_order or 0,
                item[1].poll_reading_id,
            ),
        )
    )

    distinct_samples = {view.sample.poll_sample_id for view in views}
    distinct_pollsters = {view.sample.pollster.casefold() for view in views}
    if not views:
        evidence_tier: Literal["C0", "C1", "C2"] = "C0"
    elif len(distinct_samples) >= 2 and len(distinct_pollsters) >= 2:
        evidence_tier = "C2"
    else:
        evidence_tier = "C1"

    eligible: list[_EstimateReading] = []
    for view in views:
        if (
            view.is_stale
            or not view.matches_ballot
            or view.reading.response_coverage != "complete"
        ):
            continue
        values = _estimate_values(view)
        if values is None:
            continue
        candidate_shares, residual = values
        eligible.append(_EstimateReading(view, candidate_shares, residual))

    by_field: dict[frozenset[str], list[_EstimateReading]] = defaultdict(list)
    for item in eligible:
        by_field[frozenset(item.candidate_shares)].append(item)
    replicated = {
        field: items
        for field, items in by_field.items()
        if len({item.view.sample.pollster.casefold() for item in items}) >= 2
        and len({item.view.sample.poll_sample_id for item in items}) >= 2
    }
    if not replicated:
        reason = "no_qualifying_poll" if evidence_tier == "C0" else "insufficient_replication"
        return WardPollingResult(
            evidence_tier,
            views,
            PollingEstimateResult("unavailable", reason),
        )

    maximal_fields = [
        field
        for field in replicated
        if not any(field < other for other in by_field)
    ]
    if not maximal_fields:
        return WardPollingResult(
            evidence_tier,
            views,
            PollingEstimateResult(
                "unavailable", "expanded_field_awaiting_replication"
            ),
        )
    if len(maximal_fields) != 1:
        return WardPollingResult(
            evidence_tier,
            views,
            PollingEstimateResult("unavailable", "incomparable_fields"),
        )

    field = maximal_fields[0]
    latest_by_pollster: dict[str, _EstimateReading] = {}
    for item in replicated[field]:
        pollster = item.view.sample.pollster.casefold()
        current = latest_by_pollster.get(pollster)
        ordering = (
            item.view.sample.fieldwork_end,
            item.view.sample.evidence_available_at,
            item.view.sample.poll_sample_id,
            item.view.reading.document_display_order or 0,
            item.view.reading.poll_reading_id,
        )
        if current is None or ordering > (
            current.view.sample.fieldwork_end,
            current.view.sample.evidence_available_at,
            current.view.sample.poll_sample_id,
            current.view.reading.document_display_order or 0,
            current.view.reading.poll_reading_id,
        ):
            latest_by_pollster[pollster] = item
    selected = tuple(
        sorted(
            latest_by_pollster.values(),
            key=lambda item: item.view.sample.pollster.casefold(),
        )
    )
    divisor = Decimal(len(selected))
    name_by_id = {
        candidate.candidate_id: candidate.candidate_name
        for candidate in final_ballot
    }
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
    residual = (
        sum(
            (item.residual_share for item in selected if item.residual_share is not None),
            Decimal("0"),
        )
        / divisor
        if all(item.residual_share is not None for item in selected)
        else None
    )
    unmeasured = tuple(
        candidate for candidate in final_ballot if candidate.candidate_id not in field
    )
    estimate = PollingEstimateResult(
        "available" if ballot_certified else "preview",
        "qualifying_evidence" if ballot_certified else "provisional_ballot",
        estimates,
        residual,
        tuple(item.view.sample.poll_sample_id for item in selected),
        tuple(item.view.reading.poll_reading_id for item in selected),
        unmeasured,
    )
    return WardPollingResult(evidence_tier, views, estimate)
