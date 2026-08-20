"""Frozen Mayoral publication-gate registry (ADR 0003, 0005, 0032, 0033).

Publication gates are frozen by model version (ADR 0005): the required evidence
tier per public quantity and the historical-unlock counts are fixed here before
the 2026 forecast is evaluated, not tuned on the current race. Each public
quantity is gated independently (ADR 0003); Incumbent Defeat Probability is Not
Applicable — not merely unavailable — in an open-seat race.

Two gates live here, both necessary and neither sufficient (the Band Stability
Gate and operational-integrity checks apply downstream):

  1. Current-cycle tier floor (ADR 0033): the quantity's required evidence tier
     must be reached by the current cycle's polling.
  2. Historical unlock (ADR 0005): the required tier must have appeared in at
     least three distinct Held-Out Election Cycles. Frozen from the 2003-2023
     corpus, M2 appeared in 7 cycles and M3 in 6, so no quantity is
     history-blocked in this version (see docs/research/mayoral-evidence-tiers.md).
"""

from __future__ import annotations

from enum import Enum

from backend.model.mayoral_evidence_tier import (
    MayoralEvidenceTier,
    MayoralEvidenceTierResult,
)

# Public mayoral quantity identifiers. CLOSE_RESULT and INCUMBENT_DEFEAT match
# the evaluation metric quantities; CHALLENGER_WIN is the per-challenger
# Candidate Win Probability.
CLOSE_RESULT = "close_result"
INCUMBENT_DEFEAT = "incumbent_defeat"
CHALLENGER_WIN = "challenger_win"

# Frozen with the model version (ADR 0005). Bump on any gate change and rerun the
# complete historical evaluation.
MAYORAL_GATE_REGISTRY_VERSION = "2026-08-19"

# Required current-cycle evidence tier per quantity (ADR 0033 floors).
MAYORAL_QUANTITY_REQUIRED_TIER: dict[str, MayoralEvidenceTier] = {
    CLOSE_RESULT: MayoralEvidenceTier.M2_POST_FINAL,
    INCUMBENT_DEFEAT: MayoralEvidenceTier.M2_POST_FINAL,
    CHALLENGER_WIN: MayoralEvidenceTier.M3_REPLICATED_POST_FINAL,
}

# Distinct Held-Out Election Cycles in which each tier appeared (2003-2023 corpus,
# per-cycle Final-Ballot boundaries). Frozen literals (ADR 0005), not recomputed.
MAYORAL_TIER_HISTORICAL_CYCLE_COUNTS: dict[MayoralEvidenceTier, int] = {
    MayoralEvidenceTier.M2_POST_FINAL: 7,
    MayoralEvidenceTier.M3_REPLICATED_POST_FINAL: 6,
}
MAYORAL_TIER_UNLOCK_MINIMUM_CYCLES = 3


class QuantityGateStatus(Enum):
    """Registry-level verdict, before the stability and integrity gates."""

    UNLOCKED = "unlocked"
    TIER_TOO_LOW = "tier_too_low"  # current-cycle polling has not reached the floor
    HISTORY_BLOCKED = "history_blocked"  # tier appeared in < 3 cycles (ADR 0005)
    NOT_APPLICABLE = "not_applicable"  # e.g. Incumbent Defeat in an open seat


def mayoral_quantity_gate_status(
    quantity: str,
    tier_result: MayoralEvidenceTierResult,
    *,
    race_has_incumbent: bool,
    candidate_id: str | None = None,
) -> QuantityGateStatus:
    """Apply the tier floor (ADR 0033) and historical unlock (ADR 0005).

    Returns the registry verdict only; a quantity that is UNLOCKED here still
    faces the Band Stability Gate (ADR 0018) and operational-integrity checks
    (ADR 0032) before it can publish.
    """

    if quantity == INCUMBENT_DEFEAT and not race_has_incumbent:
        return QuantityGateStatus.NOT_APPLICABLE

    required = MAYORAL_QUANTITY_REQUIRED_TIER[quantity]
    if (
        MAYORAL_TIER_HISTORICAL_CYCLE_COUNTS.get(required, 0)
        < MAYORAL_TIER_UNLOCK_MINIMUM_CYCLES
    ):
        return QuantityGateStatus.HISTORY_BLOCKED

    if quantity == CHALLENGER_WIN:
        if candidate_id is None:
            raise ValueError("challenger win gate requires a candidate_id")
        eligible = tier_result.challenger_win_eligible(candidate_id)
    elif quantity == CLOSE_RESULT:
        eligible = tier_result.close_result_eligible
    elif quantity == INCUMBENT_DEFEAT:
        eligible = tier_result.incumbent_defeat_eligible
    else:
        raise ValueError(f"unknown mayoral quantity {quantity!r}")

    return QuantityGateStatus.UNLOCKED if eligible else QuantityGateStatus.TIER_TOO_LOW
