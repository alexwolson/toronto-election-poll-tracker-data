import math
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone

import pytest

from backend.model.mayoral_evaluation import (
    CLOSE_RESULT,
    INCUMBENT_DEFEAT,
    INCUMBENT_MARGIN,
    MEAN_CANDIDATE_SHARE_CRPS,
    MAYORAL_MODEL_FAMILY_LOG_GUARD,
    MAYORAL_MODEL_FAMILY_PRIMARY,
    WINNER_LOG_SCORE,
    WINNING_MARGIN,
    ElectionCycle,
    ElectionOutcome,
    EvaluationPrediction,
    FullBallotShareDraws,
    LeadTimeSnapshot,
    binary_brier_metric,
    binary_log_loss_metric,
    candidate_share_quantity,
    compare_against_baseline,
    empirical_crps,
    evaluate_mayoral_model,
    evaluate_with_regular_election_sensitivity,
    qualify_model_ladder,
    scalar_crps_metric,
    score_prediction,
)


@dataclass(frozen=True)
class _Evidence:
    key: str


def _analysis_cutoff(days_before_election: int) -> datetime:
    election_day = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
    return election_day - timedelta(days=days_before_election)


def _outcome(
    *,
    incumbent_wins: bool,
    close_threshold: float = 0.05,
) -> ElectionOutcome:
    return ElectionOutcome(
        candidate_shares=(
            {"incumbent": 0.6, "challenger": 0.4}
            if incumbent_wins
            else {"incumbent": 0.4, "challenger": 0.6}
        ),
        incumbent_candidate_id="incumbent",
        close_threshold=close_threshold,
    )


def _cycle(
    election_cycle_id: str,
    *,
    incumbent_wins: bool = True,
    election_type: str = "general",
    lead_times: tuple[int, ...] = (30, 7),
    close_threshold: float = 0.05,
) -> ElectionCycle:
    return ElectionCycle(
        election_cycle_id=election_cycle_id,
        election_type=election_type,
        snapshots=tuple(
            LeadTimeSnapshot(
                days_before_election=days,
                analysis_cutoff=_analysis_cutoff(days),
                evidence_revision=f"{election_cycle_id}:{days}:v1",
                evidence=_Evidence(election_cycle_id),
            )
            for days in lead_times
        ),
        outcome=_outcome(
            incumbent_wins=incumbent_wins,
            close_threshold=close_threshold,
        ),
    )


def _defeat_prediction(probability: float) -> EvaluationPrediction:
    losses = round(probability * 100)
    assert probability == pytest.approx(losses / 100)
    draws = (
        ((0.4, 0.6),) * losses
        + ((0.6, 0.4),) * (100 - losses)
    )
    return EvaluationPrediction(
        full_ballot_share_draws=FullBallotShareDraws(
            candidate_ids=("incumbent", "challenger"),
            draws=draws,
        )
    )


def test_scores_derive_from_one_full_ballot_artifact() -> None:
    outcome = _outcome(incumbent_wins=True)
    prediction = EvaluationPrediction(
        full_ballot_share_draws=FullBallotShareDraws(
            candidate_ids=("incumbent", "challenger"),
            draws=(
                (0.65, 0.35),
                (0.51, 0.49),
                (0.45, 0.55),
                (0.49, 0.51),
            ),
        )
    )

    scores = score_prediction(outcome, prediction)

    assert scores[WINNER_LOG_SCORE] == pytest.approx(-math.log(0.5))
    assert scores[binary_brier_metric(INCUMBENT_DEFEAT)] == pytest.approx(0.25)
    assert scores[binary_log_loss_metric(INCUMBENT_DEFEAT)] == pytest.approx(
        -math.log(0.5)
    )
    assert scores[binary_brier_metric(CLOSE_RESULT)] == pytest.approx(0.25)
    assert scores[binary_log_loss_metric(CLOSE_RESULT)] == pytest.approx(
        -math.log(0.5)
    )
    assert scores[
        scalar_crps_metric(candidate_share_quantity("incumbent"))
    ] == pytest.approx(0.06125)
    assert scores[
        scalar_crps_metric(candidate_share_quantity("challenger"))
    ] == pytest.approx(0.06125)
    assert scores[MEAN_CANDIDATE_SHARE_CRPS] == pytest.approx(0.06125)
    assert scores[scalar_crps_metric(WINNING_MARGIN)] == pytest.approx(0.0825)
    assert scores[scalar_crps_metric(INCUMBENT_MARGIN)] == pytest.approx(0.1225)


