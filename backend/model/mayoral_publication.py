"""Compose a public Mayoral quantity's publication decision (M3 gate logic).

This orchestrates the frozen registry (tier floor + historical unlock, ADR 0033
/ 0005), operational-integrity fail-closed (ADR 0032), and the shared Band
Stability Gate (ADR 0018) into one per-quantity verdict. Each quantity is gated
independently (ADR 0003), and its evidence tier is always reported alongside the
verdict, never folded into it (ADR 0033).

The orchestrator consumes already-computed Mandatory Sensitivity Variants; the
production of those variants from the live endpoint (running each seam and
reducing draws to a quantity probability + 99% error interval) is model-to-gate
wiring and belongs to snapshot integration (INT), not to this gate layer.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from backend.model.mayoral_evidence_tier import (
    MayoralEvidenceTier,
    MayoralEvidenceTierResult,
)
from backend.model.mayoral_publication_gates import (
    QuantityGateStatus,
    mayoral_quantity_gate_status,
)
from backend.model.publication import (
    ProbabilityBand,
    SensitivityVariant,
    evaluate_band_stability,
)


class Availability(Enum):
    """The public availability state of a quantity (ADR 0003, 0033)."""

    AVAILABLE = "Forecast Available"
    UNAVAILABLE = "Forecast Unavailable"
    NOT_APPLICABLE = "Not Applicable"


@dataclass(frozen=True, slots=True)
class MayoralQuantityPublication:
    """A quantity's availability, its published band (if any), and its tier."""

    quantity: str
    candidate_id: str | None
    tier: MayoralEvidenceTier
    availability: Availability
    band: ProbabilityBand | None
    reason: str

    @property
    def is_published(self) -> bool:
        return self.availability is Availability.AVAILABLE


def compose_mayoral_quantity_publication(
    quantity: str,
    tier_result: MayoralEvidenceTierResult,
    *,
    race_has_incumbent: bool,
    candidate_id: str | None = None,
    variants: Iterable[SensitivityVariant] | None = None,
) -> MayoralQuantityPublication:
    """Resolve one public mayoral quantity to Available / Unavailable / N/A."""

    tier = tier_result.tier
    status = mayoral_quantity_gate_status(
        quantity,
        tier_result,
        race_has_incumbent=race_has_incumbent,
        candidate_id=candidate_id,
    )

    def result(
        availability: Availability,
        band: ProbabilityBand | None,
        reason: str,
    ) -> MayoralQuantityPublication:
        return MayoralQuantityPublication(
            quantity=quantity,
            candidate_id=candidate_id,
            tier=tier,
            availability=availability,
            band=band,
            reason=reason,
        )

    if status is QuantityGateStatus.NOT_APPLICABLE:
        return result(Availability.NOT_APPLICABLE, None, "not applicable in this race")
    if status is QuantityGateStatus.HISTORY_BLOCKED:
        return result(
            Availability.UNAVAILABLE,
            None,
            "required tier has not appeared in three Held-Out Election Cycles",
        )
    if status is QuantityGateStatus.TIER_TOO_LOW:
        return result(
            Availability.UNAVAILABLE,
            None,
            f"current-cycle polling has not reached the required tier ({tier.label})",
        )

    # UNLOCKED: fail closed on missing variants (ADR 0032), then the stability gate.
    variant_tuple = tuple(variants) if variants is not None else ()
    if not variant_tuple:
        return result(
            Availability.UNAVAILABLE,
            None,
            "no sensitivity variants were computed",
        )

    decision = evaluate_band_stability(variant_tuple)
    if decision.is_published:
        return result(Availability.AVAILABLE, decision.band, "")
    return result(Availability.UNAVAILABLE, None, decision.reason)
