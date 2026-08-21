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
from dataclasses import dataclass
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
            )
        )
        tokens = _name_tokens(row["candidate_name"])
        if tokens:
            name_variants[person_id].add(tokens)
    return dict(history), dict(name_variants)


def _share(row: dict[str, str]) -> float | None:
    value = row["vote_share"].strip()
    return float(value) if value else None


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


def candidate_features(
    records: list[CandidacyRecord], *, is_sitting_incumbent: bool
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
    fired = (_fire(hint, fields, is_open_contest=is_open_contest) for hint in hints)
    return tuple(hint for hint in fired if hint is not None)
