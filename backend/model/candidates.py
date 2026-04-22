"""Candidate status metadata used by modelling and polling APIs."""

from __future__ import annotations

from typing import TypedDict


class CandidateProfile(TypedDict):
    id: str
    name: str
    summary: str


CANDIDATE_STATUS: dict[str, list[CandidateProfile]] = {
    "declared": [
        {
            "id": "bradford",
            "name": "Brad Bradford",
            "summary": "Ward 19 city councillor since 2018 and declared 2026 mayoral candidate.",
        },
        {
            "id": "sanders",
            "name": "Lyall Sanders",
            "summary": "Social activist and declared 2026 mayoral candidate.",
        },
    ],
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
