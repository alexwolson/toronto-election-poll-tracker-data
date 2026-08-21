"""Live mayoral forecast feed for the frontend package (INT).

Turns the qualified Mayoral Endpoint Bridge into the published per-candidate
quantities. This module holds the parts that are pure functions of the model's
share draws — the three public quantities and their Monte-Carlo error intervals —
decoupled from the outcome-scoring path in ``mayoral_evaluation`` (which needs a
known outcome). Fitting the endpoint on the live target, running the Mandatory
Sensitivity Variants, and composing the M3 publication gates build on these.

Quantities (ADR 0003/0033), all derived from the full-ballot share draws:
- Candidate Win Probability: the draw fraction in which a candidate has the top
  share (an exact tie splits that draw's winner weight among the tied).
- Close-Result Probability: the draw fraction whose winning margin is within the
  close threshold.
- Incumbent-Defeat Probability: one minus the incumbent's win probability.

Each probability carries a two-sided 99% Monte-Carlo error interval (Wilson score
on the draw count) for the Band Stability Gate (ADR 0018).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from backend.model.mayoral_evaluation import FullBallotShareDraws

# Two-sided 99% normal quantile, for the Monte-Carlo error interval (ADR 0018).
_Z_99 = 2.5758293035489004


@dataclass(frozen=True, slots=True)
class QuantityEstimate:
    """A probability point estimate plus its two-sided 99% MC error interval."""

    probability: float
    interval_lower: float
    interval_upper: float


def _wilson_interval(p: float, n: int) -> tuple[float, float]:
    """Two-sided 99% Wilson score interval for a proportion p from n draws.

    Wilson is used rather than the normal approximation because it stays inside
    [0, 1] and is well-behaved near 0 and 1, where the Band Stability Gate is most
    sensitive; the point estimate p always lies within the returned interval.
    """
    if n <= 0:
        raise ValueError("draw count must be positive")
    z2 = _Z_99 * _Z_99
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    half = (_Z_99 * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n))) / denom
    return max(0.0, center - half), min(1.0, center + half)


def _estimate(p: float, n: int) -> QuantityEstimate:
    lower, upper = _wilson_interval(p, n)
    return QuantityEstimate(probability=p, interval_lower=lower, interval_upper=upper)


@dataclass(frozen=True, slots=True)
class MayoralForecastQuantities:
    """Every public quantity for one fitted set of share draws."""

    candidate_win: dict[str, QuantityEstimate]
    close_result: QuantityEstimate
    incumbent_defeat: QuantityEstimate | None  # None in an open race


def forecast_quantities(
    draws: FullBallotShareDraws,
    *,
    incumbent_candidate_id: str | None,
    close_threshold: float = 0.05,
) -> MayoralForecastQuantities:
    """Reduce full-ballot share draws to the published quantities + 99% intervals."""
    candidate_ids = draws.candidate_ids
    draw_count = len(draws.draws)
    win_weight = dict.fromkeys(candidate_ids, 0.0)
    close_draws = 0
    for draw in draws.draws:
        maximum = max(draw)
        tied = [index for index, share in enumerate(draw) if share == maximum]
        weight = 1.0 / (draw_count * len(tied))
        for index in tied:
            win_weight[candidate_ids[index]] += weight
        leading = sorted(draw, reverse=True)[:2]
        if leading[0] - leading[1] <= close_threshold:
            close_draws += 1

    candidate_win = {
        candidate_id: _estimate(win_weight[candidate_id], draw_count)
        for candidate_id in candidate_ids
    }
    close_result = _estimate(close_draws / draw_count, draw_count)
    incumbent_defeat: QuantityEstimate | None = None
    if incumbent_candidate_id is not None:
        if incumbent_candidate_id not in win_weight:
            raise ValueError("incumbent_candidate_id is not on the ballot")
        incumbent_defeat = _estimate(
            1.0 - win_weight[incumbent_candidate_id], draw_count
        )
    return MayoralForecastQuantities(
        candidate_win=candidate_win,
        close_result=close_result,
        incumbent_defeat=incumbent_defeat,
    )
