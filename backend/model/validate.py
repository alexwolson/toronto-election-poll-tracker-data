"""Validation functions for raw input DataFrames.

Each function raises ValidationError with a descriptive message on failure.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

# Fixed metadata columns in polls.csv. Every other numeric column is treated
# as a candidate share column. This keeps the schema open-ended: new candidates
# can be added as columns without touching the validation code.
POLL_METADATA_COLS = frozenset(
    {
        "poll_id",
        "firm",
        "date_conducted",
        "date_published",
        "sample_size",
        "methodology",
        "field_tested",
        "notes",
    }
)

SHARE_TOLERANCE = 0.01  # allow up to 1% rounding error


def _is_na(value: Any) -> bool:
    """Return True if value is None, NaN, or pd.NA (scalar check, type-checker safe)."""
    if value is None:
        return True
    try:
        return bool(math.isnan(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


class ValidationError(ValueError):
    pass


def _share_cols(df: pd.DataFrame) -> list[str]:
    """Return all columns that are candidate share columns.

    Any numeric column not in POLL_METADATA_COLS is treated as a share column.
    This includes 'undecided' and any candidate column regardless of whether
    the candidate is registered in the name registry.
    """
    return [
        c
        for c in df.columns
        if c not in POLL_METADATA_COLS and pd.api.types.is_numeric_dtype(df[c])
    ]


def validate_polls(df: pd.DataFrame) -> None:
    """Validate a polls DataFrame against the polls.csv schema."""
    required = ["poll_id", "firm", "date_conducted", "date_published", "field_tested"]
    _check_required_columns(df, required, "polls")

    share_columns = _share_cols(df)

    # Vote shares must sum to <= 1.0 (+ tolerance) per row
    if share_columns:
        row_sums = df[share_columns].fillna(0).sum(axis=1)
        bad = df[row_sums > 1.0 + SHARE_TOLERANCE]
        if not bad.empty:
            raise ValidationError(
                f"Poll share columns sum to more than 1.0 in rows: "
                f"{bad['poll_id'].tolist()}"
            )

    # field_tested must be consistent with share columns:
    # 1. Every key in field_tested must have a corresponding column in the CSV.
    # 2. Every share column must appear in field_tested for that row.
    for _, row in df.iterrows():
        raw_val = row["field_tested"]
        tested_raw = str(raw_val) if not _is_na(raw_val) else ""
        tested_keys = [k.strip() for k in tested_raw.split(",") if k.strip()]

        # Direction 1: field_tested key without a column
        missing_cols = [k for k in tested_keys if k not in df.columns]
        if missing_cols:
            raise ValidationError(
                f"poll_id {row['poll_id']!r}: field_tested lists {missing_cols} "
                f"but no corresponding column(s) exist in the CSV"
            )

        # Direction 2: share column not listed in field_tested for this row
        undeclared = [
            c for c in share_columns if not _is_na(row[c]) and c not in tested_keys
        ]
        if undeclared:
            raise ValidationError(
                f"poll_id {row['poll_id']!r}: column(s) {undeclared} have values "
                f"but are not listed in field_tested"
            )

    # date_conducted must be <= date_published
    conducted = pd.to_datetime(df["date_conducted"], errors="coerce")
    published = pd.to_datetime(df["date_published"], errors="coerce")

    unparseable = df[conducted.isna() | published.isna()]
    if not unparseable.empty:
        raise ValidationError(
            f"Unparseable date values in rows: {unparseable['poll_id'].tolist()}"
        )

    bad_dates = df[conducted > published]
    if not bad_dates.empty:
        raise ValidationError(
            f"date_conducted is after date_published in rows: "
            f"{bad_dates['poll_id'].tolist()}"
        )

    # poll_id must be unique
    null_ids = df[df["poll_id"].isna()]
    if not null_ids.empty:
        raise ValidationError(f"Missing poll_id in {len(null_ids)} row(s)")

    dupes = df[df["poll_id"].duplicated()]
    if not dupes.empty:
        raise ValidationError(f"Duplicate poll_id values: {dupes['poll_id'].tolist()}")

    # sample_size must be positive if present
    if "sample_size" in df.columns:
        bad_n = df[df["sample_size"].notna() & (df["sample_size"] <= 0)]
        if not bad_n.empty:
            raise ValidationError(
                f"sample_size must be positive in rows: {bad_n['poll_id'].tolist()}"
            )


def validate_council_alignment(df: pd.DataFrame) -> None:
    """Validate a council_alignment DataFrame against the council_alignment.csv schema."""
    required = [
        "ward",
        "councillor_name",
        "alignment_chow",
        "alignment_tory",
        "last_updated",
    ]
    _check_required_columns(df, required, "council_alignment")

    # ward must be 1–25
    bad_ward = df[~df["ward"].between(1, 25)]
    if not bad_ward.empty:
        raise ValidationError(f"ward values outside 1–25: {bad_ward['ward'].tolist()}")

    # alignment scores must be in [0, 1]
    for col in ["alignment_chow", "alignment_tory"]:
        bad = df[~df[col].between(0, 1)]
        if not bad.empty:
            raise ValidationError(
                f"{col} values outside [0, 1] in wards: {bad['ward'].tolist()}"
            )

    # no duplicate wards
    dupes = df[df["ward"].duplicated()]
    if not dupes.empty:
        raise ValidationError(f"Duplicate ward values: {dupes['ward'].tolist()}")


def validate_defeatability(df: pd.DataFrame) -> None:
    """Validate a ward_defeatability DataFrame against the ward_defeatability.csv schema."""
    required = [
        "ward",
        "councillor_name",
        "election_year",
        "is_byelection_incumbent",
        "is_running",
        "vote_share",
        "electorate_share",
        "defeatability_score",
        "last_updated",
    ]
    _check_required_columns(df, required, "ward_defeatability")

    # ward must be 1–25
    bad_ward = df[~df["ward"].between(1, 25)]
    if not bad_ward.empty:
        raise ValidationError(f"ward values outside 1–25: {bad_ward['ward'].tolist()}")

    # no duplicate wards
    dupes = df[df["ward"].duplicated()]
    if not dupes.empty:
        raise ValidationError(f"Duplicate ward values: {dupes['ward'].tolist()}")

    # election_year must be a positive integer
    bad_year = df[~df["election_year"].gt(0)]
    if not bad_year.empty:
        raise ValidationError(
            f"election_year must be a positive integer in wards: {bad_year['ward'].tolist()}"
        )

    # vote_share must be in (0, 1]
    bad_vs = df[~df["vote_share"].between(0, 1, inclusive="right")]
    if not bad_vs.empty:
        raise ValidationError(
            f"vote_share values outside (0, 1] in wards: {bad_vs['ward'].tolist()}"
        )

    # electorate_share must be in (0, 1]
    bad_es = df[~df["electorate_share"].between(0, 1, inclusive="right")]
    if not bad_es.empty:
        raise ValidationError(
            f"electorate_share values outside (0, 1] in wards: {bad_es['ward'].tolist()}"
        )

    # defeatability_score must be in 0-100
    bad_score = df[~df["defeatability_score"].between(0, 100)]
    if not bad_score.empty:
        raise ValidationError(
            f"defeatability_score values outside 0–100 in wards: {bad_score['ward'].tolist()}"
        )

    # is_running must be boolean
    if df["is_running"].dtype != bool:
        bad_running = df[~df["is_running"].isin([True, False])]
        if not bad_running.empty:
            raise ValidationError(
                f"is_running must be boolean in wards: {bad_running['ward'].tolist()}"
            )

    # last_updated must be parseable as a date
    last_updated = pd.to_datetime(df["last_updated"], errors="coerce")
    bad_dates = df[last_updated.isna()]
    if not bad_dates.empty:
        raise ValidationError(
            f"Unparseable last_updated values in wards: {bad_dates['ward'].tolist()}"
        )


def validate_mayoral_results(df: pd.DataFrame) -> None:
    """Validate a mayoral_results DataFrame from fetch_elections.py."""
    required = ["year", "ward", "candidate", "votes"]
    _check_required_columns(df, required, "mayoral_results")

    # ward must be 1–25
    bad_ward = df[~df["ward"].between(1, 25)]
    if not bad_ward.empty:
        raise ValidationError(f"ward values outside 1–25: {bad_ward['ward'].tolist()}")

    # votes must be non-negative
    bad_votes = df[df["votes"] < 0]
    if not bad_votes.empty:
        raise ValidationError(
            f"votes must be non-negative in rows with candidate: "
            f"{bad_votes['candidate'].tolist()}"
        )

    # candidate must not be null
    null_candidates = df[df["candidate"].isna()]
    if not null_candidates.empty:
        raise ValidationError(
            f"missing candidate name in {len(null_candidates)} row(s)"
        )


def validate_registered_electors(df: pd.DataFrame) -> None:
    """Validate a registered_electors DataFrame from fetch_elections.py."""
    required = ["year", "ward", "eligible_electors"]
    _check_required_columns(df, required, "registered_electors")

    # ward must be 1–25
    bad_ward = df[~df["ward"].between(1, 25)]
    if not bad_ward.empty:
        raise ValidationError(f"ward values outside 1–25: {bad_ward['ward'].tolist()}")

    # eligible_electors must be positive
    bad_electors = df[df["eligible_electors"] <= 0]
    if not bad_electors.empty:
        raise ValidationError(
            f"eligible_electors must be positive in wards: "
            f"{bad_electors['ward'].tolist()}"
        )

    # no duplicate ward+year pairs
    dupes = df[df.duplicated(subset=["year", "ward"])]
    if not dupes.empty:
        raise ValidationError(
            f"Duplicate ward/year pairs: "
            f"{list(zip(dupes['year'].tolist(), dupes['ward'].tolist()))}"
        )


def validate_ward_population(df: pd.DataFrame) -> None:
    """Validate a ward_population DataFrame from fetch_ward_profiles.py."""
    required = ["ward", "pop_2016", "pop_2021"]
    _check_required_columns(df, required, "ward_population")

    if len(df) != 25:
        raise ValidationError(f"Expected 25 wards, got {len(df)}")

    bad_ward = df[~df["ward"].between(1, 25)]
    if not bad_ward.empty:
        raise ValidationError(f"ward values outside 1–25: {bad_ward['ward'].tolist()}")

    dupes = df[df["ward"].duplicated()]
    if not dupes.empty:
        raise ValidationError(f"Duplicate ward values: {dupes['ward'].tolist()}")

    for col in ("pop_2016", "pop_2021"):
        bad = df[df[col] <= 0]
        if not bad.empty:
            raise ValidationError(
                f"{col} must be positive in wards: {bad['ward'].tolist()}"
            )


def validate_challengers(df: pd.DataFrame) -> None:
    """Validate a challengers DataFrame against the challengers.csv schema."""
    required = [
        "ward",
        "candidate_name",
        "name_recognition_tier",
        "fundraising_tier",
        "mayoral_alignment",
        "is_endorsed_by_departing",
        "last_updated",
    ]
    _check_required_columns(df, required, "challengers")

    # ward must be 1–25
    bad_ward = df[~df["ward"].between(1, 25)]
    if not bad_ward.empty:
        raise ValidationError(f"ward values outside 1–25: {bad_ward['ward'].tolist()}")

    # tiers must be valid
    valid_recog = {"well-known", "known", "unknown"}
    bad_recog = df[~df["name_recognition_tier"].isin(valid_recog)]
    if not bad_recog.empty:
        raise ValidationError(
            f"Invalid name_recognition_tier in wards: {bad_recog['ward'].tolist()}"
        )

    valid_fund = {"high", "medium", "low"}
    bad_fund = df[~df["fundraising_tier"].isin(valid_fund)]
    if not bad_fund.empty:
        raise ValidationError(
            f"Invalid fundraising_tier in wards: {bad_fund['ward'].tolist()}"
        )


def _check_required_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValidationError(f"{name}: missing required columns: {missing}")
