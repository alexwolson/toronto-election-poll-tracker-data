"""Incumbency-informed candidate for the Mayoral Endpoint (ADR 0013).

This specification layers a single structural prior on the incumbent's
election-day vote share on top of the polling-only firm-balanced bridge.  The
prior is estimated from the Mayoral Comparison Population and enters only as a
mean-shift of the incumbent's point share, weighted against the fitted polling
concentration so that strong or plentiful polls overwhelm it.  Incumbency never
becomes a direct win-probability bonus: every published quantity is still
derived from the same full-field Election Outcome Draws.

The variant receives operational weight only if it qualifies against the
polling-only baseline under the whole-election protocol; otherwise it is
retained as the Mandatory Sensitivity Variant.  Nothing here is wired to a live
snapshot or authorized for publication.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median

from backend.model.mayoral_endpoint import (
    MayoralEndpointFit,
    draws_from_point,
    fit_mayoral_endpoint,
)
from backend.model.mayoral_evaluation import (
    EvaluationPrediction,
    FullBallotShareDraws,
    HeldOutCycle,
    TrainingCycle,
)
from backend.model.mayoral_incumbency import MayoralIncumbencyPopulation

BASE_VARIANT = "firm-balanced-bridge"
DEFAULT_PRIOR_PSEUDOCOUNT = 8.0


class IncumbencyEndpointError(ValueError):
    """Raised when the incumbency-informed variant cannot be formed deterministically."""


def incumbency_prior_share(
    population: MayoralIncumbencyPopulation,
    *,
    exclude_city: str,
    exclude_year: int,
) -> float:
    """Prior mean incumbent share, partially pooled with leave-one-trial-out.

    The single trial matching the target election (``exclude_city`` in
    ``exclude_year``) is removed so a Toronto target never informs its own prior,
    while every other trial -- including Toronto's other defences -- stays in the
    pool (ADR 0013).
    """

    trials = tuple(
        trial
        for trial in population.v1_trials
        if not (
            trial.city_id == exclude_city and trial.election_date.year == exclude_year
        )
    )
    if not trials:
        raise IncumbencyEndpointError(
            "incumbency prior requires at least one comparison trial after exclusion"
        )
    return float(median(float(trial.incumbent_share) for trial in trials))


def _target_city_year(election_cycle_id: str) -> tuple[str, int]:
    city, separator, year = election_cycle_id.rpartition("_")
    if not separator or not city or not (year.isdigit() and len(year) == 4):
        raise IncumbencyEndpointError(
            f"cannot derive city and year from election cycle id {election_cycle_id!r}"
        )
    return city, int(year)


def _reallocate(
    candidate_ids: tuple[str, ...],
    point_shares: tuple[float, ...],
    incumbent_id: str,
    incumbent_share: float,
) -> tuple[float, ...]:
    poll_share = point_shares[candidate_ids.index(incumbent_id)]
    remaining = 1.0 - poll_share
    if remaining <= 0.0:
        raise IncumbencyEndpointError(
            "cannot reallocate around an incumbent already holding the whole ballot"
        )
    scale = (1.0 - incumbent_share) / remaining
    adjusted = tuple(
        incumbent_share if candidate_id == incumbent_id else share * scale
        for candidate_id, share in zip(candidate_ids, point_shares, strict=True)
    )
    total = sum(adjusted)
    if not math.isfinite(total) or total <= 0.0:
        raise IncumbencyEndpointError("incumbency-adjusted point estimate is invalid")
    return tuple(value / total for value in adjusted)


def apply_incumbency_prior(
    fit: MayoralEndpointFit,
    *,
    election_cycle_id: str,
    incumbent_candidate_id: str | None,
    population: MayoralIncumbencyPopulation,
    prior_pseudocount: float,
) -> tuple[float, ...]:
    """Return the point estimate after shrinking the incumbent's share to the prior.

    In an open race the point estimate is returned unchanged.  Otherwise the
    incumbent's share is a precision-weighted blend of the polling point and the
    prior mean, using the fitted concentration as the polling weight so that
    strong evidence overwhelms the prior.
    """

    if incumbent_candidate_id is None:
        return fit.point_shares
    if incumbent_candidate_id not in fit.candidate_ids:
        raise IncumbencyEndpointError(
            f"incumbent {incumbent_candidate_id!r} is not on the Final Ballot"
        )
    if not math.isfinite(prior_pseudocount) or prior_pseudocount < 0.0:
        raise IncumbencyEndpointError(
            "prior_pseudocount must be a finite non-negative number"
        )

    city, year = _target_city_year(election_cycle_id)
    prior_mean = incumbency_prior_share(
        population, exclude_city=city, exclude_year=year
    )
    poll_share = fit.point_shares[fit.candidate_ids.index(incumbent_candidate_id)]
    weight = prior_pseudocount + fit.concentration
    posterior = (
        prior_pseudocount * prior_mean + fit.concentration * poll_share
    ) / weight
    return _reallocate(
        fit.candidate_ids, fit.point_shares, incumbent_candidate_id, posterior
    )


@dataclass(frozen=True, slots=True)
class IncumbencyInformedPredictor:
    """Fold-local incumbency-informed predictor accepted by the evaluation harness."""

    population: MayoralIncumbencyPopulation
    draw_count: int = 2048
    prior_pseudocount: float = DEFAULT_PRIOR_PSEUDOCOUNT
    base_variant: str = BASE_VARIANT

    def __post_init__(self) -> None:
        if type(self.draw_count) is not int or self.draw_count <= 0:
            raise ValueError("draw_count must be a positive integer")
        if not math.isfinite(self.prior_pseudocount) or self.prior_pseudocount < 0.0:
            raise ValueError("prior_pseudocount must be a finite non-negative number")

    def __call__(
        self,
        training_cycles: tuple[TrainingCycle, ...],
        target: HeldOutCycle,
    ) -> EvaluationPrediction:
        fit = fit_mayoral_endpoint(training_cycles, target, variant=self.base_variant)
        point = apply_incumbency_prior(
            fit,
            election_cycle_id=target.election_cycle_id,
            incumbent_candidate_id=target.incumbent_candidate_id,
            population=self.population,
            prior_pseudocount=self.prior_pseudocount,
        )
        draws = draws_from_point(
            fit.candidate_ids, point, fit.concentration, self.draw_count
        )
        return EvaluationPrediction(
            FullBallotShareDraws(candidate_ids=fit.candidate_ids, draws=draws)
        )
