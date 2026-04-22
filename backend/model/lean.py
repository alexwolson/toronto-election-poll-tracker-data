"""Part 1: Ward Mayoral Lean computation.

Consumes processed mayoral results, computes per-ward deviation from city-wide
results for tracked candidates, and averages across elections.
"""

from __future__ import annotations

import pandas as pd

from .names import CanonicalNameError, canonical_name

# Tracked candidates for ward lean (those with historical data on 25-ward map)
TRACKED_CANDIDATES = {
    "chow",
    "tory",
    "bradford",
    "bailao",
    "furey",
    "matlow",
}

RELIABILITY = {
    "tory": "high",
    "chow": "high",
    "bailao": "high",
    "furey": "moderate",
    "bradford": "low",
    "matlow": "low",
}


def compute_ward_mayoral_lean(results_df: pd.DataFrame) -> pd.DataFrame:
    """Compute ward-level lean for tracked mayoral candidates.

    Returns a DataFrame with columns [ward, candidate, lean, reliability].
    Lean is the average deviation from the city-wide result across elections.
    """
    df = results_df.copy()

    # Map names to canonical keys, drop unmapped candidates
    def _map_name(name: str) -> str | None:
        try:
            return canonical_name(name)
        except CanonicalNameError:
            return None

    df["candidate_key"] = df["candidate"].apply(_map_name)
    df = df.dropna(subset=["candidate_key"])

    # Total votes per year and ward
    # (Note: we use the original results_df for totals to include all candidates)
    ward_totals = (
        results_df.groupby(["year", "ward"])["votes"].sum().reset_index(name="ward_total")
    )

    # City-wide totals per year (all candidates)
    city_totals = (
        results_df.groupby(["year"])["votes"].sum().reset_index(name="city_total")
    )

    # City-wide candidate totals per year (tracked candidates)
    city_cand_totals = (
        df.groupby(["year", "candidate_key"])["votes"]
        .sum()
        .reset_index(name="city_cand_votes")
    )

    # Join everything back
    df = df.merge(ward_totals, on=["year", "ward"])
    df = df.merge(city_totals, on=["year"])
    df = df.merge(city_cand_totals, on=["year", "candidate_key"])

    # S_w,e^c: candidate share in ward w in election e
    df["ward_share"] = df["votes"] / df["ward_total"]

    # S_city,e^c: candidate share city-wide in election e
    df["city_share"] = df["city_cand_votes"] / df["city_total"]

    # Deviation: delta_w,e^c = S_w,e^c - S_city,e^c
    df["deviation"] = df["ward_share"] - df["city_share"]

    # Average deviation across all elections for each candidate and ward
    leans = (
        df.groupby(["ward", "candidate_key"])["deviation"]
        .mean()
        .reset_index(name="lean")
    )
    leans = leans.rename(columns={"candidate_key": "candidate"})

    # Filter for only tracked candidates (though we already filtered earlier)
    leans = leans[leans["candidate"].isin(TRACKED_CANDIDATES)]

    # Add reliability
    leans["reliability"] = leans["candidate"].map(RELIABILITY)

    return leans
