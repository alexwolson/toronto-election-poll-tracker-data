"""Whole-election evaluation for candidate mayoral forecasting models.

The harness owns validation folds, coherent quantity derivation, scoring, and
aggregation, but not a statistical model. Callers inject a ``fit_predict``
callback and may put any canonical evidence view in ``LeadTimeSnapshot``.

Every prediction is one validated full-Final-Ballot distribution of candidate
share draws. Winner, defeat, close-result, share, and margin quantities all
come from that artifact; a model cannot submit mutually contradictory answers.
Scores are averaged across cutoffs within an election before elections receive
equal weight, so repeated cutoffs never masquerade as independent cycles.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Literal, Protocol


ElectionType = Literal["general", "by_election"]
EvaluationPopulation = Literal["all_elections", "regular_elections_only"]

CLOSE_RESULT = "close_result"
INCUMBENT_DEFEAT = "incumbent_defeat"
INCUMBENT_MARGIN = "incumbent_margin"
MEAN_CANDIDATE_SHARE_CRPS = "shares:mean_candidate_crps"
WINNING_MARGIN = "winning_margin"
WINNER_LOG_SCORE = "winner:log_score"

_PROBABILITY_TOLERANCE = 1e-9


def binary_brier_metric(quantity: str) -> str:
    """Return the stable metric key for a binary quantity's Brier score."""
    return f"binary:{_quantity_name(quantity)}:brier"


def binary_log_loss_metric(quantity: str) -> str:
    """Return the stable metric key for a binary quantity's log loss."""
    return f"binary:{_quantity_name(quantity)}:log_loss"


def scalar_crps_metric(quantity: str) -> str:
    """Return the stable metric key for a derived scalar quantity's CRPS."""
    return f"scalar:{_quantity_name(quantity)}:crps"


# Keep the predeclared qualification keys import-safe: the public helper below
# validates quantity names through a private function defined later in the
# module, while these constants must exist during module initialization.
MAYORAL_MODEL_FAMILY_PRIMARY = "scalar:winning_margin:crps"
MAYORAL_MODEL_FAMILY_LOG_GUARD = WINNER_LOG_SCORE


def candidate_share_quantity(candidate_id: str) -> str:
    """Return the derived scalar quantity name for one candidate's share."""
    return f"candidate_share:{_identifier(candidate_id, 'candidate_id')}"


@dataclass(frozen=True, slots=True)
class ElectionOutcome:
    """Complete observed Final Ballot candidate shares for one election."""

    candidate_shares: Mapping[str, float]
    incumbent_candidate_id: str | None = None
    close_threshold: float = 0.05

    def __post_init__(self) -> None:
        shares = _validated_share_mapping(
            self.candidate_shares,
            label="election outcome candidate shares",
        )
        object.__setattr__(self, "candidate_shares", shares)
        threshold = _as_finite_float(self.close_threshold, "close_threshold")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("close_threshold must lie in [0, 1]")
        object.__setattr__(self, "close_threshold", threshold)
        if self.incumbent_candidate_id is not None:
            incumbent_id = _identifier(
                self.incumbent_candidate_id,
                "incumbent_candidate_id",
            )
            if incumbent_id not in shares:
                raise ValueError("incumbent_candidate_id is not on the Final Ballot")
            object.__setattr__(self, "incumbent_candidate_id", incumbent_id)
        maximum = max(shares.values())
        if sum(share == maximum for share in shares.values()) != 1:
            raise ValueError("election outcome must have one observed winner")

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(self.candidate_shares)

    @property
    def winner_id(self) -> str:
        return max(self.candidate_shares, key=self.candidate_shares.__getitem__)

    @property
    def winning_margin(self) -> float:
        leading = sorted(self.candidate_shares.values(), reverse=True)[:2]
        return leading[0] - leading[1]

    @property
    def is_close(self) -> bool:
        return self.winning_margin <= self.close_threshold

    @property
    def incumbent_defeated(self) -> bool | None:
        if self.incumbent_candidate_id is None:
            return None
        return self.winner_id != self.incumbent_candidate_id

    @property
    def incumbent_margin(self) -> float | None:
        if self.incumbent_candidate_id is None:
            return None
        incumbent_share = self.candidate_shares[self.incumbent_candidate_id]
        strongest_challenger = max(
            share
            for candidate_id, share in self.candidate_shares.items()
            if candidate_id != self.incumbent_candidate_id
        )
        return incumbent_share - strongest_challenger


