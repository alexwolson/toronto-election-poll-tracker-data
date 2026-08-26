#!/usr/bin/env python3
"""Validate polling data and build a Results-pinned Polling release bundle.

The Polling repository owns source provenance, cleaned poll tables and factual
polling feeds only. It does not refresh election results or run forecast models.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
DEFAULT_RESULTS = ROOT.parent.parent / "toronto-election-results" / "dist"


def _run(label: str, command: list[str], *, dry_run: bool) -> None:
    print(f"\n{label}\n  {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-bundle", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--results-release", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.skip_tests:
        _run("Validate polling repository", [PYTHON, "-m", "pytest", "-q"], dry_run=args.dry_run)
    _run(
        "Build Results-pinned Polling release",
        [
            PYTHON,
            "-m",
            "polling_data.release_bundle",
            "build",
            "--results-bundle",
            str(args.results_bundle),
            "--results-release",
            args.results_release,
            "--output",
            str(args.output),
        ],
        dry_run=args.dry_run,
    )
    print("\nPolling refresh complete." if not args.dry_run else "\nDry run complete.")


if __name__ == "__main__":
    main()
