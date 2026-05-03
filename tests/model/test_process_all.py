"""Tests for process_all.py import correctness."""
import importlib
import importlib.util
import pathlib
import sys

import pandas as pd

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


def test_process_all_imports_cleanly():
    """process_all must import without ModuleNotFoundError.

    This catches the src.* → backend.model.* migration bug.
    """
    # Remove any cached version so we get a fresh import
    for key in list(sys.modules.keys()):
        if "process_all" in key:
            del sys.modules[key]

    spec = importlib.util.spec_from_file_location(
        "scripts.process_all",
        str(_REPO_ROOT / "scripts" / "process_all.py"),
    )
    assert spec is not None, "Could not locate scripts/process_all.py — check _REPO_ROOT path"

    module = importlib.util.module_from_spec(spec)
    # We only test that the module-level code (imports, constants) doesn't crash.
    # We don't call main() since that requires data files.
    try:
        spec.loader.exec_module(module)
    except SystemExit:
        pass  # main() calls sys.exit on missing files — that's fine

    assert module is not None
    # Verify the key backend.model symbols are importable — this is the actual bug we're guarding
    from backend.model import aggregator, coattails, lean, names, validate  # noqa: F401


def _load_process_all():
    spec = importlib.util.spec_from_file_location(
        "scripts.process_all",
        str(_REPO_ROOT / "scripts" / "process_all.py"),
    )
    assert spec is not None, "Could not locate scripts/process_all.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# process_challengers_merged
# ---------------------------------------------------------------------------

def _defeatability_df(ward: int, councillor_name: str, is_running: bool = True) -> pd.DataFrame:
    return pd.DataFrame([{
        "ward": ward,
        "councillor_name": councillor_name,
        "is_running": is_running,
        "election_year": 2022,
        "is_byelection_incumbent": False,
        "vote_share": 0.5,
        "electorate_share": 0.5,
        "defeatability_score": 40,
        "notes": "",
        "last_updated": "2024-01-01",
        "pop_growth_pct": 0.0,
    }])


def test_process_challengers_merged_empty_api_returns_empty(tmp_path):
    pa = _load_process_all()
    councillor_path = tmp_path / "councillor_registered.csv"
    pd.DataFrame(columns=["ward", "first_name", "last_name", "status", "date_nomination"]).to_csv(councillor_path, index=False)
    editorial_path = tmp_path / "challengers.csv"
    pd.DataFrame(columns=["ward", "candidate_name", "name_recognition_tier", "fundraising_tier", "mayoral_alignment", "is_endorsed_by_departing", "notes", "last_updated"]).to_csv(editorial_path, index=False)
    defeatability = _defeatability_df(1, "Some Incumbent")
    result = pa.process_challengers_merged(councillor_path, editorial_path, defeatability)
    assert result.empty


def test_process_challengers_merged_incumbent_is_excluded(tmp_path):
    pa = _load_process_all()
    councillor_path = tmp_path / "councillor_registered.csv"
    pd.DataFrame([
        {"ward": 1, "first_name": "Some", "last_name": "Incumbent", "status": "Active", "date_nomination": "2026-05-01"},
        {"ward": 1, "first_name": "Real", "last_name": "Challenger", "status": "Active", "date_nomination": "2026-05-01"},
    ]).to_csv(councillor_path, index=False)
    editorial_path = tmp_path / "challengers.csv"
    pd.DataFrame(columns=["ward", "candidate_name", "name_recognition_tier", "fundraising_tier", "mayoral_alignment", "is_endorsed_by_departing", "notes", "last_updated"]).to_csv(editorial_path, index=False)
    defeatability = _defeatability_df(1, "Some Incumbent", is_running=True)
    result = pa.process_challengers_merged(councillor_path, editorial_path, defeatability)
    assert len(result) == 1
    assert result.iloc[0]["candidate_name"] == "Real Challenger"


