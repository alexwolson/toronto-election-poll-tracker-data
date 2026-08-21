from backend.model.mayoral_evidence_tier import (
    MayoralEvidenceTier,
    MayoralPollSampleEvidence,
    classify_mayoral_evidence_tier,
)

# The 2026 certified viable field, known once nominations close (ADR 0002/0033/0046).
FINAL_FIELD = frozenset({"chow", "bradford", "alexander"})


def _sample(sample_id, pollster, measured=("chow", "bradford", "alexander")):
    return MayoralPollSampleEvidence(
        sample_id=sample_id,
        pollster=pollster,
        measured_candidates=frozenset(measured),
    )


def _classify(samples, final_field=FINAL_FIELD):
    return classify_mayoral_evidence_tier(samples, final_field=final_field)


def test_tier_labels_are_the_adr_0033_wording() -> None:
    assert MayoralEvidenceTier.M0_STRUCTURAL.label == "M0 — Structural Only"
    assert MayoralEvidenceTier.M1_PRE_FINAL.label == "M1 — Pre-Final Polling"
    assert MayoralEvidenceTier.M2_POST_FINAL.label == "M2 — Final-Field Polling"
    assert (
        MayoralEvidenceTier.M3_REPLICATED_POST_FINAL.label
        == "M3 — Replicated Final-Field Polling"
    )


def test_no_qualifying_poll_is_structural_only() -> None:
    result = _classify([])
    assert result.tier is MayoralEvidenceTier.M0_STRUCTURAL
    assert not result.close_result_eligible
    assert not result.incumbent_defeat_eligible
    assert not result.challenger_win_eligible("bradford")


def test_before_certification_the_field_is_unknown_and_nothing_is_final_field() -> None:
    # final_field is None until the Final Ballot is certified: samples exist but
    # none can be final-field, so the cycle caps at M1 and unlocks nothing.
    samples = [
        _sample("a", "Forum Research"),
        _sample("b", "Liaison Strategies"),
    ]
    result = _classify(samples, final_field=None)
    assert result.tier is MayoralEvidenceTier.M1_PRE_FINAL
    assert not result.close_result_eligible
    assert not result.challenger_win_eligible("bradford")
    assert result.final_field_sample_ids == ()


def test_poll_missing_a_viable_candidate_is_not_final_field() -> None:
    # A poll fielded before Alexander entered measured only {chow, bradford};
    # it does not measure the certified field and stays M1.
    samples = [
        _sample("a", "Liaison Strategies", ("chow", "bradford")),
        _sample("b", "Mainstreet Research", ("chow", "bradford")),
    ]
    result = _classify(samples)
    assert result.tier is MayoralEvidenceTier.M1_PRE_FINAL
    assert result.final_field_sample_ids == ()


def test_poll_measuring_a_dropped_out_candidate_is_not_final_field() -> None:
    # A poll that individually measured a candidate absent from the final ballot
    # (e.g. Tory) reflects a stale field and is not final-field.
    samples = [_sample("a", "Liaison Strategies", ("chow", "bradford", "tory"))]
    result = _classify(samples)
    assert result.tier is MayoralEvidenceTier.M1_PRE_FINAL


def test_one_final_field_sample_reaches_m2_and_unlocks_close_and_defeat() -> None:
    samples = [
        _sample("a", "Liaison Strategies", ("chow", "bradford")),  # pre-field
        _sample("b", "Forum Research"),  # measures the certified field
    ]
    result = _classify(samples)
    assert result.tier is MayoralEvidenceTier.M2_POST_FINAL
    assert result.close_result_eligible
    assert result.incumbent_defeat_eligible
    assert result.challenger_win_eligible("bradford") is False  # needs M3
    assert result.final_field_sample_ids == ("b",)


def test_replicated_final_field_reaches_m3_and_unlocks_measured_challenger() -> None:
    # Exactly the 2026 case: three settled-field samples across two pollsters.
    samples = [
        _sample("forum", "Forum Research"),
        _sample("liaison-aug5", "Liaison Strategies"),
        _sample("liaison-aug20", "Liaison Strategies"),
    ]
    result = _classify(samples)
    assert result.tier is MayoralEvidenceTier.M3_REPLICATED_POST_FINAL
    assert result.close_result_eligible
    assert result.challenger_win_eligible("bradford") is True
    assert result.challenger_win_eligible("alexander") is True


def test_three_final_field_from_one_pollster_stays_m2() -> None:
    # Replication requires at least two pollsters; multiple samples from one do not.
    samples = [
        _sample("a", "Liaison Strategies"),
        _sample("b", "Liaison Strategies"),
        _sample("c", "Liaison Strategies"),
    ]
    result = _classify(samples)
    assert result.tier is MayoralEvidenceTier.M2_POST_FINAL
    assert result.challenger_win_eligible("bradford") is False


def test_challenger_win_needs_two_final_field_among_its_measurements() -> None:
    # Three samples measuring bradford across two pollsters, but only ONE final-field.
    samples = [
        _sample("a", "Forum Research"),  # final-field
        _sample("b", "Liaison Strategies", ("chow", "bradford")),  # not final-field
        _sample("c", "Mainstreet Research", ("chow", "bradford")),  # not final-field
    ]
    result = _classify(samples)
    assert result.challenger_win_eligible("bradford") is False