@dataclass(frozen=True, slots=True)
class FullBallotShareDraws:
    """Validated, immutable election-day share draws for the full ballot.

    An exact top-share tie divides that draw's winner weight equally among the
    tied candidates; observed outcomes themselves must have a unique winner.
    """

    candidate_ids: tuple[str, ...]
    draws: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        candidate_ids = tuple(
            _identifier(candidate_id, "candidate_id")
            for candidate_id in self.candidate_ids
        )
        if len(candidate_ids) < 2:
            raise ValueError("full ballot must contain at least two candidates")
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("full ballot candidate_ids must be unique")
        normalized_draws: list[tuple[float, ...]] = []
        for draw_number, raw_draw in enumerate(self.draws, 1):
            if len(raw_draw) != len(candidate_ids):
                raise ValueError(
                    f"full ballot draw {draw_number} has {len(raw_draw)} shares; "
                    f"expected {len(candidate_ids)}"
                )
            draw = tuple(
                _as_finite_float(
                    share,
                    f"full ballot draw {draw_number} share",
                )
                for share in raw_draw
            )
            if any(share < 0.0 for share in draw):
                raise ValueError("full ballot draw shares must be non-negative")
            total = sum(draw)
            if not math.isclose(
                total,
                1.0,
                rel_tol=0.0,
                abs_tol=_PROBABILITY_TOLERANCE,
            ):
                raise ValueError(
                    f"full ballot draw shares must sum to 1; received {total}"
                )
            normalized_draws.append(draw)
        if not normalized_draws:
            raise ValueError("full ballot prediction must contain at least one draw")
        object.__setattr__(self, "candidate_ids", candidate_ids)
        object.__setattr__(self, "draws", tuple(normalized_draws))


@dataclass(frozen=True, slots=True)
class EvaluationPrediction:
    """The sole model-output artifact accepted by the evaluation harness."""

    full_ballot_share_draws: FullBallotShareDraws

    def __post_init__(self) -> None:
        if not isinstance(self.full_ballot_share_draws, FullBallotShareDraws):
            raise TypeError(
                "full_ballot_share_draws must be FullBallotShareDraws"
            )


@dataclass(frozen=True, slots=True)
class LeadTimeSnapshot:
    """Evidence available at one pre-declared number of days before election."""

    days_before_election: int
    analysis_cutoff: datetime
    evidence_revision: str
    evidence: object

    def __post_init__(self) -> None:
        if (
            type(self.days_before_election) is not int
            or self.days_before_election < 0
        ):
            raise ValueError("days_before_election must be a non-negative integer")
        if (
            not isinstance(self.analysis_cutoff, datetime)
            or self.analysis_cutoff.utcoffset() is None
        ):
            raise ValueError("analysis_cutoff must be an offset-aware datetime")
        _identifier(self.evidence_revision, "evidence_revision")


@dataclass(frozen=True, slots=True)
class ElectionCycle:
    """Adapter-facing evaluation view of one historical election cycle."""

    election_cycle_id: str
    election_type: ElectionType
    snapshots: tuple[LeadTimeSnapshot, ...]
    outcome: ElectionOutcome

    def __post_init__(self) -> None:
        _identifier(self.election_cycle_id, "election_cycle_id")
        if self.election_type not in {"general", "by_election"}:
            raise ValueError("election_type must be 'general' or 'by_election'")
        lead_times = [snapshot.days_before_election for snapshot in self.snapshots]
        if len(lead_times) != len(set(lead_times)):
            raise ValueError(
                f"cycle {self.election_cycle_id!r} has duplicate lead times"
            )
        ordered = sorted(
            self.snapshots,
            key=lambda snapshot: snapshot.days_before_election,
            reverse=True,
        )
        if any(
            earlier.analysis_cutoff >= later.analysis_cutoff
            for earlier, later in zip(ordered, ordered[1:])
        ):
            raise ValueError(
                f"cycle {self.election_cycle_id!r} analysis cutoffs must move "
                "forward as election day approaches"
            )


