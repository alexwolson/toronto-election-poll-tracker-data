from backend.model.mayoral_evaluation import FullBallotShareDraws
from backend.model.mayoral_forecast_feed import forecast_quantities

CANDS = ("chow", "bradford", "alexander")
DRAWS = FullBallotShareDraws(
    candidate_ids=CANDS,
    draws=(
        (0.50, 0.30, 0.20),  # chow wins, margin 0.20 (not close)
        (0.45, 0.40, 0.15),  # chow wins, margin 0.05 (close)
        (0.40, 0.45, 0.15),  # bradford wins, margin 0.05 (close)
        (0.50, 0.25, 0.25),  # chow wins, margin 0.25 (not close)
    ),
)


def test_candidate_win_probabilities_are_draw_fractions_summing_to_one() -> None:
    q = forecast_quantities(DRAWS, incumbent_candidate_id="chow")
    assert q.candidate_win["chow"].probability == 0.75
    assert q.candidate_win["bradford"].probability == 0.25
    assert q.candidate_win["alexander"].probability == 0.0
    total = sum(e.probability for e in q.candidate_win.values())
    assert abs(total - 1.0) < 1e-9


def test_close_result_probability_counts_within_threshold_margins() -> None:
    q = forecast_quantities(DRAWS, incumbent_candidate_id="chow")
    assert q.close_result.probability == 0.5  # two of four draws within 0.05


def test_incumbent_defeat_is_one_minus_incumbent_win() -> None:
    q = forecast_quantities(DRAWS, incumbent_candidate_id="chow")
    assert q.incumbent_defeat.probability == 0.25
    assert (
        forecast_quantities(DRAWS, incumbent_candidate_id=None).incumbent_defeat is None
    )


def test_error_intervals_contain_the_estimate_and_stay_in_unit_interval() -> None:
    q = forecast_quantities(DRAWS, incumbent_candidate_id="chow")
    for e in [*q.candidate_win.values(), q.close_result, q.incumbent_defeat]:
        assert 0.0 <= e.interval_lower <= e.probability <= e.interval_upper <= 1.0


def test_a_tied_top_share_splits_the_winner_weight() -> None:
    tied = FullBallotShareDraws(
        candidate_ids=("a", "b"), draws=((0.5, 0.5), (0.5, 0.5))
    )
    q = forecast_quantities(tied, incumbent_candidate_id=None)
    assert q.candidate_win["a"].probability == 0.5
    assert q.candidate_win["b"].probability == 0.5
