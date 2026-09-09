from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from backend.model.poll_ingest import TABLES
from backend.model.poll_sources import PollSourceContractError
from scripts import ingest_poll_source as command
from tests.model.test_poll_ingest import _valid_spec

ROOT = Path(__file__).resolve().parents[2]


def _project_copy(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    shutil.copytree(ROOT / "data/raw/polls", project / "data/raw/polls")
    return project


def _table_bytes(bundle: Path) -> dict[str, bytes]:
    return {table: (bundle / f"{table}.csv").read_bytes() for table in TABLES}


def _current_spec() -> dict[str, list[dict[str, str]]]:
    spec = _valid_spec()
    document = spec["source_documents"][0]
    document.update(
        {
            "source_document_id": "test_doc_2026",
            "publisher_url": "https://example.org/test.html",
            "retrieval_url": "https://example.org/test.html",
            "retrieved_at": "2026-09-10T12:00:00Z",
            "media_type": "text/html",
            "local_path": "data/source_documents/current_mayoral/test_doc_2026.html",
            "page_count": "",
            "text_layer_status": "present",
            "visual_qa_status": "pending",
        }
    )
    link = spec["poll_sample_documents"][0]
    link.update(
        {
            "poll_sample_id": "test-city-2026-09-09-n500",
            "source_document_id": "test_doc_2026",
        }
    )
    sample = spec["poll_samples"][0]
    sample.update(
        {
            "poll_sample_id": "test-city-2026-09-09-n500",
            "election_cycle_id": "toronto-2026",
            "fieldwork_start": "2026-09-08",
            "fieldwork_end": "2026-09-09",
            "publication_date": "2026-09-09",
            "evidence_available_at": "2026-09-10T00:00:00-04:00",
        }
    )
    reading = spec["poll_readings"][0]
    reading.update(
        {
            "poll_reading_id": "test-reading-2026",
            "poll_sample_id": "test-city-2026-09-09-n500",
            "source_document_id": "test_doc_2026",
            "contest_id": "toronto-mayor-2026",
        }
    )
    for response in spec["poll_responses"]:
        response["poll_reading_id"] = "test-reading-2026"
    return spec


def _write_spec(tmp_path: Path, spec: object) -> Path:
    spec_path = tmp_path / "poll.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path


def test_parser_requires_current_cycle_mode_but_preserves_historical_shorthand() -> None:
    assert command._parse_args(["current-cycle", "poll.json"]) == (
        "current-cycle",
        Path("poll.json"),
    )
    assert command._parse_args(["poll.json"]) == ("historical", Path("poll.json"))


def test_current_cycle_command_ingests_and_verifies_only_new_artifacts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _project_copy(tmp_path)
    historical = project / "data/raw/polls/historical_mayoral"
    historical_before = _table_bytes(historical)
    artifact = project / "data/source_documents/current_mayoral/test_doc_2026.html"
    artifact.parent.mkdir(parents=True)
    payload = b"<!doctype html><html><body>poll release</body></html>"
    artifact.write_bytes(payload)

    command.main(
        ["current-cycle", str(_write_spec(tmp_path, _current_spec()))],
        root=project,
    )

    with (project / "data/raw/polls/source_documents.csv").open(newline="") as handle:
        documents = {row["source_document_id"]: row for row in csv.DictReader(handle)}
    ingested = documents["test_doc_2026"]
    assert ingested["sha256"] == hashlib.sha256(payload).hexdigest()
    assert ingested["visual_qa_status"] == "pending"
    assert _table_bytes(historical) == historical_before
    output = capsys.readouterr().out
    assert "new bundle counts" in output
    assert "uv run python -m pytest -q" in output
    assert "scripts/refresh_all.py --results-bundle" in output


def test_current_cycle_command_restores_every_csv_after_artifact_failure(
    tmp_path: Path,
) -> None:
    project = _project_copy(tmp_path)
    current = project / "data/raw/polls"
    historical = current / "historical_mayoral"
    current_before = _table_bytes(current)
    historical_before = _table_bytes(historical)
    artifact = project / "data/source_documents/current_mayoral/test_doc_2026.html"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"not an HTML document")

    with pytest.raises(PollSourceContractError, match="bytes do not match media_type"):
        command.main(
            ["current-cycle", str(_write_spec(tmp_path, _current_spec()))],
            root=project,
        )

    assert _table_bytes(current) == current_before
    assert _table_bytes(historical) == historical_before
