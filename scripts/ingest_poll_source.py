#!/usr/bin/env python3
"""CLI for the thin poll-source ingestion helper.

Given a JSON spec holding the five source-contract sections (the values I extract
by hand from a document), for each source document it fetches the artifact if
missing, computes sha256 / byte-size / page-count, then appends the rows via the
tested ``ingest_poll_source`` core (all-or-nothing, contract-validated), verifies
the artifact bytes, and prints the new inventory counts. Historical ingestion
also runs ``reconstruct --check``.

It never parses a PDF for numbers, never sets ``visual_qa_status`` (that stays a
deliberate attestation in the spec, per the SCHEMA full-document standard), and
never edits the legacy crosswalk mapping.

Usage:
  uv run scripts/ingest_poll_source.py current-cycle path/to/spec.json
  uv run scripts/ingest_poll_source.py historical path/to/spec.json

The one-argument historical form remains supported for compatibility.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.poll_ingest import TABLES, ingest_poll_source
from backend.model.poll_sources import (
    load_poll_source_bundle,
    verify_poll_source_artifacts,
)

HISTORICAL_BUNDLE = Path("data/raw/polls/historical_mayoral")
CURRENT_CYCLE_BUNDLE = Path("data/raw/polls")


def _page_count(pdf: Path) -> str:
    output = subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True
    ).stdout
    for line in output.splitlines():
        if line.startswith("Pages:"):
            return line.split()[1]
    raise SystemExit(f"could not read page count from {pdf}")


def _prepare_document(doc: dict, root: Path) -> None:
    if doc.get("retrieval_status") != "retrieved":
        print(f"  {doc['source_document_id']}: no retrieved artifact to verify")
        return

    local_path = doc.get("local_path")
    if not local_path:
        raise SystemExit(
            f"{doc['source_document_id']}: retrieved document has no local_path"
        )
    local = root / local_path
    if not local.exists():
        url = doc.get("retrieval_url") or doc.get("publisher_url")
        if not url:
            raise SystemExit(
                f"{doc['source_document_id']}: no local file and no URL to fetch"
            )
        local.parent.mkdir(parents=True, exist_ok=True)
        print(f"fetching {doc['source_document_id']} …")
        subprocess.run(
            ["curl", "-sL", "--max-time", "120", "-o", str(local), url], check=True
        )
    doc["sha256"] = hashlib.sha256(local.read_bytes()).hexdigest()
    doc["byte_size"] = str(local.stat().st_size)
    if doc.get("media_type") == "application/pdf":
        doc["page_count"] = _page_count(local)
    print(
        f"  {doc['source_document_id']}: {doc['byte_size']} bytes, sha256 {doc['sha256'][:12]}…"
    )


def _parse_args(argv: list[str] | None) -> tuple[str, Path]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("current-cycle", "historical"))
    parser.add_argument("spec", type=Path, help="path to the five-section JSON spec")
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) == 1 and arguments[0] not in {"-h", "--help"}:
        arguments.insert(0, "historical")
    args = parser.parse_args(arguments)
    return args.mode, args.spec


def _print_next_steps(mode: str) -> None:
    if mode == "current-cycle":
        print("\nnext validation commands:")
        print("  uv run python -m pytest -q")
        print(
            "  uv run python scripts/refresh_all.py --results-bundle "
            '"$RUN_ROOT/results" --results-release "$RESULTS_TAG"'
        )
        return
    print(
        "\nnext (deliberate, manual): bump the inventory count-assertions to these "
        "totals; and to retire legacy proxies, add _MAPPED_LEGACY_READINGS entries "
        "then run reconstruct --write."
    )


def main(argv: list[str] | None = None, *, root: Path = ROOT) -> None:
    mode, spec_path = _parse_args(argv)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    for doc in spec.get("source_documents", []):
        _prepare_document(doc, root)

    current_cycle = mode == "current-cycle"
    bundle_dir = root / (CURRENT_CYCLE_BUNDLE if current_cycle else HISTORICAL_BUNDLE)
    snapshots = {
        table: (bundle_dir / f"{table}.csv").read_bytes() for table in TABLES
    }
    try:
        counts = ingest_poll_source(
            spec,
            bundle_dir=bundle_dir,
            require_audited_sources=not current_cycle,
        )
        bundle = load_poll_source_bundle(
            str(bundle_dir), require_audited_sources=not current_cycle
        )
        if current_cycle:
            document_ids = {
                document["source_document_id"]
                for document in spec["source_documents"]
            }
            verify_poll_source_artifacts(
                bundle, root, source_document_ids=document_ids
            )
        else:
            verify_poll_source_artifacts(bundle, root)
            subprocess.run(
                [sys.executable, "scripts/reconstruct_historical_mayoral.py", "--check"],
                cwd=root,
                check=True,
            )
    except Exception:
        for table, data in snapshots.items():
            (bundle_dir / f"{table}.csv").write_bytes(data)
        raise

    print("\ningested and validated. new bundle counts:")
    for name, value in counts.items():
        print(f"  {name}: {value}")
    _print_next_steps(mode)


if __name__ == "__main__":
    main()
