"""Run the election model and return JSON results."""

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .candidates import build_candidate_status
from .council import (
    COUNCIL_ASSESSMENT_VERSION,
    COUNCIL_MODEL_VERSION,
    candidate_key,
    classify_race_evidence,
    nominations_closed,
)
from .forecast import build_forecast
from .mayoral import build_mayoral_evidence
from .phase import detect_phase

COUNCIL_SNAPSHOT_SCHEMA_VERSION = 3

def _data_dir() -> Path:
    return Path(__file__).parent.parent.parent / "data" / "processed"


@lru_cache(maxsize=1)
def load_processed_data() -> dict:
    """Load all processed data files."""
    d = _data_dir()
    mayor_reg_path = d / "mayor_registered.csv"
    mayor_registered = (
        pd.read_csv(mayor_reg_path).to_dict("records")
        if mayor_reg_path.exists()
        else []
    )
    return {
        "defeatability": pd.read_csv(d / "ward_defeatability.csv"),
        "challengers": pd.read_csv(d / "challengers.csv"),
        "leans": pd.read_csv(d / "ward_mayoral_lean.csv"),
        "coattails": pd.read_csv(d / "coattail_adjustments.csv"),
        "polls": pd.read_csv(d / "polls.csv"),
        "approval": pd.read_csv(d / "approval_ratings.csv"),
        "ward_poll_readings": pd.read_csv(d / "ward_poll_readings.csv"),
        "historical_council": pd.read_csv(d / "historical_council_results.csv"),
        "mayor_registered": mayor_registered,
    }


@lru_cache(maxsize=1)
def build_mayoral_products() -> tuple[dict, object]:
    """Build the public mayoral contract and shared Council draws once."""
    data = load_processed_data()
    evidence = build_mayoral_evidence(data["polls"], data["approval"])
    forecast, draws = build_forecast(data["polls"])
    return {**evidence, "forecast": forecast}, draws


def _derive_endorsed_by_departing(
    challengers: pd.DataFrame, ward_data: pd.DataFrame
) -> pd.DataFrame:
    """Derive is_endorsed_by_departing from the named endorsements list.

    For open-seat wards (is_running=False), checks whether the departing
    councillor's name appears as a token in the challenger's endorsements field.
    All other wards get False.
    """
    departing = (
        ward_data[~ward_data["is_running"].astype(bool)][["ward", "councillor_name"]]
        .set_index("ward")["councillor_name"]
        .to_dict()
    )

    def _check(row: pd.Series) -> bool:
        departing_name = departing.get(int(row["ward"]))
        if not departing_name:
            return False
        raw = row.get("endorsements", "")
        if pd.isna(raw):
            return False
        tokens = [e.strip() for e in str(raw).split("|")]
        return departing_name in tokens

    result = challengers.copy()
    result["is_endorsed_by_departing"] = result.apply(_check, axis=1)
    return result


def _ensure_generic_challenger(
    challengers: pd.DataFrame, ward_data: pd.DataFrame
) -> pd.DataFrame:
    required_cols = [
        "ward",
        "candidate_name",
        "name_recognition_tier",
        "mayoral_alignment",
        "endorsements",
    ]
    out = challengers.copy()
    for col in required_cols:
        if col not in out.columns:
            out[col] = None

    rows = []
    wards_with_challengers = (
        set(out["ward"].dropna().astype(int).tolist()) if not out.empty else set()
    )
    for _, row in ward_data.iterrows():
        ward = int(row["ward"])
        if not bool(row.get("is_running", True)):
            continue
        if ward not in wards_with_challengers:
            rows.append(
                {
                    "ward": ward,
                    "candidate_name": "Generic Challenger",
                    "name_recognition_tier": "unknown",
                    "mayoral_alignment": "unaligned",
                    "endorsements": "",
                }
            )

    if rows:
        out = pd.concat([out, pd.DataFrame(rows)], ignore_index=True)

    return out


