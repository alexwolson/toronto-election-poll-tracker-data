"""Mayoral current-cycle polling evidence tier (ADR 0033, 0046).

Every public Mayoral quantity displays its evidence tier — M0 Structural Only,
M1 Pre-Final Polling, M2 Final-Field Polling, or M3 Replicated Final-Field
Polling — separately from whether the quantity is Available. The tier sets
eligibility *floors* only: it is a necessary condition, never a sufficient one,
and never a confidence rating. Every other Publication Gate still applies
downstream.

A sample is **final-field** when the certified Final Ballot is set and the named
candidates it individually measured equal the certified viable field — the
candidates the forecast models distinctly (ADR 0046). This replaces the earlier
fieldwork-date boundary (ADR 0033): what matters is that the poll measured the
field that will actually be on the ballot, not the calendar date it was fielded.
A poll missing a viable candidate (fielded before that candidate entered) or
measuring a candidate absent from the final ballot (fielded before they withdrew)
is not final-field. Until the field is certified (`final_field is None`) no
sample can be final-field, so the cycle caps at M1 — which correctly withholds
before nominations close, and self-protects against a surprise filing: if the
certified field contains someone no poll measured, nothing is final-field.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MayoralEvidenceTier(Enum):
    """The four mayoral evidence tiers, ranked; labels are ADR 0033/0046 verbatim."""

    M0_STRUCTURAL = (0, "M0 — Structural Only")
    M1_PRE_FINAL = (1, "M1 — Pre-Final Polling")
    M2_POST_FINAL = (2, "M2 — Final-Field Polling")
    M3_REPLICATED_POST_FINAL = (3, "M3 — Replicated Final-Field Polling")

    def __init__(self, rank: int, label: str) -> None:
        self.rank = rank
        self.label = label


@dataclass(frozen=True, slots=True)
class MayoralPollSampleEvidence:
    """One current-cycle Distinct Poll Sample, reduced to what the tier needs."""

    sample_id: str
    pollster: str
    measured_candidates: frozenset[str]


def _is_final_field(
    measured_candidates: frozenset[str], final_field: frozenset[str] | None
) -> bool:
    # Final-field iff the certified viable field is known and the sample measured
    # exactly it: no viable candidate missing, no dropped-out candidate carried.
    return final_field is not None and measured_candidates == final_field


@dataclass(frozen=True, slots=True)
class MayoralEvidenceTierResult:
    """The classified tier plus per-quantity eligibility floors (ADR 0033/0046)."""

    tier: MayoralEvidenceTier
    final_field_sample_ids: tuple[str, ...]
    _samples: tuple[MayoralPollSampleEvidence, ...]
    _final_field_ids: frozenset[str]

    @property
    def close_result_eligible(self) -> bool:
        # Close-Result Probability requires at least one final-field sample (M2).
        return self.tier.rank >= MayoralEvidenceTier.M2_POST_FINAL.rank

    @property
    def incumbent_defeat_eligible(self) -> bool:
        # Incumbent Defeat Probability requires at least one final-field sample (M2).
        return self.tier.rank >= MayoralEvidenceTier.M2_POST_FINAL.rank

    def challenger_win_eligible(self, candidate_id: str) -> bool:
        # A challenger's Candidate Win Probability requires M3 for that challenger:
        # >=3 Distinct Poll Samples measuring the challenger, across >=2 pollsters,
        # with >=2 of those final-field.
        measuring = [
            sample
            for sample in self._samples
            if candidate_id in sample.measured_candidates
        ]
        if len(measuring) < 3:
            return False
        if len({sample.pollster for sample in measuring}) < 2:
            return False
        final_field = sum(
            1 for sample in measuring if sample.sample_id in self._final_field_ids
        )
        return final_field >= 2


def classify_mayoral_evidence_tier(
    samples: object,
    *,
    final_field: frozenset[str] | None,
) -> MayoralEvidenceTierResult:
    """Classify current-cycle qualifying Distinct Poll Samples into a tier.

    `samples` are the already-qualifying Distinct Poll Samples for the current
    cycle; `final_field` is the certified viable field (or None before the Final
    Ballot is set). Tier progression: M0 (none) -> M1 (qualifying, none
    final-field) -> M2 (>=1 final-field) -> M3 (replicated final-field: >=3
    samples, >=2 pollsters, >=2 final-field).
    """

    samples = tuple(samples)
    final_field_ids = frozenset(
        sample.sample_id
        for sample in samples
        if _is_final_field(sample.measured_candidates, final_field)
    )
    final_field_sample_ids = tuple(
        sample.sample_id for sample in samples if sample.sample_id in final_field_ids
    )

    if not samples:
        tier = MayoralEvidenceTier.M0_STRUCTURAL
    elif not final_field_ids:
        tier = MayoralEvidenceTier.M1_PRE_FINAL
    elif (
        len(samples) >= 3
        and len({sample.pollster for sample in samples}) >= 2
        and len(final_field_ids) >= 2
    ):
        tier = MayoralEvidenceTier.M3_REPLICATED_POST_FINAL
    else:
        tier = MayoralEvidenceTier.M2_POST_FINAL

    return MayoralEvidenceTierResult(
        tier=tier,
        final_field_sample_ids=final_field_sample_ids,
        _samples=samples,
        _final_field_ids=final_field_ids,
    )
