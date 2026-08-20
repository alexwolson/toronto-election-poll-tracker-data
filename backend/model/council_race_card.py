"""Race-card signals: CDI exposure triggers + derived competitiveness facts (ADR 0043).

The presentational layer of the Council v1 race card. Two kinds of signal, both
strictly non-predictive:

* **Exposure triggers** — the Council Defeatability Index surfaced as Matt
  Elliott's pre-specified, house-voice watch-list cues (never odds, never a
  Safe/Competitive verdict, ADR 0036). Thresholds are fixed to the CDI report, not
  tuned. Triggers describe an *incumbent's* structural exposure, so they are gated
  off for open seats.
* **Competitiveness facts** — plain facts a reader can weigh (last winning margin,
  whether more than one candidate has previously won the ward, field size), which
  convey the shape of a race without our calling it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.model.council_biography import CouncilElectionResult
from backend.model.council_race import CouncilRace, WardIncumbent

CURRENT_BOUNDARY_ERA = "25_ward"

# Fixed to the CDI validation report (never threshold-tuned — that overfits).
_NARROW_WIN_MAX_SHARE = 0.35
_HIGH_EXPOSURE_MIN_SCORE = 65  # the report's Youden-J operating point

COUNCIL_INCUMBENT_BASE_RATE_COPY = (
    "Toronto council incumbents rarely lose — about 6% in a normal election — "
    "so a fired trigger means elevated attention, not a likely defeat."
)


@dataclass(frozen=True, slots=True)
class ExposureTrigger:
    key: str
    copy: str


_NARROW_PRIOR_WIN = ExposureTrigger(
    "narrow_prior_win",
    "won with under 35% of the vote, below the range where incumbents typically feel safe",
)
_WARD_GROWTH = ExposureTrigger(
    "ward_growth_exceeds_cushion",
    "the ward has added more electors since the win than the incumbent's margin of victory",
)
_HIGH_EXPOSURE = ExposureTrigger(
    "high_structural_exposure",
    "among the most structurally exposed wards on the combined index",
)


def _parse_new_voter_margin(notes: str) -> int | None:
    match = re.search(r"New Voter Margin:\s*([+-]?\d+)", notes)
    return int(match.group(1)) if match else None


def exposure_triggers(incumbent: WardIncumbent) -> tuple[ExposureTrigger, ...]:
    """The CDI watch-list triggers an incumbent's own numbers fire (ungated)."""
    triggers: list[ExposureTrigger] = []
    if (
        incumbent.vote_share is not None
        and incumbent.vote_share < _NARROW_WIN_MAX_SHARE
    ):
        triggers.append(_NARROW_PRIOR_WIN)
    new_voter_margin = _parse_new_voter_margin(incumbent.notes)
    if new_voter_margin is not None and new_voter_margin > 0:
        triggers.append(_WARD_GROWTH)
    if (
        incumbent.defeatability_score is not None
        and incumbent.defeatability_score >= _HIGH_EXPOSURE_MIN_SCORE
    ):
        triggers.append(_HIGH_EXPOSURE)
    return tuple(triggers)


def race_exposure_triggers(race: CouncilRace) -> tuple[ExposureTrigger, ...]:
    """Exposure triggers for a race, gated off when the seat is open."""
    if race.is_open_seat:
        return ()
    return exposure_triggers(race.incumbent)


@dataclass(frozen=True, slots=True)
class PriorResult:
    ward: str
    year: int
    winner_name: str
    winner_votes: int
    winner_share: float
    runner_up_name: str | None
    runner_up_votes: int | None
    runner_up_share: float | None
    field_size: int

    @property
    def margin_votes(self) -> int | None:
        if self.runner_up_votes is None:
            return None
        return self.winner_votes - self.runner_up_votes

    @property
    def margin_share(self) -> float | None:
        if self.runner_up_share is None:
            return None
        return self.winner_share - self.runner_up_share


def build_prior_results(
    results: tuple[CouncilElectionResult, ...],
    year: int = 2022,
    boundary_era: str = CURRENT_BOUNDARY_ERA,
) -> dict[str, PriorResult]:
    by_ward: dict[str, list[CouncilElectionResult]] = {}
    for row in results:
        if row.election_year == year and row.boundary_era == boundary_era:
            by_ward.setdefault(row.ward, []).append(row)
    prior: dict[str, PriorResult] = {}
    for ward, rows in by_ward.items():
        ordered = sorted(rows, key=lambda r: r.votes, reverse=True)
        winner = ordered[0]
        runner_up = ordered[1] if len(ordered) > 1 else None
        prior[ward] = PriorResult(
            ward=ward,
            year=year,
            winner_name=winner.candidate_name,
            winner_votes=winner.votes,
            winner_share=winner.vote_share,
            runner_up_name=runner_up.candidate_name if runner_up else None,
            runner_up_votes=runner_up.votes if runner_up else None,
            runner_up_share=runner_up.vote_share if runner_up else None,
            field_size=len(rows),
        )
    return prior


@dataclass(frozen=True, slots=True)
class CompetitivenessFacts:
    field_size: int
    candidates_who_won_this_ward: int
    both_won_this_ward: bool
    prior_margin_votes: int | None
    prior_margin_share: float | None


def derive_competitiveness_facts(
    race: CouncilRace, prior: PriorResult | None
) -> CompetitivenessFacts:
    won_this_ward = sum(
        1
        for candidate in race.candidates
        if candidate.biography is not None
        and candidate.biography.wins_in_ward(race.ward, CURRENT_BOUNDARY_ERA)
    )
    return CompetitivenessFacts(
        field_size=len(race.candidates),
        candidates_who_won_this_ward=won_this_ward,
        both_won_this_ward=won_this_ward >= 2,
        prior_margin_votes=prior.margin_votes if prior else None,
        prior_margin_share=prior.margin_share if prior else None,
    )