def _load_council_calibration() -> dict:
    path = _data_dir() / "council_forecast_calibration.json"
    if not path.exists():
        return {
            "model_version": COUNCIL_MODEL_VERSION,
            "status": "error",
            "unavailable_reasons": ["calibration_artifact_missing"],
            "diagnostics": {},
            "gates": {},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _enrich_challenger_history(
    challengers: pd.DataFrame,
    historical_results: pd.DataFrame,
    ward_data: pd.DataFrame,
) -> pd.DataFrame:
    """Attach objective prior ward performance without converting it to odds."""
    result = challengers.copy()
    result["_candidate_key"] = result["candidate_name"].map(candidate_key)
    # Only compare current wards with elections on the same 25-ward boundaries.
    history = historical_results[
        historical_results["election_year"].astype(int) >= 2018
    ].copy()
    history["_candidate_key"] = history["candidate_name"].map(candidate_key)
    history = history.sort_values("election_year", ascending=False)
    history_lookup = {
        (int(row["ward"]), str(row["_candidate_key"])): row
        for _, row in history.drop_duplicates(["ward", "_candidate_key"]).iterrows()
    }
    prior_runner_up = {
        int(row["ward"]): candidate_key(row.get("prior_runner_up", ""))
        for _, row in ward_data.iterrows()
    }

    prior_shares: list[float | None] = []
    prior_years: list[int | None] = []
    returning_runner_up: list[bool] = []
    for _, row in result.iterrows():
        key = (int(row["ward"]), str(row["_candidate_key"]))
        historical = history_lookup.get(key)
        prior_shares.append(
            float(historical["vote_share"]) if historical is not None else None
        )
        prior_years.append(
            int(historical["election_year"]) if historical is not None else None
        )
        returning_runner_up.append(
            bool(prior_runner_up.get(int(row["ward"])))
            and prior_runner_up[int(row["ward"])] == str(row["_candidate_key"])
        )

    result["prior_ward_vote_share"] = prior_shares
    result["prior_ward_election_year"] = prior_years
    result["is_returning_runner_up"] = returning_runner_up
    return result.drop(columns=["_candidate_key"])


def _polls_for_ward(readings: pd.DataFrame, ward: int) -> list[dict]:
    ward_rows = readings[readings["ward"] == ward]
    polls: list[dict] = []
    for poll_id, group in ward_rows.groupby("poll_id", sort=False):
        first = group.iloc[0]
        source = first.get("source_url")
        polls.append(
            {
                "poll_id": str(poll_id),
                "firm": str(first["firm"]),
                "date_conducted": str(first["date_conducted"]),
                "date_published": str(first["date_published"]),
                "sample_size": int(first["sample_size"]),
                "methodology": str(first.get("methodology", "")),
                "denominator": str(first["denominator"]),
                "ballot_status": str(first["ballot_status"]),
                "undecided_share": float(first["undecided_share"]),
                "source_url": None if pd.isna(source) or not str(source).strip() else str(source),
                "candidates": [
                    {
                        "id": str(row["candidate_id"]),
                        "name": str(row["candidate_name"]),
                        "share": float(row["share"]),
                        "is_incumbent": bool(row["is_incumbent"]),
                        "is_residual": bool(row["is_residual"]),
                        "registration_status": str(row["registration_status"]),
                    }
                    for _, row in group.iterrows()
                ],
            }
        )
    return polls


def _forecast_unavailable_reasons(calibration: dict) -> list[str]:
    reasons = [str(reason) for reason in calibration.get("unavailable_reasons", [])]
    if not nominations_closed():
        reasons.insert(0, "candidate_field_not_final")
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(reasons))


def _load_published_mayoral_race() -> dict:
    """Reuse the immutable mayoral product for Council-only rebuilds."""
    path = _data_dir() / "polls_snapshot.json"
    if path.exists():
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        race = snapshot.get("mayoral_race")
        if isinstance(race, dict) and isinstance(race.get("forecast"), dict):
            return race
    race, _draws = build_mayoral_products()
    return race


