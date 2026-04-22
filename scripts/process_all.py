#!/usr/bin/env python3
"""Process all raw inputs into clean, validated CSVs for the model.

Reads from data/raw/, validates, normalises, writes to data/processed/.
Fails fast: exits with a clear error if any validation step fails.

Run: uv run scripts/process_all.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backend.model.aggregator import aggregate_polls, get_latest_scenario_polls
from backend.model.coattails import compute_coattail_adjustment
from backend.model.lean import compute_ward_mayoral_lean
from backend.model.names import KNOWN_CANDIDATES
from backend.model.validate import (
    ValidationError,
    validate_challengers,
    validate_council_alignment,
    validate_defeatability,
    validate_mayoral_results,
    validate_polls,
    validate_registered_electors,
    validate_ward_population,
)

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
TIMESTAMP = datetime.now(timezone.utc).isoformat()


def process_polls(input_path: Path) -> pd.DataFrame:
    """Load, validate, and normalise polls CSV."""
    if not input_path.exists():
        print(f"ERROR: polls file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path)

    try:
        validate_polls(df)
    except ValidationError as e:
        print(f"ERROR in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Normalise dates to ISO strings
    df["date_conducted"] = pd.to_datetime(df["date_conducted"]).dt.strftime("%Y-%m-%d")
    df["date_published"] = pd.to_datetime(df["date_published"]).dt.strftime("%Y-%m-%d")

    return df


def process_council_alignment(input_path: Path) -> pd.DataFrame:
    """Load, validate, and normalise council alignment CSV."""
    if not input_path.exists():
        print(f"ERROR: council alignment file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path)

    try:
        df["ward"] = df["ward"].astype(int)
        validate_council_alignment(df)
    except (ValidationError, ValueError) as e:
        print(f"ERROR in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    return df


def process_defeatability(
    input_path: Path,
    pop_growth: pd.Series | None = None,
    preserve_metadata_from: Path | None = None,
) -> pd.DataFrame:
    """Load, validate, and normalise ward defeatability CSV.

    If pop_growth is provided (a Series indexed by ward), its values are used
    to populate pop_growth_pct, overriding any value in the raw CSV.
    If not provided, pop_growth_pct defaults to 0.0.
    """
    if not input_path.exists():
        print(f"ERROR: defeatability file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path)

    if "Ward" in df.columns:
        rename_map = {
            "Ward": "ward",
            "Elected Councillor": "councillor_name",
            "Vote Share": "vote_share",
            "Elector Share": "electorate_share",
            "Defeatability Score": "defeatability_score",
            "New Voter Margin": "new_voter_margin",
        }
        df = df.rename(columns=rename_map)
        df = df[df["ward"].astype(str).str.strip().str.match(r"^\d+$")].copy()
        df["ward"] = df["ward"].astype(int)

        for col in ["vote_share", "electorate_share"]:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.strip()
                .astype(float)
                / 100.0
            )

        df["defeatability_score"] = pd.to_numeric(
            df["defeatability_score"], errors="coerce"
        )
        df["notes"] = ""
        if "new_voter_margin" in df.columns:
            df["notes"] = "New Voter Margin: " + df["new_voter_margin"].astype(str)

        if preserve_metadata_from is not None and preserve_metadata_from.exists():
            prior = pd.read_csv(preserve_metadata_from)
            prior_meta = prior[
                [
                    "ward",
                    "election_year",
                    "is_byelection_incumbent",
                    "is_running",
                    "last_updated",
                ]
            ].drop_duplicates(subset=["ward"])
            df = df.merge(prior_meta, on="ward", how="left")
        else:
            df["election_year"] = 2022
            df["is_byelection_incumbent"] = False
            df["is_running"] = True
            df["last_updated"] = datetime.now(timezone.utc).date().isoformat()

        df["election_year"] = df["election_year"].fillna(2022).astype(int)
        df["is_byelection_incumbent"] = (
            df["is_byelection_incumbent"].fillna(False).astype(bool)
        )
        df["is_running"] = df["is_running"].fillna(True).astype(bool)
        df["last_updated"] = df["last_updated"].fillna(
            datetime.now(timezone.utc).date().isoformat()
        )

        df = df[
            [
                "ward",
                "councillor_name",
                "election_year",
                "is_byelection_incumbent",
                "is_running",
                "vote_share",
                "electorate_share",
                "defeatability_score",
                "notes",
                "last_updated",
            ]
        ]

    try:
        df["ward"] = df["ward"].astype(int)
        df["election_year"] = df["election_year"].astype(int)
        validate_defeatability(df)
    except (ValidationError, ValueError) as e:
        print(f"ERROR in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Normalise last_updated to ISO date string
    df["last_updated"] = pd.to_datetime(df["last_updated"]).dt.strftime("%Y-%m-%d")

    if pop_growth is not None:
        df["pop_growth_pct"] = df["ward"].map(pop_growth).fillna(0.0)
    else:
        df["pop_growth_pct"] = 0.0

    return df


def process_defeatability_full(input_path: Path) -> pd.DataFrame:
    """Load and normalise full defeatability table including mayor row."""
    if not input_path.exists():
        print(
            f"ERROR: full defeatability file not found: {input_path}", file=sys.stderr
        )
        sys.exit(1)

    df = pd.read_csv(input_path)

    required = ["Ward", "Elected Councillor", "Defeatability Score"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(
            f"ERROR in {input_path}: full defeatability missing required columns: {missing}",
            file=sys.stderr,
        )
        sys.exit(1)

    score = pd.to_numeric(df["Defeatability Score"], errors="coerce")
    if score.isna().any():
        print(
            f"ERROR in {input_path}: Defeatability Score must be numeric for all rows",
            file=sys.stderr,
        )
        sys.exit(1)

    bad_score = score[(score < 0) | (score > 100)]
    if not bad_score.empty:
        print(
            f"ERROR in {input_path}: Defeatability Score values outside 0-100",
            file=sys.stderr,
        )
        sys.exit(1)

    if not (df["Ward"].astype(str).str.strip().str.lower() == "mayor").any():
        print(
            f"ERROR in {input_path}: expected a 'Mayor' row for structural context",
            file=sys.stderr,
        )
        sys.exit(1)

    return df


def process_challengers(input_path: Path) -> pd.DataFrame:
    """Load and validate challengers CSV."""
    if not input_path.exists():
        print(f"ERROR: challengers file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path)

    try:
        df["ward"] = df["ward"].astype(int)
        validate_challengers(df)
    except (ValidationError, ValueError) as e:
        print(f"ERROR in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    return df


def process_mayoral_results(input_path: Path) -> pd.DataFrame:
    """Load and validate mayoral results CSV."""
    if not input_path.exists():
        print(f"ERROR: mayoral results file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path)

    try:
        df["ward"] = df["ward"].astype(int)
        df["year"] = df["year"].astype(int)
        validate_mayoral_results(df)
    except (ValidationError, ValueError) as e:
        print(f"ERROR in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    return df


def process_registered_electors(input_path: Path) -> pd.DataFrame:
    """Load and validate registered electors CSV."""
    if not input_path.exists():
        print(
            f"ERROR: registered electors file not found: {input_path}", file=sys.stderr
        )
        sys.exit(1)

    df = pd.read_csv(input_path)

    try:
        df["ward"] = df["ward"].astype(int)
        df["year"] = df["year"].astype(int)
        validate_registered_electors(df)
    except (ValidationError, ValueError) as e:
        print(f"ERROR in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    return df


def process_ward_population(input_path: Path) -> pd.Series:
    """Load ward population CSV and return pop_growth_pct per ward as a Series.

    Returns a Series indexed by ward number (1–25).
    Growth = (pop_2021 - pop_2016) / pop_2016
    """
    if not input_path.exists():
        print(f"ERROR: ward population file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path)

    try:
        df["ward"] = df["ward"].astype(int)
        df["pop_2016"] = df["pop_2016"].astype(int)
        df["pop_2021"] = df["pop_2021"].astype(int)
        validate_ward_population(df)
    except (ValidationError, ValueError) as e:
        print(f"ERROR in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    growth = (df["pop_2021"] - df["pop_2016"]) / df["pop_2016"]
    return growth.set_axis(df["ward"]).rename_axis("ward")


def write_processed(
    df: pd.DataFrame, output_path: Path, timestamp: str = TIMESTAMP
) -> None:
    """Write a processed DataFrame to CSV.

    Writes a sidecar .meta file with the generation timestamp.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    meta_path = output_path.with_suffix(".meta")
    meta_path.write_text(f"generated_at={timestamp}\n", encoding="utf-8")
    print(f"  Written: {output_path}")


