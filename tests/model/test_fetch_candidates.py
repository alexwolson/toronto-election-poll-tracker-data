# tests/model/test_fetch_candidates.py
"""Tests for fetch_candidates.py parsing logic."""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def fc():
    return _load_module()


def _load_module():
    path = _REPO_ROOT / "scripts" / "fetch_candidates.py"
    spec = importlib.util.spec_from_file_location("scripts.fetch_candidates", str(path))
    assert spec is not None, f"Could not load fetch_candidates.py — expected at {path}"
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


MOCK_MAYOR_RESPONSE = {
    "seq": "1777763280544",
    "spaces": " ",
    "candidates": [
        {
            "name": "Bradford, Brad",
            "firstName": "Brad",
            "lastName": "Bradford",
            "dateNomination": "01-May-2026",
            "office": 1,
            "status": "Active",
            "email": "",
            "phone": None,
            "socialMedias": [],
        },
        {
            "name": "Sanders, Lyall",
            "firstName": "Lyall",
            "lastName": "Sanders",
            "dateNomination": "01-May-2026",
            "office": 1,
            "status": "Active",
            "email": "",
            "phone": None,
            "socialMedias": [],
        },
    ],
}

MOCK_COUNCILLOR_RESPONSE = {
    "seq": "1777763280544",
    "spaces": " ",
    "ward": [
        {
            "name": "Name:1",
            "num": 1,
            "n": 1,
            "candidate": [
                {
                    "name": "Perks, Gord",
                    "firstName": "Gord",
                    "lastName": "Perks",
                    "dateNomination": "01-May-2026",
                    "office": 2,
                    "status": "Active",
                    "email": "",
                    "phone": None,
                    "socialMedias": [],
                }
            ],
        },
        {
            "name": "Name:2",
            "num": 2,
            "n": 2,
            "candidate": [
                {
                    "name": "Layton, Mike",
                    "firstName": "Mike",
                    "lastName": "Layton",
                    "dateNomination": "01-May-2026",
                    "office": 2,
                    "status": "Active",
                    "email": "",
                    "phone": None,
                    "socialMedias": [],
                }
            ],
        },
    ],
}


def test_parse_date_standard(fc):
    assert fc._parse_date("01-May-2026") == "2026-05-01"


def test_parse_date_other_month(fc):
    assert fc._parse_date("15-Oct-2026") == "2026-10-15"


def test_parse_mayor_response_returns_correct_fields(fc):
    records = fc._parse_mayor_response(MOCK_MAYOR_RESPONSE)
    assert len(records) == 2
    assert records[0] == {
        "first_name": "Brad",
        "last_name": "Bradford",
        "status": "Active",
        "date_nomination": "2026-05-01",
    }


def test_parse_mayor_response_all_candidates(fc):
    records = fc._parse_mayor_response(MOCK_MAYOR_RESPONSE)
    last_names = [r["last_name"] for r in records]
    assert "Bradford" in last_names
    assert "Sanders" in last_names


def test_parse_councillor_response_includes_ward(fc):
    records = fc._parse_councillor_response(MOCK_COUNCILLOR_RESPONSE)
    assert len(records) == 2
    assert records[0] == {
        "ward": 1,
        "first_name": "Gord",
        "last_name": "Perks",
        "status": "Active",
        "date_nomination": "2026-05-01",
    }


def test_parse_councillor_response_ward_is_int(fc):
    records = fc._parse_councillor_response(MOCK_COUNCILLOR_RESPONSE)
    for r in records:
        assert isinstance(r["ward"], int)


def test_fetch_candidates_imports_cleanly():
    """Module-level imports must not crash."""
    _load_module()
