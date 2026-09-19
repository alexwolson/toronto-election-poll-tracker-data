"""Lightweight Toronto mayoral forecast: a recency/precision-weighted poll average
with uncertainty decomposed into three explicit, separately-calibrated mechanisms:

  1. polling error   — the polls are wrong about the race *now* (symmetric).
  2. campaign drift   — genuine opinion movement between now and election day (symmetric).
  3. Alexander consolidation — his soft third-place vote partly migrates (directional:
     mostly to the challenger, some to the incumbent, some stays home). Evidence-calibrated
     and deliberately hedged (see docs/lightweight-mayoral-forecast-methodology.md).

Pure NumPy; a full run is milliseconds. The forecast also returns a decomposition of the
challenger's win probability across the three mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np


@dataclass(frozen=True)
class Poll:
    firm: str
    date: date
    n: float | None
    shares: dict[str, float]  # candidate_id/"other" -> share (as reported)


@dataclass(frozen=True)
class ForecastConfig:
    field: tuple[
        str, ...
    ]  # viable named candidates; field[0] is the leader/incumbent frame
    election_date: date
    asof: date
    half_life_days: float = 21.0
    house_dispersion_floor: float = 0.010
    # Component 1 + 2: symmetric per-candidate share SDs (calibrated to historical
    # terminal poll error and residual drift; see methodology doc).
    polling_error_sd: float = 0.045
    drift_sd: float = 0.035
    # Component 3: Alexander consolidation (directional). His soft vote fraction is drawn
    # uniformly across [soft_lo, soft_hi]; a small dropout/endorsement chance forces it high.
    consolidation_candidate: str = "alexander"
    consolidation_target: str = "bradford"  # gets split_to_target of the moved vote
    consolidation_incumbent: str = "chow"  # gets split_to_incumbent
    soft_fraction_range: tuple[float, float] = (0.30, 0.70)
    split_to_target: float = 0.55  # rest (1 - target - incumbent) stays home
    split_to_incumbent: float = 0.20
    dropout_prob: float = 0.05
    n_sims: int = 200_000
    seed: int = 20260919


def _prep_polls(polls, cfg):
    kept = []
    for p in polls:
        if not all(c in p.shares and p.shares[c] not in (None, "") for c in cfg.field):
            continue
        named = {c: float(p.shares[c]) for c in cfg.field}
        other = max(1e-6, 1.0 - sum(named.values()))
        total = sum(named.values()) + other
        vec = np.array([named[c] for c in cfg.field] + [other]) / total
        kept.append((p, vec))
    if not kept:
        raise ValueError("No polls cover the full viable field")
    return kept


def _weights(kept, cfg):
    w = []
    for p, _ in kept:
        days_old = (cfg.asof - p.date).days
        recency = 0.5 ** (max(0, days_old) / cfg.half_life_days)
        w.append(recency * (p.n or 600.0))
    return np.array(w) / np.sum(w)


def _simulate(mean, labels, cfg, *, polling, drift, consolidation, seed):
    """Monte-Carlo election-day shares. Booleans toggle each mechanism (for decomposition).
    Returns (win_prob dict over named, winner_gap samples, sims array)."""
    rng = np.random.default_rng(seed)
    nnamed = len(cfg.field)
    n = cfg.n_sims
    centre = np.tile(mean, (n, 1)).astype(float)  # (n, ncat)

    if consolidation and cfg.consolidation_candidate in labels:
        ai = labels.index(cfg.consolidation_candidate)
        ti = labels.index(cfg.consolidation_target)
        ci = labels.index(cfg.consolidation_incumbent)
        lo, hi = cfg.soft_fraction_range
        soft = rng.uniform(lo, hi, size=n)
        soft = np.where(
            rng.random(n) < cfg.dropout_prob, hi, soft
        )  # dropout -> top of range
        moved = soft * centre[:, ai]
        stay_home = moved * (1.0 - cfg.split_to_target - cfg.split_to_incumbent)
        centre[:, ai] -= moved
        centre[:, ti] += moved * cfg.split_to_target
        centre[:, ci] += moved * cfg.split_to_incumbent
        centre /= (1.0 - stay_home)[
            :, None
        ]  # those who stay home leave the voting electorate

    var = (cfg.polling_error_sd**2 if polling else 0.0) + (
        cfg.drift_sd**2 if drift else 0.0
    )
    sd = np.sqrt(var)
    if sd > 0:
        log_sd = sd / np.maximum(mean, 0.08)  # per-candidate share-SD -> log-space
        draws = np.log(centre) + rng.normal(0.0, 1.0, size=(n, len(labels))) * log_sd
    else:
        draws = np.log(centre)
    draws -= draws.max(axis=1, keepdims=True)
    ev = np.exp(draws)
    sims = ev / ev.sum(axis=1, keepdims=True)

    winners = sims[:, :nnamed].argmax(axis=1)
    win_prob = {cfg.field[i]: float((winners == i).mean()) for i in range(nnamed)}
    ordered = np.sort(sims[:, :nnamed], axis=1)
    winner_gap = ordered[:, -1] - ordered[:, -2]
    return win_prob, winner_gap, sims


def forecast(polls, cfg: ForecastConfig):
    kept = _prep_polls(polls, cfg)
    labels = list(cfg.field) + ["other"]
    P = np.vstack([vec for _, vec in kept])
    w = _weights(kept, cfg)
    mean = w @ P
    # house/sampling floor folded into polling_error via the config; keep a diagnostic
    house_sd = float(np.sqrt(w @ (P - mean) ** 2).max())

    win_prob, winner_gap, sims = _simulate(
        mean, labels, cfg, polling=True, drift=True, consolidation=True, seed=cfg.seed
    )

    # Decomposition of the challenger's win probability (common random seed per stage).
    tgt = cfg.consolidation_target

    def wp(**kw):
        return _simulate(mean, labels, cfg, seed=cfg.seed, **kw)[0][tgt]

    b_none = wp(polling=False, drift=False, consolidation=False)
    b_poll = wp(polling=True, drift=False, consolidation=False)
    b_pd = wp(polling=True, drift=True, consolidation=False)
    b_all = win_prob[tgt]
    decomposition = {
        "target": tgt,
        "baseline_no_uncertainty": b_none,
        "from_polling_error": b_poll - b_none,
        "from_campaign_drift": b_pd - b_poll,
        "from_alexander_consolidation": b_all - b_pd,
        "total": b_all,
    }

    days_to = max(0, (cfg.election_date - cfg.asof).days)
    q = lambda c, p: float(np.quantile(sims[:, labels.index(c)], p))
    bands = {
        c: {
            "p05": q(c, 0.05),
            "p50": q(c, 0.50),
            "mean": float(mean[labels.index(c)]),
            "p95": q(c, 0.95),
        }
        for c in labels
    }
    ci, bi = 0, 1
    margin = sims[:, ci] - sims[:, bi]
    return {
        "labels": labels,
        "mean_shares": {c: float(mean[i]) for i, c in enumerate(labels)},
        "house_sd": house_sd,
        "win_prob": win_prob,
        "bands": bands,
        "decomposition": decomposition,
        "margin_chow_bradford": {
            "p05": float(np.quantile(margin, 0.05)),
            "p50": float(np.quantile(margin, 0.5)),
            "p95": float(np.quantile(margin, 0.95)),
            "p_positive": float((margin > 0).mean()),
        },
        "winner_gap_samples": winner_gap,
        "close_prob": float((winner_gap < 0.05).mean()),
        "n_polls_used": len(kept),
        "days_to_election": days_to,
    }
