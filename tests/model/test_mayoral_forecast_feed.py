from pathlib import Path
from types import SimpleNamespace

from backend.model.mayoral_evaluation import FullBallotShareDraws
from backend.model.mayoral_forecast_feed import (
    _variant_predictors,
    build_mayoral_forecast_feed,
    forecast_quantities,
)
from backend.model.publication_manifest import load_live_cycle

ROOT = Path(__file__).resolve().parents[2]

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


def _stub(pollsters):
    return SimpleNamespace(
        final_field_sample_ids=("s1", "s2", "s3"),
        final_field_pollsters=tuple(pollsters),
    )


def test_leave_one_pollster_out_is_not_applicable_below_three_pollsters() -> None:
    # ADR 0048: with < 3 pollsters, dropping one leaves too little to refit, so
    # the variant is omitted rather than failing the gate.
    two = {label for label, _ in _variant_predictors(_stub(("Forum", "Liaison")), ROOT)}
    assert not any(label.startswith("leave-out-pollster:") for label in two)
    # the rest of the mandatory suite is still present
    assert {
        "bridge-base",
        "comparator-baseline",
        "tail-low",
        "tail-high",
        "incumbency-prior",
    } <= two

    three = {
        label
        for label, _ in _variant_predictors(
            _stub(("Forum", "Liaison", "Mainstreet")), ROOT
        )
    }
    assert sum(label.startswith("leave-out-pollster:") for label in three) == 3


def test_uncertified_forecast_is_unavailable_at_tier_m1() -> None:
    # Before the field is certified the tier is M1 and every predictive quantity is
    # tier-gated Unavailable (no variant suite is run).
    live_cycle = {
        **load_live_cycle(ROOT / "data/raw/elections/live_cycle.json"),
        "field_certified": False,
    }
    feed = build_mayoral_forecast_feed(ROOT, live_cycle)
    assert feed["evidence_tier"] == "M1 — Pre-Final Polling"
    assert feed["close_result"]["availability"] == "Forecast Unavailable"
    assert all(
        card["availability"] == "Forecast Unavailable"
        for card in feed["candidate_win"].values()
    )
