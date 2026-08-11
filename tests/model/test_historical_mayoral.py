"""Validation for sourced Toronto mayoral calibration data."""

import pandas as pd
import pytest


def test_historical_poll_view_is_long_form_and_sourced() -> None:
    polls = pd.read_csv("data/raw/polls/historical_mayoral_polls.csv")
    required = {
        "election_id", "election_date", "poll_id", "firm", "date_published",
        "sample_size", "field_tested", "source_url", "candidate_id", "share",
        "is_residual",
    }
    assert required.issubset(polls.columns)
    assert set(polls["election_id"].unique()) == {
        "toronto_2014", "toronto_2018", "toronto_2022", "toronto_2023"
    }
    assert polls["source_url"].str.startswith("https://").all()
    assert polls["share"].between(0.0, 1.0).all()
    assert polls.groupby("poll_id")["share"].sum().between(0.99, 1.01).all()


def test_historical_outcomes_cover_each_election_and_residual() -> None:
    outcomes = pd.read_csv("data/raw/polls/historical_mayoral_outcomes.csv")
    assert outcomes.groupby("election_id")["is_residual"].any().all()
    for _, group in outcomes.groupby("election_id"):
        assert group["share"].sum() == pytest.approx(1.0, abs=0.001)

