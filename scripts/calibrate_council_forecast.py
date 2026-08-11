#!/usr/bin/env python3
"""Calibrate and gate the historical Toronto incumbent-retention model.

The artifact is diagnostic as well as operational. A fitted model is retained
for research and sensitivity work even when publication gates fail; public
snapshots then carry explicit unavailable reasons instead of precise odds.

Run: uv run scripts/calibrate_council_forecast.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.model.council import (
    COUNCIL_MODEL_VERSION,
    FEATURES,
    build_historical_incumbent_cases,
    cross_validate_retention,
    fit_ridge_logit,
)

RESULTS_PATH = Path("data/raw/elections/historical_council_results.csv")
CASES_PATH = Path("data/processed/historical_council_incumbent_cases.csv")
ARTIFACT_PATH = Path("data/processed/council_forecast_calibration.json")
MINIMUM_CASES = 100
MINIMUM_LOSSES = 10


def main() -> None:
    results = pd.read_csv(RESULTS_PATH)
    cases = build_historical_incumbent_cases(results)
    diagnostics = cross_validate_retention(cases)
    model = fit_ridge_logit(cases)

    gates = {
        "minimum_historical_cases": diagnostics["case_count"] >= MINIMUM_CASES,
        "minimum_incumbent_losses": diagnostics["incumbent_losses"] >= MINIMUM_LOSSES,
        "beats_incumbent_base_rate": bool(diagnostics["beats_baseline"]),
    }
    unavailable_reasons = [name for name, passed in gates.items() if not passed]
    artifact = {
        "model_version": COUNCIL_MODEL_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "available" if all(gates.values()) else "insufficient_data",
        "unavailable_reasons": unavailable_reasons,
        "gates": gates,
        "thresholds": {
            "minimum_historical_cases": MINIMUM_CASES,
            "minimum_incumbent_losses": MINIMUM_LOSSES,
            "must_beat_incumbent_base_rate_on_brier_and_log_loss": True,
        },
        "diagnostics": diagnostics,
        "fit": {
            "feature_names": ["intercept", *FEATURES],
            "coefficients": model.coefficients.tolist(),
            "covariance": np.asarray(model.covariance).tolist(),
            "feature_means": model.feature_means,
            "feature_scales": model.feature_scales,
            "method": "regularized_logistic_incumbent_retention",
        },
        "data": {
            "elections": sorted(cases["election_year"].astype(int).unique().tolist()),
            "stable_boundary_pairs": ["2003-2006", "2006-2010", "2010-2014", "2018-2022"],
            "source": "City of Toronto official councillor results",
        },
    }

    CASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    cases.to_csv(CASES_PATH, index=False)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(
        f"Written {CASES_PATH}: {len(cases)} incumbent cases, "
        f"{diagnostics['incumbent_losses']} losses"
    )
    print(
        f"Written {ARTIFACT_PATH}: {artifact['status']} "
        f"({', '.join(unavailable_reasons) or 'all gates passed'})"
    )


if __name__ == "__main__":
    main()
