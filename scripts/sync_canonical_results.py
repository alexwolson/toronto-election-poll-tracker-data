#!/usr/bin/env python3
"""Vendor the canonical Toronto election-results dataset into this repo.

This repo no longer pulls or processes election results itself; it consumes the
canonical dataset built in the sibling `toronto-election-results` repo (ADR 0044).
This dev-time step copies that repo's built outputs into `data/raw/canonical/` so
the vendored snapshot -- not a cross-repo path -- is what deploys.

Run:  uv run scripts/sync_canonical_results.py [--source PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT.parent.parent / "toronto-election-results" / "data" / "out"
DEST = ROOT / "data" / "raw" / "canonical"

FILES = ("toronto_election_results.csv", "council_composition.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="canonical toronto-election-results data/out directory",
    )
    args = parser.parse_args()
    source: Path = args.source
    if not source.is_dir():
        raise SystemExit(f"canonical source not found: {source}")

    DEST.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        src = source / name
        if not src.exists():
            raise SystemExit(f"missing canonical file: {src}")
        shutil.copyfile(src, DEST / name)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()[:12]
        rows = sum(1 for _ in src.open()) - 1
        print(f"  vendored {name}: {rows} rows, sha256 {digest}")
    print(f"canonical results vendored into {DEST.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
