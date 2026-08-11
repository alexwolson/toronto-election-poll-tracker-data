"""Ballot-aware probabilistic forecast for the Toronto mayoral race.

The live model is a dynamic multinomial choice-set model.  Polls contribute
only the candidates they actually offered; obsolete candidates and catch-all
responses are folded into a residual category for the current target field.
Approval data are intentionally absent from this module.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .mayoral import exact_field_polls, field_candidates
from .mayoral_config import (
    ELECTION_DATE,
    FORECAST_MODEL_VERSION,
    RESIDUAL_ID,
    TARGET_FIELD,
)

DEFAULT_SEED = 20260810
DEFAULT_SAMPLE_SIZE = 800
MIN_CURRENT_POLLS = 2
MIN_CURRENT_FIRMS = 2
MAX_CURRENT_POLL_AGE_DAYS = 21
DEFAULT_CALIBRATION = {
    "weekly_sigma": 0.055,
    "house_sigma": 0.075,
    "field_sigma": 0.12,
    "poll_concentration": 140.0,
}


@dataclass(frozen=True)
class ChoiceSetData:
    candidate_ids: tuple[str, ...]
    firms: tuple[str, ...]
    fields: tuple[str, ...]
    n_weeks: int
    observations: tuple[dict[str, Any], ...]
    target_field_index: int
    future_weeks: float


def _week_index(dates: pd.Series, reference: pd.Timestamp) -> tuple[pd.Timestamp, np.ndarray, int]:
    start = dates.min().normalize() - pd.Timedelta(days=int(dates.min().weekday()))
    indices = ((dates - start).dt.days // 7).astype(int).to_numpy()
    n_weeks = int(max(indices.max() + 1, ((reference - start).days // 7) + 1))
    return start, indices, n_weeks


def prepare_choice_set_data(
    polls: pd.DataFrame,
    reference_date: datetime | None = None,
) -> ChoiceSetData:
    if polls.empty:
        raise ValueError("At least one poll is required")
    ref = pd.Timestamp(reference_date or datetime.now(UTC)).normalize()
    ref = ref.tz_localize(UTC) if ref.tzinfo is None else ref.tz_convert(UTC)
    dates = pd.to_datetime(polls["date_published"], utc=True, errors="coerce")
    valid = dates.notna() & (dates <= ref)
    frame = polls[valid].copy().reset_index(drop=True)
    dates = dates[valid].reset_index(drop=True)
    if frame.empty:
        raise ValueError("No polls are available on or before the reference date")

    _, week_indices, n_weeks = _week_index(dates, ref)
    firms = tuple(sorted(frame["firm"].fillna("Unknown").astype(str).unique()))
    firm_index = {firm: index for index, firm in enumerate(firms)}

    signatures = []
    prepared: list[dict[str, Any]] = []
    for row_index, row in frame.iterrows():
        offered = field_candidates(row.get("field_tested"))
        present = [candidate for candidate in TARGET_FIELD if candidate in offered]
        if not present:
            continue
        # Preserve the full original ballot in the field effect. Candidates
        # outside today's target field are represented inside residual support,
        # but a crowded ballot must not be conflated with a true head-to-head.
        signature = "|".join(sorted(offered))
        signatures.append(signature)
        shares = []
        indices = []
        for candidate_index, candidate in enumerate(TARGET_FIELD):
            if candidate not in present:
                continue
            value = pd.to_numeric(row.get(candidate), errors="coerce")
            if pd.isna(value):
                continue
            shares.append(float(value))
            indices.append(candidate_index)
        residual = max(0.0, 1.0 - sum(shares))
        shares.append(residual)

        sample_size = pd.to_numeric(row.get("sample_size"), errors="coerce")
        n = int(sample_size) if pd.notna(sample_size) and sample_size > 0 else DEFAULT_SAMPLE_SIZE
        counts = [int(round(n * share)) for share in shares[:-1]]
        counts.append(max(0, n - sum(counts)))
        firm = str(row.get("firm")) if pd.notna(row.get("firm")) else "Unknown"
        prepared.append(
            {
                "poll_id": str(row.get("poll_id", row_index)),
                "week": int(week_indices[row_index]),
                "firm": firm_index[firm],
                "signature": signature,
                "candidate_indices": tuple(indices),
                "counts": tuple(counts),
                "sample_size": n,
            }
        )

    target_signature = "|".join(sorted(TARGET_FIELD))
    fields = tuple(sorted(set(signatures) | {target_signature}))
    field_index = {field: index for index, field in enumerate(fields)}
    observations = tuple(
        {**observation, "field": field_index[observation.pop("signature")]}
        for observation in prepared
    )
    election = pd.Timestamp(ELECTION_DATE, tz=UTC)
    future_weeks = max(0.0, (election - ref).total_seconds() / (7 * 86400))
    return ChoiceSetData(
        candidate_ids=tuple(TARGET_FIELD),
        firms=firms,
        fields=fields,
        n_weeks=n_weeks,
        observations=observations,
        target_field_index=field_index[target_signature],
        future_weeks=future_weeks,
    )


def _calibration_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "processed" / "mayoral_forecast_calibration.json"


def load_calibration(path: Path | None = None) -> dict[str, Any]:
    target = path or _calibration_path()
    if not target.exists():
        return {"status": "missing", "parameters": DEFAULT_CALIBRATION, "metrics": {}}
    data = json.loads(target.read_text(encoding="utf-8"))
    parameters = {**DEFAULT_CALIBRATION, **data.get("parameters", {})}
    return {**data, "parameters": parameters}


def forecast_data_gate(
    polls: pd.DataFrame,
    reference_date: datetime | None = None,
) -> list[str]:
    ref = pd.Timestamp(reference_date or datetime.now(UTC)).normalize()
    ref = ref.tz_localize(UTC) if ref.tzinfo is None else ref.tz_convert(UTC)
    current = exact_field_polls(polls, TARGET_FIELD)
    reasons: list[str] = []
    if len(current) < MIN_CURRENT_POLLS:
        reasons.append("At least two current-field polls are required.")
    if current.get("firm", pd.Series(dtype=str)).astype(str).nunique() < MIN_CURRENT_FIRMS:
        reasons.append("Current-field polls must come from at least two firms.")
    for candidate in TARGET_FIELD:
        observations = pd.to_numeric(current.get(candidate), errors="coerce").notna().sum()
        if int(observations) < 2:
            reasons.append(f"{candidate} must be measured in at least two current-field polls.")
    if not current.empty:
        latest = pd.to_datetime(current["date_published"], utc=True, errors="coerce").max()
        if pd.isna(latest) or int((ref - latest).days) > MAX_CURRENT_POLL_AGE_DAYS:
            reasons.append("The latest current-field poll is more than 21 days old.")
    return reasons


def _run_numpyro(
    data: ChoiceSetData,
    parameters: dict[str, float],
    seed: int,
    warmup: int,
    samples: int,
    chains: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    import jax.numpy as jnp
    from jax import random
    import numpyro
    import numpyro.distributions as dist
    from numpyro.diagnostics import summary
    from numpyro.infer import MCMC, NUTS

    weekly_sigma = float(parameters["weekly_sigma"])
    house_sigma = float(parameters["house_sigma"])
    field_sigma = float(parameters["field_sigma"])
    poll_concentration = float(parameters["poll_concentration"])
    n_candidates = len(data.candidate_ids)

    def model() -> None:
        initial = numpyro.sample(
            "initial_utility", dist.Normal(0.0, 1.0).expand([n_candidates])
        )
        if data.n_weeks > 1:
            innovations = numpyro.sample(
                "weekly_innovations",
                dist.Normal(0.0, weekly_sigma).expand([data.n_weeks - 1, n_candidates]),
            )
            states = jnp.concatenate(
                [initial[jnp.newaxis, :], initial[jnp.newaxis, :] + jnp.cumsum(innovations, axis=0)],
                axis=0,
            )
        else:
            states = initial[jnp.newaxis, :]

        house_raw = numpyro.sample(
            "house_raw", dist.Normal(0.0, house_sigma).expand([len(data.firms), n_candidates])
        )
        house = house_raw - jnp.mean(house_raw, axis=0, keepdims=True)
        field_raw = numpyro.sample(
            "field_raw", dist.Normal(0.0, field_sigma).expand([len(data.fields), n_candidates])
        )
        field = field_raw - jnp.mean(field_raw, axis=0, keepdims=True)

        for index, observation in enumerate(data.observations):
            candidate_indices = jnp.array(observation["candidate_indices"], dtype=jnp.int32)
            logits = states[observation["week"], candidate_indices]
            logits = logits + house[observation["firm"], candidate_indices]
            logits = logits + field[observation["field"], candidate_indices]
            logits = jnp.concatenate([logits, jnp.zeros(1)])
            probabilities = jnp.exp(logits - jnp.max(logits))
            probabilities = probabilities / probabilities.sum()
            concentration = jnp.clip(probabilities * poll_concentration, 1e-3)
            numpyro.sample(
                f"poll_{index}",
                dist.DirichletMultinomial(
                    concentration=concentration,
                    total_count=observation["sample_size"],
                ),
                obs=jnp.array(observation["counts"], dtype=jnp.int32),
            )

        future_scale = weekly_sigma * math.sqrt(max(data.future_weeks, 1e-6))
        drift = numpyro.sample(
            "election_drift", dist.Normal(0.0, future_scale).expand([n_candidates])
        )
        election_logits = states[-1] + field[data.target_field_index] + drift
        election_logits = jnp.concatenate([election_logits, jnp.zeros(1)])
        election_probs = jnp.exp(election_logits - jnp.max(election_logits))
        numpyro.deterministic("election_probabilities", election_probs / election_probs.sum())

    numpyro.set_host_device_count(chains)
    mcmc = MCMC(
        NUTS(model, target_accept_prob=0.9),
        num_warmup=warmup,
        num_samples=samples,
        num_chains=chains,
        chain_method="sequential",
        progress_bar=False,
    )
    mcmc.run(random.PRNGKey(seed))
    chain_samples = mcmc.get_samples(group_by_chain=True)
    probabilities = np.asarray(chain_samples["election_probabilities"]).reshape(
        -1, n_candidates + 1
    )
    stats = summary(
        {"election_probabilities": chain_samples["election_probabilities"]},
        group_by_chain=True,
    )
    rhats = [
        float(item)
        for value in stats.values()
        for item in np.asarray(value["r_hat"]).reshape(-1)
    ]
    effective = [
        float(item)
        for value in stats.values()
        for item in np.asarray(value["n_eff"]).reshape(-1)
    ]
    divergences = int(np.asarray(mcmc.get_extra_fields(group_by_chain=True)["diverging"]).sum())
    return probabilities, {
        "r_hat_max": round(max(rhats), 4),
        "bulk_ess_min": round(min(effective), 1),
        "divergences": divergences,
        "draw_count": int(probabilities.shape[0]),
    }


def conservative_current_field_draws(
    polls: pd.DataFrame,
    reference_date: datetime | None = None,
    n_draws: int = 5000,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Wide fallback draws for Council when the public forecast is unavailable."""
    current = exact_field_polls(polls, TARGET_FIELD)
    if current.empty:
        return np.empty((0, len(TARGET_FIELD) + 1))
    ref = pd.Timestamp(reference_date or datetime.now(UTC)).normalize()
    ref = ref.tz_localize(UTC) if ref.tzinfo is None else ref.tz_convert(UTC)
    dates = pd.to_datetime(current["date_published"], utc=True)
    weights = 0.5 ** (((ref - dates).dt.total_seconds() / 86400.0).clip(lower=0) / 12.0)
    shares = np.array(
        [
            float((pd.to_numeric(current[candidate]) * weights).sum() / weights.sum())
            for candidate in TARGET_FIELD
        ]
    )
    mean = np.append(shares, max(0.001, 1.0 - float(shares.sum())))
    mean = mean / mean.sum()
    rng = np.random.default_rng(seed)
    # A deliberately low concentration reflects firm, field, and campaign risk.
    return rng.dirichlet(mean * 70.0, size=n_draws)


