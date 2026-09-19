"""Build data/processed/mayoral_forecast.json from the lightweight poll-average model.

Emits schema v3 ("central-band-with-sensitivity-v1"): a central estimate (bridge-base,
calibrated to historical Toronto margin error ~5 weeks out) plus stable/volatile stress
variants, published as the finest ADR-0006 band on which all variants agree, with the
per-variant sensitivity range. See AUTONOMOUS-RUN-2026-09-18.md for the decision record.
"""

import csv
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from lightweight_mayoral.model import ForecastConfig, Poll, forecast

REPO = Path(__file__).resolve().parent.parent
POLLS = REPO / "data" / "raw" / "polls" / "polls.csv"
LIVE = REPO / "data" / "raw" / "elections" / "live_cycle.json"
OUT = REPO / "data" / "processed" / "mayoral_forecast.json"

TIER = "Lightweight poll-average — central band with assumption sensitivity"
# ADR-0006 band grids (verbatim from backend/model/publication.py), finest first.
GRID10 = [
    (0.0, 0.05, "0–<5%", "less than 1 in 10"),
    (0.05, 0.15, "5–<15%", "about 1 in 10"),
    (0.15, 0.25, "15–<25%", "about 2 in 10"),
    (0.25, 0.35, "25–<35%", "about 3 in 10"),
    (0.35, 0.45, "35–<45%", "about 4 in 10"),
    (0.45, 0.55, "45–<55%", "about 5 in 10"),
    (0.55, 0.65, "55–<65%", "about 6 in 10"),
    (0.65, 0.75, "65–<75%", "about 7 in 10"),
    (0.75, 0.85, "75–<85%", "about 8 in 10"),
    (0.85, 0.95, "85–<95%", "about 9 in 10"),
    (0.95, 1.01, "95–100%", "more than 9 in 10"),
]
GRID5 = [
    (0.0, 0.10, "0–<10%", "less than 1 in 5"),
    (0.10, 0.30, "10–<30%", "about 1 in 5"),
    (0.30, 0.50, "30–<50%", "about 2 in 5"),
    (0.50, 0.70, "50–<70%", "about 3 in 5"),
    (0.70, 0.90, "70–<90%", "about 4 in 5"),
    (0.90, 1.01, "90–100%", "more than 4 in 5"),
]

# Sensitivity variants over the three-component uncertainty model; "bridge-base" is the
# authoritative central calibration (evidence-based, see the methodology doc).
VARIANTS = {
    "bridge-base": {},  # model defaults
    "stable": {  # polls closer to gospel; Alexander's vote mostly firm (2/3 certain, Sept crosstab)
        "polling_error_sd": 0.035,
        "drift_sd": 0.020,
        "soft_fraction_range": (0.15, 0.35),
        "split_to_target": 0.45,
        "dropout_prob": 0.02,
    },
    "volatile": {  # noisier polls, movement, strategic anti-Chow consolidation beyond self-report
        "polling_error_sd": 0.055,
        "drift_sd": 0.050,
        "soft_fraction_range": (0.35, 0.70),
        "split_to_target": 0.65,
        "dropout_prob": 0.10,
    },
}
LABELS = list(VARIANTS)


def _band_idx(p, grid):
    for i, (lo, hi, _, _) in enumerate(grid):
        if lo <= p < hi:
            return i
    return len(grid) - 1


def finest_stable_band(probs):
    """Finest grid on which every variant lands in the same band (ADR-0006 rule)."""
    for grid in (GRID10, GRID5):
        idxs = {_band_idx(p, grid) for p in probs}
        if len(idxs) == 1:
            _, _, label, freq = grid[idxs.pop()]
            return label, freq
    # variants disagree even at the coarse grid: publish the coarse band of the central
    _, _, label, freq = GRID5[_band_idx(probs[0], GRID5)]
    return label, freq


def load_polls():
    field = json.loads(LIVE.read_text())["viable_field"]
    polls, ids_by_key = [], {}
    for r in csv.DictReader(POLLS.open()):
        shares = {
            c: float(r[c])
            for c in list(field) + ["other"]
            if r.get(c) not in ("", None)
        }
        p = Poll(
            firm=r["firm"],
            date=date.fromisoformat(r["date_conducted"]),
            n=float(r["sample_size"]) if r["sample_size"] else None,
            shares=shares,
        )
        polls.append(p)
        ids_by_key[id(p)] = r["poll_id"]
    return field, polls, ids_by_key


