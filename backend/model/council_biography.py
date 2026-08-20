"""Candidate electoral biography from the canonical results dataset (ADR 0043, 0044).

The descriptive backbone of the Council v1 race card: each candidate's prior
council electoral record, used to render biographies and derived competitiveness
facts — not as a model input.

Results come from the vendored canonical dataset (`toronto-election-results`,
ADR 0044), filtered to `office = councillor`. Identity is that dataset's
persistent, fuzzy-matched `candidate_id`, which links a person across years and
the 44->25 ward redraw (e.g. `c00755` John Filion spans wards 23->18) and cleanly
separates same-surname people (Mike Layton `c01140` vs Clayton Jones `c00487`) —
so the biography no longer re-implements name matching.
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
    boundary_era: str  # "44-ward" | "25-ward" (canonical ward_system)
    candidate_id: str
    candidate_name: str
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
    candidate_id: str
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
    """Load councillor rows from the vendored canonical results table."""
    with open(path, newline="", encoding="utf-8") as handle:
        rows = tuple(
            CouncilElectionResult(
                election_year=int(row["election_year"]),
                ward=row["ward_number"],
                boundary_era=row["ward_system"],
                candidate_id=row["candidate_id"],
                candidate_name=row["candidate_name"],
                votes=_to_int(row["votes"]),
                vote_share=_to_float(row["vote_share"]),
                is_winner=row["elected"] == "True",
                is_acclaimed=row["acclaimed"] == "True",
            )
            for row in csv.DictReader(handle)
            if row["office"] == "councillor"
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
    candidate_id: str, results: tuple[CouncilElectionResult, ...]
) -> CandidateBiography:
    mine = [r for r in results if r.candidate_id and r.candidate_id == candidate_id]
    mine.sort(key=lambda r: r.election_year)
    display_name = mine[-1].candidate_name if mine else candidate_id
    return CandidateBiography(
        candidate_id=candidate_id,
        display_name=display_name,
        appearances=tuple(_appearance(r) for r in mine),
    )


def build_all_biographies(
    results: tuple[CouncilElectionResult, ...],
) -> dict[str, CandidateBiography]:
    # Rows with no canonical candidate_id could not be linked to a person and are
    # skipped (they carry no cross-year biography anyway).
    ids = {r.candidate_id for r in results if r.candidate_id}
    return {cid: build_candidate_biography(cid, results) for cid in ids}