@dataclass(frozen=True, slots=True)
class TrainingCycle:
    """One training election with its fixed-grid history and target-lead view."""

    election_cycle_id: str
    election_type: ElectionType
    snapshot: LeadTimeSnapshot
    history: tuple[LeadTimeSnapshot, ...]
    outcome: ElectionOutcome


@dataclass(frozen=True, slots=True)
class HeldOutCycle:
    """A target with its known ballot metadata but no observed result."""

    election_cycle_id: str
    election_type: ElectionType
    snapshot: LeadTimeSnapshot
    candidate_ids: tuple[str, ...]
    incumbent_candidate_id: str | None


class FitPredict(Protocol):
    """Callback that fits within a fold and predicts its held-out target."""

    def __call__(
        self,
        training_cycles: tuple[TrainingCycle, ...],
        target: HeldOutCycle,
    ) -> EvaluationPrediction: ...


@dataclass(frozen=True, slots=True)
class EvaluationCycleManifest:
    """Outcome and fold identity that must match across compared reports."""

    election_cycle_id: str
    election_type: ElectionType
    candidate_shares: tuple[tuple[str, float], ...]
    incumbent_candidate_id: str | None
    close_threshold: float
    snapshots: tuple[tuple[int, datetime, str], ...]


@dataclass(frozen=True, slots=True)
class EvaluationManifest:
    population: EvaluationPopulation
    lead_times: tuple[int, ...]
    cycles: tuple[EvaluationCycleManifest, ...]


@dataclass(frozen=True, slots=True)
class CutoffEvaluation:
    days_before_election: int
    metrics: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class CycleEvaluation:
    """Cutoff scores and their within-election mean."""

    election_cycle_id: str
    election_type: ElectionType
    cutoffs: tuple[CutoffEvaluation, ...]
    metrics: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """Equal-election-weighted out-of-cycle evaluation results."""

    model_name: str
    manifest: EvaluationManifest
    cycles: tuple[CycleEvaluation, ...]
    metrics: Mapping[str, float]
    metric_cycle_counts: Mapping[str, int]
    lead_time_metrics: Mapping[int, Mapping[str, float]]

    @property
    def population(self) -> EvaluationPopulation:
        return self.manifest.population

    @property
    def lead_times(self) -> tuple[int, ...]:
        return self.manifest.lead_times


@dataclass(frozen=True, slots=True)
class EvaluationSensitivitySuite:
    """Primary Toronto fit and the mandatory regular-election-only refit."""

    all_elections: EvaluationReport
    regular_elections_only: EvaluationReport


@dataclass(frozen=True, slots=True)
class RelativeQualificationDecision:
    """Relative score comparison; not by itself publication authority."""

    candidate_model: str
    baseline_model: str
    primary_metric: str
    log_loss_guard: str
    candidate_primary_score: float
    baseline_primary_score: float
    candidate_log_loss: float
    baseline_log_loss: float
    aggregate_primary_improved: bool
    aggregate_log_loss_not_worse: bool
    aggregate_scores_finite: bool
    improved_cycles: int
    compared_cycles: int
    majority_of_cycles_improved: bool
    relative_qualifies: bool


@dataclass(frozen=True, slots=True)
class ReliabilityCheck:
    metric: str
    observed: float | None
    maximum: float
    passed: bool


@dataclass(frozen=True, slots=True)
class AbsoluteReliabilityDecision:
    """Fail-closed application of externally frozen numeric thresholds."""

    configured: bool
    passed: bool
    checks: tuple[ReliabilityCheck, ...]


@dataclass(frozen=True, slots=True)
class ModelLadderDecision:
    """Qualification state for naive, endpoint, and optional richer models."""

    endpoint_relative: RelativeQualificationDecision
    endpoint_reliability: AbsoluteReliabilityDecision
    endpoint_qualifies: bool
    richer_relative: RelativeQualificationDecision | None
    richer_reliability: AbsoluteReliabilityDecision | None
    richer_qualifies: bool | None


