from dataclasses import replace
from datetime import time, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from backend.model.historical_mayoral import load_historical_mayoral_corpus
from backend.model.historical_mayoral_evaluation import (
    build_historical_mayoral_evaluation_cycles,
)
from backend.model.mayoral_endpoint import (
    MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
    MayoralEndpointDataError,
    MayoralEndpointPredictor,
    _reading_point,
    fit_mayoral_endpoint,
    select_mayoral_endpoint_readings,
)
from backend.model.mayoral_evaluation import HeldOutCycle, TrainingCycle

ROOT = Path(__file__).resolve().parents[2]


def _cycle(cycle_id: str, days_before_election: int):
    corpus = load_historical_mayoral_corpus(ROOT)
    cycles = build_historical_mayoral_evaluation_cycles(
        corpus,
        lead_times=(days_before_election,),
        analysis_time_local=time(12),
    )
    cycle = next(row for row in cycles if row.election_cycle_id == cycle_id)
    return cycle, corpus


def _evaluation_cycles():
    corpus = load_historical_mayoral_corpus(ROOT)
    return build_historical_mayoral_evaluation_cycles(
        corpus,
        lead_times=MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
        analysis_time_local=MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    )


def _fold(target_cycle_id: str, lead_time: int):
    cycles = _evaluation_cycles()
    target_cycle = next(
        cycle for cycle in cycles if cycle.election_cycle_id == target_cycle_id
    )
    target_snapshot = next(
        row for row in target_cycle.snapshots if row.days_before_election == lead_time
    )
    training = tuple(
        TrainingCycle(
            election_cycle_id=cycle.election_cycle_id,
            election_type=cycle.election_type,
            snapshot=next(
                row for row in cycle.snapshots if row.days_before_election == lead_time
            ),
            history=cycle.snapshots,
            outcome=cycle.outcome,
        )
        for cycle in cycles
        if cycle.election_cycle_id != target_cycle_id
    )
    target = HeldOutCycle(
        election_cycle_id=target_cycle.election_cycle_id,
        election_type=target_cycle.election_type,
        snapshot=target_snapshot,
        candidate_ids=target_cycle.outcome.candidate_ids,
        incumbent_candidate_id=target_cycle.outcome.incumbent_candidate_id,
    )
    return training, target


def test_selector_uses_one_post_final_reading_per_respondent_sample() -> None:
    cycle, corpus = _cycle("toronto_2014", 1)
    selected = select_mayoral_endpoint_readings(
        cycle.snapshots[0].evidence,
        final_candidate_ids=cycle.outcome.candidate_ids,
    )

    assert len({row.poll_sample_id for row in selected}) == len(selected)
    assert all(
        next(
            sample
            for sample in corpus.poll_samples
            if sample.poll_sample_id == row.poll_sample_id
        ).fieldwork_end
        >= cycle.snapshots[0].evidence.final_ballot_evidence_available_at.date()
        for row in selected
    )
    assert "forum_2014_sep22_current_field_trend" in {
        row.poll_reading_id for row in selected
    }
    assert "forum_2014_sep12_three_way_doug" not in {
        row.poll_reading_id for row in selected
    }


def test_qualification_grid_is_the_common_poll_backed_grid() -> None:
    assert MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES == (12, 7, 3, 1)
    assert MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL == time(12)


def test_selector_prefers_the_source_published_expressed_preference_product() -> None:
    cycle, _ = _cycle("toronto_2023", 1)
    selected = select_mayoral_endpoint_readings(
        cycle.snapshots[0].evidence,
        final_candidate_ids=cycle.outcome.candidate_ids,
    )
    by_sample = {row.poll_sample_id: row for row in selected}

    forum = by_sample["forum_city_2023_05_26_n1007"]
    assert forum.poll_reading_id == "forum_2023_may26_decided_leaning"
    assert len(forum.candidate_field) == 12
    assert len(forum.candidate_shares) == 7

    ipsos = by_sample["ipsos_city_2023_06_09_13_n1001"]
    assert ipsos.poll_reading_id == "ipsos_2023_total_repercentaged"


