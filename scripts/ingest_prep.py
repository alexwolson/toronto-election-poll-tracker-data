#!/usr/bin/env python3
"""Deterministic prep for the double-read extraction workflow: fetch + render + metadata.

For each manifest document (doc_id, cycle, firm, publisher_url, retrieval_url,
local_path), fetch the artifact via curl (Wayback id_ URLs work; WebFetch cannot
reach web.archive.org), place it at the gitignored local_path, render every page
to PNG at 175 DPI under tmp/ingest_staging/<doc_id>/, and write meta.json with the
page-image paths and computed sha256 / byte-size / page-count. No pdftotext.

Usage:  uv run scripts/ingest_prep.py path/to/manifest.json
Then pass the emitted meta.json objects as `args` to poll_extract.workflow.js.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGING = ROOT / "tmp/ingest_staging"


def _page_count(pdf: Path) -> int:
    out = subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True
    ).stdout
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    raise SystemExit(f"could not read page count from {pdf}")


def prepare(doc: dict) -> dict:
    did = doc["doc_id"]
    local = ROOT / doc["local_path"]
    stage = STAGING / did
    local.parent.mkdir(parents=True, exist_ok=True)
    stage.mkdir(parents=True, exist_ok=True)
    if not local.exists():
        subprocess.run(
            [
                "curl",
                "-sL",
                "--max-time",
                "180",
                "-o",
                str(local),
                doc["retrieval_url"],
            ],
            check=True,
        )
    for old in stage.glob("page-*.png"):
        old.unlink()
    subprocess.run(
        ["pdftoppm", "-png", "-r", "175", str(local), str(stage / "page")], check=True
    )
    images = sorted(str(p) for p in stage.glob("page-*.png"))
    meta = {
        "doc_id": did,
        "cycle": doc["cycle"],
        "firm": doc["firm"],
        "publisher_url": doc["publisher_url"],
        "retrieval_url": doc["retrieval_url"],
        "local_path": doc["local_path"],
        "media_type": "application/pdf",
        "sha256": hashlib.sha256(local.read_bytes()).hexdigest(),
        "byte_size": local.stat().st_size,
        "page_count": _page_count(local),
        "page_images": images,
    }
    (stage / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ingest_prep.py <manifest.json>")
    manifest = json.loads(Path(sys.argv[1]).read_text())
    metas = [prepare(doc) for doc in manifest]
    for m in metas:
        print(
            f"{m['doc_id']}: {m['byte_size']} bytes, {m['page_count']} pages, {len(m['page_images'])} images"
        )
    # emit the workflow args (the meta array) to stdout as a single JSON line
    print("\n--- workflow args (meta array) ---")
    print(json.dumps(metas))


if __name__ == "__main__":
    main()