def test_no_independent_probability_can_contradict_the_share_draws() -> None:
    prediction = _defeat_prediction(0.0)

    scores = score_prediction(_outcome(incumbent_wins=True), prediction)

    assert scores[WINNER_LOG_SCORE] == pytest.approx(0.0)
    assert scores[binary_brier_metric(INCUMBENT_DEFEAT)] == pytest.approx(0.0)
    assert scores[binary_log_loss_metric(INCUMBENT_DEFEAT)] == pytest.approx(0.0)
    with pytest.raises(TypeError, match="winner_probabilities"):
        EvaluationPrediction(  # type: ignore[call-arg]
            full_ballot_share_draws=prediction.full_ballot_share_draws,
            winner_probabilities={"challenger": 1.0},
        )


def test_prediction_must_cover_the_exact_final_ballot_candidate_universe() -> None:
    outcome = ElectionOutcome(
        candidate_shares={
            "incumbent": 0.55,
            "challenger": 0.35,
            "other-candidate": 0.10,
        },
        incumbent_candidate_id="incumbent",
    )
    prediction = _defeat_prediction(0.2)

    with pytest.raises(ValueError, match="candidate universe"):
        score_prediction(outcome, prediction)


@pytest.mark.parametrize(
    "draws, message",
    [
        (((0.6, -0.1),), "non-negative"),
        (((0.6, 0.3),), "sum to 1"),
        (((math.nan, 0.0),), "finite"),
    ],
)
def test_each_full_ballot_draw_is_validated(draws, message) -> None:
    with pytest.raises(ValueError, match=message):
        FullBallotShareDraws(
            candidate_ids=("incumbent", "challenger"),
            draws=draws,
        )


def test_an_outcome_derives_winner_and_events_from_complete_shares() -> None:
    outcome = ElectionOutcome(
        candidate_shares={"incumbent": 0.48, "challenger": 0.52},
        incumbent_candidate_id="incumbent",
        close_threshold=0.05,
    )

    assert outcome.candidate_ids == ("incumbent", "challenger")
    assert outcome.winner_id == "challenger"
    assert outcome.incumbent_defeated is True
    assert outcome.winning_margin == pytest.approx(0.04)
    assert outcome.incumbent_margin == pytest.approx(-0.04)
    assert outcome.is_close is True


def test_incumbent_defeat_and_margin_are_undefined_without_an_incumbent() -> None:
    outcome = ElectionOutcome(
        candidate_shares={"winner": 0.55, "runner-up": 0.45},
        incumbent_candidate_id=None,
    )
    prediction = EvaluationPrediction(
        FullBallotShareDraws(
            candidate_ids=("winner", "runner-up"),
            draws=((0.6, 0.4), (0.4, 0.6)),
        )
    )

    scores = score_prediction(outcome, prediction)

    assert binary_brier_metric(INCUMBENT_DEFEAT) not in scores
    assert binary_log_loss_metric(INCUMBENT_DEFEAT) not in scores
    assert scalar_crps_metric(INCUMBENT_MARGIN) not in scores


def test_empirical_crps_is_zero_for_a_point_mass_on_the_result() -> None:
    assert empirical_crps((0.42, 0.42, 0.42), 0.42) == pytest.approx(0.0)


