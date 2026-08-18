"""Unit tests for historical mayoral poll parsing helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def historical_fetcher():
    script = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "fetch_historical_mayoral_polls.py"
    )
    spec = importlib.util.spec_from_file_location(
        "scripts.fetch_historical_mayoral_polls", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("April 29-May 2, 2023", "2023-05-02"),
        ("April 29 - May 2, 2023", "2023-05-02"),
        ("May 10-11, 2026", "2026-05-11"),
        ("June 23, 2023", "2023-06-23"),
    ],
)
def test_date_uses_end_of_fieldwork_range(historical_fetcher, raw, expected):
    assert historical_fetcher._date(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,007", 1007),
        ("1,007.0", 1007),
        ("780", 780),
        (780.0, 780),
        ("—", None),
    ],
)
def test_sample_size_preserves_thousands_separator(
    historical_fetcher, raw, expected
):
    assert historical_fetcher._sample(raw) == expected
