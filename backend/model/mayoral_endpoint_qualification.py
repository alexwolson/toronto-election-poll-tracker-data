"""Reproducible qualification run for the polling-only Mayoral Endpoint.

This module is the single orchestration interface for the endpoint model
ladder.  It fixes the historical cutoffs, comparator, bridge, draw count, and
proper-score contract while leaving absolute reliability maxima explicitly
deferred.  It has no live snapshot or publication side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from backend.model.historical_mayoral import HistoricalMayoralCorpus
from backend.model.historical_mayoral_evaluation import (
    build_historical_mayoral_evaluation_cycles,
)
from backend.model.mayoral_endpoint import (
    MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
    MayoralEndpointPredictor,
)
from backend.model.mayoral_evaluation import (
    MAYORAL_MODEL_FAMILY_LOG_GUARD,
    MAYORAL_MODEL_FAMILY_PRIMARY,
    EvaluationSensitivitySuite,
    ModelLadderDecision,
    evaluate_with_regular_election_sensitivity,
    qualify_model_ladder,
)


MAYORAL_ENDPOINT_EVALUATION_DRAW_COUNT: Final = 4096
MAYORAL_ENDPOINT_ABSOLUTE_MAXIMUM_SCORES: Final[Mapping[str, float] | None] = None


@dataclass(frozen=True, slots=True)
class MayoralEndpointQualification:
    """Complete relative and fail-closed absolute endpoint evaluation."""

    comparator: EvaluationSensitivitySuite
    bridge: EvaluationSensitivitySuite
    all_elections: ModelLadderDecision
    regular_elections_only: ModelLadderDecision

    @property
    def qualifies(self) -> bool:
        return (
            self.all_elections.endpoint_qualifies
            and self.regular_elections_only.endpoint_qualifies
        )


def evaluate_mayoral_endpoint_qualification(
    corpus: HistoricalMayoralCorpus,
) -> MayoralEndpointQualification:
    """Run the frozen comparator/bridge ladder without publication authority."""

    cycles = build_historical_mayoral_evaluation_cycles(
        corpus,
        lead_times=MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
        analysis_time_local=MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    )
    comparator = evaluate_with_regular_election_sensitivity(
        cycles,
        lead_times=MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
        fit_predict=MayoralEndpointPredictor(
            "latest-sample-comparator",
            draw_count=MAYORAL_ENDPOINT_EVALUATION_DRAW_COUNT,
        ),
        model_name="latest-sample-comparator",
    )
    bridge = evaluate_with_regular_election_sensitivity(
        cycles,
        lead_times=MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
        fit_predict=MayoralEndpointPredictor(
            "firm-balanced-bridge",
            draw_count=MAYORAL_ENDPOINT_EVALUATION_DRAW_COUNT,
        ),
        model_name="firm-balanced-bridge",
    )
    all_elections = qualify_model_ladder(
        naive=comparator.all_elections,
        endpoint=bridge.all_elections,
        primary_metric=MAYORAL_MODEL_FAMILY_PRIMARY,
        log_loss_guard=MAYORAL_MODEL_FAMILY_LOG_GUARD,
        endpoint_maximum_scores=MAYORAL_ENDPOINT_ABSOLUTE_MAXIMUM_SCORES,
    )
    regular_elections_only = qualify_model_ladder(
        naive=comparator.regular_elections_only,
        endpoint=bridge.regular_elections_only,
        primary_metric=MAYORAL_MODEL_FAMILY_PRIMARY,
        log_loss_guard=MAYORAL_MODEL_FAMILY_LOG_GUARD,
        endpoint_maximum_scores=MAYORAL_ENDPOINT_ABSOLUTE_MAXIMUM_SCORES,
    )
    return MayoralEndpointQualification(
        comparator=comparator,
        bridge=bridge,
        all_elections=all_elections,
        regular_elections_only=regular_elections_only,
    )