def test_mayoral_model_family_qualification_uses_margin_and_winner_scores() -> None:
    assert MAYORAL_MODEL_FAMILY_PRIMARY == scalar_crps_metric(WINNING_MARGIN)
    assert MAYORAL_MODEL_FAMILY_LOG_GUARD == WINNER_LOG_SCORE


def test_each_fold_holds_out_a_whole_cycle_at_the_same_fixed_lead_time() -> None:
    cycles = tuple(_cycle(year) for year in ("2014", "2018", "2022"))
    calls: list[tuple[str, int, tuple[tuple[str, int], ...]]] = []

    def fit_predict(training, target):
        calls.append(
            (
                target.election_cycle_id,
                target.snapshot.days_before_election,
                tuple(
                    (
                        example.election_cycle_id,
                        example.snapshot.days_before_election,
                    )
                    for example in training
                ),
            )
        )
        assert not hasattr(target, "outcome")
        assert target.candidate_ids == ("incumbent", "challenger")
        return _defeat_prediction(0.2)

    report = evaluate_mayoral_model(
        cycles,
        lead_times=(30, 7),
        fit_predict=fit_predict,
        model_name="endpoint",
    )

    assert len(calls) == 6
    for target_id, lead_time, training in calls:
        assert target_id not in {
            election_cycle_id for election_cycle_id, _ in training
        }
        assert {days for _, days in training} == {lead_time}
    assert [cycle.election_cycle_id for cycle in report.cycles] == [
        "2014",
        "2018",
        "2022",
    ]
    assert all(len(cycle.cutoffs) == 2 for cycle in report.cycles)


def test_each_training_fold_exposes_the_complete_fixed_cutoff_history() -> None:
    cycles = tuple(_cycle(year, lead_times=(30, 10)) for year in ("2014", "2018"))
    observed = []

    def fit_predict(training, target):
        observed.extend(
            (
                target.election_cycle_id,
                example.election_cycle_id,
                example.snapshot.days_before_election,
                tuple(row.days_before_election for row in example.history),
            )
            for example in training
        )
        return _defeat_prediction(0.2)

    evaluate_mayoral_model(
        cycles,
        lead_times=(30, 10),
        fit_predict=fit_predict,
        model_name="history-aware",
    )

    assert observed
    assert all(history == (30, 10) for _, _, _, history in observed)
    assert {target_lead for _, _, target_lead, _ in observed} == {30, 10}


def test_fixed_cutoffs_must_exist_for_every_cycle() -> None:
    cycles = (
        _cycle("2018"),
        _cycle("2022", lead_times=(30,)),
    )

    with pytest.raises(ValueError, match="2022.*7"):
        evaluate_mayoral_model(
            cycles,
            lead_times=(30, 7),
            fit_predict=lambda training, target: _defeat_prediction(0.2),
            model_name="endpoint",
        )


def test_analysis_cutoff_must_be_aware_and_follow_lead_time_order() -> None:
    with pytest.raises(ValueError, match="offset-aware"):
        LeadTimeSnapshot(
            7,
            datetime(2026, 10, 19, 12),
            "naive:7:v1",
            _Evidence("naive"),
        )

    with pytest.raises(ValueError, match="must move forward"):
        ElectionCycle(
            election_cycle_id="bad-order",
            election_type="general",
            snapshots=(
                LeadTimeSnapshot(
                    30,
                    _analysis_cutoff(7),
                    "bad-order:30:v1",
                    _Evidence("bad-order"),
                ),
                LeadTimeSnapshot(
                    7,
                    _analysis_cutoff(30),
                    "bad-order:7:v1",
                    _Evidence("bad-order"),
                ),
            ),
            outcome=_outcome(incumbent_wins=True),
        )


