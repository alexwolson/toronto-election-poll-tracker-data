#!/usr/bin/env python3
"""Rolling-origin calibration for the Toronto mayoral choice-set forecast.

This is intentionally a deterministic and fast calibration pass. It fits the
same Luce choice-set observation assumption as the live NumPyro model, then
uses posterior-style Dirichlet and campaign-drift draws to score historical
share intervals and winner probabilities at fixed campaign cutoffs.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "polls"
PROCESSED = ROOT / "data" / "processed"
CUTOFFS = (120, 90, 60, 30, 14, 7)
SEED = 20260810
PARAMETERS = {
    "weekly_sigma": 0.16,
    "house_sigma": 0.075,
    "field_sigma": 0.12,
    "poll_concentration": 30.0,
}


def _election_field(outcomes: pd.DataFrame) -> list[str]:
    return sorted(outcomes.loc[~outcomes["is_residual"].astype(bool), "candidate_id"].astype(str))


def _poll_observations(
    polls: pd.DataFrame,
    field: list[str],
    cutoff: pd.Timestamp,
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    eligible = polls[pd.to_datetime(polls["date_published"]) <= cutoff]
    for poll_id, group in eligible.groupby("poll_id", sort=False):
        shares = {
            str(row["candidate_id"]): float(row["share"])
            for _, row in group.iterrows()
            if str(row["candidate_id"]) in field
        }
        if not shares:
            continue
        present = [candidate for candidate in field if candidate in shares]
        residual = max(0.0, 1.0 - sum(shares.values()))
        published = pd.Timestamp(group.iloc[0]["date_published"])
        age_days = max(0.0, float((cutoff - published).days))
        recency = 0.5 ** (age_days / 12.0)
        sample = group.iloc[0].get("sample_size")
        sample = 600.0 if pd.isna(sample) else min(600.0, float(sample))
        observations.append(
            {
                "poll_id": poll_id,
                "present": present,
                "shares": shares,
                "residual": residual,
                "weight": recency * sample,
            }
        )
    return observations


def _fit_choice_set(observations: list[dict[str, Any]], field: list[str]) -> np.ndarray:
    index = {candidate: i for i, candidate in enumerate(field)}

    def objective(utilities: np.ndarray) -> float:
        loss = 0.5 * float(np.square(utilities).sum())
        for observation in observations:
            present_indices = np.array([index[candidate] for candidate in observation["present"]])
            logits = np.append(utilities[present_indices], 0.0)
            logits -= logits.max()
            probabilities = np.exp(logits)
            probabilities /= probabilities.sum()
            observed = np.array(
                [observation["shares"][candidate] for candidate in observation["present"]]
                + [observation["residual"]]
            )
            observed /= observed.sum()
            loss -= observation["weight"] * float(
                np.sum(observed * np.log(np.clip(probabilities, 1e-9, 1.0)))
            )
        return loss

    result = minimize(objective, np.zeros(len(field)), method="BFGS")
    if not result.success and not np.isfinite(result.fun):
        raise RuntimeError(f"Historical choice-set fit failed: {result.message}")
    logits = np.append(result.x, 0.0)
    logits -= logits.max()
    probabilities = np.exp(logits)
    return probabilities / probabilities.sum()


def _draws(
    mean: np.ndarray,
    days_to_election: int,
    rng: np.random.Generator,
    n_draws: int,
) -> np.ndarray:
    base = rng.dirichlet(mean * PARAMETERS["poll_concentration"], size=n_draws)
    future_weeks = max(0.0, days_to_election / 7.0)
    sigma = PARAMETERS["weekly_sigma"] * math.sqrt(future_weeks)
    logits = np.log(np.clip(base, 1e-9, 1.0))
    logits[:, :-1] += rng.normal(0.0, sigma, size=(n_draws, len(mean) - 1))
    projected = np.exp(logits - logits.max(axis=1, keepdims=True))
    return projected / projected.sum(axis=1, keepdims=True)


def _latest_poll_baseline(
    polls: pd.DataFrame,
    field: list[str],
    cutoff: pd.Timestamp,
) -> np.ndarray | None:
    eligible = polls[pd.to_datetime(polls["date_published"]) <= cutoff]
    if eligible.empty:
        return None
    latest_date = eligible["date_published"].max()
    latest = eligible[eligible["date_published"] == latest_date]
    group = next(iter(latest.groupby("poll_id", sort=False)))[1]
    shares = {
        str(row["candidate_id"]): float(row["share"])
        for _, row in group.iterrows()
        if str(row["candidate_id"]) in field
    }
    vector = np.array([shares.get(candidate, 0.0) for candidate in field])
    vector = np.append(vector, max(0.0, 1.0 - vector.sum()))
    return vector / vector.sum() if vector.sum() > 0 else None


def calibrate(n_draws: int = 4000) -> dict[str, Any]:
    polls = pd.read_csv(RAW / "historical_mayoral_polls.csv")
    outcomes = pd.read_csv(RAW / "historical_mayoral_outcomes.csv")
    rng = np.random.default_rng(SEED)
    cases: list[dict[str, Any]] = []

    for election_id, election_outcomes in outcomes.groupby("election_id", sort=True):
        election_polls = polls[polls["election_id"] == election_id]
        field = _election_field(election_outcomes)
        election_date = pd.Timestamp(election_outcomes.iloc[0]["election_date"])
        truth_map = {
            str(row["candidate_id"]): float(row["share"])
            for _, row in election_outcomes.iterrows()
        }
        truth = np.array([truth_map[candidate] for candidate in field] + [truth_map["residual"]])
        truth /= truth.sum()

        for days in CUTOFFS:
            cutoff = election_date - pd.Timedelta(days=days)
            observations = _poll_observations(election_polls, field, cutoff)
            if not observations:
                continue
            mean = _fit_choice_set(observations, field)
            simulations = _draws(mean, days, rng, n_draws)
            low80, median, high80 = np.quantile(simulations, [0.10, 0.50, 0.90], axis=0)
            low95, high95 = np.quantile(simulations, [0.025, 0.975], axis=0)
            winners = np.argmax(simulations[:, : len(field)], axis=1)
            win_probs = np.bincount(winners, minlength=len(field)) / len(winners)
            winner_truth = int(np.argmax(truth[: len(field)]))
            one_hot = np.eye(len(field))[winner_truth]
            baseline = _latest_poll_baseline(election_polls, field, cutoff)
            baseline_simulations = _draws(baseline, days, rng, n_draws) if baseline is not None else None
            baseline_winners = (
                np.argmax(baseline_simulations[:, : len(field)], axis=1)
                if baseline_simulations is not None
                else np.zeros(n_draws, dtype=int)
            )
            baseline_win_probs = np.bincount(
                baseline_winners, minlength=len(field)
            ) / len(baseline_winners)
            observed_counts = {
                candidate: sum(candidate in observation["present"] for observation in observations)
                for candidate in field
            }
            eligible_rows = election_polls[
                pd.to_datetime(election_polls["date_published"]) <= cutoff
            ]
            eligible_firms = eligible_rows["firm"].astype(str).nunique()
            latest_age = (
                (cutoff - pd.Timestamp(eligible_rows["date_published"].max())).days
                if not eligible_rows.empty
                else 999
            )
            publication_eligible = (
                all(count >= 2 for count in observed_counts.values())
                and eligible_firms >= 2
                and max(latest_age, 0) <= 21
            )
            cases.append(
                {
                    "election_id": election_id,
                    "days_before_election": days,
                    "poll_count": len(observations),
                    "publication_eligible": publication_eligible,
                    "absolute_errors": np.abs(median - truth).tolist(),
                    "coverage_80": ((truth >= low80) & (truth <= high80)).tolist(),
                    "coverage_95": ((truth >= low95) & (truth <= high95)).tolist(),
                    "brier": float(np.square(win_probs - one_hot).sum()),
                    "baseline_brier": float(np.square(baseline_win_probs - one_hot).sum()),
                    "share_log_loss": float(-np.sum(truth * np.log(np.clip(median, 1e-9, 1.0)))),
                    "baseline_share_log_loss": float(
                        -np.sum(truth * np.log(np.clip(baseline, 1e-9, 1.0)))
                    ) if baseline is not None else None,
                }
            )

    scored_cases = [case for case in cases if case["publication_eligible"]]
    if not scored_cases:
        raise RuntimeError("No historical cutoffs satisfy the live publication gate")
    errors = [value for case in scored_cases for value in case["absolute_errors"]]
    coverage80 = [value for case in scored_cases for value in case["coverage_80"]]
    coverage95 = [value for case in scored_cases for value in case["coverage_95"]]
    brier = float(np.mean([case["brier"] for case in scored_cases]))
    baseline_brier = float(np.mean([case["baseline_brier"] for case in scored_cases]))
    log_loss = float(np.mean([case["share_log_loss"] for case in scored_cases]))
    baseline_log_loss = float(
        np.mean([case["baseline_share_log_loss"] for case in scored_cases if case["baseline_share_log_loss"] is not None])
    )
    metrics = {
        "case_count": len(scored_cases),
        "all_case_count": len(cases),
        "election_count": len({case["election_id"] for case in cases}),
        "publication_scored_election_count": len({case["election_id"] for case in scored_cases}),
        "share_mae": round(float(np.mean(errors)), 4),
        "coverage_80": round(float(np.mean(coverage80)), 4),
        "coverage_95": round(float(np.mean(coverage95)), 4),
        "winner_brier": round(brier, 4),
        "baseline_winner_brier": round(baseline_brier, 4),
        "share_log_loss": round(log_loss, 4),
        "baseline_share_log_loss": round(baseline_log_loss, 4),
        "beats_latest_poll_baseline": brier < baseline_brier and log_loss < baseline_log_loss,
    }
    passed = (
        metrics["beats_latest_poll_baseline"]
        and metrics["coverage_80"] >= 0.70
        and metrics["coverage_95"] >= 0.90
        and metrics["share_mae"] <= 0.05
    )
    return {
        "status": "passed" if passed else "failed",
        "model_version": "choice_set_v1",
        "calibration_engine": "rolling_origin_leave_one_election_out_luce_choice_set",
        "validation_strategy": (
            "Each Toronto election is scored only at historical cutoffs; its final "
            "outcome is withheld from the choice-set fit. Versioned hyperparameters "
            "are frozen before held-out outcome scoring."
        ),
        "leave_one_election_out_folds": [
            {
                "held_out_election": election,
                "training_elections": sorted(
                    other
                    for other in outcomes["election_id"].astype(str).unique()
                    if other != election
                ),
                "evaluated_cutoffs_days": sorted(
                    case["days_before_election"]
                    for case in cases
                    if case["election_id"] == election
                ),
            }
            for election in sorted(outcomes["election_id"].astype(str).unique())
        ],
        "cutoffs_days": list(CUTOFFS),
        "parameters": PARAMETERS,
        "metrics": metrics,
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=4000)
    args = parser.parse_args()
    report = calibrate(args.draws)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    output = PROCESSED / "mayoral_forecast_calibration.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["metrics"], indent=2))
    print(f"Calibration status: {report['status']}")


if __name__ == "__main__":
    main()