def test_selector_ignores_poll_residual_and_normalizes_only_numeric_candidates() -> (
    None
):
    cycle, _ = _cycle("toronto_2018", 1)
    selected = select_mayoral_endpoint_readings(
        cycle.snapshots[0].evidence,
        final_candidate_ids=cycle.outcome.candidate_ids,
    )
    forum = next(
        row
        for row in selected
        if row.poll_reading_id == "forum_2018_oct10_decided_leaning"
    )

    assert set(forum.candidate_shares) == {"tory", "keesmaat"}
    assert sum(forum.candidate_shares.values(), Decimal(0)) == Decimal(1)
    assert forum.candidate_shares["tory"] == Decimal(56) / Decimal(85)
    assert forum.candidate_shares["keesmaat"] == Decimal(29) / Decimal(85)


def test_partial_unknown_head_to_head_is_not_forecast_evidence() -> None:
    cycle, _ = _cycle("toronto_2018", 1)
    selected = select_mayoral_endpoint_readings(
        cycle.snapshots[0].evidence,
        final_candidate_ids=cycle.outcome.candidate_ids,
    )

    assert "dart_2018_head_to_head" not in {row.poll_reading_id for row in selected}


def test_non_general_reading_is_not_forecast_evidence_even_in_isolation() -> None:
    cycle, _ = _cycle("toronto_2023", 1)
    evidence = cycle.snapshots[0].evidence
    sample_id = "liaison_city_2023_06_22_23_n1086"
    sample = next(
        row for row in evidence.poll_samples if row.poll_sample_id == sample_id
    )
    readings = tuple(
        replace(row, reading_purpose="routed_subgroup")
        for row in evidence.poll_readings
        if row.poll_sample_id == sample_id
    )
    reading_ids = {row.poll_reading_id for row in readings}
    isolated = replace(
        evidence,
        poll_samples=(sample,),
        poll_readings=readings,
        poll_responses=tuple(
            row for row in evidence.poll_responses if row.poll_reading_id in reading_ids
        ),
    )

    assert (
        select_mayoral_endpoint_readings(
            isolated,
            final_candidate_ids=cycle.outcome.candidate_ids,
        )
        == ()
    )


def test_no_poll_endpoint_fails_instead_of_inventing_a_uniform_forecast() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    cycles = build_historical_mayoral_evaluation_cycles(
        corpus,
        lead_times=(28,),
        analysis_time_local=time(12),
    )
    target_cycle = next(
        cycle for cycle in cycles if cycle.election_cycle_id == "toronto_2022"
    )
    training = tuple(
        TrainingCycle(
            election_cycle_id=cycle.election_cycle_id,
            election_type=cycle.election_type,
            snapshot=cycle.snapshots[0],
            history=cycle.snapshots,
            outcome=cycle.outcome,
        )
        for cycle in cycles
        if cycle.election_cycle_id != target_cycle.election_cycle_id
    )
    target = HeldOutCycle(
        election_cycle_id=target_cycle.election_cycle_id,
        election_type=target_cycle.election_type,
        snapshot=target_cycle.snapshots[0],
        candidate_ids=target_cycle.outcome.candidate_ids,
        incumbent_candidate_id=target_cycle.outcome.incumbent_candidate_id,
    )

    with pytest.raises(MayoralEndpointDataError, match="no eligible poll evidence"):
        fit_mayoral_endpoint(
            training,
            target,
            variant="firm-balanced-bridge",
        )


def test_bridge_is_firm_balanced_and_distinct_from_the_latest_poll_comparator() -> None:
    training, target = _fold("toronto_2023", 1)
    comparator = fit_mayoral_endpoint(
        training,
        target,
        variant="latest-sample-comparator",
    )
    bridge = fit_mayoral_endpoint(
        training,
        target,
        variant="firm-balanced-bridge",
    )

    assert comparator.candidate_ids == bridge.candidate_ids
    assert comparator.point_shares != bridge.point_shares
    assert comparator.tail_mass_total == bridge.tail_mass_total
    assert sum(bridge.point_shares) == pytest.approx(1.0)


