from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from backend.model.mayoral_incumbency import (
    load_mayoral_incumbency_population,
    verify_mayoral_incumbency_artifacts,
)


ROOT = Path(__file__).resolve().parents[2]


def test_frozen_v1_population_is_thirteen_wins_in_nineteen_trials() -> None:
    population = load_mayoral_incumbency_population(ROOT)
    summary = population.summary()

    assert len(population.trials) == 20
    assert len(population.v1_trials) == 19
    assert summary.attempts == 19
    assert summary.wins == 13
    assert summary.losses == 6
    assert summary.empirical_win_rate == Decimal(13) / Decimal(19)
    assert {
        trial.city_id for trial in population.v1_trials
    } == {"toronto", "ottawa", "hamilton", "mississauga", "brampton"}


def test_toronto_2000_is_only_a_three_year_term_sensitivity() -> None:
    population = load_mayoral_incumbency_population(ROOT)
    trial = population.toronto_2000_sensitivity_trial
    summary = population.summary(include_toronto_2000=True)

    assert trial.trial_id == "toronto_2000"
    assert trial.term_length_years == 3
    assert trial not in population.v1_trials
    assert summary.attempts == 20
    assert summary.wins == 14
    assert summary.losses == 6


def test_trial_outcomes_are_derived_from_source_votes() -> None:
    population = load_mayoral_incumbency_population(ROOT)
    by_id = {trial.trial_id: trial for trial in population.trials}

    hamilton_2006 = by_id["hamilton_2006"]
    assert not hamilton_2006.incumbent_won
    assert hamilton_2006.incumbent_margin_share == Decimal(-452) / Decimal(125239)

    toronto_2022 = by_id["toronto_2022"]
    assert toronto_2022.incumbent_won
    assert toronto_2022.incumbent_share == Decimal(342158) / Decimal(551890)
    assert toronto_2022.incumbent_margin_share == Decimal(243633) / Decimal(551890)


def test_leave_one_city_out_partitions_hold_out_complete_city_histories() -> None:
    population = load_mayoral_incumbency_population(ROOT)
    folds = population.leave_one_city_out_folds()

    assert len(folds) == 5
    assert sum(len(fold.held_out_trials) for fold in folds) == 19
    for fold in folds:
        assert len(fold.training_trials) + len(fold.held_out_trials) == 19
        assert {trial.city_id for trial in fold.held_out_trials} == {
            fold.held_out_city_id
        }
        assert fold.held_out_city_id not in {
            trial.city_id for trial in fold.training_trials
        }


def test_hamilton_2006_is_admitted_with_an_explicit_secondary_grade() -> None:
    population = load_mayoral_incumbency_population(ROOT)

    assert population.is_v1_ready
    assert population.source_gaps == ()
    assert {
        trial.trial_id for trial in population.corroborated_secondary_trials
    } == {"hamilton_2006"}
    assert all(
        source.sha256 and source.local_path and source.byte_size
        for source in population.source_documents
        if source.verification_status == "verified_artifact"
    )


def test_all_recovered_comparison_artifacts_match_the_tracked_manifest() -> None:
    population = load_mayoral_incumbency_population(ROOT)

    verify_mayoral_incumbency_artifacts(population, ROOT)
