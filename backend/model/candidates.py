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
    "potential": [],
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
    "olivia chow": {
        "id": "chow",
        "name": "Olivia Chow",
        "summary": "Incumbent mayor since 2023; registered for re-election on May 25, 2026.",
    },
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
    # Editorial and declined ids are reserved so an API-derived last-name slug
    # can never collide with them (e.g. Braeden Chow must not get id "chow").
    used_ids = (
        {profile["id"] for profile in _CANDIDATE_EDITORIAL.values()}
        | {profile["id"] for profile in CANDIDATE_STATUS["potential"]}
        | DECLINED_CANDIDATE_IDS
    )
    declared: list[CandidateProfile] = []
    for record in declared_records:
        if record.get("status") != "Active":
            continue
        name_key = f"{record['first_name']} {record['last_name']}".lower()
        editorial = _CANDIDATE_EDITORIAL.get(name_key)
        if editorial:
            declared.append(editorial)
            continue
        candidate_id = record["last_name"].lower()
        if candidate_id in used_ids:
            candidate_id = name_key.replace(" ", "-")
        used_ids.add(candidate_id)
        declared.append(
            {
                "id": candidate_id,
                "name": f"{record['first_name']} {record['last_name']}",
                "summary": "",
            }
        )

    declared_ids = {profile["id"] for profile in declared}
    return {
        "declared": declared,
        "potential": [
            profile
            for profile in CANDIDATE_STATUS["potential"]
            if profile["id"] not in declared_ids
        ],
        "declined": CANDIDATE_STATUS["declined"],
    }