def test_global_uncertainty_fit_does_not_change_with_target_lead_time() -> None:
    early_training, early_target = _fold("toronto_2022", 7)
    late_training, late_target = _fold("toronto_2022", 1)
    early = fit_mayoral_endpoint(
        early_training,
        early_target,
        variant="firm-balanced-bridge",
    )
    late = fit_mayoral_endpoint(
        late_training,
        late_target,
        variant="firm-balanced-bridge",
    )

    assert (
        early_target.snapshot.evidence_revision
        == late_target.snapshot.evidence_revision
    )
    assert early.point_shares == late.point_shares
    assert early.tail_mass_total == late.tail_mass_total
    assert early.concentration == late.concentration

    predictor = MayoralEndpointPredictor("firm-balanced-bridge", draw_count=64)
    assert (
        predictor(
            early_training,
            early_target,
        ).full_ballot_share_draws
        == predictor(
            late_training,
            late_target,
        ).full_ballot_share_draws
    )


def test_ineligible_new_evidence_does_not_change_monte_carlo_draws() -> None:
    early_training, early_target = _fold("toronto_2018", 3)
    late_training, late_target = _fold("toronto_2018", 1)
    assert (
        early_target.snapshot.evidence_revision
        != late_target.snapshot.evidence_revision
    )

    predictor = MayoralEndpointPredictor("firm-balanced-bridge", draw_count=64)
    assert (
        predictor(
            early_training,
            early_target,
        ).full_ballot_share_draws
        == predictor(
            late_training,
            late_target,
        ).full_ballot_share_draws
    )


def test_predictor_returns_deterministic_distinct_full_ballot_draws() -> None:
    training, target = _fold("toronto_2023", 1)
    predictor = MayoralEndpointPredictor("firm-balanced-bridge", draw_count=64)

    first = predictor(training, target).full_ballot_share_draws
    second = predictor(training, target).full_ballot_share_draws

    assert first == second
    assert first.candidate_ids == target.candidate_ids
    assert len(first.draws) == 64
    assert all(sum(draw) == pytest.approx(1.0) for draw in first.draws)
    obscure = [
        index
        for index, candidate_id in enumerate(first.candidate_ids)
        if candidate_id.startswith("toronto_2023:")
    ][:2]
    assert obscure
    assert any(draw[obscure[0]] != draw[obscure[1]] for draw in first.draws)


def test_reported_zero_is_treated_as_rounded_support_not_impossibility() -> None:
    cycle, _ = _cycle("toronto_2023", 1)
    selected = select_mayoral_endpoint_readings(
        cycle.snapshots[0].evidence,
        final_candidate_ids=cycle.outcome.candidate_ids,
    )
    reading = next(
        row
        for row in selected
        if row.poll_reading_id == "liaison_2023_06_22_23_decided"
    )

    assert all(share > 0 for share in reading.candidate_shares.values())


def test_tail_and_poll_exclusion_sensitivity_seams_change_the_fit() -> None:
    training, target = _fold("toronto_2023", 1)
    base = fit_mayoral_endpoint(
        training,
        target,
        variant="firm-balanced-bridge",
    )
    high_tail = fit_mayoral_endpoint(
        training,
        target,
        variant="firm-balanced-bridge",
        tail_mass_multiplier=1.5,
    )
    excluded = fit_mayoral_endpoint(
        training,
        target,
        variant="firm-balanced-bridge",
        excluded_pollsters=frozenset({"Forum Research"}),
    )

    assert high_tail.tail_mass_total == pytest.approx(base.tail_mass_total * 1.5)
    assert high_tail.point_shares != base.point_shares
    assert excluded.effective_poll_sample_ids != base.effective_poll_sample_ids


def test_fit_distinguishes_eligible_history_from_effective_poll_inputs() -> None:
    training, target = _fold("toronto_2023", 1)
    fit = fit_mayoral_endpoint(
        training,
        target,
        variant="firm-balanced-bridge",
    )

    assert len(fit.eligible_poll_sample_ids) == 17
    assert len(fit.effective_poll_sample_ids) == 4
    assert set(fit.effective_poll_sample_ids) < set(fit.eligible_poll_sample_ids)


