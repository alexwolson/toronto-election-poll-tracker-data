#!/usr/bin/env python3
"""Evaluate the incumbency-informed endpoint against the polling-only bridge.

Runs the incumbency-informed variant (ADR 0013) and the firm-balanced bridge
baseline through the frozen whole-election harness, reports the primary
winning-margin CRPS and the log-score guard, and prints the qualify-or-not
verdict (ADR 0030) plus a prior-strength sensitivity. No publication authority.

Run from the data project root:  uv run scripts/evaluate_incumbency_endpoint.py
"""

from __future__ import annotations

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
    MayoralEndpointPredictor,
)
from backend.model.mayoral_endpoint_qualification import (
    MAYORAL_ENDPOINT_EVALUATION_DRAW_COUNT,
)
from backend.model.mayoral_evaluation import (
    MAYORAL_MODEL_FAMILY_LOG_GUARD,
    MAYORAL_MODEL_FAMILY_PRIMARY,
    evaluate_with_regular_election_sensitivity,
    qualify_model_ladder,
)
from backend.model.mayoral_incumbency import load_mayoral_incumbency_population
from backend.model.mayoral_incumbency_endpoint import (
    DEFAULT_PRIOR_PSEUDOCOUNT,
    IncumbencyInformedPredictor,
)

LEAD_TIMES = MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES
DRAWS = MAYORAL_ENDPOINT_EVALUATION_DRAW_COUNT


def _suite(cycles, fit_predict, name):
    return evaluate_with_regular_election_sensitivity(
        cycles, lead_times=LEAD_TIMES, fit_predict=fit_predict, model_name=name
    )


def main() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    population = load_mayoral_incumbency_population(ROOT)
    cycles = build_historical_mayoral_evaluation_cycles(
        corpus,
        lead_times=LEAD_TIMES,
        analysis_time_local=MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    )

    bridge = _suite(
        cycles,
        MayoralEndpointPredictor("firm-balanced-bridge", draw_count=DRAWS),
        "firm-balanced-bridge",
    )
    incumbency = _suite(
        cycles,
        IncumbencyInformedPredictor(
            population=population,
            draw_count=DRAWS,
            prior_pseudocount=DEFAULT_PRIOR_PSEUDOCOUNT,
        ),
        "incumbency-informed",
    )

    print(
        f"=== incumbency-informed vs firm-balanced bridge (w={DEFAULT_PRIOR_PSEUDOCOUNT}) ==="
    )
    for population_label, bridge_report, incumbency_report in (
        ("all_elections", bridge.all_elections, incumbency.all_elections),
        (
            "regular_elections_only",
            bridge.regular_elections_only,
            incumbency.regular_elections_only,
        ),
    ):
        bp = bridge_report.metrics[MAYORAL_MODEL_FAMILY_PRIMARY]
        ip = incumbency_report.metrics[MAYORAL_MODEL_FAMILY_PRIMARY]
        bg = bridge_report.metrics[MAYORAL_MODEL_FAMILY_LOG_GUARD]
        ig = incumbency_report.metrics[MAYORAL_MODEL_FAMILY_LOG_GUARD]
        decision = qualify_model_ladder(
            naive=bridge_report,
            endpoint=incumbency_report,
            primary_metric=MAYORAL_MODEL_FAMILY_PRIMARY,
            log_loss_guard=MAYORAL_MODEL_FAMILY_LOG_GUARD,
            endpoint_maximum_scores=None,
        )
        print(f"\n[{population_label}]")
        print(
            f"  winning-margin CRPS (primary):  bridge {bp:.5f} -> incumbency {ip:.5f}  ({ip - bp:+.5f})"
        )
        print(
            f"  winner log score (guard):       bridge {bg:.5f} -> incumbency {ig:.5f}  ({ig - bg:+.5f})"
        )
        print(
            f"  incumbency-informed qualifies over bridge? -> {decision.endpoint_qualifies}"
        )

    print("\n=== per-cycle winning-margin CRPS (incumbent cycles only differ) ===")
    bridge_cycles = {c.election_cycle_id: c for c in bridge.all_elections.cycles}
    for c in incumbency.all_elections.cycles:
        b = bridge_cycles[c.election_cycle_id].metrics[MAYORAL_MODEL_FAMILY_PRIMARY]
        i = c.metrics[MAYORAL_MODEL_FAMILY_PRIMARY]
        tag = "" if abs(i - b) > 1e-9 else "  (open race: identical to bridge)"
        print(f"  {c.election_cycle_id:<14} {b:.5f} -> {i:.5f}  ({i - b:+.5f}){tag}")

    print("\n=== prior-strength sensitivity (all_elections primary CRPS) ===")
    base = bridge.all_elections.metrics[MAYORAL_MODEL_FAMILY_PRIMARY]
    print(f"  bridge baseline                 {base:.5f}")
    for weight in (0.0, 4.0, 8.0, 16.0):
        suite = _suite(
            cycles,
            IncumbencyInformedPredictor(
                population=population, draw_count=DRAWS, prior_pseudocount=weight
            ),
            f"incumbency-w{weight}",
        )
        value = suite.all_elections.metrics[MAYORAL_MODEL_FAMILY_PRIMARY]
        note = "  (w=0 reduces to the bridge)" if weight == 0.0 else ""
        print(
            f"  incumbency-informed  w={weight:<5}      {value:.5f}  ({value - base:+.5f}){note}"
        )


if __name__ == "__main__":
    main()
