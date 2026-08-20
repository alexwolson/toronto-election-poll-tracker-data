"""Mayoral current-cycle polling evidence tier (ADR 0033).

Every public Mayoral quantity displays its evidence tier — M0 Structural Only,
M1 Pre-Final Polling, M2 Post-Final Polling, or M3 Replicated Post-Final Polling
— separately from whether the quantity is Available. The tier sets eligibility
*floors* only: it is a necessary condition, never a sufficient one, and never a
confidence rating. Every other Publication Gate still applies downstream.

A sample is post-Final when its fieldwork interval overlaps or follows the
conservative date-time when the certified Final Ballot was publicly knowable
(nomination close, ADR 0002); a sample completed entirely before that boundary
is pre-Final. Comparison honours the source's recorded precision: a date-only
fieldwork end that lands on the boundary day overlaps the intra-day boundary and
so counts as post-Final.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class MayoralEvidenceTier(Enum):
    """The four mayoral evidence tiers, ranked; labels are ADR 0033 verbatim."""

    M0_STRUCTURAL = (0, "M0 — Structural Only")
    M1_PRE_FINAL = (1, "M1 — Pre-Final Polling")
    M2_POST_FINAL = (2, "M2 — Post-Final Polling")
    M3_REPLICATED_POST_FINAL = (3, "M3 — Replicated Post-Final Polling")

    def __init__(self, rank: int, label: str) -> None:
        self.rank = rank
        self.label = label


@dataclass(frozen=True, slots=True)
class MayoralPollSampleEvidence:
    """One current-cycle Distinct Poll Sample, reduced to what the tier needs."""

    sample_id: str
    pollster: str
    fieldwork_end: date | datetime
    measured_candidates: frozenset[str]


def _is_post_final(fieldwork_end: date | datetime, nomination_close: datetime) -> bool:
    # datetime precision: direct instant comparison. date precision: the sample's
    # fieldwork day overlaps the boundary iff that day is on or after the boundary
    # day (a sample completed entirely before the boundary ends on an earlier day).
    if isinstance(fieldwork_end, datetime):
        return fieldwork_end >= nomination_close
    return fieldwork_end >= nomination_close.date()


@dataclass(frozen=True, slots=True)
class MayoralEvidenceTierResult:
    """The classified tier plus per-quantity eligibility floors (ADR 0033)."""

    tier: MayoralEvidenceTier
    post_final_sample_ids: tuple[str, ...]
    _samples: tuple[MayoralPollSampleEvidence, ...]
    _post_final_ids: frozenset[str]

    @property
    def close_result_eligible(self) -> bool:
        # Close-Result Probability requires at least one post-Final sample (M2).
        return self.tier.rank >= MayoralEvidenceTier.M2_POST_FINAL.rank

    @property
    def incumbent_defeat_eligible(self) -> bool:
        # Incumbent Defeat Probability requires at least one post-Final sample (M2).
        return self.tier.rank >= MayoralEvidenceTier.M2_POST_FINAL.rank

    def challenger_win_eligible(self, candidate_id: str) -> bool:
        # A challenger's Candidate Win Probability requires M3 for that challenger:
        # >=3 Distinct Poll Samples measuring the challenger, across >=2 pollsters,
        # with >=2 of those post-Final.
        measuring = [
            sample
            for sample in self._samples
            if candidate_id in sample.measured_candidates
        ]
        if len(measuring) < 3:
            return False
        if len({sample.pollster for sample in measuring}) < 2:
            return False
        post_final = sum(
            1 for sample in measuring if sample.sample_id in self._post_final_ids
        )
        return post_final >= 2


def classify_mayoral_evidence_tier(
    samples: object,
    *,
    nomination_close: datetime,
) -> MayoralEvidenceTierResult:
    """Classify current-cycle qualifying Distinct Poll Samples into a tier.

    `samples` are the already-qualifying Distinct Poll Samples for the current
    cycle. Tier progression: M0 (none) -> M1 (qualifying, all pre-Final) -> M2
    (>=1 post-Final) -> M3 (replicated post-Final: >=3 samples, >=2 pollsters,
    >=2 post-Final).
    """

    samples = tuple(samples)
    post_final_ids = frozenset(
        sample.sample_id
        for sample in samples
        if _is_post_final(sample.fieldwork_end, nomination_close)
    )
    post_final_sample_ids = tuple(
        sample.sample_id for sample in samples if sample.sample_id in post_final_ids
    )

    if not samples:
        tier = MayoralEvidenceTier.M0_STRUCTURAL
    elif not post_final_ids:
        tier = MayoralEvidenceTier.M1_PRE_FINAL
    elif (
        len(samples) >= 3
        and len({sample.pollster for sample in samples}) >= 2
        and len(post_final_ids) >= 2
    ):
        tier = MayoralEvidenceTier.M3_REPLICATED_POST_FINAL
    else:
        tier = MayoralEvidenceTier.M2_POST_FINAL

    return MayoralEvidenceTierResult(
        tier=tier,
        post_final_sample_ids=post_final_sample_ids,
        _samples=samples,
        _post_final_ids=post_final_ids,
    )
