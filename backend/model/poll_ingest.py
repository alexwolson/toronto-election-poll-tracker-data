"""Thin ingestion helper for the audited historical poll bundle.

Appends one poll's already-extracted structured spec to the five-table source
contract (see ``data/raw/polls/SCHEMA.md``) and validates it by loading the
bundle in audited mode.  It never parses a PDF and never edits the legacy
crosswalk mapping (``_MAPPED_LEGACY_READINGS``); artifact byte verification and
crosswalk reconciliation are separate steps.  On any structural or contract
violation it restores every CSV, so a rejected spec leaves the bundle unchanged.
"""

from __future__ import annotations

import csv
from pathlib import Path

from backend.model.poll_sources import load_poll_source_bundle

TABLES = (
    "source_documents",
    "poll_sample_documents",
    "poll_samples",
    "poll_readings",
    "poll_responses",
)


class IngestError(ValueError):
    """Raised when a poll spec is structurally unusable for ingestion."""


def _line_terminator(path: Path) -> str:
    return "\r\n" if b"\r\n" in path.read_bytes()[:4096] else "\n"


def _append_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with open(path, newline="") as handle:
        fieldnames = next(csv.reader(handle))
    unknown = {key for row in rows for key in row} - set(fieldnames)
    if unknown:
        raise IngestError(
            f"{path.name}: spec has columns not in the schema: {sorted(unknown)}"
        )
    term = _line_terminator(path)
    if not path.read_bytes().endswith(term.encode()):
        with open(path, "a", newline="") as handle:
            handle.write(term)
    with open(path, "a", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, restval="", lineterminator=term
        )
        for row in rows:
            writer.writerow(row)


def _count(path: Path) -> int:
    with open(path, newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def ingest_poll_source(
    spec: object,
    *,
    bundle_dir: str | Path,
    require_audited_sources: bool = True,
) -> dict[str, int]:
    """Append one poll's rows to the bundle and validate the contract.

    ``spec`` maps each of the five table names to a list of row dicts holding
    only the non-blank fields; any schema column absent from a row is written
    blank.  Returns the new per-table row counts.  Raises and leaves every CSV
    unchanged on any structural or contract violation, so ingestion is
    all-or-nothing.  ``require_audited_sources`` is True for the fully-audited
    historical corpus; the current-cycle bundle carries explicit gap statuses
    (e.g. a blocked sample) and validates in manifest mode (False).
    """

    bundle_dir = Path(bundle_dir)
    if (
        not isinstance(spec, dict)
        or set(spec) != set(TABLES)
        or not all(isinstance(spec[table], list) for table in TABLES)
    ):
        raise IngestError(
            "spec must be a dict mapping each of these sections to a list of "
            f"row dicts: {list(TABLES)}"
        )

    snapshots = {table: (bundle_dir / f"{table}.csv").read_bytes() for table in TABLES}
    try:
        for table in TABLES:
            _append_rows(bundle_dir / f"{table}.csv", spec[table])
        load_poll_source_bundle(
            str(bundle_dir), require_audited_sources=require_audited_sources
        )
    except Exception:
        for table, data in snapshots.items():
            (bundle_dir / f"{table}.csv").write_bytes(data)
        raise
    return {table: _count(bundle_dir / f"{table}.csv") for table in TABLES}
