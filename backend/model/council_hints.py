"""Candidate-specific historical-hint flags for the Council race card.

These are **historical frontend context, not predictions, causal effects, or model
inputs** — the six supported hints from the `defeatability-index` catalog
(`data/raw/hints/`, ADR 0043). Each hint is a candidate-specific historical
association measured on the 2010/2014/2022 stable-boundary general elections; here
we compute, for each 2026 registered councillor candidate, which hints *trigger*
and attach the catalog's ready `frontend_copy`, estimate, and evidence tier.

Identity follows the vendored contract with one deliberate relaxation the
maintainer chose: a 2026 registration is resolved to a single upstream
`person_id` by a **generous** name match (accent/order/middle-name tolerant,
across all offices), but its history is then exactly the candidacies upstream
linked to that `person_id` — we never re-discover a person by sweeping same-named
candidacies. A name that resolves to two different `person_id`s is left unmatched
rather than guessed. Only `person_id`-linked candidacies are attributable; rows
upstream left unlinked contribute to no one.

History scope (contract `history_scope`): the non-council offices are mayor, MP,
MPP, and trustee; "council" is councillor only. A Returning councillor — a prior
councillor winner who is not the ward's sitting incumbent — has their council
record count toward the combined elected-office measures; a sitting incumbent's
does not. Wins include acclamations; margins are signed vote-share (winner:
share minus runner-up; loser: share minus winner), null for an acclamation with
no runner-up.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

# Contract history_scope.non_council_office_types; "council" is councillor only.
_NON_COUNCIL_OFFICES = frozenset({"mayor", "mp", "mpp", "trustee"})
_COUNCIL_OFFICE = "councillor"


def _name_tokens(name: str) -> frozenset[str]:
    cleaned = re.sub(r"[^a-z\s]", " ", name.lower().replace(",", " "))
    return frozenset(token for token in cleaned.split() if len(token) > 1)


@dataclass(frozen=True, slots=True)
class SupportedHint:
    hint_id: str
    subject: str  # own_history | opponent_history
    candidate_regime: str  # open_contest | all_primary_regimes
    trigger_field: str
    trigger_operator: str
    trigger_value: str
    effect_pp: float
    ci_low_pp: float
    ci_high_pp: float
    effect_unit: str
    evidence_tier: str
    frontend_copy: str


def load_supported_hints(path: str | Path) -> tuple[SupportedHint, ...]:
    with open(path, newline="", encoding="utf-8") as handle:
        return tuple(
            SupportedHint(
                hint_id=row["hint_id"],
                subject=row["subject"],
                candidate_regime=row["candidate_regime"],
                trigger_field=row["trigger_field"],
                trigger_operator=row["trigger_operator"],
                trigger_value=row["trigger_value"],
                effect_pp=float(row["adjusted_vote_share_effect_pp"]),
                ci_low_pp=float(row["ci_low_pp"]),
                ci_high_pp=float(row["ci_high_pp"]),
                effect_unit=row["effect_unit"],
                evidence_tier=row["evidence_tier"],
                frontend_copy=row["frontend_copy"],
            )
            for row in csv.DictReader(handle)
            if row["catalog_status"] == "publish"
        )


def load_hint_contract(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


@dataclass(frozen=True, slots=True)
class CandidacyRecord:
    person_id: str
    office_type: str
    election_date: str  # ISO date; lexical order == chronological
    is_win: bool
    vote_share: float
    margin: float | None  # signed vote-share margin; None for acclamation w/o runner-up
    contest_id: str = ""
    district_name: str = ""  # riding/ward; blank for some rows
    party_name: str = ""  # blank for non-partisan (municipal) races
    represented_body: str = ""  # e.g. canada_house_of_commons, toronto_city_council
    vote_rank: int | None = None  # 1 == first; where they placed
    field_size: int | None = None  # candidates in the contest


def load_officeholding_history(
    path: str | Path,
) -> tuple[dict[str, list[CandidacyRecord]], dict[str, set[frozenset[str]]]]:
    """All-offices candidacy history keyed by upstream ``person_id``, plus each
    person's set of name token-sets (for the generous 2026 name resolver).
    Rows upstream left ``person_id``-blank are unattributable and skipped."""
    with Path(path).open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    # Per-contest winner / runner-up vote shares, for signed margins.
    by_contest: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_contest[row["contest_id"]].append(row)
    contest_top: dict[str, tuple[str, float | None, float | None]] = {}
    for contest_id, entries in by_contest.items():
        ordered = sorted(
            entries,
            key=lambda r: int(r["votes"]) if r["votes"].strip() else -1,
            reverse=True,
        )
        winner_share = _share(ordered[0])
        runner_up_share = _share(ordered[1]) if len(ordered) > 1 else None
        contest_top[contest_id] = (
            ordered[0]["candidacy_id"],
            winner_share,
            runner_up_share,
        )

    history: dict[str, list[CandidacyRecord]] = defaultdict(list)
    name_variants: dict[str, set[frozenset[str]]] = defaultdict(set)
    for row in rows:
        person_id = row["person_id"].strip()
        if not person_id:
            continue
        winner_candidacy, winner_share, runner_up_share = contest_top[row["contest_id"]]
        share = _share(row) or 0.0
        if row["candidacy_id"] == winner_candidacy:
            margin = share - runner_up_share if runner_up_share is not None else None
        else:
            margin = share - winner_share if winner_share is not None else None
        history[person_id].append(
            CandidacyRecord(
                person_id=person_id,
                office_type=row["office_type"],
                election_date=row["election_date"],
                is_win=row["elected"] == "True" or row["acclaimed"] == "True",
                vote_share=share,
                margin=margin,
                contest_id=row["contest_id"],
                district_name=row.get("district_name", "").strip(),
                party_name=row.get("party_name", "").strip(),
                represented_body=row.get("represented_body", "").strip(),
                vote_rank=_int(row.get("vote_rank")),
                field_size=_int(row.get("n_candidates")),
            )
        )
        tokens = _name_tokens(row["candidate_name"])
        if tokens:
            name_variants[person_id].add(tokens)
    return dict(history), dict(name_variants)


def _share(row: dict[str, str]) -> float | None:
    value = row["vote_share"].strip()
    return float(value) if value else None


def _int(value: str | None) -> int | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def resolve_person_id(
    first_name: str,
    last_name: str,
    name_variants: dict[str, set[frozenset[str]]],
) -> str | None:
    """Generous name -> single upstream person_id, or None if unmatched/ambiguous.

    A registration matches a person when its token-set is a subset of, or a
    superset of, any of that person's name token-sets (so middle names and word
    order do not block a match). Matching two different person_ids is ambiguous
    identity and returns None rather than guessing.
    """
    query = _name_tokens(f"{first_name} {last_name}")
    if not query:
        return None
    matched: set[str] = set()
    for person_id, variants in name_variants.items():
        if any(query <= variant or variant <= query for variant in variants):
            matched.add(person_id)
    return next(iter(matched)) if len(matched) == 1 else None


@dataclass(frozen=True, slots=True)
class CandidateFeatures:
    has_prior_elected_office: bool
    prior_office_types_won: frozenset[str]
    prior_elected_candidacy_count: int
    prior_elected_victory_count: int
    most_recent_prior_elected_margin: float | None
    # Provenance carriers (ticket 02); default empty so aggregate-only construction
    # in tests still works.
    candidate_name: str = ""
    qualifying_records: tuple[CandidacyRecord, ...] = ()
    most_recent_qualifying: CandidacyRecord | None = None


def candidate_features(
    records: list[CandidacyRecord], *, name: str = "", is_sitting_incumbent: bool
) -> CandidateFeatures:
    non_council_wins = [
        r for r in records if r.office_type in _NON_COUNCIL_OFFICES and r.is_win
    ]
    council_wins = [r for r in records if r.office_type == _COUNCIL_OFFICE and r.is_win]
    returning_councillor = bool(council_wins) and not is_sitting_incumbent
    # Qualifying elected-office candidacies: all non-council, plus council only for
    # a Returning councillor (contract combined_prior_elected_office / margin_rule).
    qualifying = [r for r in records if r.office_type in _NON_COUNCIL_OFFICES]
    if returning_councillor:
        qualifying += [r for r in records if r.office_type == _COUNCIL_OFFICE]
    most_recent = max(qualifying, key=lambda r: r.election_date) if qualifying else None
    return CandidateFeatures(
        has_prior_elected_office=bool(non_council_wins) or returning_councillor,
        prior_office_types_won=frozenset(r.office_type for r in records if r.is_win),
        prior_elected_candidacy_count=len(qualifying),
        prior_elected_victory_count=sum(1 for r in qualifying if r.is_win),
        most_recent_prior_elected_margin=most_recent.margin if most_recent else None,
        candidate_name=name,
        qualifying_records=tuple(qualifying),
        most_recent_qualifying=most_recent,
    )


@dataclass(frozen=True, slots=True)
class PastElection:
    """One prior candidacy for the descriptive candidate history (ADR 0050)."""

    year: int
    election_date: str  # full ISO date; the ordering key (year is for display)
    office_type: str
    represented_body: str
    district_name: str | None
    party_name: str | None  # None for non-partisan (municipal) races
    result: str  # "won" | "lost"
    vote_share: float | None
    rank: int | None  # placement, 1 == first
    field_size: int | None  # candidates in the contest


def past_election_history(records: list[CandidacyRecord]) -> tuple[PastElection, ...]:
    """Every past candidacy (won and lost), most recent first, one row per contest.

    A ranked-ballot contest appears as several rows for one candidate (intermediate
    rounds); collapse each contest to a single race — won if any round is a win,
    taking the strongest round's share. Party/district are None where the source
    leaves them blank (municipal races carry no party)."""
    by_contest: dict[str, list[CandidacyRecord]] = defaultdict(list)
    for record in records:
        by_contest[record.contest_id].append(record)
    elections: list[PastElection] = []
    for group in by_contest.values():
        head = group[0]
        shares = [r.vote_share for r in group if r.vote_share is not None]
        ranks = [r.vote_rank for r in group if r.vote_rank is not None]
        sizes = [r.field_size for r in group if r.field_size is not None]
        elections.append(
            PastElection(
                year=int(head.election_date[:4]),
                election_date=head.election_date,
                office_type=head.office_type,
                represented_body=head.represented_body,
                district_name=head.district_name or None,
                party_name=head.party_name or None,
                result="won" if any(r.is_win for r in group) else "lost",
                vote_share=max(shares) if shares else None,
                rank=min(ranks) if ranks else None,  # best (final) placement
                field_size=max(sizes) if sizes else None,
            )
        )
    # Full-date descending: same-year races order by their actual dates (ISO
    # dates sort lexically == chronologically).
    elections.sort(key=lambda e: e.election_date, reverse=True)
    return tuple(elections)


_POSITIVE_OWN_PRESENCE = frozenset(
    {"own_any_prior_elected_office__open_contest", "own_prior_win_type__trustee"}
)
_NEGATIVE_OPPONENT = frozenset(
    {
        "opponent_any_prior_elected_office__open_contest",
        "opponent_strongest_prior_elected_margin",
    }
)


def signal_direction(hint_id: str, value: float | None) -> str:
    """Signed historical direction of a fired hint for the candidate whose card it
    appears on: ``"positive"`` or ``"negative"`` (ticket 02).

    Derived from the candidate's actual value AND the measured association, not the
    coefficient alone — a negative most-recent margin or a measured-zero victory
    count reads negative even though those associations' coefficients are positive.
    Opponent-history signals are negative for the subject (a stronger opponent).
    The direction carries no magnitude, probability, or causal claim.
    """
    if hint_id in _POSITIVE_OWN_PRESENCE:
        return "positive"
    if hint_id in _NEGATIVE_OPPONENT:
        return "negative"
    if hint_id == "own_most_recent_prior_elected_margin":
        return "positive" if (value or 0) > 0 else "negative"
    if hint_id == "own_prior_elected_victory_count":
        return "positive" if int(value or 0) >= 1 else "negative"
    return "negative"


@dataclass(frozen=True, slots=True)
class SignalSource:
    """Structured provenance behind a fired signal (ticket 02): the concrete race
    (or aggregate) it rests on, so the frontend can explain it specifically instead
    of printing catalog prose. ``opponent_name`` is set only for opponent signals;
    ``coverage`` distinguishes a measured zero from resolved history."""

    opponent_name: str | None
    office_type: str | None
    year: int | None
    district_name: str | None
    result: str | None  # won | lost
    rank: int | None
    field_size: int | None
    margin: float | None
    victory_count: int | None
    qualifying_candidacy_count: int | None
    coverage: str  # resolved | measured_zero


def _source_from_record(
    record: CandidacyRecord | None,
    *,
    opponent_name: str | None = None,
    victory_count: int | None = None,
    qualifying_candidacy_count: int | None = None,
    coverage: str = "resolved",
) -> SignalSource:
    return SignalSource(
        opponent_name=opponent_name,
        office_type=record.office_type if record else None,
        year=int(record.election_date[:4]) if record else None,
        district_name=(record.district_name or None) if record else None,
        result=("won" if record.is_win else "lost") if record else None,
        rank=record.vote_rank if record else None,
        field_size=record.field_size if record else None,
        margin=record.margin if record else None,
        victory_count=victory_count,
        qualifying_candidacy_count=qualifying_candidacy_count,
        coverage=coverage,
    )


@dataclass(frozen=True, slots=True)
class FiredHint:
    hint_id: str
    subject: str
    value: float | int | None  # continuous hints carry their per-candidate value
    frontend_copy: str
    effect_pp: float
    ci_low_pp: float
    ci_high_pp: float
    effect_unit: str
    evidence_tier: str
    direction: str = ""  # positive | negative (ticket 02)
    source: SignalSource | None = None  # structured provenance (ticket 02)


def _fire(
    hint: SupportedHint,
    fields: dict[str, object],
    *,
    is_open_contest: bool,
) -> FiredHint | None:
    if hint.candidate_regime == "open_contest" and not is_open_contest:
        return None
    value: float | int | None = None
    if hint.trigger_operator == "equals":
        fired = fields[hint.trigger_field] is True
    elif hint.trigger_operator == "contains_office_type":
        won = fields[hint.trigger_field]
        fired = isinstance(won, frozenset) and hint.trigger_value in won
    elif hint.trigger_operator == "continuous":
        candidate_value = fields[hint.trigger_field]
        fired = candidate_value is not None
        value = candidate_value if fired else None  # type: ignore[assignment]
    elif hint.trigger_operator == "continuous_prior_elected_history_only":
        fired = int(fields["prior_elected_candidacy_count"]) > 0  # type: ignore[arg-type]
        value = int(fields[hint.trigger_field]) if fired else None  # type: ignore[arg-type]
    else:
        return None
    if not fired:
        return None
    return FiredHint(
        hint_id=hint.hint_id,
        subject=hint.subject,
        value=value,
        frontend_copy=hint.frontend_copy,
        effect_pp=hint.effect_pp,
        ci_low_pp=hint.ci_low_pp,
        ci_high_pp=hint.ci_high_pp,
        effect_unit=hint.effect_unit,
        evidence_tier=hint.evidence_tier,
        direction=signal_direction(hint.hint_id, value),
    )


def fire_candidate_hints(
    features: CandidateFeatures,
    opponents: list[CandidateFeatures],
    *,
    is_open_contest: bool,
    hints: tuple[SupportedHint, ...],
) -> tuple[FiredHint, ...]:
    """Fire the supported hints for one candidate given their features and the
    features of their matched ward opponents."""
    opponent_margins = [
        o.most_recent_prior_elected_margin
        for o in opponents
        if o.most_recent_prior_elected_margin is not None
    ]
    fields: dict[str, object] = {
        "has_prior_elected_office": features.has_prior_elected_office,
        "prior_office_types_won": features.prior_office_types_won,
        "most_recent_prior_elected_margin": features.most_recent_prior_elected_margin,
        "prior_elected_candidacy_count": features.prior_elected_candidacy_count,
        "prior_elected_victory_count": features.prior_elected_victory_count,
        "any_prior_elected_office_opponent": any(
            o.has_prior_elected_office for o in opponents
        ),
        "strongest_opponent_prior_elected_margin": (
            max(opponent_margins) if opponent_margins else None
        ),
    }
    fired = [
        hint
        for hint in (
            _fire(hint, fields, is_open_contest=is_open_contest) for hint in hints
        )
        if hint is not None
    ]

    # Provenance anchors (ticket 02): the concrete race behind each fired signal.
    own_wins = [r for r in features.qualifying_records if r.is_win]
    most_recent_own_win = max(own_wins, key=lambda r: r.election_date, default=None)
    trustee_win = max(
        (
            r
            for r in features.qualifying_records
            if r.is_win and r.office_type == "trustee"
        ),
        key=lambda r: r.election_date,
        default=None,
    )
    strongest_opp = max(
        (o for o in opponents if o.most_recent_prior_elected_margin is not None),
        key=lambda o: o.most_recent_prior_elected_margin,
        default=None,
    )
    opp_with_office = max(
        (o for o in opponents if o.has_prior_elected_office),
        key=lambda o: (
            o.most_recent_prior_elected_margin
            if o.most_recent_prior_elected_margin is not None
            else -9.0
        ),
        default=None,
    )

    def source_for(hint_id: str) -> SignalSource | None:
        if hint_id == "own_most_recent_prior_elected_margin":
            return _source_from_record(features.most_recent_qualifying)
        if hint_id == "own_prior_elected_victory_count":
            count = features.prior_elected_victory_count
            return _source_from_record(
                features.most_recent_qualifying,
                victory_count=count,
                qualifying_candidacy_count=features.prior_elected_candidacy_count,
                coverage="measured_zero" if count == 0 else "resolved",
            )
        if hint_id == "own_any_prior_elected_office__open_contest":
            return _source_from_record(
                most_recent_own_win or features.most_recent_qualifying
            )
        if hint_id == "own_prior_win_type__trustee":
            return _source_from_record(trustee_win)
        if hint_id == "opponent_strongest_prior_elected_margin" and strongest_opp:
            return _source_from_record(
                strongest_opp.most_recent_qualifying,
                opponent_name=strongest_opp.candidate_name,
            )
        if (
            hint_id == "opponent_any_prior_elected_office__open_contest"
            and opp_with_office
        ):
            return _source_from_record(
                opp_with_office.most_recent_qualifying,
                opponent_name=opp_with_office.candidate_name,
            )
        return None

    return tuple(replace(hint, source=source_for(hint.hint_id)) for hint in fired)