def empirical_crps(draws: Sequence[float], observed: float) -> float:
    """Return exact CRPS for an equally weighted empirical scalar forecast."""
    values = tuple(
        _as_finite_float(value, "scalar forecast draw") for value in draws
    )
    if not values:
        raise ValueError("scalar forecast draws must not be empty")
    truth = _as_finite_float(observed, "scalar outcome")
    count = len(values)
    absolute_error = sum(abs(value - truth) for value in values) / count
    ordered = sorted(values)
    pairwise_dispersion = sum(
        (2 * index - count + 1) * value
        for index, value in enumerate(ordered)
    )
    score = absolute_error - pairwise_dispersion / (count * count)
    return max(0.0, score)


def score_prediction(
    outcome: ElectionOutcome,
    prediction: EvaluationPrediction,
) -> dict[str, float]:
    """Derive and score every supported quantity from coherent share draws."""
    distribution = prediction.full_ballot_share_draws
    if set(distribution.candidate_ids) != set(outcome.candidate_ids):
        raise ValueError(
            "prediction candidate universe must exactly match the Final Ballot"
        )
    index_by_candidate = {
        candidate_id: index
        for index, candidate_id in enumerate(distribution.candidate_ids)
    }
    draw_count = len(distribution.draws)
    winner_probabilities = dict.fromkeys(distribution.candidate_ids, 0.0)
    candidate_draws = {
        candidate_id: [] for candidate_id in distribution.candidate_ids
    }
    winning_margin_draws: list[float] = []
    incumbent_margin_draws: list[float] = []
    close_draws = 0
    incumbent_index = (
        None
        if outcome.incumbent_candidate_id is None
        else index_by_candidate[outcome.incumbent_candidate_id]
    )

    for draw in distribution.draws:
        maximum = max(draw)
        tied_winners = [index for index, share in enumerate(draw) if share == maximum]
        winner_weight = 1.0 / (draw_count * len(tied_winners))
        for index in tied_winners:
            candidate_id = distribution.candidate_ids[index]
            winner_probabilities[candidate_id] += winner_weight
        for candidate_id, index in index_by_candidate.items():
            candidate_draws[candidate_id].append(draw[index])
        leading = sorted(draw, reverse=True)[:2]
        winning_margin = leading[0] - leading[1]
        winning_margin_draws.append(winning_margin)
        close_draws += winning_margin <= outcome.close_threshold
        if incumbent_index is not None:
            strongest_challenger = max(
                share for index, share in enumerate(draw) if index != incumbent_index
            )
            incumbent_margin_draws.append(
                draw[incumbent_index] - strongest_challenger
            )

    scores = {
        WINNER_LOG_SCORE: _negative_log_probability(
            _clamp_probability(winner_probabilities[outcome.winner_id])
        )
    }
    _add_binary_scores(
        scores,
        CLOSE_RESULT,
        close_draws / draw_count,
        outcome.is_close,
    )
    if outcome.incumbent_candidate_id is not None:
        defeat_probability = _clamp_probability(
            1.0 - winner_probabilities[outcome.incumbent_candidate_id]
        )
        _add_binary_scores(
            scores,
            INCUMBENT_DEFEAT,
            defeat_probability,
            bool(outcome.incumbent_defeated),
        )
    candidate_share_scores: list[float] = []
    for candidate_id in outcome.candidate_ids:
        score = empirical_crps(
            candidate_draws[candidate_id],
            outcome.candidate_shares[candidate_id],
        )
        scores[scalar_crps_metric(candidate_share_quantity(candidate_id))] = score
        candidate_share_scores.append(score)
    scores[MEAN_CANDIDATE_SHARE_CRPS] = (
        sum(candidate_share_scores) / len(candidate_share_scores)
    )
    scores[scalar_crps_metric(WINNING_MARGIN)] = empirical_crps(
        winning_margin_draws,
        outcome.winning_margin,
    )
    if outcome.incumbent_margin is not None:
        scores[scalar_crps_metric(INCUMBENT_MARGIN)] = empirical_crps(
            incumbent_margin_draws,
            outcome.incumbent_margin,
        )
    return scores


