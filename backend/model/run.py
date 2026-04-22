"""Run the election model and return JSON results."""

from functools import lru_cache
from pathlib import Path

import pandas as pd

from .aggregator import aggregate_polls, get_latest_scenario_polls, get_scenario_polls
from .aggregator import exclude_polls_with_declined_candidates
from .candidates import CANDIDATE_STATUS, DECLINED_CANDIDATE_IDS
from .phase import detect_phase
from .simulation import WardSimulation, SAFE_DEFEATABILITY_THRESHOLD


SCENARIOS = {
    "chow_bradford": ["chow", "bradford"],
}

DEFAULT_SCENARIO = "chow_bradford"


def _data_dir() -> Path:
    return Path(__file__).parent.parent.parent / "data" / "processed"


@lru_cache(maxsize=1)
def load_processed_data() -> dict:
    """Load all processed data files."""
    d = _data_dir()
    return {
        "defeatability": pd.read_csv(d / "ward_defeatability.csv"),
        "challengers": pd.read_csv(d / "challengers.csv"),
        "leans": pd.read_csv(d / "ward_mayoral_lean.csv"),
        "coattails": pd.read_csv(d / "coattail_adjustments.csv"),
        "polls": pd.read_csv(d / "polls.csv"),
        "ward_polls": pd.read_csv(d / "ward_polls.csv"),
    }


def _classify_race(row: dict, challengers_for_ward: list[dict]) -> str:
    if not row["is_running"]:
        return "open"
    viable = [
        c
        for c in challengers_for_ward
        if c["name_recognition_tier"] in ("well-known", "known")
    ]
    if viable:
        return "competitive"
    if row.get("defeatability_score", 0) >= SAFE_DEFEATABILITY_THRESHOLD:
        return "competitive"
    return "safe"


def _ensure_generic_challenger(
    challengers: pd.DataFrame, ward_data: pd.DataFrame
) -> pd.DataFrame:
    required_cols = [
        "ward",
        "candidate_name",
        "name_recognition_tier",
        "fundraising_tier",
        "mayoral_alignment",
        "is_endorsed_by_departing",
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
                    "fundraising_tier": "low",
                    "mayoral_alignment": "unaligned",
                    "is_endorsed_by_departing": False,
                }
            )

    if rows:
        out = pd.concat([out, pd.DataFrame(rows)], ignore_index=True)

    return out


@lru_cache(maxsize=1)
def run_model() -> dict:
    """Run the full model pipeline and return structured results."""
    data = load_processed_data()
    data["challengers"] = _ensure_generic_challenger(
        data["challengers"], data["defeatability"]
    )

    polls_df = data["polls"]
    candidates = SCENARIOS.get(DEFAULT_SCENARIO, [])
    eligible_polls = exclude_polls_with_declined_candidates(
        polls_df, DECLINED_CANDIDATE_IDS
    )
    scenario_polls = get_scenario_polls(eligible_polls, candidates)
    current_polls = get_latest_scenario_polls(scenario_polls)

    mayoral_shares = aggregate_polls(current_polls, candidates)
    mayoral_shares = {k: v for k, v in mayoral_shares.items() if v > 0.001}
    mayoral_averages = pd.DataFrame(
        [{"candidate": k, "share": v} for k, v in mayoral_shares.items()]
    )

    sim = WardSimulation(
        ward_data=data["defeatability"],
        mayoral_averages=mayoral_averages,
        coattails=data["coattails"],
        challengers=data["challengers"],
        leans=data["leans"],
        ward_polls=data["ward_polls"],
    )
    results = sim.run()

    challengers_by_ward: dict[int, list[dict]] = {}
    for rec in data["challengers"].to_dict("records"):
        challengers_by_ward.setdefault(rec["ward"], []).append(rec)

    coattails_indexed = data["coattails"].set_index("ward")

    wards_out = []
    for row in data["defeatability"].to_dict("records"):
        ward_num = row["ward"]
        ward_challengers = challengers_by_ward.get(ward_num, [])
        row["win_probability"] = round(
            results["win_probabilities"].get(ward_num, 0.0), 4
        )
        row["win_probability_interval"] = results["incumbent_probability_interval"].get(
            ward_num, {"low": 0.0, "high": 0.0}
        )
        row["race_class"] = _classify_race(row, ward_challengers)
        row["factors"] = results["factors"].get(
            ward_num, {"vuln": 0.0, "coat": 0.0, "chal": 0.0}
        )
        row["candidate_win_probabilities"] = results["candidate_win_probabilities"].get(
            ward_num, {}
        )
        if ward_num in coattails_indexed.index:
            cr = coattails_indexed.loc[ward_num]
            row["coattail_detail"] = {
                "alignment": round(float(cr["alignment"]), 4),
                "alignment_delta": round(float(cr["alignment_delta"]), 4),
                "ward_lean": round(float(cr["lean"]), 4),
            }
        wards_out.append(row)

    return {
        "wards": wards_out,
        "challengers": data["challengers"].to_dict("records"),
        "composition_mean": round(float(results["composition_mean"]), 2),
        "composition_std": round(float(results["composition_std"]), 2),
        "composition_by_mayor": results["composition_by_mayor"],
        "mayoral_averages": mayoral_shares,
        "phase": detect_phase(data["challengers"]),
        "scenarios": SCENARIOS,
        "default_scenario": DEFAULT_SCENARIO,
        "candidate_status": CANDIDATE_STATUS,
    }
