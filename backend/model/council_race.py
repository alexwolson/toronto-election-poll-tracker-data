"""Per-ward Council race assembly (C1 increment 2, ADR 0043).

Joins three sources into one `CouncilRace` per ward: the current incumbent from
`ward_defeatability.csv` (the canonical, by-election-aware incumbency source), the
2026 candidate field from `councillor_registered.csv`, and each candidate's
electoral biography (council_biography.py).

Open-seat status is **derived from the fresh registered field**, not the incumbency
file's `is_running` flag: the incumbent seeks re-election iff they appear in the
current field, which stays correct when the flag goes stale (e.g. an incumbent who
withdraws after the flag was last set). The `is_running` flag is kept only as a
cross-check — `incumbency_flag_disagrees` marks wards where the two disagree, for
editorial review (a real withdrawal the flag missed, or a name-match miss).

Matching a current-cycle registration name to a historical `candidate_id` is a
fuzzy join: the registration gives "First Last" and no id, so we index the
canonical people by the **token set** of their (normalized) name and match
exactly. A token set that maps to more than one candidate_id is treated as
unmatched rather than guessed — a missing biography degrades to "newcomer", never
to a wrong record. Middle names / nicknames that break exact token-set equality
are a known, safe-direction limitation (they show as newcomers).
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from backend.model.council_biography import CandidateBiography


@dataclass(frozen=True, slots=True)
class WardIncumbent:
    ward: str
    name: str
    is_running: bool
    is_byelection_incumbent: bool
    defeatability_score: int | None
    vote_share: float | None
    notes: str
    biography: CandidateBiography | None


@dataclass(frozen=True, slots=True)
class RaceCandidate:
    display_name: str
    status: str
    candidate_id: str | None
    biography: CandidateBiography | None

    @property
    def is_matched(self) -> bool:
        return self.candidate_id is not None


@dataclass(frozen=True, slots=True)
class CouncilRace:
    ward: str
    incumbent: WardIncumbent
    is_open_seat: bool  # derived: the incumbent is absent from the current field
    incumbent_in_field: bool
    incumbency_flag_disagrees: bool  # field membership vs the is_running flag
    candidates: tuple[RaceCandidate, ...]


def _name_tokens(name: str) -> frozenset[str]:
    cleaned = re.sub(r"[^a-z\s]", " ", name.lower().replace(",", " "))
    return frozenset(token for token in cleaned.split() if len(token) > 1)


def _build_name_index(
    biographies: dict[str, CandidateBiography],
) -> tuple[dict[frozenset[str], str], set[frozenset[str]]]:
    """Map each unambiguous name token-set to its candidate_id.

    A token-set claimed by more than one key is recorded as ambiguous and
    excluded, so a lookup on it returns nothing rather than an arbitrary match.
    """
    index: dict[frozenset[str], str] = {}
    ambiguous: set[frozenset[str]] = set()
    for key, bio in biographies.items():
        tokens = _name_tokens(bio.display_name)
        if not tokens:
            continue
        if tokens in ambiguous:
            continue
        existing = index.get(tokens)
        if existing is not None and existing != key:
            del index[tokens]
            ambiguous.add(tokens)
        else:
            index[tokens] = key
    return index, ambiguous


def _match_tokens(
    tokens: frozenset[str],
    index: dict[frozenset[str], str],
    ambiguous: set[frozenset[str]],
    biographies: dict[str, CandidateBiography],
) -> CandidateBiography | None:
    if not tokens or tokens in ambiguous:
        return None
    key = index.get(tokens)
    return biographies[key] if key is not None else None


def match_biography(
    first_name: str,
    last_name: str,
    biographies: dict[str, CandidateBiography],
) -> CandidateBiography | None:
    """Match a current-cycle candidate name to a historical biography, or None."""
    index, ambiguous = _build_name_index(biographies)
    tokens = _name_tokens(f"{first_name} {last_name}")
    return _match_tokens(tokens, index, ambiguous, biographies)


def _to_int(value: str) -> int | None:
    return int(value) if value.strip() else None


def _to_float(value: str) -> float | None:
    return float(value) if value.strip() else None


def load_ward_incumbency(path: str | Path) -> dict[str, dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return {row["ward"]: row for row in csv.DictReader(handle)}


def load_registered_field(path: str | Path) -> dict[str, list[dict[str, str]]]:
    field: dict[str, list[dict[str, str]]] = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            field.setdefault(row["ward"], []).append(row)
    return field


def build_council_races(
    incumbency: dict[str, dict[str, str]],
    field: dict[str, list[dict[str, str]]],
    biographies: dict[str, CandidateBiography],
) -> dict[str, CouncilRace]:
    index, ambiguous = _build_name_index(biographies)

    def match(name_tokens: frozenset[str]) -> CandidateBiography | None:
        return _match_tokens(name_tokens, index, ambiguous, biographies)

    races: dict[str, CouncilRace] = {}
    for ward, row in incumbency.items():
        is_running = row["is_running"].strip().lower() == "true"
        incumbent = WardIncumbent(
            ward=ward,
            name=row["councillor_name"],
            is_running=is_running,
            is_byelection_incumbent=row.get("is_byelection_incumbent", "")
            .strip()
            .lower()
            == "true",
            defeatability_score=_to_int(row.get("defeatability_score", "")),
            vote_share=_to_float(row.get("vote_share", "")),
            notes=row.get("notes", ""),
            biography=match(_name_tokens(row["councillor_name"])),
        )
        candidates = []
        field_token_sets = []
        for entry in field.get(ward, []):
            tokens = _name_tokens(f"{entry['first_name']} {entry['last_name']}")
            field_token_sets.append(tokens)
            bio = match(tokens)
            candidates.append(
                RaceCandidate(
                    display_name=f"{entry['first_name']} {entry['last_name']}",
                    status=entry.get("status", ""),
                    candidate_id=bio.candidate_id if bio else None,
                    biography=bio,
                )
            )
        # Open-seat is derived from the fresh registered field, not the (staler)
        # is_running flag: the incumbent seeks re-election iff they appear in it.
        incumbent_tokens = _name_tokens(incumbent.name)
        incumbent_in_field = any(
            len(incumbent_tokens & tokens) >= 2 for tokens in field_token_sets
        )
        races[ward] = CouncilRace(
            ward=ward,
            incumbent=incumbent,
            is_open_seat=not incumbent_in_field,
            incumbent_in_field=incumbent_in_field,
            incumbency_flag_disagrees=incumbent_in_field != is_running,
            candidates=tuple(candidates),
        )
    return races
