from pathlib import Path

from backend.model.historical_mayoral import load_historical_mayoral_corpus
from backend.model.mayoral_endpoint import MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES
from backend.model.mayoral_endpoint_qualification import (
    MAYORAL_ENDPOINT_ABSOLUTE_MAXIMUM_SCORES,
    MAYORAL_ENDPOINT_EVALUATION_DRAW_COUNT,
    MayoralEndpointQualification,
    evaluate_mayoral_endpoint_qualification,
)
from backend.model.mayoral_evaluation import (
    MAYORAL_MODEL_FAMILY_LOG_GUARD,
    MAYORAL_MODEL_FAMILY_PRIMARY,
)

ROOT = Path(__file__).resolve().parents[2]


def test_endpoint_qualification_run_is_frozen_and_fail_closed() -> None:
    result = evaluate_mayoral_endpoint_qualification(
        load_historical_mayoral_corpus(ROOT)
    )

    assert MAYORAL_ENDPOINT_EVALUATION_DRAW_COUNT == 4096
    assert MAYORAL_ENDPOINT_ABSOLUTE_MAXIMUM_SCORES is None
    assert result.comparator.all_elections.lead_times == (
        MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES
    )
    assert result.bridge.all_elections.manifest == (
        result.comparator.all_elections.manifest
    )
    assert result.bridge.regular_elections_only.manifest == (
        result.comparator.regular_elections_only.manifest
    )
    assert result.all_elections.endpoint_relative.primary_metric == (
        MAYORAL_MODEL_FAMILY_PRIMARY
    )
    assert result.all_elections.endpoint_relative.log_loss_guard == (
        MAYORAL_MODEL_FAMILY_LOG_GUARD
    )
    assert not result.all_elections.endpoint_reliability.configured
    assert not result.regular_elections_only.endpoint_reliability.configured
    assert not result.qualifies


class _StubDecision:
    """Minimal stand-in exposing only endpoint_qualifies for the gate test."""

    def __init__(self, qualifies: bool) -> None:
        self.endpoint_qualifies = qualifies


def _qualification(*, all_elections: bool, regular: bool):
    return MayoralEndpointQualification(
        comparator=None,  # type: ignore[arg-type]
        bridge=None,  # type: ignore[arg-type]
        all_elections=_StubDecision(all_elections),  # type: ignore[arg-type]
        regular_elections_only=_StubDecision(regular),  # type: ignore[arg-type]
    )


def test_qualification_gate_excludes_by_elections() -> None:
    # ADR 0040: by-elections (2023) are structurally unlike general elections, so
    # the regular-elections-only population is authoritative and all_elections is
    # report-only. The gate must track regular_elections_only regardless of the
    # all_elections outcome.
    assert _qualification(all_elections=False, regular=True).qualifies is True
    assert _qualification(all_elections=True, regular=False).qualifies is False
    assert _qualification(all_elections=True, regular=True).qualifies is True
    assert _qualification(all_elections=False, regular=False).qualifies is False
