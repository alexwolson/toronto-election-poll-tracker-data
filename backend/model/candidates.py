"""Candidate status metadata used by modelling and polling APIs."""

from __future__ import annotations

from typing import TypedDict


class CandidateProfile(TypedDict):
    id: str
    name: str
    summary: str


# Editorial potential/declined — people who have NOT filed nomination papers.
# "declared" is derived dynamically from the city API via build_candidate_status().
CANDIDATE_STATUS: dict[str, list[CandidateProfile]] = {
    "potential": [
        {
            "id": "chow",
            "name": "Olivia Chow",
            "summary": "Incumbent mayor; decision on 2026 run pending.",
        },
    ],
    "declined": [
        {
            "id": "furey",
            "name": "Anthony Furey",
            "summary": "2023 mayoral by-election finisher; confirmed he will not run in 2026.",
        },
        {
            "id": "bailao",
            "name": "Ana Bailao",
            "summary": "Former deputy mayor; declined to run in 2026.",
        },
        {
            "id": "ford",
            "name": "Michael Ford",
            "summary": "Former MPP and ex-city councillor; declined to run in 2026.",
        },
        {
            "id": "matlow",
            "name": "Josh Matlow",
            "summary": "Ward 12 city councillor; declined to run in 2026.",
        },
        {
            "id": "mendicino",
            "name": "Marco Mendicino",
            "summary": "Former federal minister and MP; declined to run in 2026.",
        },
        {
            "id": "mulroney",
            "name": "Ben Mulroney",
            "summary": "Media personality; declined to run in 2026.",
        },
        {
            "id": "phillips",
            "name": "Rod Phillips",
            "summary": "Former Ontario finance minister; declined to run in 2026.",
        },
        {
            "id": "tory",
            "name": "John Tory",
            "summary": "Former mayor of Toronto; declined to run in 2026.",
        },
    ],
}

DECLINED_CANDIDATE_IDS = {candidate["id"] for candidate in CANDIDATE_STATUS["declined"]}

# Editorial summaries for candidates who may file nomination papers.
# Keyed by lowercase "firstname lastname". Used by build_candidate_status().
_CANDIDATE_EDITORIAL: dict[str, CandidateProfile] = {
    "brad bradford": {
        "id": "bradford",
        "name": "Brad Bradford",
        "summary": "Ward 19 city councillor since 2018 and declared 2026 mayoral candidate.",
    },
    "lyall sanders": {
        "id": "sanders",
        "name": "Lyall Sanders",
        "summary": "Social activist and declared 2026 mayoral candidate.",
    },
}


def build_candidate_status(
    declared_records: list[dict],
) -> dict[str, list[CandidateProfile]]:
    """Build complete candidate status from API records + editorial data.

    declared_records: list of dicts with keys first_name, last_name, status.
    Only records with status == 'Active' are included in declared.
    """
    declared: list[CandidateProfile] = []
    for record in declared_records:
        if record.get("status") != "Active":
            continue
        name_key = f"{record['first_name']} {record['last_name']}".lower()
        editorial = _CANDIDATE_EDITORIAL.get(name_key)
        if editorial:
            declared.append(editorial)
        else:
            declared.append(
                {
                    "id": record["last_name"].lower(),
                    "name": f"{record['first_name']} {record['last_name']}",
                    "summary": "",
                }
            )

    return {
        "declared": declared,
        "potential": CANDIDATE_STATUS["potential"],
        "declined": CANDIDATE_STATUS["declined"],
    }
