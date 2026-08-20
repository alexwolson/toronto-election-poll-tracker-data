from datetime import UTC, date, datetime

from backend.model.mayoral_evidence_tier import (
    MayoralEvidenceTier,
    MayoralPollSampleEvidence,
    classify_mayoral_evidence_tier,
)
from backend.model.mayoral_publication_gates import (
    CHALLENGER_WIN,
    CLOSE_RESULT,
    INCUMBENT_DEFEAT,
    MAYORAL_QUANTITY_REQUIRED_TIER,
    MAYORAL_TIER_HISTORICAL_CYCLE_COUNTS,
    MAYORAL_TIER_UNLOCK_MINIMUM_CYCLES,
    QuantityGateStatus,
    mayoral_quantity_gate_status,
)

NOM = datetime(2026, 8, 21, 18, 0, tzinfo=UTC)


def _tier(samples):
    return classify_mayoral_evidence_tier(samples, nomination_close=NOM)


def _s(sid, pollster, end, measured=("chow", "bradford")):
    return MayoralPollSampleEvidence(sid, pollster, end, frozenset(measured))


def test_required_tiers_follow_adr_0033_floors() -> None:
    assert MAYORAL_QUANTITY_REQUIRED_TIER[CLOSE_RESULT] is (
        MayoralEvidenceTier.M2_POST_FINAL
    )
    assert MAYORAL_QUANTITY_REQUIRED_TIER[INCUMBENT_DEFEAT] is (
        MayoralEvidenceTier.M2_POST_FINAL
    )
    assert MAYORAL_QUANTITY_REQUIRED_TIER[CHALLENGER_WIN] is (
        MayoralEvidenceTier.M3_REPLICATED_POST_FINAL
    )


def test_frozen_history_counts_clear_the_three_cycle_floor() -> None:
    # ADR 0005: a tier must appear in >=3 Held-Out Election Cycles to unlock a
    # quantity. Frozen from the 2003-2023 corpus: M2 in 7, M3 in 6.
    assert MAYORAL_TIER_UNLOCK_MINIMUM_CYCLES == 3
    assert MAYORAL_TIER_HISTORICAL_CYCLE_COUNTS[MayoralEvidenceTier.M2_POST_FINAL] == 7
    assert (
        MAYORAL_TIER_HISTORICAL_CYCLE_COUNTS[
            MayoralEvidenceTier.M3_REPLICATED_POST_FINAL
        ]
        == 6
    )
    for tier, count in MAYORAL_TIER_HISTORICAL_CYCLE_COUNTS.items():
        assert count >= MAYORAL_TIER_UNLOCK_MINIMUM_CYCLES, tier


def test_incumbent_defeat_is_not_applicable_in_an_open_seat() -> None:
    tier = _tier([_s("a", "Forum", date(2026, 9, 20))])  # M2
    status = mayoral_quantity_gate_status(
        INCUMBENT_DEFEAT, tier, race_has_incumbent=False
    )
    assert status is QuantityGateStatus.NOT_APPLICABLE


def test_m2_unlocks_close_and_incumbent_defeat_when_incumbent_runs() -> None:
    tier = _tier([_s("a", "Forum", date(2026, 9, 20))])  # M2
    assert (
        mayoral_quantity_gate_status(CLOSE_RESULT, tier, race_has_incumbent=True)
        is QuantityGateStatus.UNLOCKED
    )
    assert (
        mayoral_quantity_gate_status(INCUMBENT_DEFEAT, tier, race_has_incumbent=True)
        is QuantityGateStatus.UNLOCKED
    )


def test_pre_final_tier_is_too_low_for_any_predictive_quantity() -> None:
    tier = _tier([_s("a", "Forum", date(2026, 8, 5))])  # M1
    assert (
        mayoral_quantity_gate_status(CLOSE_RESULT, tier, race_has_incumbent=True)
        is QuantityGateStatus.TIER_TOO_LOW
    )


def test_challenger_win_needs_m3_for_that_challenger() -> None:
    samples = [
        _s("a", "Forum", date(2026, 9, 15), ("chow", "bradford")),
        _s("b", "Liaison", date(2026, 9, 20), ("chow", "bradford")),
        _s("c", "Mainstreet", date(2026, 9, 22), ("chow", "bradford")),
    ]
    tier = _tier(samples)
    assert (
        mayoral_quantity_gate_status(
            CHALLENGER_WIN, tier, race_has_incumbent=True, candidate_id="bradford"
        )
        is QuantityGateStatus.UNLOCKED
    )
    # alexander is not individually measured -> tier too low for that challenger.
    assert (
        mayoral_quantity_gate_status(
            CHALLENGER_WIN, tier, race_has_incumbent=True, candidate_id="alexander"
        )
        is QuantityGateStatus.TIER_TOO_LOW
    )
