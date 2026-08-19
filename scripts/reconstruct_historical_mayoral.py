#!/usr/bin/env python3
"""Build and audit the non-live canonical historical mayoral corpus.

This script never changes the live forecast or snapshot. ``--write`` rebuilds
the election manifest, complete official outcomes, and the legacy crosswalk;
``--check`` fails if committed tables differ from a fresh reconstruction.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.model.historical_mayoral import (
    CROSSWALK_COLUMNS,
    ELECTION_COLUMNS,
    OUTCOME_COLUMNS,
    audit_historical_mayoral_corpus,
    build_legacy_crosswalk_rows,
    build_mayoral_election_rows,
    build_mayoral_outcome_rows,
    load_historical_mayoral_corpus,
)

TABLES = (
    (
        ROOT / "data/raw/elections/mayoral_elections.csv",
        ELECTION_COLUMNS,
        lambda: build_mayoral_election_rows(),
    ),
    (
        ROOT / "data/raw/elections/mayoral_outcomes.csv",
        OUTCOME_COLUMNS,
        lambda: build_mayoral_outcome_rows(
            {
                2010: ROOT / "data/raw/elections/mayoral_results_2010_official.csv",
                2014: ROOT / "data/raw/elections/mayoral_results_2014_official.csv",
            },
            ROOT / "data/raw/elections/mayoral_results.csv",
        ),
    ),
    (
        ROOT / "data/raw/polls/legacy_historical_poll_crosswalk.csv",
        CROSSWALK_COLUMNS,
        lambda: build_legacy_crosswalk_rows(
            ROOT / "data/raw/polls/historical_mayoral_polls.csv"
        ),
    ),
)


def _render(columns: tuple[str, ...], rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _rebuild(*, write: bool) -> None:
    stale: list[str] = []
    for path, columns, build in TABLES:
        rendered = _render(columns, build())
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
        elif not path.is_file() or path.read_text(encoding="utf-8") != rendered:
            stale.append(str(path.relative_to(ROOT)))
    if stale:
        raise SystemExit(
            "Canonical historical tables are stale or missing: " + ", ".join(stale)
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="rebuild tracked tables")
    group.add_argument("--check", action="store_true", help="verify tracked tables")
    args = parser.parse_args()
    if args.write or args.check:
        _rebuild(write=args.write)
    corpus = load_historical_mayoral_corpus(ROOT)
    print(json.dumps(asdict(audit_historical_mayoral_corpus(corpus)), indent=2))


if __name__ == "__main__":
    main()
