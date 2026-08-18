#!/usr/bin/env python3
"""CLI for the thin poll-source ingestion helper.

Given a JSON spec holding the five source-contract sections (the values I extract
by hand from a document), for each source document it fetches the artifact if
missing, computes sha256 / byte-size / page-count, then appends the rows via the
tested ``ingest_poll_source`` core (all-or-nothing, audited-validated), verifies
the artifact bytes, runs ``reconstruct --check``, and prints the new inventory
counts.

It never parses a PDF for numbers, never sets ``visual_qa_status`` (that stays a
deliberate attestation in the spec, per the SCHEMA full-document standard), and
never edits the legacy crosswalk mapping.

Usage:  uv run scripts/ingest_poll_source.py path/to/spec.json
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.poll_ingest import ingest_poll_source
from backend.model.poll_sources import (
    load_poll_source_bundle,
    verify_poll_source_artifacts,
)

BUNDLE = ROOT / "data/raw/polls/historical_mayoral"


def _page_count(pdf: Path) -> str:
    output = subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True
    ).stdout
    for line in output.splitlines():
        if line.startswith("Pages:"):
            return line.split()[1]
    raise SystemExit(f"could not read page count from {pdf}")


def _prepare_document(doc: dict) -> None:
    local = ROOT / doc["local_path"]
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


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ingest_poll_source.py <spec.json>")
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for doc in spec.get("source_documents", []):
        _prepare_document(doc)

    counts = ingest_poll_source(spec, bundle_dir=BUNDLE)

    bundle = load_poll_source_bundle(str(BUNDLE), require_audited_sources=True)
    verify_poll_source_artifacts(bundle, ROOT)
    subprocess.run(
        [sys.executable, "scripts/reconstruct_historical_mayoral.py", "--check"],
        cwd=ROOT,
        check=True,
    )

    print("\ningested and validated. new bundle counts:")
    for name, value in counts.items():
        print(f"  {name}: {value}")
    print(
        "\nnext (deliberate, manual): bump the inventory count-assertions to these "
        "totals; and to retire legacy proxies, add _MAPPED_LEGACY_READINGS entries "
        "then run reconstruct --write."
    )


if __name__ == "__main__":
    main()
