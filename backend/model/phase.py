"""Temporal phase detection for the Toronto 2026 model (Part 9 of spec).

Three phases correspond to data availability over the campaign:
  Phase 1: Pre-registration — no challenger data available.
  Phase 2: Registration open — candidates registered, no financial filings yet.
  Phase 3: Financial filings — full model inputs available.
"""
from __future__ import annotations

import pandas as pd

PHASE_DESCRIPTIONS: dict[int, dict[str, str]] = {
    1: {
        "label": "Phase 1 — Structural Factors Only",
        "description": (
            "Candidate registration has not yet opened. Projections reflect structural "
            "factors only: incumbent vulnerability scores, ward mayoral leans, and "
            "councillor alignment. No challenger data is available."
        ),
    },
    2: {
        "label": "Phase 2 — Registration Period",
        "description": (
            "Candidates have registered. The model incorporates name recognition tiers "
            "but full financial data is not yet available. Ward classifications are "
            "preliminary and carry higher uncertainty."
        ),
    },
    3: {
        "label": "Phase 3 — Financial Filings Available",
        "description": (
            "Financial filing data is incorporated. The model runs at full capacity. "
            "Ward classifications and win probabilities reflect all available inputs."
        ),
    },
}


def detect_phase(challengers: pd.DataFrame) -> dict:
    """Detect the current model phase from the challengers dataset.

    Returns a dict with keys: phase (int), label (str), description (str).
    """
    real = challengers[challengers["candidate_name"] != "Generic Challenger"] if not challengers.empty else challengers
    if real.empty:
        phase = 1
    elif "fundraising_tier" not in real.columns or real["fundraising_tier"].isna().all():
        phase = 2
    else:
        phase = 3

    return {"phase": phase, **PHASE_DESCRIPTIONS[phase]}