def main() -> None:
    print("Processing polls...")
    polls = process_polls(RAW / "polls" / "polls.csv")
    write_processed(polls, PROCESSED / "polls.csv")

    print("Computing mayoral polling average...")
    scenario_polls = get_latest_scenario_polls(polls)
    avg_results = aggregate_polls(scenario_polls, KNOWN_CANDIDATES)
    avg_df = pd.DataFrame(
        [{"candidate": c, "share": s} for c, s in avg_results.items()]
    )
    avg_df = avg_df.sort_values(by="share", ascending=False)
    write_processed(avg_df, PROCESSED / "mayoral_polling_average.csv")

    print("Processing mayoral results...")
    results = process_mayoral_results(RAW / "elections" / "mayoral_results.csv")
    write_processed(results, PROCESSED / "mayoral_results.csv")

    print("Computing ward mayoral lean...")
    leans = compute_ward_mayoral_lean(results)
    write_processed(leans, PROCESSED / "ward_mayoral_lean.csv")

    print("Processing registered electors...")
    electors = process_registered_electors(
        RAW / "elections" / "registered_electors.csv"
    )
    write_processed(electors, PROCESSED / "registered_electors.csv")

    print("Processing council alignment...")
    council_path = RAW / "council_votes" / "council_alignment.csv"
    council_df = None
    if council_path.exists():
        council_df = process_council_alignment(council_path)
        write_processed(council_df, PROCESSED / "council_alignment.csv")
    else:
        print(f"  Skipping: {council_path} (not found)")

    if council_df is not None:
        print("Computing coattail adjustments...")
        chow_avg = avg_results.get("chow", 0.0)
        coattails = compute_coattail_adjustment(council_df, leans, chow_avg)
        write_processed(coattails, PROCESSED / "coattail_adjustments.csv")

    print("Processing ward population growth...")
    population_path = RAW / "census" / "ward_population.csv"
    pop_growth = None
    if population_path.exists():
        pop_growth = process_ward_population(population_path)
        write_processed(
            pd.DataFrame(
                {"ward": pop_growth.index, "pop_growth_pct": pop_growth.values}
            ),
            PROCESSED / "ward_population_growth.csv",
        )
    else:
        print(f"  Skipping: {population_path} (not found, growth will be 0.0)")

    print("Processing ward defeatability...")
    defeatability_path = RAW / "defeatability" / "ward_defeatability.csv"
    watcher_path = RAW / "defeatability" / "data-qT4Kx.csv"
    source_path = watcher_path if watcher_path.exists() else defeatability_path
    if source_path.exists():
        defeatability = process_defeatability(
            source_path,
            pop_growth=pop_growth,
            preserve_metadata_from=defeatability_path
            if defeatability_path.exists()
            else None,
        )
        write_processed(defeatability, PROCESSED / "ward_defeatability.csv")
    else:
        print(f"  Skipping: {source_path} (not found)")

    print("Processing full defeatability table...")
    full_defeatability_path = RAW / "defeatability" / "data-qT4Kx.csv"
    if full_defeatability_path.exists():
        defeatability_full = process_defeatability_full(full_defeatability_path)
        write_processed(defeatability_full, PROCESSED / "defeatability_full.csv")
    else:
        print(f"  Skipping: {full_defeatability_path} (not found)")

    print("Processing challengers...")
    challengers_path = RAW / "candidates" / "challengers.csv"
    if challengers_path.exists():
        challengers = process_challengers(challengers_path)
        write_processed(challengers, PROCESSED / "challengers.csv")
    else:
        print(f"  Skipping: {challengers_path} (not found)")

    print("Done. All outputs written to data/processed/.")


if __name__ == "__main__":
    main()
