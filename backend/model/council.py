"""Evidence and calibration helpers for the Council race model.

The public Council product deliberately separates:

* structural evidence (the prior result and current registered field),
* an editorial race assessment (Safe, Competitive, or Open), and
* a publishable election forecast, which is withheld until its data and
  historical-calibration gates pass.

This module contains no mayoral-poll-to-council vote conversion. Mayoral mood
is retained as a documented sensitivity analysis, not treated as ward polling.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from .mayoral_config import NOMINATION_CLOSE

COUNCIL_MODEL_VERSION = "incumbent_retention_v1"
COUNCIL_ASSESSMENT_VERSION = "structural_assessment_v1"
HISTORICAL_PAIRS = ((2003, 2006), (2006, 2010), (2010, 2014), (2018, 2022))
CONTINUOUS_FEATURES = ("prior_share", "prior_margin", "log_candidate_count")
BINARY_FEATURES = ("returning_runner_up", "first_term")
FEATURES = (*CONTINUOUS_FEATURES, *BINARY_FEATURES)

# Race assessment thresholds operate on evidence, not on forecast probability.
# They are intentionally simple, versioned, and testable.
HIGH_VULNERABILITY = 55.0
ELEVATED_VULNERABILITY = 40.0
STRONG_PRIOR_CHALLENGER_SHARE = 0.25


def candidate_key(value: object) -> str:
    """Order-insensitive candidate key across changing City name formats."""
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_name = "".join(char for char in normalized if not unicodedata.combining(char))
    tokens = re.findall(r"[a-z0-9]+", ascii_name.lower())
    return " ".join(sorted(tokens))


def build_historical_incumbent_cases(results: pd.DataFrame) -> pd.DataFrame:
    """Create stable-boundary incumbent re-election cases from official results."""
    required = {
        "election_year",
        "ward",
        "candidate_name",
        "candidate_key",
        "vote_share",
        "is_winner",
        "is_acclaimed",
    }
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"Historical council results missing columns: {sorted(missing)}")

    rows: list[dict[str, Any]] = []
    winners_by_year: dict[int, pd.DataFrame] = {
        int(year): group[group["is_winner"].astype(bool)].copy()
        for year, group in results.groupby("election_year")
    }

    for prior_year, election_year in HISTORICAL_PAIRS:
        prior = results[results["election_year"] == prior_year]
        current = results[results["election_year"] == election_year]
        if prior.empty or current.empty:
            continue
        prior_winners = prior[prior["is_winner"].astype(bool)]
        for _, incumbent in prior_winners.iterrows():
            if bool(incumbent["is_acclaimed"]):
                # An acclamation has no informative prior vote share or margin.
                continue
            ward = int(incumbent["ward"])
            field = current[current["ward"] == ward]
            key = str(incumbent["candidate_key"])
            incumbent_row = field[field["candidate_key"] == key]
            if incumbent_row.empty:
                # Open seat: not an incumbent-retention case.
                continue

            ordered_prior = prior[prior["ward"] == ward].sort_values(
                "vote_share", ascending=False
            )
            if len(ordered_prior) < 2:
                continue
            runner_up = ordered_prior.iloc[1]
            prior_margin = float(ordered_prior.iloc[0]["vote_share"]) - float(
                runner_up["vote_share"]
            )

            previous_years = [
                year
                for year in winners_by_year
                if year < prior_year
                and (
                    (prior_year <= 2014 and year <= 2014)
                    or (prior_year >= 2018 and year >= 2018)
                )
            ]
            won_previous = any(
                not winners_by_year[year][
                    (winners_by_year[year]["ward"] == ward)
                    & (winners_by_year[year]["candidate_key"] == key)
                ].empty
                for year in previous_years
            )
            current_keys = set(field["candidate_key"].astype(str))
            rows.append(
                {
                    "prior_election": prior_year,
                    "election_year": election_year,
                    "ward": ward,
                    "incumbent_name": incumbent["candidate_name"],
                    "prior_share": float(incumbent["vote_share"]),
                    "prior_margin": prior_margin,
                    "candidate_count": int(len(field)),
                    "log_candidate_count": math.log(max(2, len(field))),
                    "returning_runner_up": float(
                        str(runner_up["candidate_key"]) in current_keys
                    ),
                    "first_term": float(not won_previous),
                    "incumbent_won": int(bool(incumbent_row.iloc[0]["is_winner"])),
                }
            )

    cases = pd.DataFrame(rows)
    if cases.empty:
        raise ValueError("No historical incumbent re-election cases were derived")
    if cases.duplicated(["election_year", "ward"]).any():
        raise ValueError("Historical incumbent cases are not unique by election and ward")
    return cases.sort_values(["election_year", "ward"]).reset_index(drop=True)


@dataclass(frozen=True)
class RidgeLogit:
    coefficients: np.ndarray
    covariance: np.ndarray
    feature_means: dict[str, float]
    feature_scales: dict[str, float]
    feature_names: tuple[str, ...] = FEATURES


def _design_matrix(
    rows: pd.DataFrame,
    means: dict[str, float],
    scales: dict[str, float],
) -> np.ndarray:
    columns: list[np.ndarray] = [np.ones(len(rows), dtype=float)]
    for feature in CONTINUOUS_FEATURES:
        columns.append(
            (rows[feature].to_numpy(dtype=float) - means[feature]) / scales[feature]
        )
    for feature in BINARY_FEATURES:
        columns.append(rows[feature].to_numpy(dtype=float))
    return np.column_stack(columns)


def fit_ridge_logit(cases: pd.DataFrame, max_iter: int = 100) -> RidgeLogit:
    """Fit a small regularized retention model with a transparent Newton solver."""
    means = {feature: float(cases[feature].mean()) for feature in CONTINUOUS_FEATURES}
    scales = {
        feature: max(float(cases[feature].std(ddof=0)), 1e-6)
        for feature in CONTINUOUS_FEATURES
    }
    design = _design_matrix(cases, means, scales)
    outcome = cases["incumbent_won"].to_numpy(dtype=float)
    base_rate = (float(outcome.sum()) + 1.0) / (len(outcome) + 2.0)
    prior_mean = np.zeros(design.shape[1], dtype=float)
    prior_mean[0] = math.log(base_rate / (1.0 - base_rate))
    # Weakly informative priors stabilize eight historical losses without
    # forcing the result to the near-certain all-incumbents-win baseline.
    prior_precision = np.array([0.16, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=float)
    beta = prior_mean.copy()

    for _ in range(max_iter):
        linear = np.clip(design @ beta, -30.0, 30.0)
        probability = 1.0 / (1.0 + np.exp(-linear))
        weights = np.maximum(probability * (1.0 - probability), 1e-8)
        gradient = design.T @ (probability - outcome) + prior_precision * (
            beta - prior_mean
        )
        hessian = design.T @ (weights[:, None] * design) + np.diag(
            prior_precision
        )
        step = np.linalg.solve(hessian, gradient)
        beta_next = beta - step
        if float(np.max(np.abs(step))) < 1e-8:
            beta = beta_next
            break
        beta = beta_next

    linear = np.clip(design @ beta, -30.0, 30.0)
    probability = 1.0 / (1.0 + np.exp(-linear))
    weights = np.maximum(probability * (1.0 - probability), 1e-8)
    hessian = design.T @ (weights[:, None] * design) + np.diag(prior_precision)
    covariance = np.linalg.inv(hessian)
    return RidgeLogit(beta, covariance, means, scales)


def predict_retention(model: RidgeLogit, rows: pd.DataFrame) -> np.ndarray:
    design = _design_matrix(rows, model.feature_means, model.feature_scales)
    linear = np.clip(design @ model.coefficients, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-linear))


def cross_validate_retention(cases: pd.DataFrame) -> dict[str, Any]:
    """Leave one election cycle out and compare with an incumbent-base-rate prior."""
    predictions: list[float] = []
    baselines: list[float] = []
    outcomes: list[int] = []
    folds: list[dict[str, Any]] = []
    for election_year in sorted(cases["election_year"].unique()):
        train = cases[cases["election_year"] != election_year]
        test = cases[cases["election_year"] == election_year]
        model = fit_ridge_logit(train)
        fold_predictions = predict_retention(model, test)
        base_rate = (float(train["incumbent_won"].sum()) + 1.0) / (len(train) + 2.0)
        predictions.extend(fold_predictions.tolist())
        baselines.extend([base_rate] * len(test))
        outcomes.extend(test["incumbent_won"].astype(int).tolist())
        folds.append(
            {
                "held_out_election": int(election_year),
                "case_count": int(len(test)),
                "incumbent_losses": int((1 - test["incumbent_won"]).sum()),
            }
        )

    y = np.asarray(outcomes, dtype=float)
    pred = np.clip(np.asarray(predictions), 1e-6, 1.0 - 1e-6)
    base = np.clip(np.asarray(baselines), 1e-6, 1.0 - 1e-6)
    brier = float(np.mean((pred - y) ** 2))
    baseline_brier = float(np.mean((base - y) ** 2))
    log_loss = float(-np.mean(y * np.log(pred) + (1 - y) * np.log(1 - pred)))
    baseline_log_loss = float(
        -np.mean(y * np.log(base) + (1 - y) * np.log(1 - base))
    )
    return {
        "case_count": int(len(cases)),
        "election_count": int(cases["election_year"].nunique()),
        "incumbent_wins": int(cases["incumbent_won"].sum()),
        "incumbent_losses": int((1 - cases["incumbent_won"]).sum()),
        "retention_rate": float(cases["incumbent_won"].mean()),
        "winner_brier": brier,
        "baseline_winner_brier": baseline_brier,
        "share_log_loss": log_loss,
        "baseline_share_log_loss": baseline_log_loss,
        "beats_baseline": brier < baseline_brier and log_loss < baseline_log_loss,
        "folds": folds,
    }


def nominations_closed(reference_date: datetime | None = None) -> bool:
    reference = reference_date or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    return reference >= NOMINATION_CLOSE


def classify_race_evidence(
    *,
    is_running: bool,
    vulnerability_score: float,
    strongest_challenger_tier: str | None,
    returning_runner_up: bool,
    prior_runner_up_share: float | None,
    direct_poll_available: bool,
) -> tuple[str, list[str]]:
    """Return a public race assessment and exhaustive evidence reasons."""
    if not is_running:
        return "open", ["no_running_incumbent"]

    strong_challenger = strongest_challenger_tier == "well-known"
    strong_rematch = returning_runner_up and (
        prior_runner_up_share is not None
        and prior_runner_up_share >= STRONG_PRIOR_CHALLENGER_SHARE
    )
    # A generic "known" label is descriptive familiarity, not demonstrated
    # electoral strength. It cannot by itself move a ward to Competitive.
    credible_challenger = strong_challenger or strong_rematch
    reasons: list[str] = []
    if vulnerability_score >= HIGH_VULNERABILITY:
        reasons.append("high_structural_vulnerability")
    if vulnerability_score >= ELEVATED_VULNERABILITY and credible_challenger:
        reasons.append("elevated_vulnerability_with_credible_challenger")
    if strong_challenger:
        reasons.append("well_known_challenger")
    if strong_rematch:
        reasons.append("strong_returning_runner_up")
    if direct_poll_available:
        reasons.append("direct_ward_poll_available")

    return ("competitive", reasons) if reasons else ("safe", ["no_competitive_trigger"])
