from datetime import UTC, date, datetime

from backend.model.mayoral_evidence_tier import (
    MayoralEvidenceTier,
    MayoralPollSampleEvidence,
    classify_mayoral_evidence_tier,
)

# The 2026 Final Ballot becomes knowable at nomination close (ADR 0002/0033).
NOMINATION_CLOSE = datetime(2026, 8, 21, 18, 0, tzinfo=UTC)


def _sample(sample_id, pollster, fieldwork_end, measured=("chow", "bradford")):
    return MayoralPollSampleEvidence(
        sample_id=sample_id,
        pollster=pollster,
        fieldwork_end=fieldwork_end,
        measured_candidates=frozenset(measured),
    )


def _classify(samples):
    return classify_mayoral_evidence_tier(samples, nomination_close=NOMINATION_CLOSE)


def test_tier_labels_are_the_adr_0033_wording_verbatim() -> None:
    assert MayoralEvidenceTier.M0_STRUCTURAL.label == "M0 — Structural Only"
    assert MayoralEvidenceTier.M1_PRE_FINAL.label == "M1 — Pre-Final Polling"
    assert MayoralEvidenceTier.M2_POST_FINAL.label == "M2 — Post-Final Polling"
    assert (
        MayoralEvidenceTier.M3_REPLICATED_POST_FINAL.label
        == "M3 — Replicated Post-Final Polling"
    )


def test_no_qualifying_poll_is_structural_only() -> None:
    result = _classify([])
    assert result.tier is MayoralEvidenceTier.M0_STRUCTURAL
    assert not result.close_result_eligible
    assert not result.incumbent_defeat_eligible
    assert not result.challenger_win_eligible("bradford")


def test_pre_final_polling_only_is_m1_and_unlocks_nothing() -> None:
    # Every 2026 poll today is pre-Final (nominations close 2026-08-21).
    samples = [
        _sample("a", "Forum Research", date(2026, 8, 5)),
        _sample("b", "Liaison Strategies", date(2026, 8, 7)),
    ]
    result = _classify(samples)
    assert result.tier is MayoralEvidenceTier.M1_PRE_FINAL
    assert not result.close_result_eligible
    assert not result.incumbent_defeat_eligible
    assert not result.challenger_win_eligible("bradford")
    assert result.post_final_sample_ids == ()


def test_one_post_final_sample_reaches_m2_and_unlocks_close_and_defeat() -> None:
    samples = [
        _sample("a", "Forum Research", date(2026, 8, 5)),  # pre-Final
        _sample("b", "Liaison Strategies", date(2026, 9, 20)),  # post-Final
    ]
    result = _classify(samples)
    assert result.tier is MayoralEvidenceTier.M2_POST_FINAL
    assert result.close_result_eligible
    assert result.incumbent_defeat_eligible
    assert result.challenger_win_eligible("bradford") is False  # needs M3
    assert result.post_final_sample_ids == ("b",)


def test_boundary_day_sample_overlaps_and_counts_as_post_final() -> None:
    # A sample whose fieldwork ends ON nomination-close day overlaps the 18:00
    # boundary and is post-Final; one ending the day before is pre-Final.
    on_day = _classify([_sample("x", "Forum Research", date(2026, 8, 21))])
    assert on_day.tier is MayoralEvidenceTier.M2_POST_FINAL
    day_before = _classify([_sample("y", "Forum Research", date(2026, 8, 20))])
    assert day_before.tier is MayoralEvidenceTier.M1_PRE_FINAL


def test_datetime_precision_is_compared_against_the_intra_day_boundary() -> None:
    before = _classify(
        [_sample("x", "Forum", datetime(2026, 8, 21, 12, 0, tzinfo=UTC))]
    )
    assert before.tier is MayoralEvidenceTier.M1_PRE_FINAL  # noon < 18:00
    after = _classify([_sample("y", "Forum", datetime(2026, 8, 21, 19, 0, tzinfo=UTC))])
    assert after.tier is MayoralEvidenceTier.M2_POST_FINAL  # 19:00 > 18:00


def test_replicated_post_final_reaches_m3_and_unlocks_measured_challenger() -> None:
    samples = [
        _sample("a", "Forum Research", date(2026, 9, 15), ("chow", "bradford")),
        _sample("b", "Liaison Strategies", date(2026, 9, 20), ("chow", "bradford")),
        _sample(
            "c", "Mainstreet", date(2026, 8, 10), ("chow", "bradford")
        ),  # pre-Final
    ]
    result = _classify(samples)
    # 3 samples, 3 pollsters, 2 post-Final -> M3.
    assert result.tier is MayoralEvidenceTier.M3_REPLICATED_POST_FINAL
    assert result.close_result_eligible
    assert result.challenger_win_eligible("bradford") is True


def test_m3_field_but_challenger_measured_in_only_two_is_not_win_eligible() -> None:
    samples = [
        _sample("a", "Forum Research", date(2026, 9, 15), ("chow", "bradford")),
        _sample("b", "Liaison Strategies", date(2026, 9, 20), ("chow", "bradford")),
        _sample("c", "Mainstreet", date(2026, 9, 22), ("chow", "alexander")),
    ]
    result = _classify(samples)
    assert result.tier is MayoralEvidenceTier.M3_REPLICATED_POST_FINAL
    assert result.challenger_win_eligible("bradford") is False  # measured in only 2
    assert result.challenger_win_eligible("alexander") is False  # measured in only 1


def test_three_post_final_from_one_pollster_stays_m2() -> None:
    # Replication requires at least two pollsters; multiple samples from one do not.
    samples = [
        _sample("a", "Forum Research", date(2026, 9, 15)),
        _sample("b", "Forum Research", date(2026, 9, 18)),
        _sample("c", "Forum Research", date(2026, 9, 20)),
    ]
    result = _classify(samples)
    assert result.tier is MayoralEvidenceTier.M2_POST_FINAL
    assert result.challenger_win_eligible("bradford") is False


def test_challenger_win_needs_two_post_final_among_its_measurements() -> None:
    # Three samples measuring bradford across two pollsters, but only ONE post-Final.
    samples = [
        _sample("a", "Forum Research", date(2026, 9, 15)),  # post-Final
        _sample("b", "Liaison Strategies", date(2026, 8, 1)),  # pre-Final
        _sample("c", "Mainstreet", date(2026, 8, 3)),  # pre-Final
    ]
    result = _classify(samples)
    assert result.challenger_win_eligible("bradford") is False
