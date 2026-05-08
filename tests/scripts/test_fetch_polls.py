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


def test_parse_share_integer_percent(fp):
    assert fp._parse_share("35%") == pytest.approx(0.35)


def test_parse_share_em_dash(fp):
    assert fp._parse_share("—") is None


def test_parse_share_en_dash(fp):
    assert fp._parse_share("–") is None


def test_parse_share_empty(fp):
    assert fp._parse_share("") is None


def test_parse_share_small_value(fp):
    assert fp._parse_share("8%") == pytest.approx(0.08)


from bs4 import BeautifulSoup


def test_firm_slug_known(fp):
    assert fp._firm_slug("Liaison Strategies") == "liaison"


def test_firm_slug_variant(fp):
    assert fp._firm_slug("Pallas") == "pallas"


def test_firm_slug_unknown(fp):
    with pytest.raises(ValueError, match="Unknown polling firm"):
        fp._firm_slug("Mystery Pollsters Inc.")


def test_candidate_col_names_maps_known(fp):
    headers = ["Polling Firm", "Methodology", "Poll Date", "Sample Size", "MOE",
               "Bradford", "Chow", "Lead"]
    result = fp._candidate_col_names(headers)
    assert result == {"Bradford": "bradford", "Chow": "chow"}


def test_candidate_col_names_skips_metadata(fp):
    headers = ["Polling Firm", "Poll Date", "MOE", "Lead"]
    assert fp._candidate_col_names(headers) == {}


def _make_table(headers: list[str]) -> "BeautifulSoup":
    ths = "".join(f"<th>{h}</th>" for h in headers)
    html = f"<table class='wikitable'><tbody><tr>{ths}</tr></tbody></table>"
    return BeautifulSoup(html, "lxml").find("table")


def test_is_polling_table_true(fp):
    table = _make_table(["Polling Firm", "Methodology", "Poll Date", "Sample Size"])
    assert fp._is_polling_table(table) is True


def test_is_polling_table_false_missing_poll_date(fp):
    table = _make_table(["Polling Firm", "Methodology", "Sample Size"])
    assert fp._is_polling_table(table) is False


def test_is_polling_table_false_non_polling(fp):
    table = _make_table(["Candidate", "Party", "Status"])
    assert fp._is_polling_table(table) is False
