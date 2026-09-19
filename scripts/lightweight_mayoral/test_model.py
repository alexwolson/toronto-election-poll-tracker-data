from datetime import date

from .model import ForecastConfig, Poll, forecast

FIELD = ("chow", "bradford", "alexander")
ASOF = date(2026, 9, 19)
ELECTION = date(2026, 10, 26)


def mk(shares, d=date(2026, 9, 5), n=1000, firm="X"):
    return Poll(firm=firm, date=d, n=n, shares=shares)


def cfg(**kw):
    base = {
        "field": FIELD,
        "election_date": ELECTION,
        "asof": ASOF,
        "n_sims": 60_000,
        "seed": 1,
    }
    base.update(kw)
    return ForecastConfig(**base)


CURRENT = [mk({"chow": 0.50, "bradford": 0.39, "alexander": 0.10, "other": 0.01})]


def test_shares_normalised_and_reproducible():
    r1, r2 = forecast(CURRENT, cfg()), forecast(CURRENT, cfg())
    assert abs(sum(r1["mean_shares"].values()) - 1.0) < 1e-9
    assert abs(sum(r1["win_prob"].values()) - 1.0) < 1e-9
    assert r1["win_prob"] == r2["win_prob"]


def test_other_is_not_a_winner_and_named_probs_sum_to_one():
    r = forecast(CURRENT, cfg())
    assert set(r["win_prob"]) == set(FIELD)
    assert abs(sum(r["win_prob"].values()) - 1.0) < 1e-9


def test_clear_leader_favoured_but_challenger_has_a_real_chance():
    r = forecast(CURRENT, cfg())
    wp = r["win_prob"]
    assert wp["chow"] > wp["bradford"] > wp["alexander"]
    assert 0.70 < wp["chow"] < 0.97
    assert wp["alexander"] < 0.05


def test_consolidation_helps_the_challenger():
    """Turning on the Alexander->Bradford consolidation raises Bradford's chance."""
    off = forecast(CURRENT, cfg(soft_fraction_range=(0.0, 0.0), dropout_prob=0.0))
    on = forecast(CURRENT, cfg())
    assert on["win_prob"]["bradford"] > off["win_prob"]["bradford"]


def test_dropout_probability_raises_the_challenger():
    lo = forecast(CURRENT, cfg(dropout_prob=0.0))
    hi = forecast(CURRENT, cfg(dropout_prob=0.5))
    assert hi["win_prob"]["bradford"] >= lo["win_prob"]["bradford"]


def test_more_symmetric_uncertainty_shrinks_leader_advantage():
    calm = forecast(CURRENT, cfg(polling_error_sd=0.02, drift_sd=0.01))
    wild = forecast(CURRENT, cfg(polling_error_sd=0.08, drift_sd=0.06))
    assert wild["win_prob"]["chow"] < calm["win_prob"]["chow"]


def test_decomposition_is_consistent_and_nonnegative():
    d = forecast(CURRENT, cfg())["decomposition"]
    assert d["target"] == "bradford"
    total = (
        d["baseline_no_uncertainty"]
        + d["from_polling_error"]
        + d["from_campaign_drift"]
        + d["from_alexander_consolidation"]
    )
    assert abs(total - d["total"]) < 1e-9
    # each mechanism adds (weakly) to the challenger's chance here
    assert d["from_polling_error"] >= -0.01
    assert d["from_alexander_consolidation"] >= -0.01


def test_recency_weighting_favours_recent_polls():
    polls = [
        mk(
            {"chow": 0.30, "bradford": 0.55, "alexander": 0.14, "other": 0.01},
            d=date(2026, 6, 1),
        ),
        mk(
            {"chow": 0.52, "bradford": 0.35, "alexander": 0.12, "other": 0.01},
            d=date(2026, 9, 12),
        ),
    ]
    r = forecast(polls, cfg())
    assert r["mean_shares"]["chow"] > r["mean_shares"]["bradford"]