def test_aggregate_scores_average_cutoffs_within_cycles_then_cycles_equally() -> None:
    cycles = (_cycle("2014"), _cycle("2018"))
    probabilities = {
        ("2014", 30): 0.0,
        ("2014", 7): 0.2,
        ("2018", 30): 0.4,
        ("2018", 7): 0.6,
    }

    report = evaluate_mayoral_model(
        cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(
            probabilities[
                (target.election_cycle_id, target.snapshot.days_before_election)
            ]
        ),
        model_name="endpoint",
    )

    metric = binary_brier_metric(INCUMBENT_DEFEAT)
    by_cycle = {
        cycle.election_cycle_id: cycle.metrics[metric]
        for cycle in report.cycles
    }
    assert by_cycle == pytest.approx({"2014": 0.02, "2018": 0.26})
    assert report.metrics[metric] == pytest.approx(0.14)


def test_relative_comparison_counts_elections_not_repeated_cutoffs() -> None:
    cycles = tuple(
        _cycle(election_cycle_id)
        for election_cycle_id in ("a", "b", "c")
    )
    baseline = evaluate_mayoral_model(
        cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(0.4),
        model_name="baseline",
    )
    candidate_probabilities = {"a": 0.0, "b": 0.41, "c": 0.41}
    candidate = evaluate_mayoral_model(
        cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(
            candidate_probabilities[target.election_cycle_id]
        ),
        model_name="candidate",
    )

    decision = compare_against_baseline(
        candidate,
        baseline,
        primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
        log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
    )

    assert decision.aggregate_primary_improved is True
    assert decision.improved_cycles == 1
    assert decision.majority_of_cycles_improved is False
    assert decision.relative_qualifies is False


def test_relative_comparison_rejects_brier_gain_with_worse_log_loss() -> None:
    cycles = tuple(
        _cycle(election_cycle_id, lead_times=(14,))
        for election_cycle_id in ("a", "b", "c", "d", "e")
    )
    baseline = evaluate_mayoral_model(
        cycles,
        lead_times=(14,),
        fit_predict=lambda training, target: _defeat_prediction(0.5),
        model_name="baseline",
    )
    candidate_probabilities = {
        "a": 0.01,
        "b": 0.01,
        "c": 0.01,
        "d": 0.01,
        "e": 0.99,
    }
    candidate = evaluate_mayoral_model(
        cycles,
        lead_times=(14,),
        fit_predict=lambda training, target: _defeat_prediction(
            candidate_probabilities[target.election_cycle_id]
        ),
        model_name="candidate",
    )

    decision = compare_against_baseline(
        candidate,
        baseline,
        primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
        log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
    )

    assert decision.aggregate_primary_improved is True
    assert decision.majority_of_cycles_improved is True
    assert decision.aggregate_log_loss_not_worse is False
    assert decision.relative_qualifies is False


def test_relative_comparison_fails_closed_on_a_non_finite_score() -> None:
    cycles = tuple(
        _cycle(election_cycle_id, lead_times=(14,))
        for election_cycle_id in ("a", "b", "c")
    )
    baseline = evaluate_mayoral_model(
        cycles,
        lead_times=(14,),
        fit_predict=lambda training, target: _defeat_prediction(1.0),
        model_name="certain-but-wrong",
    )
    candidate = evaluate_mayoral_model(
        cycles,
        lead_times=(14,),
        fit_predict=lambda training, target: _defeat_prediction(0.5),
        model_name="candidate",
    )

    decision = compare_against_baseline(
        candidate,
        baseline,
        primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
        log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
    )

    assert math.isinf(decision.baseline_log_loss)
    assert decision.aggregate_primary_improved is True
    assert decision.aggregate_scores_finite is False
    assert decision.aggregate_log_loss_not_worse is False
    assert decision.relative_qualifies is False


