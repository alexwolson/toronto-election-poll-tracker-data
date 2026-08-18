#!/usr/bin/env python3
"""Print the non-public, fail-closed Mayoral Endpoint qualification run."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.historical_mayoral import load_historical_mayoral_corpus
from backend.model.mayoral_endpoint import (
    MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL,
    MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
)
from backend.model.mayoral_endpoint_qualification import (
    MAYORAL_ENDPOINT_ABSOLUTE_MAXIMUM_SCORES,
    MAYORAL_ENDPOINT_EVALUATION_DRAW_COUNT,
    evaluate_mayoral_endpoint_qualification,
)
from backend.model.mayoral_evaluation import (
    CLOSE_RESULT,
    INCUMBENT_DEFEAT,
    MAYORAL_MODEL_FAMILY_LOG_GUARD,
    MAYORAL_MODEL_FAMILY_PRIMARY,
    MEAN_CANDIDATE_SHARE_CRPS,
    EvaluationReport,
    binary_brier_metric,
    binary_log_loss_metric,
)


_SUMMARY_METRICS = (
    MAYORAL_MODEL_FAMILY_PRIMARY,
    MAYORAL_MODEL_FAMILY_LOG_GUARD,
    MEAN_CANDIDATE_SHARE_CRPS,
    binary_brier_metric(CLOSE_RESULT),
    binary_log_loss_metric(CLOSE_RESULT),
    binary_brier_metric(INCUMBENT_DEFEAT),
    binary_log_loss_metric(INCUMBENT_DEFEAT),
)


def _metric_summary(metrics: object) -> dict[str, float]:
    return {
        metric: metrics[metric]  # type: ignore[index]
        for metric in _SUMMARY_METRICS
        if metric in metrics  # type: ignore[operator]
    }


def _report_summary(report: EvaluationReport) -> dict[str, object]:
    return {
        "population": report.population,
        "metrics": _metric_summary(report.metrics),
        "cycles": {
            cycle.election_cycle_id: _metric_summary(cycle.metrics)
            for cycle in report.cycles
        },
        "manifest": {
            cycle.election_cycle_id: [
                {
                    "days_before_election": lead,
                    "analysis_cutoff": cutoff.isoformat(),
                    "evidence_revision": revision,
                }
                for lead, cutoff, revision in cycle.snapshots
            ]
            for cycle in report.manifest.cycles
        },
    }


def main() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    result = evaluate_mayoral_endpoint_qualification(corpus)
    payload = {
        "status": "qualified" if result.qualifies else "not_qualified",
        "publication_authority": False,
        "configuration": {
            "lead_times": MAYORAL_ENDPOINT_EVALUATION_LEAD_TIMES,
            "analysis_time_local": str(MAYORAL_ENDPOINT_ANALYSIS_TIME_LOCAL),
            "draw_count": MAYORAL_ENDPOINT_EVALUATION_DRAW_COUNT,
            "primary_metric": MAYORAL_MODEL_FAMILY_PRIMARY,
            "log_loss_guard": MAYORAL_MODEL_FAMILY_LOG_GUARD,
            "absolute_maximum_scores": MAYORAL_ENDPOINT_ABSOLUTE_MAXIMUM_SCORES,
        },
        "corpus": {
            "source_documents": len(corpus.source_documents),
            "poll_samples": len(corpus.poll_samples),
            "poll_readings": len(corpus.poll_readings),
            "poll_responses": len(corpus.poll_responses),
        },
        "comparator": {
            "all_elections": _report_summary(result.comparator.all_elections),
            "regular_elections_only": _report_summary(
                result.comparator.regular_elections_only
            ),
        },
        "bridge": {
            "all_elections": _report_summary(result.bridge.all_elections),
            "regular_elections_only": _report_summary(
                result.bridge.regular_elections_only
            ),
        },
        "qualification": {
            "all_elections": asdict(result.all_elections),
            "regular_elections_only": asdict(result.regular_elections_only),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