def run_model(mayoral_race: dict | None = None) -> dict:
    """Build the evidence-led Council contract.

    Precise ward odds and Council composition are deliberately absent while
    publication gates fail. Race status remains useful, but is explicitly an
    evidence assessment rather than a synonym for a calibrated probability.
    """
    data = load_processed_data()
    data["challengers"] = _derive_endorsed_by_departing(
        data["challengers"], data["defeatability"]
    )
    data["challengers"] = _enrich_challenger_history(
        data["challengers"], data["historical_council"], data["defeatability"]
    )

    mayoral_race = mayoral_race or _load_published_mayoral_race()
    calibration = _load_council_calibration()
    unavailable_reasons = _forecast_unavailable_reasons(calibration)
    forecast_status = "available" if not unavailable_reasons else "insufficient_data"

    challengers_by_ward: dict[int, list[dict]] = {}
    for rec in data["challengers"].to_dict("records"):
        challengers_by_ward.setdefault(int(rec["ward"]), []).append(rec)

    coattails_indexed = data["coattails"].set_index("ward")

    wards_out = []
    for row in data["defeatability"].to_dict("records"):
        ward_num = int(row["ward"])
        ward_challengers = challengers_by_ward.get(ward_num, [])
        tier_order = {"unknown": 0, "known": 1, "well-known": 2}
        strongest_tier = max(
            (
                str(candidate.get("name_recognition_tier", "unknown"))
                for candidate in ward_challengers
            ),
            key=lambda tier: tier_order.get(tier, 0),
            default=None,
        )
        returning_runner_up = any(
            bool(candidate.get("is_returning_runner_up", False))
            for candidate in ward_challengers
        )
        ward_polls = _polls_for_ward(data["ward_poll_readings"], ward_num)
        current_field_poll_count = sum(
            poll["ballot_status"] == "current_field" for poll in ward_polls
        )
        race_class, race_reasons = classify_race_evidence(
            is_running=bool(row["is_running"]),
            vulnerability_score=float(row["defeatability_score"]),
            strongest_challenger_tier=strongest_tier,
            returning_runner_up=returning_runner_up,
            prior_runner_up_share=(
                float(row["prior_runner_up_share"])
                if pd.notna(row.get("prior_runner_up_share"))
                else None
            ),
            direct_poll_available=current_field_poll_count > 0,
        )

        prior_result = {
            "election_year": int(row["election_year"]),
            "incumbent_share": float(row["vote_share"]),
            "electorate_share": float(row["electorate_share"]),
            "margin": (
                float(row["prior_margin_share"])
                if pd.notna(row.get("prior_margin_share"))
                else None
            ),
            "runner_up": (
                str(row["prior_runner_up"])
                if pd.notna(row.get("prior_runner_up"))
                else None
            ),
            "runner_up_share": (
                float(row["prior_runner_up_share"])
                if pd.notna(row.get("prior_runner_up_share"))
                else None
            ),
            "by_election": bool(row["is_byelection_incumbent"]),
        }
        credible_count = sum(
            candidate.get("name_recognition_tier") == "well-known"
            or (
                candidate.get("prior_ward_vote_share") is not None
                and not pd.isna(candidate.get("prior_ward_vote_share"))
                and float(candidate["prior_ward_vote_share"]) >= 0.10
            )
            for candidate in ward_challengers
        )
        row["race_class"] = race_class
        row["race_status_reasons"] = race_reasons
        row["evidence"] = {
            "prior_result": prior_result,
            "registered_field": {
                "candidate_count": len(ward_challengers)
                + (1 if bool(row["is_running"]) else 0),
                "challenger_count": len(ward_challengers),
                "known_challenger_count": sum(
                    candidate.get("name_recognition_tier") == "known"
                    for candidate in ward_challengers
                ),
                "well_known_challenger_count": sum(
                    candidate.get("name_recognition_tier") == "well-known"
                    for candidate in ward_challengers
                ),
                "credible_challenger_count": credible_count,
                "strongest_name_recognition_tier": strongest_tier,
                "returning_runner_up": returning_runner_up,
            },
            "ward_polling": {
                "availability": "available" if ward_polls else "unavailable",
                "current_field_poll_count": current_field_poll_count,
                "total_poll_count": len(ward_polls),
                "polls": ward_polls,
            },
        }
        row["forecast"] = {
            "status": forecast_status,
            "unavailable_reasons": unavailable_reasons,
            "model_version": COUNCIL_MODEL_VERSION,
            "incumbent_win_probability": None,
            "incumbent_probability_interval": None,
        }
        if ward_num in coattails_indexed.index:
            cr = coattails_indexed.loc[ward_num]
            row["evidence"]["mayoral_context"] = {
                "status": "context_only",
                "used_in_ward_forecast": False,
                "councillor_chow_alignment": round(float(cr["alignment"]), 4),
                "alignment_vs_council_average": round(
                    float(cr["alignment_delta"]), 4
                ),
                "ward_chow_lean": round(float(cr["lean"]), 4),
            }
        wards_out.append(row)

    status_counts = {
        status: sum(ward["race_class"] == status for ward in wards_out)
        for status in ("safe", "competitive", "open")
    }
    as_of_values = [
        str(value)
        for frame, column in [
            (data["defeatability"], "last_updated"),
            (data["challengers"], "last_updated"),
            (data["ward_poll_readings"], "date_published"),
        ]
        if column in frame.columns
        for value in frame[column].dropna().tolist()
    ]

    return {
        "schema_version": COUNCIL_SNAPSHOT_SCHEMA_VERSION,
        "as_of": max(as_of_values) if as_of_values else None,
        "wards": wards_out,
        "challengers": data["challengers"].to_dict("records"),
        "council_model": {
            "assessment": {
                "version": COUNCIL_ASSESSMENT_VERSION,
                "status_counts": status_counts,
                "total_wards": len(wards_out),
                "meaning": (
                    "Race status is an evidence assessment, not a calibrated "
                    "incumbent win probability."
                ),
            },
            "forecast": {
                "status": forecast_status,
                "unavailable_reasons": unavailable_reasons,
                "model_version": COUNCIL_MODEL_VERSION,
                "diagnostics": calibration.get("diagnostics", {}),
                "gates": calibration.get("gates", {}),
            },
            "composition": {
                "status": "unavailable",
                "unavailable_reasons": ["ward_forecast_unavailable"],
                "mean_incumbents_returned": None,
                "interval": None,
                "conditional_on_mayor": {},
            },
            "mayoral_context": {
                "forecast_version": mayoral_race["forecast"]["model_version"],
                "forecast_status": mayoral_race["forecast"]["status"],
                "used_in_public_ward_odds": False,
            },
        },
        "mayoral_forecast_version": mayoral_race["forecast"]["model_version"],
        "mayoral_forecast_status": mayoral_race["forecast"]["status"],
        "phase": detect_phase(
            data["challengers"],
            has_financials=any(
                (_data_dir().parent / "raw" / "financial").glob("*.csv")
            ),
        ),
        "candidate_status": build_candidate_status(data["mayor_registered"]),
    }
