#!/usr/bin/env python3
"""Vendor the historical-hint catalog + contract from the defeatability-index project.

The candidate-specific historical hints on the Council race card (ADR 0043) are
computed here but their definitions, trigger conditions, frontend copy, and
evidence tiers come from the sibling `defeatability-index` analysis. This dev-time
step copies its two published artifacts into `data/raw/hints/` so the vendored
snapshot -- not a cross-repo path -- is what the build reads. Re-run when the
upstream analysis is refreshed.

Run:  uv run scripts/sync_historical_hints.py [--source PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = (
    ROOT.parent / "defeatability-index" / "data" / "out" / "candidate_history"
)
DEST = ROOT / "data" / "raw" / "hints"

FILES = ("supported_historical_hints.csv", "historical_hint_contract.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="defeatability-index candidate_history output directory",
    )
    args = parser.parse_args()
    source: Path = args.source
    if not source.is_dir():
        raise SystemExit(f"hint source not found: {source}")

    DEST.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        src = source / name
        if not src.exists():
            raise SystemExit(f"missing hint artifact: {src}")
        shutil.copyfile(src, DEST / name)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()[:12]
        print(f"  vendored {name}: sha256 {digest}")
    print(f"historical-hint artifacts vendored into {DEST.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