def test_process_challengers_merged_open_seat_includes_all(tmp_path):
    pa = _load_process_all()
    councillor_path = tmp_path / "councillor_registered.csv"
    pd.DataFrame([
        {"ward": 1, "first_name": "Some", "last_name": "Incumbent", "status": "Active", "date_nomination": "2026-05-01"},
        {"ward": 1, "first_name": "Real", "last_name": "Challenger", "status": "Active", "date_nomination": "2026-05-01"},
    ]).to_csv(councillor_path, index=False)
    editorial_path = tmp_path / "challengers.csv"
    pd.DataFrame(columns=["ward", "candidate_name", "name_recognition_tier", "fundraising_tier", "mayoral_alignment", "is_endorsed_by_departing", "notes", "last_updated"]).to_csv(editorial_path, index=False)
    defeatability = _defeatability_df(1, "Some Incumbent", is_running=False)
    result = pa.process_challengers_merged(councillor_path, editorial_path, defeatability)
    assert len(result) == 2


def test_process_challengers_merged_editorial_overlay_applied(tmp_path):
    pa = _load_process_all()
    councillor_path = tmp_path / "councillor_registered.csv"
    pd.DataFrame([
        {"ward": 5, "first_name": "Jane", "last_name": "Doe", "status": "Active", "date_nomination": "2026-05-01"},
    ]).to_csv(councillor_path, index=False)
    editorial_path = tmp_path / "challengers.csv"
    pd.DataFrame([{
        "ward": 5,
        "candidate_name": "Jane Doe",
        "name_recognition_tier": "well-known",
        "fundraising_tier": "high",
        "mayoral_alignment": "pro-chow",
        "is_endorsed_by_departing": True,
        "notes": "well funded",
        "last_updated": "2026-05-01",
    }]).to_csv(editorial_path, index=False)
    defeatability = _defeatability_df(5, "Other Person", is_running=True)
    result = pa.process_challengers_merged(councillor_path, editorial_path, defeatability)
    assert len(result) == 1
    assert result.iloc[0]["name_recognition_tier"] == "well-known"
    assert result.iloc[0]["fundraising_tier"] == "high"
    assert bool(result.iloc[0]["is_endorsed_by_departing"]) is True


def test_process_challengers_merged_defaults_for_unmatched(tmp_path):
    pa = _load_process_all()
    councillor_path = tmp_path / "councillor_registered.csv"
    pd.DataFrame([
        {"ward": 7, "first_name": "New", "last_name": "Person", "status": "Active", "date_nomination": "2026-05-01"},
    ]).to_csv(councillor_path, index=False)
    editorial_path = tmp_path / "challengers.csv"
    pd.DataFrame(columns=["ward", "candidate_name", "name_recognition_tier", "fundraising_tier", "mayoral_alignment", "is_endorsed_by_departing", "notes", "last_updated"]).to_csv(editorial_path, index=False)
    defeatability = _defeatability_df(7, "Someone Else", is_running=True)
    result = pa.process_challengers_merged(councillor_path, editorial_path, defeatability)
    assert len(result) == 1
    assert result.iloc[0]["name_recognition_tier"] == "unknown"
    assert result.iloc[0]["fundraising_tier"] == "low"
    assert result.iloc[0]["mayoral_alignment"] == "unaligned"
    assert bool(result.iloc[0]["is_endorsed_by_departing"]) is False


def test_process_challengers_merged_output_satisfies_challengers_schema(tmp_path):
    from backend.model.validate import validate_challengers
    pa = _load_process_all()
    councillor_path = tmp_path / "councillor_registered.csv"
    pd.DataFrame([
        {"ward": 3, "first_name": "Test", "last_name": "Candidate", "status": "Active", "date_nomination": "2026-05-01"},
    ]).to_csv(councillor_path, index=False)
    editorial_path = tmp_path / "challengers.csv"
    pd.DataFrame(columns=["ward", "candidate_name", "name_recognition_tier", "fundraising_tier", "mayoral_alignment", "is_endorsed_by_departing", "notes", "last_updated"]).to_csv(editorial_path, index=False)
    defeatability = _defeatability_df(3, "Other Incumbent", is_running=True)
    result = pa.process_challengers_merged(councillor_path, editorial_path, defeatability)
    validate_challengers(result)  # must not raise
