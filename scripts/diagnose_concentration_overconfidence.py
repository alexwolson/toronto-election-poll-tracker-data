#!/usr/bin/env python3
"""Diagnose whether the endpoint's fitted Dirichlet concentration is over-confident.

The endpoint fits one global concentration ``kappa = (1 - sum p^2) / MSE - 1`` by
method of moments, matching the Dirichlet's total variance to the training cycles'
average candidate-share squared error. This script asks three questions on the
current (post-ADR-0038) endpoint:

  Part 1  Calibration: across every fold, does the realized winning margin fall
          inside the predictive interval at the nominal rate?
  Part 2  Leverage: how much does each training cycle move the fitted kappa, and
          which cycle's realized error dominates it?
  Part 3  Is the one miscalibrated fold (2023) fixable by a stabler kappa, or is
          the point estimate itself the binding constraint?

Read-only; no model change and no publication side effects.
Run from the data project root:  uv run scripts/diagnose_concentration_overconfidence.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.historical_mayoral import load_historical_mayoral_corpus
from backend.model.historical_mayoral_evaluation import (
    build_historical_mayoral_evaluation_cycles,
)
from backend.model.mayoral_endpoint import (
    MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
    _filter_selected,
    _fit_concentration,
    _fit_tail_mass,
    _point_estimate,
    _selected_for_cycle,
    fit_mayoral_endpoint,
)
from backend.model.mayoral_evaluation import HeldOutCycle, TrainingCycle

VARIANT = "firm-balanced-bridge"
DRAWS = 8000


def _training_at(cycles, lead, exclude=None):
    return tuple(
        TrainingCycle(
            election_cycle_id=c.election_cycle_id,
            election_type=c.election_type,
            snapshot=next(s for s in c.snapshots if s.days_before_election == lead),
            history=c.snapshots,
            outcome=c.outcome,
        )
        for c in cycles
        if c.election_cycle_id != exclude
    )


def _held(target, lead):
    return HeldOutCycle(
        election_cycle_id=target.election_cycle_id,
        election_type=target.election_type,
        snapshot=next(s for s in target.snapshots if s.days_before_election == lead),
        candidate_ids=target.outcome.candidate_ids,
        incumbent_candidate_id=target.outcome.incumbent_candidate_id,
    )


def _fit_selection(cycle):
    snap = min(cycle.history, key=lambda s: s.days_before_election)
    return _filter_selected(
        _selected_for_cycle(
            snap.evidence,
            cycle.outcome.candidate_ids,
            expected_election_cycle_id=cycle.election_cycle_id,
            analysis_cutoff=snap.analysis_cutoff,
        ),
        excluded_poll_sample_ids=frozenset(),
        excluded_pollsters=frozenset(),
    )


def _margin_draws(candidate_ids, point, concentration):
    canonical = tuple(sorted(zip(candidate_ids, point, strict=True)))
    seed_material = json.dumps(
        {"candidate_point": canonical, "concentration": concentration},
        separators=(",", ":"),
    ).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    pt = np.asarray(tuple(s for _, s in canonical), dtype=float)
    draws = rng.dirichlet(np.maximum(pt * concentration, 1e-12), size=DRAWS)
    top_two = np.sort(draws, axis=1)[:, -2:]
    return top_two[:, 1] - top_two[:, 0]


def _cycle_squared_error(cycle, tail_mass):
    selected = _fit_selection(cycle)
    point = _point_estimate(
        selected, cycle.outcome.candidate_ids, tail_mass=tail_mass, variant=VARIANT
    )
    observed = tuple(
        cycle.outcome.candidate_shares[c] for c in cycle.outcome.candidate_ids
    )
    return sum((a - p) ** 2 for a, p in zip(observed, point, strict=True))


def main() -> None:
    lead_times = MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES
    corpus = load_historical_mayoral_corpus(ROOT)
    cycles = build_historical_mayoral_evaluation_cycles(
        corpus,
        lead_times=lead_times,
        analysis_time_local=MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    )

    print("=== PART 1: winning-margin calibration (current endpoint) ===")
    print(
        f"{'cycle':<14}{'lead':>5}{'realized':>10}{'p05':>8}{'p50':>8}{'p95':>8}"
        f"{'PIT':>7}{'in80%':>7}{'kappa':>8}"
    )
    caught = 0
    total = 0
    per_cycle_pit: dict[str, list[float]] = {}
    for target in cycles:
        for lead in lead_times:
            fit = fit_mayoral_endpoint(
                _training_at(cycles, lead, exclude=target.election_cycle_id),
                _held(target, lead),
                variant=VARIANT,
            )
            margins = _margin_draws(
                fit.candidate_ids, fit.point_shares, fit.concentration
            )
            realized = target.outcome.winning_margin
            p05, p10, p50, p90, p95 = (
                float(np.quantile(margins, q)) for q in (0.05, 0.10, 0.50, 0.90, 0.95)
            )
            pit = float((margins <= realized).mean())
            hit80 = p10 <= realized <= p90
            caught += hit80
            total += 1
            per_cycle_pit.setdefault(target.election_cycle_id, []).append(pit)
            print(
                f"{target.election_cycle_id:<14}{lead:>5}{realized:>10.4f}"
                f"{p05:>8.4f}{p50:>8.4f}{p95:>8.4f}{pit:>7.2f}"
                f"{('Y' if hit80 else 'MISS'):>7}{fit.concentration:>8.1f}"
            )
    print(
        f"\ncentral-80% interval caught the realized margin in {caught}/{total} folds "
        f"(nominal ~80%); honest unit is 4 cycles."
    )
    print(
        "per-cycle mean PIT:",
        {k: round(sum(v) / len(v), 2) for k, v in per_cycle_pit.items()},
        "  (near 0 = realized far below predicted margin = over-confident)",
    )

    print("\n=== PART 2: concentration leverage (fit at lead=1) ===")
    all_training = _training_at(cycles, lead=1)
    tail = _fit_tail_mass(
        all_training, {c.election_cycle_id: _fit_selection(c) for c in all_training}
    )
    kappa_all = _fit_concentration(
        all_training,
        tail_mass=tail,
        variant=VARIANT,
        excluded_poll_sample_ids=frozenset(),
        excluded_pollsters=frozenset(),
    )
    print(f"tail_mass={tail:.4f}   kappa(all 4 cycles)={kappa_all:.1f}")
    for drop in all_training:
        subset = tuple(
            t for t in all_training if t.election_cycle_id != drop.election_cycle_id
        )
        k = _fit_concentration(
            subset,
            tail_mass=tail,
            variant=VARIANT,
            excluded_poll_sample_ids=frozenset(),
            excluded_pollsters=frozenset(),
        )
        sq = _cycle_squared_error(drop, tail)
        print(
            f"  drop {drop.election_cycle_id:<14} -> kappa={k:>6.1f}   "
            f"(that cycle's share sq-error={sq:.5f})"
        )

    print("\n=== PART 3: is the 2023 miss fixable by a stabler kappa? ===")
    target = next(c for c in cycles if c.election_cycle_id == "toronto_2023")
    fit = fit_mayoral_endpoint(
        _training_at(cycles, lead=1, exclude="toronto_2023"),
        _held(target, 1),
        variant=VARIANT,
    )
    realized = target.outcome.winning_margin
    top = sorted(
        zip(fit.candidate_ids, fit.point_shares), key=lambda kv: kv[1], reverse=True
    )[:3]
    print(
        f"2023 point top-3: {[(k, round(v, 4)) for k, v in top]}   realized margin={realized:.4f}"
    )
    print(f"{'kappa':>8}{'p05':>9}{'p50':>9}{'p95':>9}{'PIT':>7}{'90% CI':>9}")
    for kappa in (fit.concentration, kappa_all, 28.0, 15.0, 8.0):
        margins = _margin_draws(fit.candidate_ids, fit.point_shares, kappa)
        p05, p50, p95 = (float(np.quantile(margins, q)) for q in (0.05, 0.5, 0.95))
        pit = float((margins <= realized).mean())
        verdict = "caught" if p05 <= realized <= p95 else "missed"
        print(f"{kappa:>8.1f}{p05:>9.4f}{p50:>9.4f}{p95:>9.4f}{pit:>7.2f}{verdict:>9}")

    print("\n=== PART 4: production concentration (all four cycles in training) ===")
    print(
        f"a 2026 target trains on every historical cycle, so it uses kappa={kappa_all:.1f}, "
        "not the leave-one-out value. Coverage of each historical margin at that kappa:"
    )
    print(
        f"{'cycle':<14}{'realized':>10}{'p05':>8}{'p50':>8}{'p95':>8}{'PIT':>7}{'in80%':>7}"
    )
    for cycle in all_training:
        point = _point_estimate(
            _fit_selection(cycle),
            cycle.outcome.candidate_ids,
            tail_mass=tail,
            variant=VARIANT,
        )
        margins = _margin_draws(cycle.outcome.candidate_ids, point, kappa_all)
        realized = cycle.outcome.winning_margin
        p05, p10, p50, p90, p95 = (
            float(np.quantile(margins, q)) for q in (0.05, 0.10, 0.50, 0.90, 0.95)
        )
        pit = float((margins <= realized).mean())
        hit80 = p10 <= realized <= p90
        print(
            f"{cycle.election_cycle_id:<14}{realized:>10.4f}{p05:>8.4f}{p50:>8.4f}"
            f"{p95:>8.4f}{pit:>7.2f}{('Y' if hit80 else 'MISS'):>7}"
        )
    print(
        "NOTE: this is in-sample coverage (each cycle is in the fit), so it is optimistic "
        "by construction; it shows the production kappa spans the observed margin range, "
        "not that it is robust to a genuinely novel cycle."
    )


if __name__ == "__main__":
    main()