def evaluate_mayoral_model(
    cycles: Sequence[ElectionCycle],
    *,
    lead_times: Sequence[int],
    fit_predict: FitPredict | Callable[
        [tuple[TrainingCycle, ...], HeldOutCycle], EvaluationPrediction
    ],
    model_name: str,
    population: EvaluationPopulation = "all_elections",
) -> EvaluationReport:
    """Run leave-one-election-out evaluation at fixed lead-time cutoffs."""
    cycle_tuple = tuple(cycles)
    lead_time_tuple = _validate_evaluation_inputs(
        cycle_tuple,
        lead_times,
        model_name=model_name,
        population=population,
    )
    snapshots = {
        cycle.election_cycle_id: {
            snapshot.days_before_election: snapshot
            for snapshot in cycle.snapshots
        }
        for cycle in cycle_tuple
    }
    manifest = EvaluationManifest(
        population=population,
        lead_times=lead_time_tuple,
        cycles=tuple(
            EvaluationCycleManifest(
                election_cycle_id=cycle.election_cycle_id,
                election_type=cycle.election_type,
                candidate_shares=tuple(cycle.outcome.candidate_shares.items()),
                incumbent_candidate_id=cycle.outcome.incumbent_candidate_id,
                close_threshold=cycle.outcome.close_threshold,
                snapshots=tuple(
                    (
                        lead_time,
                        snapshots[cycle.election_cycle_id][
                            lead_time
                        ].analysis_cutoff,
                        snapshots[cycle.election_cycle_id][
                            lead_time
                        ].evidence_revision,
                    )
                    for lead_time in lead_time_tuple
                ),
            )
            for cycle in cycle_tuple
        ),
    )

    cycle_evaluations: list[CycleEvaluation] = []
    for target_cycle in cycle_tuple:
        cutoff_evaluations: list[CutoffEvaluation] = []
        for lead_time in lead_time_tuple:
            training = tuple(
                TrainingCycle(
                    election_cycle_id=training_cycle.election_cycle_id,
                    election_type=training_cycle.election_type,
                    snapshot=snapshots[training_cycle.election_cycle_id][lead_time],
                    history=tuple(
                        snapshots[training_cycle.election_cycle_id][fixed_lead_time]
                        for fixed_lead_time in lead_time_tuple
                    ),
                    outcome=training_cycle.outcome,
                )
                for training_cycle in cycle_tuple
                if training_cycle.election_cycle_id
                != target_cycle.election_cycle_id
            )
            target = HeldOutCycle(
                election_cycle_id=target_cycle.election_cycle_id,
                election_type=target_cycle.election_type,
                snapshot=snapshots[target_cycle.election_cycle_id][lead_time],
                candidate_ids=target_cycle.outcome.candidate_ids,
                incumbent_candidate_id=target_cycle.outcome.incumbent_candidate_id,
            )
            prediction = fit_predict(training, target)
            if not isinstance(prediction, EvaluationPrediction):
                raise TypeError("fit_predict must return EvaluationPrediction")
            cutoff_evaluations.append(
                CutoffEvaluation(
                    days_before_election=lead_time,
                    metrics=score_prediction(target_cycle.outcome, prediction),
                )
            )
        cycle_evaluations.append(
            CycleEvaluation(
                election_cycle_id=target_cycle.election_cycle_id,
                election_type=target_cycle.election_type,
                cutoffs=tuple(cutoff_evaluations),
                metrics=_mean_metric_maps(
                    tuple(cutoff.metrics for cutoff in cutoff_evaluations)
                ),
            )
        )

    cycle_result = tuple(cycle_evaluations)
    aggregate = _mean_metric_maps(tuple(cycle.metrics for cycle in cycle_result))
    counts = {
        metric: sum(metric in cycle.metrics for cycle in cycle_result)
        for metric in aggregate
    }
    by_lead_time = {
        lead_time: _mean_metric_maps(
            tuple(
                next(
                    cutoff.metrics
                    for cutoff in cycle.cutoffs
                    if cutoff.days_before_election == lead_time
                )
                for cycle in cycle_result
            )
        )
        for lead_time in lead_time_tuple
    }
    return EvaluationReport(
        model_name=model_name,
        manifest=manifest,
        cycles=cycle_result,
        metrics=aggregate,
        metric_cycle_counts=counts,
        lead_time_metrics=by_lead_time,
    )


