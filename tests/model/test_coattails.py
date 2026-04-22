"""Tests for coattail adjustment computation."""
import pandas as pd
from backend.model.coattails import compute_coattail_adjustment


def _make_alignment_df(wards: list[int]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ward": wards,
            "councillor_name": [f"Councillor {w}" for w in wards],
            "alignment_chow": [0.6] * len(wards),
            "alignment_tory": [0.4] * len(wards),
        }
    )


def _make_lean_df(wards: list[int]) -> pd.DataFrame:
    """Lean data covering only a subset of wards."""
    return pd.DataFrame(
        {
            "ward": wards,
            "candidate": ["chow"] * len(wards),
            "lean": [0.05] * len(wards),
        }
    )


def test_all_wards_present_when_lean_partial():
    """Every ward in alignment_df must appear in the output even if lean data
    is missing for some wards. Missing lean → lean=0.0, not dropped row.
    """
    alignment_df = _make_alignment_df([1, 2, 3, 4, 5])
    lean_df = _make_lean_df([1, 3])  # wards 2, 4, 5 have no lean entry

    result = compute_coattail_adjustment(
        alignment_df=alignment_df,
        lean_df=lean_df,
        city_wide_avg=0.35,
        incumbent_mayor_key="chow",
    )

    assert set(result["ward"].tolist()) == {1, 2, 3, 4, 5}, (
        f"Expected all 5 wards; got {sorted(result['ward'].tolist())}"
    )


def test_missing_lean_defaults_to_zero():
    """A ward with no lean entry should have lean=0.0 in the output."""
    alignment_df = _make_alignment_df([1, 2])
    lean_df = _make_lean_df([1])  # ward 2 has no lean

    result = compute_coattail_adjustment(
        alignment_df=alignment_df,
        lean_df=lean_df,
        city_wide_avg=0.35,
        incumbent_mayor_key="chow",
    )

    ward2 = result[result["ward"] == 2].iloc[0]
    assert ward2["lean"] == 0.0, f"Expected lean=0.0 for ward 2, got {ward2['lean']}"
