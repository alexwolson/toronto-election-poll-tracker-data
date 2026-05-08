"""Tests for fetch_polls.py parsing logic."""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def fp():
    path = _REPO_ROOT / "scripts" / "fetch_polls.py"
    spec = importlib.util.spec_from_file_location("scripts.fetch_polls", str(path))
    assert spec is not None, f"Could not load fetch_polls.py — expected at {path}"
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_parse_date_april(fp):
    assert fp._parse_date("April 13, 2026") == "2026-04-13"


def test_parse_date_march(fp):
    assert fp._parse_date("March 8, 2026") == "2026-03-08"


def test_parse_date_invalid(fp):
    with pytest.raises(ValueError, match="Unparseable poll date"):
        fp._parse_date("not-a-date")


def test_parse_share_percentage(fp):
    assert fp._parse_share("46%") == pytest.approx(0.46)


def test_parse_share_bold_stripped(fp):
    assert fp._parse_share("35%") == pytest.approx(0.35)


def test_parse_share_em_dash(fp):
    assert fp._parse_share("—") is None


def test_parse_share_empty(fp):
    assert fp._parse_share("") is None


def test_parse_share_small_value(fp):
    assert fp._parse_share("8%") == pytest.approx(0.08)