def evaluate_with_regular_election_sensitivity(
    cycles: Sequence[ElectionCycle],
    *,
    lead_times: Sequence[int],
    fit_predict: FitPredict | Callable[
        [tuple[TrainingCycle, ...], HeldOutCycle], EvaluationPrediction
    ],
    model_name: str,
) -> EvaluationSensitivitySuite:
    """Evaluate all cycles, then refit and evaluate regular elections only."""
    cycle_tuple = tuple(cycles)
    all_elections = evaluate_mayoral_model(
        cycle_tuple,
        lead_times=lead_times,
        fit_predict=fit_predict,
        model_name=model_name,
        population="all_elections",
    )
    regular_cycles = tuple(
        cycle for cycle in cycle_tuple if cycle.election_type == "general"
    )
    regular_only = evaluate_mayoral_model(
        regular_cycles,
        lead_times=lead_times,
        fit_predict=fit_predict,
        model_name=model_name,
        population="regular_elections_only",
    )
    return EvaluationSensitivitySuite(all_elections, regular_only)


def compare_against_baseline(
    candidate: EvaluationReport,
    baseline: EvaluationReport,
    *,
    primary_metric: str,
    log_loss_guard: str,
) -> RelativeQualificationDecision:
    """Compare relative scores on one identical frozen evaluation manifest."""
    if candidate.manifest != baseline.manifest:
        raise ValueError("candidate and baseline evaluation manifests must match")
    candidate_cycles = {
        cycle.election_cycle_id: cycle for cycle in candidate.cycles
    }
    baseline_cycles = {
        cycle.election_cycle_id: cycle for cycle in baseline.cycles
    }
    for report in (candidate, baseline):
        if primary_metric not in report.metrics:
            raise ValueError(
                f"{report.model_name!r} has no primary metric {primary_metric!r}"
            )
        if log_loss_guard not in report.metrics:
            raise ValueError(
                f"{report.model_name!r} has no log-loss guard {log_loss_guard!r}"
            )

    candidate_eligible = {
        election_cycle_id
        for election_cycle_id, cycle in candidate_cycles.items()
        if primary_metric in cycle.metrics
    }
    baseline_eligible = {
        election_cycle_id
        for election_cycle_id, cycle in baseline_cycles.items()
        if primary_metric in cycle.metrics
    }
    if candidate_eligible != baseline_eligible or not candidate_eligible:
        raise ValueError("primary metric must cover the same non-empty cycle set")
    guard_candidate_eligible = {
        election_cycle_id
        for election_cycle_id, cycle in candidate_cycles.items()
        if log_loss_guard in cycle.metrics
    }
    guard_baseline_eligible = {
        election_cycle_id
        for election_cycle_id, cycle in baseline_cycles.items()
        if log_loss_guard in cycle.metrics
    }
    if guard_candidate_eligible != guard_baseline_eligible:
        raise ValueError("log-loss guard must cover the same cycle set")

    improved_cycles = sum(
        candidate_cycles[election_cycle_id].metrics[primary_metric]
        < baseline_cycles[election_cycle_id].metrics[primary_metric]
        for election_cycle_id in candidate_eligible
    )
    compared_cycles = len(candidate_eligible)
    majority_improved = improved_cycles * 2 > compared_cycles
    candidate_primary = candidate.metrics[primary_metric]
    baseline_primary = baseline.metrics[primary_metric]
    candidate_log_loss = candidate.metrics[log_loss_guard]
    baseline_log_loss = baseline.metrics[log_loss_guard]
    primary_scores_finite = all(
        math.isfinite(score) for score in (candidate_primary, baseline_primary)
    )
    log_loss_scores_finite = all(
        math.isfinite(score)
        for score in (candidate_log_loss, baseline_log_loss)
    )
    aggregate_scores_finite = primary_scores_finite and log_loss_scores_finite
    aggregate_primary_improved = (
        primary_scores_finite and candidate_primary < baseline_primary
    )
    aggregate_log_loss_not_worse = (
        log_loss_scores_finite and candidate_log_loss <= baseline_log_loss
    )
    relative_qualifies = (
        aggregate_primary_improved
        and aggregate_log_loss_not_worse
        and majority_improved
    )
    return RelativeQualificationDecision(
        candidate_model=candidate.model_name,
        baseline_model=baseline.model_name,
        primary_metric=primary_metric,
        log_loss_guard=log_loss_guard,
        candidate_primary_score=candidate_primary,
        baseline_primary_score=baseline_primary,
        candidate_log_loss=candidate_log_loss,
        baseline_log_loss=baseline_log_loss,
        aggregate_primary_improved=aggregate_primary_improved,
        aggregate_log_loss_not_worse=aggregate_log_loss_not_worse,
        aggregate_scores_finite=aggregate_scores_finite,
        improved_cycles=improved_cycles,
        compared_cycles=compared_cycles,
        majority_of_cycles_improved=majority_improved,
        relative_qualifies=relative_qualifies,
    )