def test_candidate_order_does_not_change_the_fitted_distribution() -> None:
    training, target = _fold("toronto_2023", 1)
    reversed_target = HeldOutCycle(
        election_cycle_id=target.election_cycle_id,
        election_type=target.election_type,
        snapshot=target.snapshot,
        candidate_ids=tuple(reversed(target.candidate_ids)),
        incumbent_candidate_id=target.incumbent_candidate_id,
    )
    predictor = MayoralEndpointPredictor("firm-balanced-bridge", draw_count=32)
    original = predictor(training, target).full_ballot_share_draws
    permuted = predictor(training, reversed_target).full_ballot_share_draws
    permuted_index = {
        candidate_id: index for index, candidate_id in enumerate(permuted.candidate_ids)
    }

    assert original.candidate_ids == target.candidate_ids
    assert (
        tuple(
            tuple(
                row[permuted_index[candidate_id]]
                for candidate_id in original.candidate_ids
            )
            for row in permuted.draws
        )
        == original.draws
    )


def test_cross_cycle_evidence_fails_closed() -> None:
    training, target = _fold("toronto_2023", 1)
    wrong_evidence = replace(
        target.snapshot.evidence,
        election_cycle_id="toronto_2018",
    )
    wrong_target = replace(
        target,
        snapshot=replace(target.snapshot, evidence=wrong_evidence),
    )

    with pytest.raises(MayoralEndpointDataError, match="does not match"):
        fit_mayoral_endpoint(
            training,
            wrong_target,
            variant="firm-balanced-bridge",
        )


def test_future_poll_in_an_overcomplete_snapshot_fails_closed() -> None:
    training, target = _fold("toronto_2023", 1)
    sample = target.snapshot.evidence.poll_samples[-1]
    future_sample = replace(
        sample,
        evidence_available_at=target.snapshot.analysis_cutoff + timedelta(hours=1),
    )
    samples = target.snapshot.evidence.poll_samples[:-1] + (future_sample,)
    wrong_target = replace(
        target,
        snapshot=replace(
            target.snapshot,
            evidence=replace(target.snapshot.evidence, poll_samples=samples),
        ),
    )

    with pytest.raises(MayoralEndpointDataError, match="unavailable at the cutoff"):
        fit_mayoral_endpoint(
            training,
            wrong_target,
            variant="firm-balanced-bridge",
        )


def test_fitted_tail_is_a_total_mass_not_a_per_candidate_odds() -> None:
    # ADR 0038: the endpoint learns one total Unmeasured Candidate Tail mass per
    # election -- a mass in (0, 1) -- not a per-omitted-candidate odds that grows
    # the tail with the number of omitted names. Realized totals in the
    # reconstructed cycles range from ~2.85% to ~12.4%.
    training, target = _fold("toronto_2023", 1)
    fit = fit_mayoral_endpoint(training, target, variant="firm-balanced-bridge")

    assert 0.02 <= fit.tail_mass_total <= 0.30


def test_total_tail_mass_is_invariant_to_omitted_candidate_count() -> None:
    # ADR 0038: a reading's total omitted mass does not depend on how many
    # Final-Ballot candidates it omits. The current count-scaling model fails this
    # because it allocates a per-candidate odds through a 1 + m*odds normalizer.
    cycle, _ = _cycle("toronto_2018", 1)
    reading = next(
        row
        for row in select_mayoral_endpoint_readings(
            cycle.snapshots[0].evidence,
            final_candidate_ids=cycle.outcome.candidate_ids,
        )
        if row.poll_reading_id == "forum_2018_oct10_decided_leaning"
    )
    measured = tuple(reading.candidate_shares)
    universe_small = measured + ("tail_a",)
    universe_large = measured + ("tail_a", "tail_b", "tail_c", "tail_d")
    tail_mass = 0.1

    point_small = _reading_point(reading, universe_small, tail_mass=tail_mass)
    point_large = _reading_point(reading, universe_large, tail_mass=tail_mass)
    small_tail = sum(
        share
        for cid, share in zip(universe_small, point_small)
        if cid not in reading.candidate_shares
    )
    large_tail = sum(
        share
        for cid, share in zip(universe_large, point_large)
        if cid not in reading.candidate_shares
    )

    assert small_tail == pytest.approx(tail_mass)
    assert large_tail == pytest.approx(tail_mass)
    assert small_tail == pytest.approx(large_tail)
