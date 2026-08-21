"""Descriptive mayoral polling feed for the frontend package (INT).

Purely descriptive: the current-cycle citywide mayoral polls exactly as recorded
in ``polls.csv`` (the Wikipedia-fed series), plus each candidate's reported share
over time. There is **no fitted average or pool model** — that layer is retired
(ADR 0044) and this feed makes no modelling claim. It is separate from the
forecast feed, which fits the endpoint on the audited poll bundle.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

MAYORAL_POLLING_FEED_SCHEMA_VERSION = 1

_METADATA = frozenset(
    {
        "poll_id",
        "firm",
        "date_conducted",
        "date_published",
        "sample_size",
        "methodology",
        "field_tested",
        "notes",
    }
)


@dataclass(frozen=True, slots=True)
class MayoralPoll:
    poll_id: str
    firm: str
    date_conducted: str
    date_published: str
    sample_size: int | None
    methodology: str
    field_tested: tuple[str, ...]
    shares: dict[str, float]
    notes: str


def load_mayoral_polls(path: str | Path) -> tuple[MayoralPoll, ...]:
    """Load citywide mayoral polls, newest published first."""
    polls: list[MayoralPoll] = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            shares = {
                key: float(value)
                for key, value in row.items()
                if key not in _METADATA and value.strip()
            }
            size = row["sample_size"].strip()
            polls.append(
                MayoralPoll(
                    poll_id=row["poll_id"],
                    firm=row["firm"],
                    date_conducted=row["date_conducted"],
                    date_published=row["date_published"],
                    sample_size=int(size) if size else None,
                    methodology=row["methodology"],
                    field_tested=tuple(f for f in row["field_tested"].split(",") if f),
                    shares=shares,
                    notes=row["notes"],
                )
            )
    return tuple(
        sorted(polls, key=lambda p: (p.date_published, p.poll_id), reverse=True)
    )


def build_mayoral_polling_feed(path: str | Path) -> dict:
    """Assemble the descriptive polling feed: polls (newest first), the latest
    poll, and a raw per-candidate share trend (chronological, unsmoothed)."""
    polls = load_mayoral_polls(path)
    candidates = sorted({c for p in polls for c in p.shares})
    trend: dict[str, list[dict[str, object]]] = {c: [] for c in candidates}
    for poll in sorted(polls, key=lambda p: (p.date_conducted, p.poll_id)):
        for candidate, share in poll.shares.items():
            trend[candidate].append(
                {
                    "date_conducted": poll.date_conducted,
                    "poll_id": poll.poll_id,
                    "share": share,
                }
            )
    return {
        "schema_version": MAYORAL_POLLING_FEED_SCHEMA_VERSION,
        "candidates": candidates,
        "polls": [_poll_dict(p) for p in polls],
        "latest": _poll_dict(polls[0]) if polls else None,
        "trend": trend,
    }


def _poll_dict(poll: MayoralPoll) -> dict:
    return {
        "poll_id": poll.poll_id,
        "firm": poll.firm,
        "date_conducted": poll.date_conducted,
        "date_published": poll.date_published,
        "sample_size": poll.sample_size,
        "methodology": poll.methodology,
        "field_tested": list(poll.field_tested),
        "shares": poll.shares,
        "notes": poll.notes,
    }
