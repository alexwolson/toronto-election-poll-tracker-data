"""Qualification candidate for the polling-only Mayoral Endpoint Bridge.

The selector in this module is intentionally narrower than the source
contract.  It admits one direct, Final-Ballot-compatible reading from each
respondent sample and never treats dependent readings as separate polls.  It
does not turn a Poll Residual into candidate support; reported candidate shares
are normalized only among candidates measured numerically in that reading.

The statistical bridge and its qualification comparator consume the prepared
views.  Keeping selection here makes source semantics independently testable
before any forecast family or computational toolkit is chosen.

Nothing in this module is wired to a live snapshot or authorized for public
forecasting.  The bridge remains a candidate until it clears the frozen
whole-election comparison and absolute reliability checks.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from types import MappingProxyType
from typing import Final, Literal
from zoneinfo import ZoneInfo

import numpy as np

from backend.model.mayoral_evaluation import (
    EvaluationPrediction,
    FullBallotShareDraws,
    HeldOutCycle,
    TrainingCycle,
)
from backend.model.poll_sources import PollReading, PollResponse, PollSample

_TORONTO: Final = ZoneInfo("America/Toronto")
_DENOMINATOR_PRIORITY: Final = {
    "valid_responses": 5,
    "custom": 4,
    "decided_respondents": 3,
    "all_respondents": 2,
    "not_reported": 1,
}
_POINT_FLOOR: Final = 1e-12
MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES: Final = (12, 7, 3, 1)
MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL: Final = time(12)

EndpointVariant = Literal["latest-sample-comparator", "firm-balanced-bridge"]


class MayoralEndpointDataError(ValueError):
    """Raised when endpoint evidence cannot be selected deterministically."""


@dataclass(frozen=True, slots=True)
class MayoralEndpointEvidence:
    """Source-audited poll evidence visible at one Analysis Cutoff."""

    election_cycle_id: str
    final_ballot_evidence_available_at: datetime
    poll_samples: tuple[PollSample, ...]
    poll_readings: tuple[PollReading, ...]
    poll_responses: tuple[PollResponse, ...]

    def __post_init__(self) -> None:
        if not self.election_cycle_id.strip():
            raise MayoralEndpointDataError("election_cycle_id must not be blank")
        if self.final_ballot_evidence_available_at.utcoffset() is None:
            raise MayoralEndpointDataError(
                "final_ballot_evidence_available_at must be offset-aware"
            )


@dataclass(frozen=True, slots=True)
class SelectedMayoralPollReading:
    """The single endpoint input selected from one respondent sample."""

    poll_sample_id: str
    poll_reading_id: str
    pollster: str
    fieldwork_end: date
    evidence_available_at: datetime
    candidate_field: tuple[str, ...]
    candidate_shares: Mapping[str, Decimal]

    def __post_init__(self) -> None:
        shares = dict(self.candidate_shares)
        if len(shares) < 2:
            raise MayoralEndpointDataError(
                "selected reading needs at least two numeric candidate shares"
            )
        if set(shares) - set(self.candidate_field):
            raise MayoralEndpointDataError(
                "numeric candidates must belong to the selected candidate field"
            )
        if any(value < 0 for value in shares.values()):
            raise MayoralEndpointDataError("candidate shares must be non-negative")
        total = sum(shares.values(), Decimal(0))
        if total <= 0:
            raise MayoralEndpointDataError(
                "selected reading candidate shares must have positive total"
            )
        normalized = {
            candidate_id: share / total for candidate_id, share in shares.items()
        }
        object.__setattr__(self, "candidate_shares", MappingProxyType(normalized))


@dataclass(frozen=True, slots=True)
class MayoralEndpointFit:
    """Inspectable fitted endpoint before simulation draws are generated."""

    variant: EndpointVariant
    candidate_ids: tuple[str, ...]
    point_shares: tuple[float, ...]
    tail_mass_total: float
    concentration: float
    eligible_poll_sample_ids: tuple[str, ...]
    effective_poll_sample_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MayoralEndpointPredictor:
    """Deterministic fold-local predictor accepted by the evaluation harness."""

    variant: EndpointVariant
    draw_count: int = 2048
    tail_mass_multiplier: float = 1.0
    excluded_poll_sample_ids: frozenset[str] = frozenset()
    excluded_pollsters: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.variant not in {
            "latest-sample-comparator",
            "firm-balanced-bridge",
        }:
            raise ValueError("unknown Mayoral Endpoint variant")
        if type(self.draw_count) is not int or self.draw_count <= 0:
            raise ValueError("draw_count must be a positive integer")
        _validate_sensitivity_inputs(
            self.tail_mass_multiplier,
            self.excluded_poll_sample_ids,
            self.excluded_pollsters,
        )

    def __call__(
        self,
        training_cycles: tuple[TrainingCycle, ...],
        target: HeldOutCycle,
    ) -> EvaluationPrediction:
        fit = fit_mayoral_endpoint(
            training_cycles,
            target,
            variant=self.variant,
            tail_mass_multiplier=self.tail_mass_multiplier,
            excluded_poll_sample_ids=self.excluded_poll_sample_ids,
            excluded_pollsters=self.excluded_pollsters,
        )
        draws = draws_from_point(
            fit.candidate_ids,
            fit.point_shares,
            fit.concentration,
            self.draw_count,
        )
        return EvaluationPrediction(
            FullBallotShareDraws(
                candidate_ids=fit.candidate_ids,
                draws=draws,
            )
        )


def draws_from_point(
    candidate_ids: tuple[str, ...],
    point_shares: tuple[float, ...],
    concentration: float,
    draw_count: int,
) -> tuple[tuple[float, ...], ...]:
    """Deterministically draw full-ballot shares from a fitted point + concentration.

    The seed is derived only from the canonicalized point and concentration, so a
    given (point, concentration) always yields the same draws regardless of
    candidate ordering.  Shared by the polling-only predictor and any predictor
    that post-processes the point estimate (e.g. the incumbency-informed variant).
    """

    canonical_point = tuple(sorted(zip(candidate_ids, point_shares, strict=True)))
    seed_material = json.dumps(
        {
            "candidate_point": canonical_point,
            "concentration": concentration,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    draw_candidate_ids = tuple(candidate_id for candidate_id, _ in canonical_point)
    point = np.asarray(tuple(share for _, share in canonical_point), dtype=float)
    parameters = np.maximum(point * concentration, _POINT_FLOOR)
    canonical_draws = rng.dirichlet(parameters, size=draw_count)
    draw_index = {
        candidate_id: index for index, candidate_id in enumerate(draw_candidate_ids)
    }
    return tuple(
        tuple(float(row[draw_index[candidate_id]]) for candidate_id in candidate_ids)
        for row in canonical_draws
    )


def fit_mayoral_endpoint(
    training_cycles: tuple[TrainingCycle, ...],
    target: HeldOutCycle,
    *,
    variant: EndpointVariant,
    tail_mass_multiplier: float = 1.0,
    excluded_poll_sample_ids: frozenset[str] = frozenset(),
    excluded_pollsters: frozenset[str] = frozenset(),
) -> MayoralEndpointFit:
    """Fit one polling-only endpoint entirely inside a held-out fold."""

    if not training_cycles:
        raise MayoralEndpointDataError("endpoint fitting requires training cycles")
    if variant not in {"latest-sample-comparator", "firm-balanced-bridge"}:
        raise MayoralEndpointDataError("unknown Mayoral Endpoint variant")
    _validate_sensitivity_inputs(
        tail_mass_multiplier,
        excluded_poll_sample_ids,
        excluded_pollsters,
    )
    training_selected: dict[str, tuple[SelectedMayoralPollReading, ...]] = {}
    for cycle in training_cycles:
        snapshot = min(
            cycle.history,
            key=lambda row: row.days_before_election,
        )
        training_selected[cycle.election_cycle_id] = _filter_selected(
            _selected_for_cycle(
                snapshot.evidence,
                cycle.outcome.candidate_ids,
                expected_election_cycle_id=cycle.election_cycle_id,
                analysis_cutoff=snapshot.analysis_cutoff,
            ),
            excluded_poll_sample_ids=excluded_poll_sample_ids,
            excluded_pollsters=excluded_pollsters,
        )
    selected = _filter_selected(
        _selected_for_cycle(
            target.snapshot.evidence,
            target.candidate_ids,
            expected_election_cycle_id=target.election_cycle_id,
            analysis_cutoff=target.snapshot.analysis_cutoff,
        ),
        excluded_poll_sample_ids=excluded_poll_sample_ids,
        excluded_pollsters=excluded_pollsters,
    )
    if not selected:
        raise MayoralEndpointDataError(
            "target cycle contains no eligible poll evidence at this cutoff"
        )
    tail_mass = (
        _fit_tail_mass(training_cycles, training_selected) * tail_mass_multiplier
    )
    if not math.isfinite(tail_mass) or not 0.0 < tail_mass < 1.0:
        raise MayoralEndpointDataError(
            "fitted candidate-tail mass must lie in (0, 1) after any multiplier"
        )
    concentration = _fit_concentration(
        training_cycles,
        tail_mass=tail_mass,
        variant=variant,
        excluded_poll_sample_ids=excluded_poll_sample_ids,
        excluded_pollsters=excluded_pollsters,
    )
    point = _point_estimate(
        selected,
        target.candidate_ids,
        tail_mass=tail_mass,
        variant=variant,
    )
    effective = _effective_readings(selected, variant=variant)
    return MayoralEndpointFit(
        variant=variant,
        candidate_ids=target.candidate_ids,
        point_shares=point,
        tail_mass_total=tail_mass,
        concentration=concentration,
        eligible_poll_sample_ids=tuple(row.poll_sample_id for row in selected),
        effective_poll_sample_ids=tuple(row.poll_sample_id for row in effective),
    )


def select_mayoral_endpoint_readings(
    evidence: MayoralEndpointEvidence,
    *,
    final_candidate_ids: tuple[str, ...],
) -> tuple[SelectedMayoralPollReading, ...]:
    """Select at most one endpoint reading from each Distinct Poll Sample.

    V1 deliberately uses only samples whose fieldwork reaches the conservative
    Final Ballot availability date.  A later choice-set challenger may attempt
    to earn use of pre-Final evidence; this baseline does not silently solve
    that harder problem.
    """

    final_ids = _candidate_universe(final_candidate_ids)
    samples = _unique_by_id(
        evidence.poll_samples,
        attribute="poll_sample_id",
        label="poll sample",
    )
    for sample in samples.values():
        if sample.election_cycle_id != evidence.election_cycle_id:
            raise MayoralEndpointDataError(
                f"sample {sample.poll_sample_id!r} belongs to cycle "
                f"{sample.election_cycle_id!r}, not evidence cycle "
                f"{evidence.election_cycle_id!r}"
            )
        if sample.geography_type != "citywide" or sample.geography_id != "toronto":
            raise MayoralEndpointDataError(
                f"sample {sample.poll_sample_id!r} is not Toronto citywide evidence"
            )
    readings = _unique_by_id(
        evidence.poll_readings,
        attribute="poll_reading_id",
        label="poll reading",
    )
    readings_by_sample: dict[str, list[PollReading]] = {
        sample_id: [] for sample_id in samples
    }
    for reading in readings.values():
        if reading.poll_sample_id not in samples:
            raise MayoralEndpointDataError(
                f"reading {reading.poll_reading_id!r} references an unknown sample"
            )
        if reading.contest_type != "mayoral":
            raise MayoralEndpointDataError(
                f"reading {reading.poll_reading_id!r} is not mayoral evidence"
            )
        readings_by_sample[reading.poll_sample_id].append(reading)

    responses_by_reading: dict[str, list[PollResponse]] = {
        reading_id: [] for reading_id in readings
    }
    response_keys: set[tuple[str, str]] = set()
    for response in evidence.poll_responses:
        if response.poll_reading_id not in readings:
            raise MayoralEndpointDataError(
                f"response {response.response_option_id!r} references an unknown reading"
            )
        key = (response.poll_reading_id, response.response_option_id)
        if key in response_keys:
            raise MayoralEndpointDataError(f"duplicate response relationship {key!r}")
        response_keys.add(key)
        responses_by_reading[response.poll_reading_id].append(response)

    boundary_date = evidence.final_ballot_evidence_available_at.astimezone(
        _TORONTO
    ).date()
    selected: list[SelectedMayoralPollReading] = []
    for sample in sorted(samples.values(), key=lambda row: row.poll_sample_id):
        if sample.fieldwork_end < boundary_date:
            continue
        candidates = tuple(
            candidate
            for reading in readings_by_sample[sample.poll_sample_id]
            if (
                candidate := _eligible_reading(
                    reading,
                    tuple(responses_by_reading[reading.poll_reading_id]),
                    final_ids,
                )
            )
            is not None
        )
        if not candidates:
            continue
        maxima = tuple(
            candidate
            for candidate in candidates
            if not any(
                candidate.candidate_field < other.candidate_field
                for other in candidates
            )
        )
        maximal_fields = {candidate.candidate_field for candidate in maxima}
        if len(maximal_fields) != 1:
            raise MayoralEndpointDataError(
                f"sample {sample.poll_sample_id!r} has incomparable maximal fields"
            )
        best_priority = max(candidate.denominator_priority for candidate in maxima)
        best = tuple(
            candidate
            for candidate in maxima
            if candidate.denominator_priority == best_priority
        )
        if len(best) != 1:
            raise MayoralEndpointDataError(
                f"sample {sample.poll_sample_id!r} has tied endpoint readings"
            )
        chosen = best[0]
        selected.append(
            SelectedMayoralPollReading(
                poll_sample_id=sample.poll_sample_id,
                poll_reading_id=chosen.reading.poll_reading_id,
                pollster=sample.pollster,
                fieldwork_end=sample.fieldwork_end,
                evidence_available_at=sample.evidence_available_at,
                candidate_field=tuple(sorted(chosen.candidate_field)),
                candidate_shares=chosen.candidate_shares,
            )
        )
    return tuple(
        sorted(
            selected,
            key=lambda row: (
                row.fieldwork_end,
                row.evidence_available_at,
                row.poll_sample_id,
            ),
        )
    )


def _selected_for_cycle(
    raw_evidence: object,
    candidate_ids: tuple[str, ...],
    *,
    expected_election_cycle_id: str,
    analysis_cutoff: datetime,
) -> tuple[SelectedMayoralPollReading, ...]:
    if not isinstance(raw_evidence, MayoralEndpointEvidence):
        raise MayoralEndpointDataError(
            "Mayoral Endpoint requires MayoralEndpointEvidence snapshots"
        )
    if raw_evidence.election_cycle_id != expected_election_cycle_id:
        raise MayoralEndpointDataError(
            f"endpoint evidence cycle {raw_evidence.election_cycle_id!r} does not "
            f"match evaluation cycle {expected_election_cycle_id!r}"
        )
    if analysis_cutoff.utcoffset() is None:
        raise MayoralEndpointDataError("analysis_cutoff must be offset-aware")
    future_samples = tuple(
        sample.poll_sample_id
        for sample in raw_evidence.poll_samples
        if sample.evidence_available_at > analysis_cutoff
    )
    if future_samples:
        raise MayoralEndpointDataError(
            "endpoint evidence contains sample(s) unavailable at the cutoff: "
            f"{future_samples}"
        )
    return select_mayoral_endpoint_readings(
        raw_evidence,
        final_candidate_ids=candidate_ids,
    )


def _fit_tail_mass(
    training_cycles: tuple[TrainingCycle, ...],
    selected_by_cycle: Mapping[str, tuple[SelectedMayoralPollReading, ...]],
) -> float:
    """Learn one total Unmeasured Candidate Tail mass, invariant to choice-set size.

    Each training reading contributes its realized total omitted mass (the
    combined election-day share of the Final-Ballot candidates it did not name).
    Readings are averaged within a cycle and cycles are averaged with equal
    weight.  The number of omitted candidates does not enter the estimate; ADR
    0038 records the evidence that realized total tail mass does not scale with
    it.
    """

    cycle_estimates: list[float] = []
    for cycle in training_cycles:
        reading_estimates: list[float] = []
        outcome = cycle.outcome.candidate_shares
        for reading in selected_by_cycle[cycle.election_cycle_id]:
            unmeasured = set(outcome) - set(reading.candidate_shares)
            if not unmeasured:
                continue
            tail_share = sum(outcome[candidate_id] for candidate_id in unmeasured)
            if not 0.0 < tail_share < 1.0:
                continue
            reading_estimates.append(tail_share)
        if reading_estimates:
            cycle_estimates.append(sum(reading_estimates) / len(reading_estimates))
    if not cycle_estimates:
        raise MayoralEndpointDataError(
            "training fold contains no measurable candidate-tail relationship"
        )
    tail_mass = sum(cycle_estimates) / len(cycle_estimates)
    if not math.isfinite(tail_mass) or not 0.0 < tail_mass < 1.0:
        raise MayoralEndpointDataError("fitted candidate-tail mass is invalid")
    return tail_mass


def _fit_concentration(
    training_cycles: tuple[TrainingCycle, ...],
    *,
    tail_mass: float,
    variant: EndpointVariant,
    excluded_poll_sample_ids: frozenset[str],
    excluded_pollsters: frozenset[str],
) -> float:
    """Fit one global Dirichlet concentration with equal cycle weight."""

    cycle_moments: list[tuple[float, float]] = []
    for cycle in training_cycles:
        snapshot_moments: list[tuple[float, float]] = []
        for snapshot in cycle.history:
            selected = _filter_selected(
                _selected_for_cycle(
                    snapshot.evidence,
                    cycle.outcome.candidate_ids,
                    expected_election_cycle_id=cycle.election_cycle_id,
                    analysis_cutoff=snapshot.analysis_cutoff,
                ),
                excluded_poll_sample_ids=excluded_poll_sample_ids,
                excluded_pollsters=excluded_pollsters,
            )
            if not selected:
                continue
            point = _point_estimate(
                selected,
                cycle.outcome.candidate_ids,
                tail_mass=tail_mass,
                variant=variant,
            )
            observed = tuple(
                cycle.outcome.candidate_shares[candidate_id]
                for candidate_id in cycle.outcome.candidate_ids
            )
            numerator = 1.0 - sum(value * value for value in point)
            squared_error = sum(
                (actual - predicted) ** 2
                for actual, predicted in zip(observed, point, strict=True)
            )
            snapshot_moments.append((numerator, squared_error))
        if not snapshot_moments:
            continue
        cycle_moments.append(
            (
                sum(row[0] for row in snapshot_moments) / len(snapshot_moments),
                sum(row[1] for row in snapshot_moments) / len(snapshot_moments),
            )
        )
    if not cycle_moments:
        raise MayoralEndpointDataError(
            "training fold contains no poll-backed uncertainty observations"
        )
    numerator = sum(row[0] for row in cycle_moments) / len(cycle_moments)
    squared_error = sum(row[1] for row in cycle_moments) / len(cycle_moments)
    if squared_error <= 0.0:
        raise MayoralEndpointDataError(
            "training fold cannot identify a non-zero election error floor"
        )
    raw = numerator / squared_error - 1.0
    if not math.isfinite(raw) or raw <= 0.0:
        raise MayoralEndpointDataError("fitted Dirichlet concentration is invalid")
    return raw


def _point_estimate(
    selected: tuple[SelectedMayoralPollReading, ...],
    candidate_ids: tuple[str, ...],
    *,
    tail_mass: float,
    variant: EndpointVariant,
) -> tuple[float, ...]:
    if not selected:
        raise MayoralEndpointDataError("cannot estimate an endpoint without a poll")
    effective = _effective_readings(selected, variant=variant)
    sample_points = {
        reading.poll_sample_id: _reading_point(
            reading,
            candidate_ids,
            tail_mass=tail_mass,
        )
        for reading in effective
    }
    if variant == "latest-sample-comparator":
        return _mean_vectors(
            tuple(sample_points[reading.poll_sample_id] for reading in effective)
        )
    if variant != "firm-balanced-bridge":
        raise MayoralEndpointDataError("unknown Mayoral Endpoint variant")
    by_pollster: dict[str, list[SelectedMayoralPollReading]] = {}
    for reading in effective:
        by_pollster.setdefault(reading.pollster, []).append(reading)
    firm_points: list[tuple[float, ...]] = []
    for pollster in sorted(by_pollster):
        newest = tuple(
            sample_points[reading.poll_sample_id] for reading in by_pollster[pollster]
        )
        firm_points.append(_mean_vectors(newest))
    return _mean_vectors(tuple(firm_points))


def _effective_readings(
    selected: tuple[SelectedMayoralPollReading, ...],
    *,
    variant: EndpointVariant,
) -> tuple[SelectedMayoralPollReading, ...]:
    if not selected:
        return ()
    if variant == "latest-sample-comparator":
        latest_end = max(reading.fieldwork_end for reading in selected)
        return tuple(
            reading for reading in selected if reading.fieldwork_end == latest_end
        )
    if variant != "firm-balanced-bridge":
        raise MayoralEndpointDataError("unknown Mayoral Endpoint variant")
    effective: list[SelectedMayoralPollReading] = []
    pollsters = sorted({reading.pollster for reading in selected})
    for pollster in pollsters:
        firm = tuple(reading for reading in selected if reading.pollster == pollster)
        latest_end = max(reading.fieldwork_end for reading in firm)
        effective.extend(
            reading for reading in firm if reading.fieldwork_end == latest_end
        )
    return tuple(
        sorted(
            effective,
            key=lambda row: (
                row.fieldwork_end,
                row.evidence_available_at,
                row.poll_sample_id,
            ),
        )
    )


def _reading_point(
    reading: SelectedMayoralPollReading,
    candidate_ids: tuple[str, ...],
    *,
    tail_mass: float,
) -> tuple[float, ...]:
    unmeasured_count = len(set(candidate_ids) - set(reading.candidate_shares))
    if unmeasured_count == 0:
        point = tuple(
            float(reading.candidate_shares[candidate_id])
            for candidate_id in candidate_ids
        )
        return _normalize_point(point)
    per_candidate = tail_mass / unmeasured_count
    measured_scale = 1.0 - tail_mass
    point = tuple(
        (
            float(reading.candidate_shares[candidate_id]) * measured_scale
            if candidate_id in reading.candidate_shares
            else per_candidate
        )
        for candidate_id in candidate_ids
    )
    return _normalize_point(point)


def _mean_vectors(vectors: tuple[tuple[float, ...], ...]) -> tuple[float, ...]:
    if not vectors:
        raise MayoralEndpointDataError("cannot average an empty vector set")
    width = len(vectors[0])
    if any(len(vector) != width for vector in vectors):
        raise MayoralEndpointDataError("endpoint vectors have inconsistent widths")
    return _normalize_point(
        tuple(
            sum(vector[index] for vector in vectors) / len(vectors)
            for index in range(width)
        )
    )


def _normalize_point(point: tuple[float, ...]) -> tuple[float, ...]:
    floored = tuple(max(float(value), _POINT_FLOOR) for value in point)
    total = sum(floored)
    if not math.isfinite(total) or total <= 0.0:
        raise MayoralEndpointDataError("endpoint point estimate is invalid")
    return tuple(value / total for value in floored)


@dataclass(frozen=True, slots=True)
class _EligibleReading:
    reading: PollReading
    candidate_field: frozenset[str]
    candidate_shares: Mapping[str, Decimal]
    denominator_priority: int


def _eligible_reading(
    reading: PollReading,
    responses: tuple[PollResponse, ...],
    final_ids: frozenset[str],
) -> _EligibleReading | None:
    if reading.reading_purpose != "general_vote_intention":
        return None
    candidate_rows = tuple(
        response for response in responses if response.response_kind == "candidate"
    )
    candidate_field = frozenset(
        response.candidate_id
        for response in candidate_rows
        if response.candidate_id is not None
        and response.candidate_observation_status
        in {
            "individually_published",
            "offered_not_individually_published",
        }
    )
    if len(candidate_field) < 2 or not candidate_field <= final_ids:
        return None
    if reading.response_coverage == "complete":
        pass
    elif not (
        reading.response_coverage == "partial"
        and reading.tested_choice_set_status == "complete"
        and all(
            response.share is not None
            or response.candidate_observation_status
            == "offered_not_individually_published"
            for response in candidate_rows
        )
    ):
        return None
    numeric = {
        response.candidate_id: _endpoint_candidate_share(reading, response)
        for response in candidate_rows
        if response.candidate_id is not None
        and response.candidate_observation_status == "individually_published"
        and response.share is not None
    }
    if len(numeric) < 2 or sum(numeric.values(), Decimal(0)) <= 0:
        return None
    return _EligibleReading(
        reading=reading,
        candidate_field=candidate_field,
        candidate_shares=MappingProxyType(numeric),
        denominator_priority=_DENOMINATOR_PRIORITY[reading.denominator_type],
    )


def _endpoint_candidate_share(
    reading: PollReading,
    response: PollResponse,
) -> Decimal:
    """Return a candidate share without turning a rounded zero into certainty."""

    assert response.share is not None
    if response.share != 0:
        return response.share
    increment = Decimal(10) ** (-reading.reported_share_precision)
    if reading.reported_share_unit == "percent":
        increment /= Decimal(100)
    return increment / Decimal(2)


def _filter_selected(
    selected: tuple[SelectedMayoralPollReading, ...],
    *,
    excluded_poll_sample_ids: frozenset[str],
    excluded_pollsters: frozenset[str],
) -> tuple[SelectedMayoralPollReading, ...]:
    return tuple(
        reading
        for reading in selected
        if reading.poll_sample_id not in excluded_poll_sample_ids
        and reading.pollster not in excluded_pollsters
    )


def _validate_sensitivity_inputs(
    tail_mass_multiplier: float,
    excluded_poll_sample_ids: frozenset[str],
    excluded_pollsters: frozenset[str],
) -> None:
    if not isinstance(tail_mass_multiplier, (int, float)) or isinstance(
        tail_mass_multiplier, bool
    ):
        raise MayoralEndpointDataError(
            "tail_mass_multiplier must be a finite positive number"
        )
    if not math.isfinite(tail_mass_multiplier) or tail_mass_multiplier <= 0:
        raise MayoralEndpointDataError(
            "tail_mass_multiplier must be a finite positive number"
        )
    for label, values in (
        ("excluded_poll_sample_ids", excluded_poll_sample_ids),
        ("excluded_pollsters", excluded_pollsters),
    ):
        if not isinstance(values, frozenset) or any(
            not isinstance(value, str) or not value.strip() for value in values
        ):
            raise MayoralEndpointDataError(
                f"{label} must be a frozenset of nonblank strings"
            )


def _candidate_universe(candidate_ids: tuple[str, ...]) -> frozenset[str]:
    if len(candidate_ids) < 2 or len(candidate_ids) != len(set(candidate_ids)):
        raise MayoralEndpointDataError(
            "Final Ballot candidate IDs must contain at least two unique values"
        )
    if any(not candidate_id.strip() for candidate_id in candidate_ids):
        raise MayoralEndpointDataError("Final Ballot candidate IDs must not be blank")
    return frozenset(candidate_ids)


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
            raise MayoralEndpointDataError(f"duplicate {label} ID {identifier!r}")
        result[identifier] = row
    return result