def _sensitivity(probabilities: np.ndarray, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed + 17)
    named = probabilities[:, : len(TARGET_FIELD)]
    base_winner = np.argmax(named, axis=1)
    base = np.bincount(base_winner, minlength=len(TARGET_FIELD)) / len(named)
    scenarios = {"base": base}
    for name, sigma in (
        ("field_effect", 0.035),
        ("house_error", 0.065),
        ("campaign_drift", 0.11),
    ):
        logits = np.log(np.clip(probabilities, 1e-8, 1.0))
        noise = rng.normal(0.0, sigma, size=logits.shape)
        perturbed = np.exp(logits + noise)
        perturbed /= perturbed.sum(axis=1, keepdims=True)
        winners = np.argmax(perturbed[:, : len(TARGET_FIELD)], axis=1)
        scenarios[name] = np.bincount(winners, minlength=len(TARGET_FIELD)) / len(winners)
    leaders = {int(np.argmax(values)) for values in scenarios.values()}
    leader = int(np.argmax(base))
    leader_values = [float(values[leader]) for values in scenarios.values()]
    return {
        "leader_stable": len(leaders) == 1,
        "leader_probability_swing": round(max(leader_values) - min(leader_values), 4),
        "scenarios": {
            key: {candidate: round(float(values[index]), 4) for index, candidate in enumerate(TARGET_FIELD)}
            for key, values in scenarios.items()
        },
    }