def test_ladder_blocks_richer_model_when_endpoint_absolute_checks_fail() -> None:
    cycles = tuple(
        _cycle(election_cycle_id, lead_times=(14,))
        for election_cycle_id in ("a", "b", "c")
    )

    def report(name, probability):
        return evaluate_mayoral_model(
            cycles,
            lead_times=(14,),
            fit_predict=lambda training, target: _defeat_prediction(probability),
            model_name=name,
        )

    naive = report("naive", 0.5)
    endpoint = report("endpoint", 0.4)
    richer = report("dynamic", 0.3)

    not_configured = qualify_model_ladder(
        naive=naive,
        endpoint=endpoint,
        richer=richer,
        primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
        log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
        endpoint_maximum_scores=None,
    )
    failed = qualify_model_ladder(
        naive=naive,
        endpoint=endpoint,
        richer=richer,
        primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
        log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
        endpoint_maximum_scores={
            binary_brier_metric(INCUMBENT_DEFEAT): 0.10,
        },
    )

    assert not_configured.endpoint_reliability.configured is False
    assert not_configured.endpoint_qualifies is False
    assert not_configured.richer_relative.relative_qualifies is True
    assert not_configured.richer_qualifies is False
    assert failed.endpoint_reliability.configured is True
    assert failed.endpoint_reliability.passed is False
    assert failed.endpoint_qualifies is False
    assert failed.richer_qualifies is False


def test_ladder_can_qualify_endpoint_and_richer_after_frozen_checks_pass() -> None:
    cycles = tuple(
        _cycle(election_cycle_id, lead_times=(14,))
        for election_cycle_id in ("a", "b", "c")
    )

    def report(name, probability):
        return evaluate_mayoral_model(
            cycles,
            lead_times=(14,),
            fit_predict=lambda training, target: _defeat_prediction(probability),
            model_name=name,
        )

    decision = qualify_model_ladder(
        naive=report("naive", 0.5),
        endpoint=report("endpoint", 0.4),
        richer=report("dynamic", 0.3),
        primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
        log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
        endpoint_maximum_scores={
            binary_brier_metric(INCUMBENT_DEFEAT): 0.20,
            binary_log_loss_metric(INCUMBENT_DEFEAT): 0.60,
        },
    )

    assert decision.endpoint_relative.relative_qualifies is True
    assert decision.endpoint_reliability.passed is True
    assert decision.endpoint_qualifies is True
    assert decision.richer_reliability.passed is True
    assert decision.richer_qualifies is True


def test_regular_only_sensitivity_refits_without_the_by_election() -> None:
    cycles = (
        _cycle("2018"),
        _cycle("2022"),
        ElectionCycle(
            election_cycle_id="2023-by-election",
            election_type="by_election",
            snapshots=(
                LeadTimeSnapshot(
                    30,
                    _analysis_cutoff(30),
                    "2023-by-election:30:v1",
                    _Evidence("2023-by-election"),
                ),
                LeadTimeSnapshot(
                    7,
                    _analysis_cutoff(7),
                    "2023-by-election:7:v1",
                    _Evidence("2023-by-election"),
                ),
            ),
            outcome=ElectionOutcome(
                candidate_shares={"winner": 0.55, "runner-up": 0.45},
                incumbent_candidate_id=None,
            ),
        ),
    )
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fit_predict(training, target):
        calls.append(
            (
                target.election_cycle_id,
                tuple(item.election_cycle_id for item in training),
            )
        )
        if target.election_cycle_id == "2023-by-election":
            return EvaluationPrediction(
                FullBallotShareDraws(
                    ("winner", "runner-up"),
                    ((0.6, 0.4), (0.4, 0.6)),
                )
            )
        return _defeat_prediction(0.2)

    suite = evaluate_with_regular_election_sensitivity(
        cycles,
        lead_times=(30, 7),
        fit_predict=fit_predict,
        model_name="endpoint",
    )

    assert {cycle.election_cycle_id for cycle in suite.all_elections.cycles} == {
        "2018",
        "2022",
        "2023-by-election",
    }
    assert {
        cycle.election_cycle_id
        for cycle in suite.regular_elections_only.cycles
    } == {
        "2018",
        "2022",
    }
    regular_fit_calls = [
        training
        for target, training in calls
        if target in {"2018", "2022"} and len(training) == 1
    ]
    assert regular_fit_calls == [
        ("2022",),
        ("2022",),
        ("2018",),
        ("2018",),
    ]
    assert all("2023-by-election" not in training for training in regular_fit_calls)


