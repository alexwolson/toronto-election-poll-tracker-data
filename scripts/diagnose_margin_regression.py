#!/usr/bin/env python3
"""Explain the winning-margin CRPS change from the tail-allocation switch.

ADR 0038 replaced per-omitted-candidate count-scaling with a constant-total tail
allocation. That improved candidate-share calibration but worsened winning-margin
CRPS, almost entirely in the 2023 by-election. This script reconstructs the OLD
count-scaling allocation (by temporarily restoring its per-reading rule) and the
NEW allocation, then re-scores winning-margin CRPS across every lead time exactly
as ``scripts/evaluate_mayoral_endpoint.py`` does, and reports the realized margin,
the predicted margin mean, and the fitted Dirichlet concentration for each so the
regression can be attributed to point location vs. over-confidence.

The OLD allocation is superseded, so the script rebuilds it locally rather than
importing it; ``newCRPS`` reproduces the after-change ladder and ``oldCRPS`` the
before-change ladder, which is the script's own correctness check.

Run from the data project root:  uv run scripts/diagnose_margin_regression.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import backend.model.mayoral_endpoint as endpoint
from backend.model.historical_mayoral import load_historical_mayoral_corpus
from backend.model.historical_mayoral_evaluation import (
    build_historical_mayoral_evaluation_cycles,
)
from backend.model.mayoral_endpoint import (
    MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
    fit_mayoral_endpoint,
)
from backend.model.mayoral_evaluation import (
    EvaluationPrediction,
    FullBallotShareDraws,
    HeldOutCycle,
    TrainingCycle,
    score_prediction,
)

VARIANT = "firm-balanced-bridge"
DRAW_COUNT = 4096
MARGIN_METRIC = "scalar:winning_margin:crps"
_ORIGINAL_READING_POINT = endpoint._reading_point


def _old_reading_point(reading, candidate_ids, *, tail_mass):
    """Superseded allocation: ``tail_mass`` carries a per-omitted-candidate odds."""
    odds = tail_mass
    unmeasured_count = len(set(candidate_ids) - set(reading.candidate_shares))
    normalizer = 1.0 + unmeasured_count * odds
    point = tuple(
        float(reading.candidate_shares[candidate_id]) / normalizer
        if candidate_id in reading.candidate_shares
        else odds / normalizer
        for candidate_id in candidate_ids
    )
    return endpoint._normalize_point(point)


def _old_fit_tail_odds(training_cycles, selected_by_cycle):
    cycle_estimates = []
    for cycle in training_cycles:
        reading_estimates = []
        outcome = cycle.outcome.candidate_shares
        for reading in selected_by_cycle[cycle.election_cycle_id]:
            unmeasured = set(outcome) - set(reading.candidate_shares)
            if not unmeasured:
                continue
            tail_share = sum(outcome[candidate] for candidate in unmeasured)
            if not 0.0 < tail_share < 1.0:
                continue
            reading_estimates.append(
                tail_share / ((1.0 - tail_share) * len(unmeasured))
            )
        if reading_estimates:
            cycle_estimates.append(sum(reading_estimates) / len(reading_estimates))
    return sum(cycle_estimates) / len(cycle_estimates)


def _fit_snapshot_selection(cycle):
    snapshot = min(cycle.history, key=lambda s: s.days_before_election)
    return endpoint._filter_selected(
        endpoint._selected_for_cycle(
            snapshot.evidence,
            cycle.outcome.candidate_ids,
            expected_election_cycle_id=cycle.election_cycle_id,
            analysis_cutoff=snapshot.analysis_cutoff,
        ),
        excluded_poll_sample_ids=frozenset(),
        excluded_pollsters=frozenset(),
    )


def _old_fit(training, held):
    training_selected = {
        c.election_cycle_id: _fit_snapshot_selection(c) for c in training
    }
    odds = _old_fit_tail_odds(training, training_selected)
    selected = endpoint._filter_selected(
        endpoint._selected_for_cycle(
            held.snapshot.evidence,
            held.candidate_ids,
            expected_election_cycle_id=held.election_cycle_id,
            analysis_cutoff=held.snapshot.analysis_cutoff,
        ),
        excluded_poll_sample_ids=frozenset(),
        excluded_pollsters=frozenset(),
    )
    endpoint._reading_point = _old_reading_point
    try:
        concentration = endpoint._fit_concentration(
            training,
            tail_mass=odds,
            variant=VARIANT,
            excluded_poll_sample_ids=frozenset(),
            excluded_pollsters=frozenset(),
        )
        point = endpoint._point_estimate(
            selected, held.candidate_ids, tail_mass=odds, variant=VARIANT
        )
    finally:
        endpoint._reading_point = _ORIGINAL_READING_POINT
    return point, concentration


def _folds(cycles, lead_times):
    for target in cycles:
        for lead in lead_times:
            target_snapshot = next(
                s for s in target.snapshots if s.days_before_election == lead
            )
            training = tuple(
                TrainingCycle(
                    election_cycle_id=c.election_cycle_id,
                    election_type=c.election_type,
                    snapshot=next(
                        s for s in c.snapshots if s.days_before_election == lead
                    ),
                    history=c.snapshots,
                    outcome=c.outcome,
                )
                for c in cycles
                if c.election_cycle_id != target.election_cycle_id
            )
            held = HeldOutCycle(
                election_cycle_id=target.election_cycle_id,
                election_type=target.election_type,
                snapshot=target_snapshot,
                candidate_ids=target.outcome.candidate_ids,
                incumbent_candidate_id=target.outcome.incumbent_candidate_id,
            )
            yield target, training, held


def _draws(candidate_ids, point, concentration):
    canonical = tuple(sorted(zip(candidate_ids, point, strict=True)))
    seed_material = json.dumps(
        {"candidate_point": canonical, "concentration": concentration},
        separators=(",", ":"),
    ).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    ordered_ids = tuple(candidate_id for candidate_id, _ in canonical)
    ordered_point = np.asarray(tuple(share for _, share in canonical), dtype=float)
    parameters = np.maximum(ordered_point * concentration, 1e-12)
    canonical_draws = rng.dirichlet(parameters, size=DRAW_COUNT)
    index = {candidate_id: i for i, candidate_id in enumerate(ordered_ids)}
    return tuple(
        tuple(float(row[index[candidate_id]]) for candidate_id in candidate_ids)
        for row in canonical_draws
    )


def _margin_crps_and_mean(outcome, candidate_ids, point, concentration):
    draws = _draws(candidate_ids, point, concentration)
    crps = score_prediction(
        outcome, EvaluationPrediction(FullBallotShareDraws(candidate_ids, draws))
    )[MARGIN_METRIC]
    gaps = []
    for row in draws:
        top_two = sorted(row, reverse=True)[:2]
        gaps.append(top_two[0] - top_two[1])
    return crps, sum(gaps) / len(gaps)


def main() -> None:
    lead_times = MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES
    corpus = load_historical_mayoral_corpus(ROOT)
    cycles = build_historical_mayoral_evaluation_cycles(
        corpus,
        lead_times=lead_times,
        analysis_time_local=MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    )

    aggregate: dict[str, dict[str, list[float] | float]] = {}
    for target, training, held in _folds(cycles, lead_times):
        outcome = target.outcome
        new_fit = fit_mayoral_endpoint(training, held, variant=VARIANT)
        new_crps, new_mean = _margin_crps_and_mean(
            outcome, new_fit.candidate_ids, new_fit.point_shares, new_fit.concentration
        )
        old_point, old_concentration = _old_fit(training, held)
        old_crps, old_mean = _margin_crps_and_mean(
            outcome, held.candidate_ids, old_point, old_concentration
        )
        row = aggregate.setdefault(
            target.election_cycle_id,
            {
                "realized": outcome.winning_margin,
                "old_crps": [],
                "new_crps": [],
                "old_mean": [],
                "new_mean": [],
                "old_conc": [],
                "new_conc": [],
            },
        )
        row["old_crps"].append(old_crps)
        row["new_crps"].append(new_crps)
        row["old_mean"].append(old_mean)
        row["new_mean"].append(new_mean)
        row["old_conc"].append(old_concentration)
        row["new_conc"].append(new_fit.concentration)

    def mean(values):
        return sum(values) / len(values)

    print(
        f"{'cycle':<14}{'realMargin':>11}{'oldMean':>9}{'newMean':>9}"
        f"{'oldConc':>9}{'newConc':>9}{'oldCRPS':>9}{'newCRPS':>9}{'dCRPS':>9}"
    )
    for cycle_id, row in aggregate.items():
        print(
            f"{cycle_id:<14}{row['realized']:>11.4f}"
            f"{mean(row['old_mean']):>9.4f}{mean(row['new_mean']):>9.4f}"
            f"{mean(row['old_conc']):>9.1f}{mean(row['new_conc']):>9.1f}"
            f"{mean(row['old_crps']):>9.5f}{mean(row['new_crps']):>9.5f}"
            f"{mean(row['new_crps']) - mean(row['old_crps']):>+9.5f}"
        )
    print(
        "\nCheck: newCRPS reproduces the after-change bridge per-cycle numbers and "
        "oldCRPS the before-change numbers in scripts/evaluate_mayoral_endpoint.py."
    )


if __name__ == "__main__":
    main()
