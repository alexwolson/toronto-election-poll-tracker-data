"""Contract and invariants for the ballot-aware mayoral forecast."""

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from backend.model import forecast as forecast_module
from backend.model.forecast import (
    _backtest_gate,
    build_forecast,
    conservative_current_field_draws,
    prepare_choice_set_data,
    load_calibration,
)
from backend.model.mayoral_config import TARGET_FIELD


def _polls() -> pd.DataFrame:
    return pd.read_csv("data/processed/polls.csv")


def test_choice_sets_omit_absent_candidates_instead_of_treating_them_as_zero() -> None:
    data = prepare_choice_set_data(_polls(), datetime(2026, 8, 10, tzinfo=UTC))
    head_to_head_field = data.fields.index("bradford|chow")
    head_to_head = [observation for observation in data.observations if observation["field"] == head_to_head_field]
    current = [observation for observation in data.observations if len(observation["candidate_indices"]) == 3]
    assert len(head_to_head) == 7
    assert len(current) == 2
    assert all(2 not in observation["candidate_indices"] for observation in head_to_head)
    assert all(sum(observation["counts"]) == observation["sample_size"] for observation in data.observations)
    crowded_tory_fields = [field for field in data.fields if "tory" in field and "bradford" in field and "chow" in field]
    assert crowded_tory_fields
    assert all(data.fields.index(field) != head_to_head_field for field in crowded_tory_fields)


def test_conservative_draws_preserve_residual_and_reproduce_from_seed() -> None:
    first = conservative_current_field_draws(_polls(), n_draws=100, seed=23)
    second = conservative_current_field_draws(_polls(), n_draws=100, seed=23)
    assert np.allclose(first, second)
    assert first.shape == (100, len(TARGET_FIELD) + 1)
    assert np.allclose(first.sum(axis=1), 1.0)
    assert np.all(first[:, -1] > 0.0)


def test_historical_backtest_gate_enforces_all_thresholds() -> None:
    passed = {
        "status": "passed",
        "metrics": {
            "beats_latest_poll_baseline": True,
            "coverage_80": 0.70,
            "coverage_95": 0.90,
            "share_mae": 0.05,
        },
    }
    assert _backtest_gate(passed) == []
    failed = {**passed, "metrics": {**passed["metrics"], "coverage_95": 0.89}}
    assert _backtest_gate(failed) == ["Historical 95% interval coverage is below 90%."]


def test_calibration_artifact_has_four_leave_one_election_out_folds() -> None:
    calibration = load_calibration()
    folds = calibration["leave_one_election_out_folds"]
    assert calibration["status"] == "passed"
    assert len(folds) == 4
    assert all(fold["held_out_election"] not in fold["training_elections"] for fold in folds)


def test_public_forecast_uses_named_winners_but_keeps_residual(monkeypatch: pytest.MonkeyPatch) -> None:
    draws = np.array(
        [
            [0.40, 0.30, 0.10, 0.20],
            [0.30, 0.32, 0.08, 0.30],
            [0.20, 0.15, 0.10, 0.55],
        ]
        * 200
    )
    monkeypatch.setattr(
        forecast_module,
        "_run_numpyro",
        lambda *args, **kwargs: (
            draws,
            {"r_hat_max": 1.001, "bulk_ess_min": 800.0, "divergences": 0, "draw_count": len(draws)},
        ),
    )
    monkeypatch.setattr(
        forecast_module,
        "_sensitivity",
        lambda *args, **kwargs: {"leader_stable": True, "leader_probability_swing": 0.01, "scenarios": {}},
    )
    result, returned = build_forecast(_polls())
    assert result["status"] == "available"
    assert result["residual"]["median"] > 0.0
    assert sum(candidate["win_probability"] for candidate in result["candidates"].values()) == pytest.approx(1.0)
    assert np.array_equal(returned, draws)


def test_failed_convergence_suppresses_public_odds(monkeypatch: pytest.MonkeyPatch) -> None:
    draws = conservative_current_field_draws(_polls(), n_draws=500)
    monkeypatch.setattr(
        forecast_module,
        "_run_numpyro",
        lambda *args, **kwargs: (
            draws,
            {"r_hat_max": 1.02, "bulk_ess_min": 399.0, "divergences": 1, "draw_count": len(draws)},
        ),
    )
    result, _ = build_forecast(_polls())
    assert result["status"] == "unstable"
    assert result["candidates"] == {}
    assert len(result["unavailable_reasons"]) >= 3
