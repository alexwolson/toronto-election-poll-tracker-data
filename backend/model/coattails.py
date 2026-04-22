"""Part 3: Mayoral Coattail Adjustment.

Computes how the incumbent mayor's popularity helps or hurts ward-level
candidates based on their alignment with the mayor.
"""

from __future__ import annotations

import pandas as pd

# Editorial coattail strength parameter (gamma) as per spec v0.2
COATTAIL_STRENGTH = 0.5


def compute_relative_mayor_strength(
    mayor_lean: pd.DataFrame, city_wide_avg: float
) -> pd.Series:
    """Compute the mayor's relative strength in each ward.

    P_w = L_w + (current_city_wide_mood_adjustment)

    Actually, the spec says: 'the mayor's base ward lean L_w is scaled by
    the mayor's current polling position relative to a neutral baseline.'

    For now, we'll use a simple version:
    P_w = (Ward Lean) + (City-wide share - Historical city-wide share)

    Wait, the lean is already (Ward Share - City-wide Share).
    So P_w = Lean + Polling Average is a reasonable proxy for current
    estimated support in that ward.
    """
    # This is an estimate of current support in the ward
    return mayor_lean["lean"] + city_wide_avg


def compute_coattail_adjustment(
    alignment_df: pd.DataFrame,
    lean_df: pd.DataFrame,
    city_wide_avg: float,
    incumbent_mayor_key: str | None = "chow",
    gamma: float = COATTAIL_STRENGTH,
) -> pd.DataFrame:
    """Compute coattail adjustment C_w for each ward.

    C_w = (A_w - mean(A)) * P_w * gamma
    """
    no_incumbent_mode = incumbent_mayor_key is None or (
        isinstance(incumbent_mayor_key, str)
        and incumbent_mayor_key.strip().lower() in ("none", "open")
    )
    if no_incumbent_mode:
        df = alignment_df[["ward", "councillor_name"]].copy()
        df["alignment"] = 0.0
        df["alignment_delta"] = 0.0
        df["p_w"] = 0.0
        df["coattail_adjustment"] = 0.0
        return df

    # 1. Get councillor alignment with incumbent mayor
    # Column is alignment_chow or alignment_tory
    col_name = f"alignment_{incumbent_mayor_key}"
    if col_name not in alignment_df.columns:
        raise ValueError(f"Alignment column {col_name} not found")

    df = alignment_df[["ward", "councillor_name", col_name]].copy()
    df = df.rename(columns={col_name: "alignment"})

    # 2. Centre the alignment score
    mean_alignment = df["alignment"].mean()
    df["alignment_delta"] = df["alignment"] - mean_alignment

    # 3. Get ward lean for the incumbent mayor
    mayor_lean = lean_df[lean_df["candidate"] == incumbent_mayor_key]
    if mayor_lean.empty:
        # If no lean data, assume uniform 0
        df["p_w"] = city_wide_avg
    else:
        df = df.merge(mayor_lean[["ward", "lean"]], on="ward", how="left")
        df["lean"] = df["lean"].fillna(0.0)
        df["p_w"] = df["lean"] + city_wide_avg

    # 4. Compute coattail C_w
    df["coattail_adjustment"] = df["alignment_delta"] * df["p_w"] * gamma

    return df
