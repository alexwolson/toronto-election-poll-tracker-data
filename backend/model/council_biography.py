"""Candidate electoral biography from historical council results (ADR 0043).

The descriptive backbone of the Council v1 race card: each candidate's prior
council electoral record, used to render biographies and derived competitiveness
facts — not as a model input (ADR 0009/0028 officeholding history, used
descriptively).

Identity is the dataset's own `candidate_key`, matched exactly. That key is
consistent per person across years and the 44->25 ward redraw (e.g. `filion john`
spans wards 23->18; `layton mike` spans wards 19->11), and it correctly separates
surname collisions (`clayton jones` is not `layton mike`). Exact-key matching is
therefore the honest identity *within* the historical corpus; matching an external
current-cycle name to a key is a separate concern with its own fuzzy join.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


def _to_int(value: str) -> int:
    return int(value) if value.strip() else 0


def _to_float(value: str) -> float:
    return float(value) if value.strip() else 0.0


@dataclass(frozen=True, slots=True)
class CouncilElectionResult:
    election_year: int
    ward: str
    boundary_era: str
    candidate_name: str
    candidate_key: str
    votes: int
    vote_share: float
    is_winner: bool
    is_acclaimed: bool


@dataclass(frozen=True, slots=True)
class ElectoralAppearance:
    year: int
    ward: str
    boundary_era: str
    vote_share: float
    votes: int
    is_winner: bool
    is_acclaimed: bool


@dataclass(frozen=True, slots=True)
class CandidateBiography:
    candidate_key: str
    display_name: str
    appearances: tuple[ElectoralAppearance, ...]  # chronological, year ascending

    @property
    def council_wins(self) -> int:
        return sum(1 for appearance in self.appearances if appearance.is_winner)

    @property
    def is_former_councillor(self) -> bool:
        return self.council_wins >= 1

    @property
    def most_recent_win(self) -> ElectoralAppearance | None:
        wins = [a for a in self.appearances if a.is_winner]
        return max(wins, key=lambda a: a.year) if wins else None

    @property
    def best_result(self) -> ElectoralAppearance | None:
        if not self.appearances:
            return None
        return max(self.appearances, key=lambda a: a.vote_share)

    def wins_in_ward(
        self, ward: str, boundary_era: str
    ) -> tuple[ElectoralAppearance, ...]:
        """Winning appearances in a specific ward of a specific boundary era.

        Ward numbers are only comparable within an era (the 2018 redraw reassigned
        them), so both must match.
        """
        return tuple(
            a
            for a in self.appearances
            if a.is_winner and a.ward == ward and a.boundary_era == boundary_era
        )


def load_council_results(path: str | Path) -> tuple[CouncilElectionResult, ...]:
    with open(path, newline="", encoding="utf-8") as handle:
        rows = tuple(
            CouncilElectionResult(
                election_year=int(row["election_year"]),
                ward=row["ward"],
                boundary_era=row["boundary_era"],
                candidate_name=row["candidate_name"],
                candidate_key=row["candidate_key"],
                votes=_to_int(row["votes"]),
                vote_share=_to_float(row["vote_share"]),
                is_winner=row["is_winner"] == "True",
                is_acclaimed=row["is_acclaimed"] == "True",
            )
            for row in csv.DictReader(handle)
        )
    return rows


def _appearance(result: CouncilElectionResult) -> ElectoralAppearance:
    return ElectoralAppearance(
        year=result.election_year,
        ward=result.ward,
        boundary_era=result.boundary_era,
        vote_share=result.vote_share,
        votes=result.votes,
        is_winner=result.is_winner,
        is_acclaimed=result.is_acclaimed,
    )


def build_candidate_biography(
    candidate_key: str, results: tuple[CouncilElectionResult, ...]
) -> CandidateBiography:
    mine = [r for r in results if r.candidate_key == candidate_key]
    mine.sort(key=lambda r: r.election_year)
    display_name = mine[-1].candidate_name if mine else candidate_key
    return CandidateBiography(
        candidate_key=candidate_key,
        display_name=display_name,
        appearances=tuple(_appearance(r) for r in mine),
    )


def build_all_biographies(
    results: tuple[CouncilElectionResult, ...],
) -> dict[str, CandidateBiography]:
    keys = {r.candidate_key for r in results}
    return {key: build_candidate_biography(key, results) for key in keys}