def card(quantity, candidate_id, central_p, variant_ps):
    scenarios = [
        {
            "label": lab,
            "role": "authoritative" if lab == "bridge-base" else "stress_test",
            "probability": round(float(variant_ps[lab]), 6),
        }
        for lab in LABELS
    ]
    lower = round(min(s["probability"] for s in scenarios), 6)
    upper = round(max(s["probability"] for s in scenarios), 6)
    label, freq = finest_stable_band([variant_ps[lab] for lab in LABELS])
    # bridge-base scenario probability must equal the card probability (validator)
    central = round(float(central_p), 6)
    for s in scenarios:
        if s["label"] == "bridge-base":
            s["probability"] = central
    lower, upper = min(lower, central), max(upper, central)
    return {
        "quantity": quantity,
        "candidate_id": candidate_id,
        "tier": TIER,
        "availability": "Forecast Available",
        "band": label,
        "frequency_statement": freq,
        "probability": central,
        "reason": "Poll-average central estimate; band is the finest ADR-0006 level on which "
        "the stable/central/volatile assumption variants agree.",
        "sensitivity": {
            "kind": "model_assumptions",
            "lower": lower,
            "upper": upper,
            "includes_monte_carlo_error": True,
            "scenarios": scenarios,
        },
    }


def margin_distribution(samples):
    """Reflected (at 0) Gaussian KDE of the winner-minus-runner-up gap, numpy-only."""
    s = np.asarray(samples)
    if s.size > 20000:
        s = np.random.default_rng(0).choice(s, 20000, replace=False)
    data = np.concatenate([s, -s])  # reflect at 0 so the gap density has support >= 0
    iqr = np.subtract(*np.percentile(data, [75, 25]))
    bw = max(0.9 * min(data.std(), iqr / 1.34) * data.size ** (-0.2), 1e-3)
    x = np.linspace(0.0, min(0.6, float(s.max()) * 1.1 + 0.05), 120)
    z = (x[:, None] - data[None, :]) / bw
    dens = 2.0 * np.exp(-0.5 * z**2).sum(axis=1) / (data.size * bw * np.sqrt(2 * np.pi))
    return {
        "unit": "share_gap",
        "x": [round(float(v), 6) for v in x],
        "density": [round(float(d), 6) for d in dens],
        "close_threshold": 0.05,
    }


def main():
    field, polls, ids_by_key = load_polls()
    incumbent = json.loads(LIVE.read_text())["incumbent_candidate_id"]
    asof = datetime.now(tz=timezone(timedelta(hours=-4))).date()
    base = {"field": tuple(field), "election_date": date(2026, 10, 26), "asof": asof}

    results = {}
    for lab, params in VARIANTS.items():
        results[lab] = forecast(polls, ForecastConfig(**base, **params))
    central = results["bridge-base"]

    # which polls covered the full field (what the model actually used)
    covered = [ids_by_key[id(p)] for p in polls if all(c in p.shares for c in field)]

    candidate_win = {}
    for c in field:
        variant_ps = {lab: results[lab]["win_prob"][c] for lab in LABELS}
        candidate_win[c] = card("challenger_win", c, central["win_prob"][c], variant_ps)

    close = card(
        "close_result",
        None,
        central["close_prob"],
        {lab: results[lab]["close_prob"] for lab in LABELS},
    )
    defeat = card(
        "incumbent_defeat",
        None,
        1 - central["win_prob"][incumbent],
        {lab: 1 - results[lab]["win_prob"][incumbent] for lab in LABELS},
    )

    favourite = max(field, key=lambda c: central["win_prob"][c])
    feed = {
        "schema_version": 3,
        "publication_policy": "central-band-with-sensitivity-v1",
        "analysis_cutoff": datetime.now(timezone(timedelta(hours=-4))).isoformat(
            timespec="seconds"
        ),
        "sensitivity_variant_labels": LABELS,
        "election_cycle_id": "toronto_2026",
        "evidence_tier": TIER,
        "final_field_samples": covered,
        "incumbent_candidate_id": incumbent,
        "forecast_favourite": {
            "tier": TIER,
            "availability": "Forecast Available",
            "candidate_id": favourite,
            "reason": "Highest poll-average win probability across the viable field.",
        },
        "candidate_win": candidate_win,
        "close_result": close,
        "incumbent_defeat": defeat,
        "margin_distribution": margin_distribution(central["winner_gap_samples"]),
        # Non-schema extra: how the challenger's chance splits across mechanisms (for the
        # "why does Bradford have a chance" explainer). Ignored by validateForecast.
        "challenger_chance_decomposition": {
            k: round(float(v), 6) if isinstance(v, float) else v
            for k, v in central["decomposition"].items()
        },
    }
    OUT.write_text(json.dumps(feed) + "\n")
    print(f"wrote {OUT}")
    print(
        f"  favourite={favourite}  polls_used={len(covered)}  cutoff={feed['analysis_cutoff']}"
    )
    for c in field:
        cd = candidate_win[c]
        print(
            f"  {c:10s} p={cd['probability']:.3f} band='{cd['band']}' "
            f"range=[{cd['sensitivity']['lower']:.3f},{cd['sensitivity']['upper']:.3f}]"
        )
    print(
        f"  close_result p={close['probability']:.3f}  incumbent_defeat p={defeat['probability']:.3f}"
    )


if __name__ == "__main__":
    main()