def test_regular_only_population_rejects_a_by_election_cycle() -> None:
    cycles = (
        _cycle("2022"),
        _cycle("2023", election_type="by_election"),
    )

    with pytest.raises(ValueError, match="regular_elections_only"):
        evaluate_mayoral_model(
            cycles,
            lead_times=(30, 7),
            fit_predict=lambda training, target: _defeat_prediction(0.2),
            model_name="endpoint",
            population="regular_elections_only",
        )


def test_comparison_rejects_different_evaluation_populations() -> None:
    cycles = (_cycle("2018"), _cycle("2022"))
    all_elections = evaluate_mayoral_model(
        cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(0.3),
        model_name="all",
        population="all_elections",
    )
    regular_only = evaluate_mayoral_model(
        cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(0.2),
        model_name="regular",
        population="regular_elections_only",
    )

    with pytest.raises(ValueError, match="evaluation manifests"):
        compare_against_baseline(
            regular_only,
            all_elections,
            primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
            log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
        )


def test_comparison_rejects_different_fold_or_outcome_manifests() -> None:
    baseline_cycles = (_cycle("2018"), _cycle("2022"))
    changed_cycles = (
        baseline_cycles[0],
        replace(
            baseline_cycles[1],
            outcome=replace(baseline_cycles[1].outcome, close_threshold=0.10),
        ),
    )
    baseline = evaluate_mayoral_model(
        baseline_cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(0.3),
        model_name="baseline",
    )
    changed = evaluate_mayoral_model(
        changed_cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(0.2),
        model_name="changed",
    )

    with pytest.raises(ValueError, match="evaluation manifests"):
        compare_against_baseline(
            changed,
            baseline,
            primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
            log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
        )


def test_comparison_rejects_a_different_analysis_cutoff_manifest() -> None:
    baseline_cycles = (_cycle("2018"), _cycle("2022"))
    changed_snapshot = replace(
        baseline_cycles[1].snapshots[0],
        analysis_cutoff=(
            baseline_cycles[1].snapshots[0].analysis_cutoff
            + timedelta(minutes=1)
        ),
    )
    changed_cycles = (
        baseline_cycles[0],
        replace(
            baseline_cycles[1],
            snapshots=(changed_snapshot, baseline_cycles[1].snapshots[1]),
        ),
    )
    baseline = evaluate_mayoral_model(
        baseline_cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(0.3),
        model_name="baseline",
    )
    changed = evaluate_mayoral_model(
        changed_cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(0.2),
        model_name="changed",
    )

    with pytest.raises(ValueError, match="evaluation manifests"):
        compare_against_baseline(
            changed,
            baseline,
            primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
            log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
        )


def test_comparison_rejects_a_different_evidence_revision_manifest() -> None:
    baseline_cycles = (_cycle("2018"), _cycle("2022"))
    changed_snapshot = replace(
        baseline_cycles[1].snapshots[0],
        evidence_revision="toronto_2022:30:corrected",
    )
    changed_cycles = (
        baseline_cycles[0],
        replace(
            baseline_cycles[1],
            snapshots=(changed_snapshot, baseline_cycles[1].snapshots[1]),
        ),
    )
    baseline = evaluate_mayoral_model(
        baseline_cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(0.3),
        model_name="baseline",
    )
    changed = evaluate_mayoral_model(
        changed_cycles,
        lead_times=(30, 7),
        fit_predict=lambda training, target: _defeat_prediction(0.2),
        model_name="changed",
    )

    with pytest.raises(ValueError, match="evaluation manifests"):
        compare_against_baseline(
            changed,
            baseline,
            primary_metric=binary_brier_metric(INCUMBENT_DEFEAT),
            log_loss_guard=binary_log_loss_metric(INCUMBENT_DEFEAT),
        )
