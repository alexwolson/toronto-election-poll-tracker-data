# tests/model/test_candidates.py
"""Tests for candidates.py build_candidate_status function."""
from __future__ import annotations

from backend.model.candidates import build_candidate_status


BRADFORD_RECORD = {
    "first_name": "Brad",
    "last_name": "Bradford",
    "status": "Active",
    "date_nomination": "2026-05-01",
}
UNKNOWN_RECORD = {
    "first_name": "Jane",
    "last_name": "Doe",
    "status": "Active",
    "date_nomination": "2026-05-01",
}
WITHDRAWN_RECORD = {
    "first_name": "Someone",
    "last_name": "Withdrawn",
    "status": "Withdrawn",
    "date_nomination": "2026-05-01",
}


def test_build_candidate_status_empty_records_returns_empty_declared():
    result = build_candidate_status([])
    assert result["declared"] == []


def test_build_candidate_status_known_candidate_uses_editorial_id():
    result = build_candidate_status([BRADFORD_RECORD])
    assert len(result["declared"]) == 1
    assert result["declared"][0]["id"] == "bradford"


def test_build_candidate_status_known_candidate_uses_editorial_summary():
    result = build_candidate_status([BRADFORD_RECORD])
    assert result["declared"][0]["summary"] != ""


def test_build_candidate_status_unknown_candidate_generates_id():
    result = build_candidate_status([UNKNOWN_RECORD])
    assert len(result["declared"]) == 1
    assert result["declared"][0]["id"] == "doe"


def test_build_candidate_status_unknown_candidate_empty_summary():
    result = build_candidate_status([UNKNOWN_RECORD])
    assert result["declared"][0]["summary"] == ""


def test_build_candidate_status_filters_non_active():
    result = build_candidate_status([BRADFORD_RECORD, WITHDRAWN_RECORD])
    assert len(result["declared"]) == 1
    assert result["declared"][0]["id"] == "bradford"


def test_build_candidate_status_preserves_potential_and_declined():
    result = build_candidate_status([])
    assert len(result["potential"]) > 0
    assert len(result["declined"]) > 0
    assert any(c["id"] == "chow" for c in result["potential"])


def test_build_candidate_status_unknown_candidate_full_name():
    result = build_candidate_status([UNKNOWN_RECORD])
    assert result["declared"][0]["name"] == "Jane Doe"


def test_build_candidate_status_declared_has_required_keys():
    result = build_candidate_status([BRADFORD_RECORD])
    assert set(result["declared"][0].keys()) >= {"id", "name", "summary"}