def assess_absolute_reliability(
    report: EvaluationReport,
    maximum_scores: Mapping[str, float] | None,
) -> AbsoluteReliabilityDecision:
    """Apply configured maximum-score checks, or fail closed when deferred."""
    if not maximum_scores:
        return AbsoluteReliabilityDecision(configured=False, passed=False, checks=())
    checks: list[ReliabilityCheck] = []
    for metric, raw_maximum in maximum_scores.items():
        maximum = _as_finite_float(raw_maximum, f"maximum for {metric!r}")
        if maximum < 0.0:
            raise ValueError("absolute reliability maxima must be non-negative")
        observed = report.metrics.get(metric)
        checks.append(
            ReliabilityCheck(
                metric=metric,
                observed=observed,
                maximum=maximum,
                passed=observed is not None and observed <= maximum,
            )
        )
    return AbsoluteReliabilityDecision(
        configured=True,
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )


def qualify_model_ladder(
    *,
    naive: EvaluationReport,
    endpoint: EvaluationReport,
    primary_metric: str,
    log_loss_guard: str,
    endpoint_maximum_scores: Mapping[str, float] | None,
    richer: EvaluationReport | None = None,
) -> ModelLadderDecision:
    """Qualify the endpoint and an optional richer model without bypasses.

    ``None`` thresholds mean the absolute checks remain deferred, so neither
    the endpoint nor a downstream richer model can qualify. A richer model
    must clear the same frozen absolute maxima as well as beat an endpoint that
    itself cleared both its naive comparison and absolute checks.
    """
    endpoint_relative = compare_against_baseline(
        endpoint,
        naive,
        primary_metric=primary_metric,
        log_loss_guard=log_loss_guard,
    )
    endpoint_reliability = assess_absolute_reliability(
        endpoint,
        endpoint_maximum_scores,
    )
    endpoint_qualifies = (
        endpoint_relative.relative_qualifies and endpoint_reliability.passed
    )
    if richer is None:
        return ModelLadderDecision(
            endpoint_relative=endpoint_relative,
            endpoint_reliability=endpoint_reliability,
            endpoint_qualifies=endpoint_qualifies,
            richer_relative=None,
            richer_reliability=None,
            richer_qualifies=None,
        )
    richer_relative = compare_against_baseline(
        richer,
        endpoint,
        primary_metric=primary_metric,
        log_loss_guard=log_loss_guard,
    )
    richer_reliability = assess_absolute_reliability(
        richer,
        endpoint_maximum_scores,
    )
    richer_qualifies = (
        endpoint_qualifies
        and richer_relative.relative_qualifies
        and richer_reliability.passed
    )
    return ModelLadderDecision(
        endpoint_relative=endpoint_relative,
        endpoint_reliability=endpoint_reliability,
        endpoint_qualifies=endpoint_qualifies,
        richer_relative=richer_relative,
        richer_reliability=richer_reliability,
        richer_qualifies=richer_qualifies,
    )