def _backtest_gate(calibration: dict[str, Any]) -> list[str]:
    if calibration.get("status") != "passed":
        return ["Historical Toronto backtest calibration is not available."]
    metrics = calibration.get("metrics", {})
    checks = (
        (metrics.get("beats_latest_poll_baseline") is True, "Backtests do not beat the latest-poll baseline."),
        (float(metrics.get("coverage_80", 0.0)) >= 0.70, "Historical 80% interval coverage is below 70%."),
        (float(metrics.get("coverage_95", 0.0)) >= 0.90, "Historical 95% interval coverage is below 90%."),
        (float(metrics.get("share_mae", 1.0)) <= 0.05, "Historical share MAE exceeds five points."),
    )
    return [message for passed, message in checks if not passed]


def build_forecast(
    polls: pd.DataFrame,
    reference_date: datetime | None = None,
    calibration_path: Path | None = None,
    *,
    seed: int = DEFAULT_SEED,
    warmup: int = 500,
    samples: int = 750,
    chains: int = 4,
) -> tuple[dict[str, Any], np.ndarray]:
    calibration = load_calibration(calibration_path)
    published = pd.to_datetime(polls.get("date_published"), errors="coerce")
    data_cutoff = (
        published.max().date().isoformat()
        if not published.empty and pd.notna(published.max())
        else None
    )
    reasons = forecast_data_gate(polls, reference_date) + _backtest_gate(calibration)
    fallback = conservative_current_field_draws(polls, reference_date, seed=seed)
    base = {
        "status": "insufficient_data" if reasons else "error",
        "unavailable_reasons": reasons,
        "model_version": FORECAST_MODEL_VERSION,
        "election_date": ELECTION_DATE,
        "data_cutoff": data_cutoff,
        "candidates": {},
        "residual": None,
        "diagnostics": {
            "backtest": calibration.get("metrics", {}),
            "data_gate_passed": not forecast_data_gate(polls, reference_date),
        },
    }
    if reasons:
        return base, fallback

    try:
        data = prepare_choice_set_data(polls, reference_date)
        probabilities, convergence = _run_numpyro(
            data,
            calibration["parameters"],
            seed,
            warmup,
            samples,
            chains,
        )
    except Exception as exc:
        return {
            **base,
            "status": "error",
            "unavailable_reasons": [f"Forecast sampling failed: {type(exc).__name__}."],
        }, fallback

    sensitivity = _sensitivity(probabilities, seed)
    diagnostic_reasons = []
    if convergence["divergences"] != 0:
        diagnostic_reasons.append("Forecast sampling produced divergent draws.")
    if convergence["r_hat_max"] > 1.01:
        diagnostic_reasons.append("Forecast R-hat exceeds 1.01.")
    if convergence["bulk_ess_min"] < 400:
        diagnostic_reasons.append("Forecast effective sample size is below 400.")
    if not sensitivity["leader_stable"]:
        diagnostic_reasons.append("The projected leader changes in sensitivity testing.")
    if sensitivity["leader_probability_swing"] > 0.15:
        diagnostic_reasons.append("Leader win probability moves more than 15 points in sensitivity testing.")
    if diagnostic_reasons:
        return {
            **base,
            "status": "unstable",
            "unavailable_reasons": diagnostic_reasons,
            "diagnostics": {
                "backtest": calibration.get("metrics", {}),
                "convergence": convergence,
                "sensitivity": sensitivity,
                "data_gate_passed": True,
            },
        }, probabilities

    named = probabilities[:, : len(TARGET_FIELD)]
    winners = np.argmax(named, axis=1)
    candidate_output: dict[str, Any] = {}
    for index, candidate in enumerate(TARGET_FIELD):
        low, median, high = np.quantile(probabilities[:, index], [0.10, 0.50, 0.90])
        candidate_output[candidate] = {
            "projected_share": {
                "median": round(float(median), 4),
                "low": round(float(low), 4),
                "high": round(float(high), 4),
            },
            "win_probability": round(float((winners == index).mean()), 4),
        }
    residual_low, residual_median, residual_high = np.quantile(
        probabilities[:, -1], [0.10, 0.50, 0.90]
    )
    return {
        "status": "available",
        "unavailable_reasons": [],
        "model_version": FORECAST_MODEL_VERSION,
        "election_date": ELECTION_DATE,
        "data_cutoff": data_cutoff,
        "candidates": candidate_output,
        "residual": {
            "id": RESIDUAL_ID,
            "median": round(float(residual_median), 4),
            "low": round(float(residual_low), 4),
            "high": round(float(residual_high), 4),
        },
        "diagnostics": {
            "backtest": calibration.get("metrics", {}),
            "convergence": convergence,
            "sensitivity": sensitivity,
            "data_gate_passed": True,
            "poll_count": len(data.observations),
            "firm_count": len(data.firms),
            "field_count": len(data.fields),
        },
    }, probabilities
