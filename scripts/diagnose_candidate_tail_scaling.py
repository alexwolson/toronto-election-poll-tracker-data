#!/usr/bin/env python3
"""Diagnose whether Unmeasured Candidate Tail mass scales with choice-set size.

The current Mayoral Endpoint fits one per-omitted-candidate odds
(``_fit_tail_odds``) and allocates it through a ``1 + m * odds`` normalizer
(``_reading_point``), so a reading that omits ``m`` Final-Ballot candidates
receives total tail mass ``m * odds / (1 + m * odds)`` -- an amount that rises
with ``m``.  This script measures, on the reconstructed historical corpus,
whether realized total omitted mass actually rises with ``m``, and compares the
current count-scaling model against a choice-set-size-invariant
(constant-total) allocation under leave-one-cycle-out.

It reproduces the endpoint's exact reading-selection path and reads the same
fit-snapshot (closest post-Final lead time) the fitter uses.  It has no
publication side effects.

Run from the data project root:  uv run scripts/diagnose_candidate_tail_scaling.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.historical_mayoral import load_historical_mayoral_corpus
from backend.model.historical_mayoral_evaluation import (
    build_historical_mayoral_evaluation_cycles,
)
from backend.model.mayoral_endpoint import (
    MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
    _fit_tail_odds,
    _selected_for_cycle,
)
from backend.model.mayoral_evaluation import TrainingCycle


def _selected_at_fit(cycle):
    """Readings the fitter would use: those at the closest lead-time snapshot."""
    snapshot = min(cycle.snapshots, key=lambda s: s.days_before_election)
    return _selected_for_cycle(
        snapshot.evidence,
        cycle.outcome.candidate_ids,
        expected_election_cycle_id=cycle.election_cycle_id,
        analysis_cutoff=snapshot.analysis_cutoff,
    )


def _tail_observations(cycle):
    """(m, T) for every fit-snapshot reading that omits >=1 Final-Ballot name."""
    outcome = cycle.outcome.candidate_shares
    rows = []
    for reading in _selected_at_fit(cycle):
        unmeasured = set(outcome) - set(reading.candidate_shares)
        m = len(unmeasured)
        if m == 0:
            continue
        tail = sum(outcome[candidate] for candidate in unmeasured)
        if 0.0 < tail < 1.0:
            rows.append((m, tail))
    return rows


def _cycle_total_tail(cycle):
    """Mean realized total omitted mass and mean m across fit-snapshot readings."""
    rows = _tail_observations(cycle)
    if not rows:
        return None, None
    return (
        sum(tail for _, tail in rows) / len(rows),
        sum(m for m, _ in rows) / len(rows),
    )


def _as_training(cycle, lead_times):
    snapshots = {s.days_before_election: s for s in cycle.snapshots}
    fit_snapshot = min(cycle.snapshots, key=lambda s: s.days_before_election)
    return TrainingCycle(
        election_cycle_id=cycle.election_cycle_id,
        election_type=cycle.election_type,
        snapshot=fit_snapshot,
        history=tuple(snapshots[lead] for lead in lead_times),
        outcome=cycle.outcome,
    )


def _ols(xs, ys):
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    syy = sum((y - mean_y) ** 2 for y in ys)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else float("nan")
    r = sxy / math.sqrt(sxx * syy) if sxx and syy else float("nan")
    return slope, r, n


def main() -> None:
    lead_times = MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES
    corpus = load_historical_mayoral_corpus(ROOT)
    cycles = build_historical_mayoral_evaluation_cycles(
        corpus,
        lead_times=lead_times,
        analysis_time_local=MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    )

    print("=== realized omitted mass by cycle (fit snapshot) ===")
    print(f"{'cycle':<14}{'readings':>9}{'m':>10}{'total tail T':>26}")
    all_m, all_tail = [], []
    for cycle in cycles:
        rows = _tail_observations(cycle)
        if not rows:
            print(f"{cycle.election_cycle_id:<14}{'(no tail)':>9}")
            continue
        ms = [m for m, _ in rows]
        ts = [t for _, t in rows]
        all_m.extend(ms)
        all_tail.extend(ts)
        print(
            f"{cycle.election_cycle_id:<14}{len(rows):>9}"
            f"{f'[{min(ms)},{max(ms)}]':>10}"
            f"{f'mean {sum(ts) / len(ts):.4f}  [{min(ts):.4f},{max(ts):.4f}]':>26}"
        )

    log_m = [math.log(m) for m in all_m]
    log_total_odds = [math.log(t / (1 - t)) for t in all_tail]
    log_per_candidate_odds = [
        math.log(t / ((1 - t) * m)) for m, t in zip(all_m, all_tail)
    ]
    slope_total, r_total, n = _ols(log_m, log_total_odds)
    slope_per, r_per, _ = _ols(log_m, log_per_candidate_odds)
    print(
        "\nlog(T/(1-T)) ~ log(m):        "
        f"slope={slope_total:+.3f}  r={r_total:+.3f}  (rows={n})   "
        "[+1 = current count-scaling, 0 = constant-total]"
    )
    print(
        "log(per-candidate odds) ~ log(m): "
        f"slope={slope_per:+.3f}  r={r_per:+.3f}   "
        "[0 = current, -1 = constant-total]"
    )
    print(
        "NOTE: m is near-constant within a cycle, so honest resolution is the "
        f"{len(cycles)} cycles above; the row-level r is pseudo-replicated."
    )

    print("\n=== leave-one-cycle-out: predicted vs realized TOTAL tail mass ===")
    print(
        f"{'held-out':<14}{'m':>4}{'real T':>9}"
        f"{'cur odds':>10}{'cur pred':>10}{'cur err':>9}"
        f"{'const':>9}{'const err':>11}"
    )
    current_errors, constant_errors = [], []
    for target in cycles:
        real_tail, mean_m = _cycle_total_tail(target)
        if real_tail is None:
            continue
        m = round(mean_m)
        others = [c for c in cycles if c.election_cycle_id != target.election_cycle_id]

        training = tuple(_as_training(c, lead_times) for c in others)
        selected = {c.election_cycle_id: _selected_at_fit(c) for c in others}
        odds = _fit_tail_odds(training, selected)
        current_pred = m * odds / (1.0 + m * odds)

        training_totals = [t for t, _ in (_cycle_total_tail(c) for c in others) if t]
        constant_pred = sum(training_totals) / len(training_totals)

        current_err = abs(current_pred - real_tail)
        constant_err = abs(constant_pred - real_tail)
        current_errors.append(current_err)
        constant_errors.append(constant_err)
        print(
            f"{target.election_cycle_id:<14}{m:>4}{real_tail:>9.4f}"
            f"{odds:>10.5f}{current_pred:>10.4f}{current_err:>9.4f}"
            f"{constant_pred:>9.4f}{constant_err:>11.4f}"
        )

    n_folds = len(current_errors)
    print(
        f"\nmean abs error in total tail mass:  "
        f"current={sum(current_errors) / n_folds:.4f}   "
        f"constant-total={sum(constant_errors) / n_folds:.4f}"
    )


if __name__ == "__main__":
    main()
