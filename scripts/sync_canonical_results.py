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
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT.parent.parent / "toronto-election-results" / "data" / "out"
DEST = ROOT / "data" / "raw" / "canonical"

FILES = ("election_results.csv",)


def _vendor_completed_only(src: Path, dest: Path) -> tuple[int, int]:
    """Vendor the canonical, dropping the outcome-less current cycle -- rows whose
    ``result_status`` is not ``final`` (e.g. the just-nominated 2026 field, which
    carries a null ``elected``). This repo consumes the canonical only for
    completed-election history (biographies, hint catalog, the mayoral corpus);
    the current field comes from the registration CSVs, so pending rows would only
    pollute those. Older canonicals predate the column and are vendored whole.
    """
    with src.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = list(reader)
    keep = (
        [r for r in rows if r.get("result_status") == "final"]
        if "result_status" in fields
        else rows
    )
    with dest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(keep)
    return len(keep), len(rows) - len(keep)


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
        dest = DEST / name
        kept, dropped = _vendor_completed_only(src, dest)
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()[:12]
        note = f" (dropped {dropped} pending current-cycle)" if dropped else ""
        print(f"  vendored {name}: {kept} rows{note}, sha256 {digest}")
    print(f"canonical results vendored into {DEST.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