def _validate_evaluation_inputs(
    cycles: tuple[ElectionCycle, ...],
    lead_times: Sequence[int],
    *,
    model_name: str,
    population: EvaluationPopulation,
) -> tuple[int, ...]:
    _identifier(model_name, "model_name")
    if population not in {"all_elections", "regular_elections_only"}:
        raise ValueError("unknown evaluation population")
    if population == "regular_elections_only" and any(
        cycle.election_type != "general" for cycle in cycles
    ):
        raise ValueError(
            "regular_elections_only population cannot contain a by-election"
        )
    if len(cycles) < 2:
        raise ValueError("whole-election evaluation requires at least two cycles")
    election_cycle_ids = [cycle.election_cycle_id for cycle in cycles]
    if len(election_cycle_ids) != len(set(election_cycle_ids)):
        raise ValueError("election_cycle_id values must be unique")

    lead_time_tuple = tuple(lead_times)
    if not lead_time_tuple:
        raise ValueError("at least one fixed lead time is required")
    if len(lead_time_tuple) != len(set(lead_time_tuple)):
        raise ValueError("fixed lead times must be unique")
    for lead_time in lead_time_tuple:
        if type(lead_time) is not int or lead_time < 0:
            raise ValueError("fixed lead times must be non-negative integers")
    for cycle in cycles:
        available = {
            snapshot.days_before_election for snapshot in cycle.snapshots
        }
        missing = [
            lead_time
            for lead_time in lead_time_tuple
            if lead_time not in available
        ]
        if missing:
            raise ValueError(
                f"cycle {cycle.election_cycle_id!r} is missing "
                f"fixed lead time(s) {missing}"
            )
    return lead_time_tuple


def _validated_share_mapping(
    raw_shares: Mapping[str, float],
    *,
    label: str,
) -> Mapping[str, float]:
    shares: dict[str, float] = {}
    for raw_candidate_id, raw_share in raw_shares.items():
        candidate_id = _identifier(raw_candidate_id, "candidate_id")
        share = _as_finite_float(raw_share, f"{label} for {candidate_id!r}")
        if share < 0.0:
            raise ValueError(f"{label} must be non-negative")
        shares[candidate_id] = share
    if len(shares) < 2:
        raise ValueError("Final Ballot must contain at least two candidates")
    total = sum(shares.values())
    if not math.isclose(
        total,
        1.0,
        rel_tol=0.0,
        abs_tol=_PROBABILITY_TOLERANCE,
    ):
        raise ValueError(f"{label} must sum to 1; received {total}")
    return MappingProxyType(shares)


def _add_binary_scores(
    scores: dict[str, float],
    quantity: str,
    probability: float,
    observed: bool,
) -> None:
    probability = _clamp_probability(probability)
    truth = 1.0 if observed else 0.0
    scores[binary_brier_metric(quantity)] = (probability - truth) ** 2
    probability_of_observed = probability if observed else 1.0 - probability
    scores[binary_log_loss_metric(quantity)] = _negative_log_probability(
        probability_of_observed
    )


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must not be blank")
    return value


def _quantity_name(quantity: str) -> str:
    return _identifier(quantity, "quantity name")


def _as_finite_float(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a finite number") from error
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _negative_log_probability(probability: float) -> float:
    return math.inf if probability <= 0.0 else -math.log(probability)


def _clamp_probability(probability: float) -> float:
    if not -_PROBABILITY_TOLERANCE <= probability <= 1.0 + _PROBABILITY_TOLERANCE:
        raise ValueError(f"derived probability lies outside [0, 1]: {probability}")
    return min(1.0, max(0.0, probability))


def _mean_metric_maps(metric_maps: tuple[Mapping[str, float], ...]) -> dict[str, float]:
    if not metric_maps:
        raise ValueError("cannot aggregate an empty score collection")
    metric_names = sorted({name for metrics in metric_maps for name in metrics})
    return {
        metric: sum(
            metrics[metric] for metrics in metric_maps if metric in metrics
        )
        / sum(metric in metrics for metrics in metric_maps)
        for metric in metric_names
    }
