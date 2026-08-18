from pathlib import Path
from statistics import median

import pytest

from backend.model.historical_mayoral import load_historical_mayoral_corpus
from backend.model.historical_mayoral_evaluation import (
    build_historical_mayoral_evaluation_cycles,
)
from backend.model.mayoral_endpoint import (
    MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
    MayoralEndpointPredictor,
    fit_mayoral_endpoint,
)
from backend.model.mayoral_evaluation import HeldOutCycle, TrainingCycle
from backend.model.mayoral_incumbency import load_mayoral_incumbency_population
from backend.model.mayoral_incumbency_endpoint import (
    IncumbencyInformedPredictor,
    apply_incumbency_prior,
    incumbency_prior_share,
)

ROOT = Path(__file__).resolve().parents[2]


def _cycles():
    return build_historical_mayoral_evaluation_cycles(
        load_historical_mayoral_corpus(ROOT),
        lead_times=MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
        analysis_time_local=MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    )


def _fold(cycle_id: str, lead: int):
    cycles = _cycles()
    target = next(c for c in cycles if c.election_cycle_id == cycle_id)
    training = tuple(
        TrainingCycle(
            election_cycle_id=c.election_cycle_id,
            election_type=c.election_type,
            snapshot=next(s for s in c.snapshots if s.days_before_election == lead),
            history=c.snapshots,
            outcome=c.outcome,
        )
        for c in cycles
        if c.election_cycle_id != cycle_id
    )
    held = HeldOutCycle(
        election_cycle_id=target.election_cycle_id,
        election_type=target.election_type,
        snapshot=next(s for s in target.snapshots if s.days_before_election == lead),
        candidate_ids=target.outcome.candidate_ids,
        incumbent_candidate_id=target.outcome.incumbent_candidate_id,
    )
    return training, held, target


def test_prior_share_excludes_only_the_target_election_trial() -> None:
    # ADR 0013 partial pooling with leave-one-trial-out: the Toronto 2018 trial is
    # excluded from its own prior, but the other Toronto trials stay in the pool.
    pop = load_mayoral_incumbency_population(ROOT)
    expected = float(
        median(
            float(t.incumbent_share)
            for t in pop.v1_trials
            if not (t.city_id == "toronto" and t.election_date.year == 2018)
        )
    )
    got = incumbency_prior_share(pop, exclude_city="toronto", exclude_year=2018)
    assert got == pytest.approx(expected)
    # a Toronto trial from another year is retained in the pool
    assert any(
        t.city_id == "toronto" and t.election_date.year == 2022 for t in pop.v1_trials
    )


def test_open_race_leaves_the_point_estimate_unchanged() -> None:
    training, held, _ = _fold("toronto_2023", 1)  # open race, no incumbent
    fit = fit_mayoral_endpoint(training, held, variant="firm-balanced-bridge")
    pop = load_mayoral_incumbency_population(ROOT)

    point = apply_incumbency_prior(
        fit,
        election_cycle_id=held.election_cycle_id,
        incumbent_candidate_id=held.incumbent_candidate_id,
        population=pop,
        prior_pseudocount=8.0,
    )
    assert point == fit.point_shares


def test_incumbent_share_shrinks_toward_the_prior() -> None:
    training, held, _ = _fold("toronto_2018", 1)  # Tory incumbent
    fit = fit_mayoral_endpoint(training, held, variant="firm-balanced-bridge")
    pop = load_mayoral_incumbency_population(ROOT)
    inc = held.incumbent_candidate_id
    idx = fit.candidate_ids.index(inc)
    p_poll = fit.point_shares[idx]
    p_prior = incumbency_prior_share(pop, exclude_city="toronto", exclude_year=2018)
    assert p_prior < p_poll  # prior is below Tory's polled share on this landslide

    point = apply_incumbency_prior(
        fit,
        election_cycle_id=held.election_cycle_id,
        incumbent_candidate_id=inc,
        population=pop,
        prior_pseudocount=8.0,
    )
    # incumbent share is pulled strictly between the poll and the prior
    assert p_prior < point[idx] < p_poll
    assert sum(point) == pytest.approx(1.0)
    # non-incumbent shares keep their relative proportions
    others = [i for i in range(len(fit.candidate_ids)) if i != idx]
    if len(others) >= 2 and fit.point_shares[others[1]] > 0:
        base_ratio = fit.point_shares[others[0]] / fit.point_shares[others[1]]
        new_ratio = point[others[0]] / point[others[1]]
        assert new_ratio == pytest.approx(base_ratio)


def test_zero_pseudocount_reduces_to_the_baseline() -> None:
    training, held, _ = _fold("toronto_2018", 1)
    fit = fit_mayoral_endpoint(training, held, variant="firm-balanced-bridge")
    pop = load_mayoral_incumbency_population(ROOT)
    point = apply_incumbency_prior(
        fit,
        election_cycle_id=held.election_cycle_id,
        incumbent_candidate_id=held.incumbent_candidate_id,
        population=pop,
        prior_pseudocount=0.0,
    )
    assert point == pytest.approx(fit.point_shares)


def test_predictor_matches_baseline_on_an_open_race() -> None:
    training, held, _ = _fold("toronto_2023", 1)
    pop = load_mayoral_incumbency_population(ROOT)
    incumbency = IncumbencyInformedPredictor(population=pop, draw_count=64)
    baseline = MayoralEndpointPredictor("firm-balanced-bridge", draw_count=64)

    assert (
        incumbency(training, held).full_ballot_share_draws
        == baseline(training, held).full_ballot_share_draws
    )
