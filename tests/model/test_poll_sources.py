"""Tests for the model-neutral poll source contract."""

from __future__ import annotations

import csv
import hashlib
import zipfile
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from backend.model.poll_sources import (
    POLL_READING_COLUMNS,
    POLL_RESPONSE_COLUMNS,
    POLL_SAMPLE_DOCUMENT_COLUMNS,
    POLL_SAMPLE_COLUMNS,
    SOURCE_DOCUMENT_COLUMNS,
    PollSourceContractError,
    load_poll_source_bundle,
    verify_poll_source_artifacts,
)


def _valid_tables() -> dict[str, list[dict[str, str]]]:
    document = {
        "source_document_id": "forum-ward13-2026-release",
        "document_role": "tables",
        "publisher_url": "https://example.test/forum/ward-13",
        "retrieval_url": "https://example.test/forum/ward-13.pdf",
        "retrieval_status": "retrieved",
        "retrieved_at": "2026-08-15T10:00:00-04:00",
        "media_type": "application/pdf",
        "sha256": "a" * 64,
        "local_path": "data/source_documents/current_council/ward-13.pdf",
        "byte_size": "12345",
        "page_count": "3",
        "sheet_count": "",
        "text_layer_status": "present",
        "visual_qa_status": "passed",
        "access_class": "public",
        "redistribution_status": "permitted",
        "reuse_terms_url": "https://example.test/terms",
        "notes": "",
    }
    sample = {
        "poll_sample_id": "forum-ward13-2026-08-12",
        "election_cycle_id": "toronto-2026",
        "pollster": "Forum Research",
        "sponsor": "",
        "geography_type": "ward",
        "geography_id": "toronto-ward-13",
        "fieldwork_start": "2026-08-11",
        "fieldwork_end": "2026-08-12",
        "publication_date": "2026-08-14",
        "publication_at": "2026-08-14T09:30:00-04:00",
        "publication_time_precision": "exact",
        "evidence_available_at": "2026-08-14T09:30:00-04:00",
        "collection_mode": "ivr",
        "recruited_sample_size": "800",
        "extraction_status": "extracted",
        "notes": "One respondent sample; two questions below are dependent.",
    }
    council_reading = {
        "poll_reading_id": "forum-ward13-2026-08-12-council",
        "poll_sample_id": "forum-ward13-2026-08-12",
        "source_document_id": "forum-ward13-2026-release",
        "source_locator": "page 2, council vote-intention table",
        "contest_type": "council",
        "contest_id": "toronto-ward-13-2026",
        "question_order_status": "reported",
        "question_order": "1",
        "document_display_order": "1",
        "question_text_status": "reported",
        "question_text": "Which candidate would you vote for as councillor?",
        "scenario_label": "",
        "population": "Toronto Ward 13 residents eligible to vote",
        "turnout_screen": "eligible_voters",
        "turnout_screen_text": "Eligible to vote in Ward 13",
        "denominator_type": "all_respondents",
        "denominator_text": "All respondents",
        "unweighted_base_status": "reported",
        "unweighted_base": "600",
        "weighted_base_status": "reported",
        "weighted_base": "600.0",
        "reported_base_status": "not_reported",
        "reported_base": "",
        "tested_choice_set_status": "complete",
        "response_coverage": "complete",
        "reported_share_unit": "percent",
        "reported_share_precision": "0",
        "notes": "",
        "reading_purpose": "general_vote_intention",
    }
    mayoral_reading = {
        **council_reading,
        "poll_reading_id": "forum-ward13-2026-08-12-mayoral",
        "contest_type": "mayoral",
        "contest_id": "toronto-mayor-2026",
        "question_order": "2",
        "question_text": "Which candidate would you vote for as mayor?",
        "source_locator": "page 3, mayoral vote-intention table",
    }
    responses = [
        {
            "poll_reading_id": "forum-ward13-2026-08-12-council",
            "response_option_id": "candidate-saxe",
            "response_kind": "candidate",
            "candidate_id": "saxe",
            "candidate_name": "Dianne Saxe",
            "candidate_observation_status": "individually_published",
            "response_label": "Dianne Saxe",
            "option_order": "1",
            "reported_value": "45%",
            "share": "0.45",
            "notes": "",
        },
        {
            "poll_reading_id": "forum-ward13-2026-08-12-council",
            "response_option_id": "candidate-layton",
            "response_kind": "candidate",
            "candidate_id": "layton",
            "candidate_name": "Mike Layton",
            "candidate_observation_status": "individually_published",
            "response_label": "Mike Layton",
            "option_order": "2",
            "reported_value": "40%",
            "share": "0.40",
            "notes": "",
        },
        {
            "poll_reading_id": "forum-ward13-2026-08-12-council",
            "response_option_id": "undecided",
            "response_kind": "undecided",
            "candidate_id": "",
            "candidate_name": "",
            "candidate_observation_status": "",
            "response_label": "Undecided",
            "option_order": "3",
            "reported_value": "15%",
            "share": "0.15",
            "notes": "",
        },
        {
            "poll_reading_id": "forum-ward13-2026-08-12-mayoral",
            "response_option_id": "candidate-chow",
            "response_kind": "candidate",
            "candidate_id": "chow",
            "candidate_name": "Olivia Chow",
            "candidate_observation_status": "individually_published",
            "response_label": "Olivia Chow",
            "option_order": "1",
            "reported_value": "50%",
            "share": "0.50",
            "notes": "",
        },
        {
            "poll_reading_id": "forum-ward13-2026-08-12-mayoral",
            "response_option_id": "candidate-bradford",
            "response_kind": "candidate",
            "candidate_id": "bradford",
            "candidate_name": "Brad Bradford",
            "candidate_observation_status": "individually_published",
            "response_label": "Brad Bradford",
            "option_order": "2",
            "reported_value": "30%",
            "share": "0.30",
            "notes": "",
        },
        {
            "poll_reading_id": "forum-ward13-2026-08-12-mayoral",
            "response_option_id": "undecided",
            "response_kind": "undecided",
            "candidate_id": "",
            "candidate_name": "",
            "candidate_observation_status": "",
            "response_label": "Undecided",
            "option_order": "3",
            "reported_value": "20%",
            "share": "0.20",
            "notes": "",
        },
    ]
    return {
        "source_documents.csv": [document],
        "poll_sample_documents.csv": [
            {
                "poll_sample_id": "forum-ward13-2026-08-12",
                "source_document_id": "forum-ward13-2026-release",
                "sample_locator": "pp. 1-3",
                "notes": "",
            }
        ],
        "poll_samples.csv": [sample],
        "poll_readings.csv": [council_reading, mayoral_reading],
        "poll_responses.csv": responses,
    }


_COLUMNS = {
    "source_documents.csv": SOURCE_DOCUMENT_COLUMNS,
    "poll_sample_documents.csv": POLL_SAMPLE_DOCUMENT_COLUMNS,
    "poll_samples.csv": POLL_SAMPLE_COLUMNS,
    "poll_readings.csv": POLL_READING_COLUMNS,
    "poll_responses.csv": POLL_RESPONSE_COLUMNS,
}


def _write_bundle(
    directory: Path,
    tables: dict[str, list[dict[str, str]]],
    *,
    columns: dict[str, tuple[str, ...]] | None = None,
) -> None:
    selected_columns = columns or _COLUMNS
    for filename, expected_columns in selected_columns.items():
        with (directory / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=expected_columns, extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(tables[filename])


def test_loads_two_dependent_readings_as_one_distinct_sample(tmp_path: Path) -> None:
    _write_bundle(tmp_path, _valid_tables())

    bundle = load_poll_source_bundle(tmp_path, require_audited_sources=True)

    assert len(bundle.poll_samples) == 1
    assert len(bundle.poll_readings) == 2
    assert {reading.poll_sample_id for reading in bundle.poll_readings} == {
        "forum-ward13-2026-08-12"
    }
    assert bundle.poll_responses[0].share == Decimal("0.45")
    assert bundle.poll_readings[0].reading_purpose == "general_vote_intention"


def test_rejects_unknown_reading_purpose(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["poll_readings.csv"][0]["reading_purpose"] = "horse_race_context"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="reading_purpose"):
        load_poll_source_bundle(tmp_path)


def test_rejects_schema_drift_instead_of_ignoring_it(tmp_path: Path) -> None:
    columns = dict(_COLUMNS)
    columns["source_documents.csv"] = SOURCE_DOCUMENT_COLUMNS[:-1]
    _write_bundle(tmp_path, _valid_tables(), columns=columns)

    with pytest.raises(PollSourceContractError, match="header must be exactly"):
        load_poll_source_bundle(tmp_path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("sha256", "abc", "sha256 must be 64 lowercase hex digits"),
        ("local_path", "../restricted.pdf", "safe path below data/source_documents"),
        ("access_class", "probably_public", "unknown access_class"),
    ],
)
def test_rejects_ambiguous_source_provenance(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    tables = _valid_tables()
    tables["source_documents.csv"][0][field] = value
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match=message):
        load_poll_source_bundle(tmp_path)


def test_requires_caveat_for_restricted_or_nonredistributable_source(
    tmp_path: Path,
) -> None:
    tables = _valid_tables()
    document = tables["source_documents.csv"][0]
    document["access_class"] = "institutional_restricted"
    document["redistribution_status"] = "prohibited"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="notes are required"):
        load_poll_source_bundle(tmp_path)


def test_date_only_publication_uses_conservative_evidence_timestamp(
    tmp_path: Path,
) -> None:
    tables = _valid_tables()
    sample = tables["poll_samples.csv"][0]
    sample["publication_time_precision"] = "date_only"
    sample["publication_at"] = ""
    sample["evidence_available_at"] = "2026-08-14T23:59:59-04:00"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="next Toronto day"):
        load_poll_source_bundle(tmp_path)


def test_rejects_reading_linked_to_unknown_source_document(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["poll_readings.csv"][0]["source_document_id"] = "missing-document"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="unknown source document"):
        load_poll_source_bundle(tmp_path)


def test_rejects_reading_base_larger_than_recruited_sample(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["poll_readings.csv"][0]["unweighted_base"] = "801"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="larger than its recruited sample"):
        load_poll_source_bundle(tmp_path)


def test_rejects_value_when_base_is_explicitly_not_reported(tmp_path: Path) -> None:
    tables = _valid_tables()
    reading = tables["poll_readings.csv"][0]
    reading["weighted_base_status"] = "not_reported"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="must leave its value blank"):
        load_poll_source_bundle(tmp_path)


def test_accepts_offered_candidate_without_inventing_a_share(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["poll_readings.csv"][0]["response_coverage"] = "partial"
    layton = tables["poll_responses.csv"][1]
    layton["candidate_observation_status"] = "offered_not_individually_published"
    layton["reported_value"] = ""
    layton["share"] = ""
    _write_bundle(tmp_path, tables)

    bundle = load_poll_source_bundle(tmp_path)

    loaded = next(
        response for response in bundle.poll_responses if response.candidate_id == "layton"
    )
    assert loaded.candidate_observation_status == "offered_not_individually_published"
    assert loaded.share is None


def test_rejects_share_for_candidate_known_not_to_have_been_offered(
    tmp_path: Path,
) -> None:
    tables = _valid_tables()
    saxe = tables["poll_responses.csv"][0]
    saxe["candidate_observation_status"] = "known_not_offered"
    saxe["response_label"] = ""
    saxe["option_order"] = ""
    saxe["reported_value"] = ""
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="cannot have option data"):
        load_poll_source_bundle(tmp_path)


def test_rejects_incomplete_total_claimed_as_complete(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["poll_responses.csv"][2]["reported_value"] = "5%"
    tables["poll_responses.csv"][2]["share"] = "0.05"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="do not sum to one"):
        load_poll_source_bundle(tmp_path)


def test_rejects_conflicting_candidate_names_for_one_candidate_id(
    tmp_path: Path,
) -> None:
    tables = _valid_tables()
    mayoral_candidate = tables["poll_responses.csv"][3]
    mayoral_candidate["candidate_id"] = "saxe"
    mayoral_candidate["candidate_name"] = "D. Saxe"
    _write_bundle(tmp_path, tables)

    with pytest.raises(
        PollSourceContractError,
        match="candidate_id 'saxe' maps to conflicting candidate_name values",
    ):
        load_poll_source_bundle(tmp_path)


def test_rejects_tested_ballot_unknown_when_choice_set_claims_complete(
    tmp_path: Path,
) -> None:
    tables = _valid_tables()
    saxe = tables["poll_responses.csv"][0]
    saxe["candidate_observation_status"] = "tested_ballot_unknown"
    saxe["response_label"] = ""
    saxe["option_order"] = ""
    saxe["reported_value"] = ""
    saxe["share"] = ""
    tables["poll_readings.csv"][0]["response_coverage"] = "partial"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="complete choice set"):
        load_poll_source_bundle(tmp_path)


def test_rejects_naive_evidence_timestamp(tmp_path: Path) -> None:
    tables = deepcopy(_valid_tables())
    tables["poll_samples.csv"][0]["evidence_available_at"] = "2026-08-14T09:30:00"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="must include a UTC offset"):
        load_poll_source_bundle(tmp_path)


def test_one_physical_document_can_describe_two_recruited_samples(
    tmp_path: Path,
) -> None:
    tables = _valid_tables()
    second_sample = deepcopy(tables["poll_samples.csv"][0])
    second_sample["poll_sample_id"] = "forum-ward13-2026-08-13"
    second_sample["extraction_status"] = "pending"
    tables["poll_samples.csv"].append(second_sample)
    tables["poll_sample_documents.csv"].append(
        {
            "poll_sample_id": "forum-ward13-2026-08-13",
            "source_document_id": "forum-ward13-2026-release",
            "sample_locator": "Wave 2, p. 3",
            "notes": "",
        }
    )
    _write_bundle(tmp_path, tables)

    bundle = load_poll_source_bundle(tmp_path)

    assert len(bundle.source_documents) == 1
    assert len(bundle.poll_samples) == 2
    assert len(bundle.poll_sample_documents) == 2


def test_manifest_mode_tracks_dead_link_before_extraction(tmp_path: Path) -> None:
    tables = _valid_tables()
    document = tables["source_documents.csv"][0]
    document.update(
        {
            "retrieval_url": "https://example.test/dead.pdf",
            "retrieval_status": "dead_link",
            "retrieved_at": "",
            "media_type": "application/pdf",
            "sha256": "",
            "local_path": "",
            "byte_size": "",
            "page_count": "",
            "sheet_count": "",
            "text_layer_status": "",
            "visual_qa_status": "not_applicable",
            "redistribution_status": "unknown",
            "notes": "Publisher path returns 404; recovery pending.",
        }
    )
    tables["poll_samples.csv"][0]["extraction_status"] = "blocked"
    tables["poll_readings.csv"] = []
    tables["poll_responses.csv"] = []
    _write_bundle(tmp_path, tables)

    bundle = load_poll_source_bundle(tmp_path)
    assert bundle.source_documents[0].retrieval_status == "dead_link"
    assert bundle.poll_readings == ()

    with pytest.raises(PollSourceContractError, match="is not source-audited"):
        load_poll_source_bundle(tmp_path, require_audited_sources=True)


def test_audited_sources_require_visual_qa_exactly_passed(tmp_path: Path) -> None:
    tables = _valid_tables()
    document = tables["source_documents.csv"][0]
    document.update(
        {
            "media_type": "text/html",
            "local_path": "data/source_documents/current_council/ward-13.html",
            "page_count": "",
            "text_layer_status": "present",
            "visual_qa_status": "not_applicable",
        }
    )
    _write_bundle(tmp_path, tables)

    load_poll_source_bundle(tmp_path)
    with pytest.raises(PollSourceContractError, match="visual QA has not passed"):
        load_poll_source_bundle(tmp_path, require_audited_sources=True)


def test_retrieved_pdf_requires_artifact_qa_metadata(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["source_documents.csv"][0]["page_count"] = ""
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="requires page_count"):
        load_poll_source_bundle(tmp_path)


def test_questionnaire_order_can_be_unknown_without_using_table_order(
    tmp_path: Path,
) -> None:
    tables = _valid_tables()
    reading = tables["poll_readings.csv"][0]
    reading["question_order_status"] = "not_reported"
    reading["question_order"] = ""
    reading["document_display_order"] = "4"
    _write_bundle(tmp_path, tables)

    bundle = load_poll_source_bundle(tmp_path)
    loaded = bundle.poll_readings[0]
    assert loaded.question_order is None
    assert loaded.document_display_order == 4


def test_question_text_can_be_explicitly_unreported(tmp_path: Path) -> None:
    tables = _valid_tables()
    reading = tables["poll_readings.csv"][0]
    reading["question_text_status"] = "not_reported"
    reading["question_text"] = ""
    reading["notes"] = "Outcome prose is retained here without inventing a question."
    _write_bundle(tmp_path, tables)

    bundle = load_poll_source_bundle(tmp_path)

    assert bundle.poll_readings[0].question_text_status == "not_reported"
    assert bundle.poll_readings[0].question_text is None


def test_reported_question_text_cannot_be_blank(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["poll_readings.csv"][0]["question_text"] = ""
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="reported question_text"):
        load_poll_source_bundle(tmp_path)


def test_whole_point_rounding_can_legitimately_total_102_percent(
    tmp_path: Path,
) -> None:
    tables = _valid_tables()
    tables["poll_responses.csv"].append(
        {
            "poll_reading_id": "forum-ward13-2026-08-12-council",
            "response_option_id": "other",
            "response_kind": "other",
            "candidate_id": "",
            "candidate_name": "",
            "candidate_observation_status": "",
            "response_label": "Other",
            "option_order": "4",
            "reported_value": "2%",
            "share": "0.02",
            "notes": "",
        }
    )
    _write_bundle(tmp_path, tables)

    bundle = load_poll_source_bundle(tmp_path)
    council = [
        response
        for response in bundle.poll_responses
        if response.poll_reading_id == "forum-ward13-2026-08-12-council"
    ]
    assert sum(response.share or Decimal(0) for response in council) == Decimal("1.02")


def test_normalized_share_must_match_preserved_reported_value(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["poll_responses.csv"][0]["reported_value"] = "46%"
    _write_bundle(tmp_path, tables)

    with pytest.raises(PollSourceContractError, match="does not match reported_value"):
        load_poll_source_bundle(tmp_path)


def test_verifies_retrieved_artifact_bytes(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    table_root = tmp_path / "tables"
    project_root.mkdir()
    table_root.mkdir()
    artifact = project_root / "data/source_documents/current_council/ward-13.pdf"
    artifact.parent.mkdir(parents=True)
    payload = b"%PDF-1.7\nsynthetic fixture\n%%EOF\n"
    artifact.write_bytes(payload)

    tables = _valid_tables()
    document = tables["source_documents.csv"][0]
    document["byte_size"] = str(len(payload))
    document["sha256"] = hashlib.sha256(payload).hexdigest()
    _write_bundle(table_root, tables)
    bundle = load_poll_source_bundle(table_root)

    verify_poll_source_artifacts(bundle, project_root)

    artifact.write_bytes(payload + b"changed")
    with pytest.raises(PollSourceContractError, match="byte_size mismatch"):
        verify_poll_source_artifacts(bundle, project_root)


def test_verifies_docx_as_an_ooxml_zip_artifact(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    table_root = tmp_path / "tables"
    project_root.mkdir()
    table_root.mkdir()
    artifact = project_root / "data/source_documents/current_mayoral/release.docx"
    artifact.parent.mkdir(parents=True)
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    payload = artifact.read_bytes()

    tables = _valid_tables()
    document = tables["source_documents.csv"][0]
    document.update(
        {
            "media_type": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            "local_path": "data/source_documents/current_mayoral/release.docx",
            "byte_size": str(len(payload)),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "page_count": "",
        }
    )
    _write_bundle(table_root, tables)
    bundle = load_poll_source_bundle(table_root)

    verify_poll_source_artifacts(bundle, project_root)


@pytest.mark.parametrize(
    ("media_type", "suffix", "sheet_count", "text_layer_status", "missing_entry"),
    [
        (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "docx",
            "",
            "present",
            "word/document.xml",
        ),
        (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xlsx",
            "1",
            "not_applicable",
            "xl/workbook.xml",
        ),
    ],
)
def test_ooxml_verifier_requires_media_specific_archive_entries(
    tmp_path: Path,
    media_type: str,
    suffix: str,
    sheet_count: str,
    text_layer_status: str,
    missing_entry: str,
) -> None:
    project_root = tmp_path / "project"
    table_root = tmp_path / "tables"
    project_root.mkdir()
    table_root.mkdir()
    relative_path = f"data/source_documents/current_mayoral/release.{suffix}"
    artifact = project_root / relative_path
    artifact.parent.mkdir(parents=True)
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
    payload = artifact.read_bytes()

    tables = _valid_tables()
    document = tables["source_documents.csv"][0]
    document.update(
        {
            "media_type": media_type,
            "local_path": relative_path,
            "byte_size": str(len(payload)),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "page_count": "",
            "sheet_count": sheet_count,
            "text_layer_status": text_layer_status,
        }
    )
    _write_bundle(table_root, tables)
    bundle = load_poll_source_bundle(table_root)

    with pytest.raises(PollSourceContractError, match=missing_entry):
        verify_poll_source_artifacts(bundle, project_root)


def test_ooxml_verifier_rejects_bad_crc(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    table_root = tmp_path / "tables"
    project_root.mkdir()
    table_root.mkdir()
    relative_path = "data/source_documents/current_mayoral/release.docx"
    artifact = project_root / relative_path
    artifact.parent.mkdir(parents=True)
    marker = b"synthetic-document-payload"
    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", marker)
    corrupted = bytearray(artifact.read_bytes())
    marker_offset = corrupted.index(marker)
    corrupted[marker_offset] ^= 1
    artifact.write_bytes(corrupted)
    payload = bytes(corrupted)

    tables = _valid_tables()
    document = tables["source_documents.csv"][0]
    document.update(
        {
            "media_type": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            "local_path": relative_path,
            "byte_size": str(len(payload)),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "page_count": "",
        }
    )
    _write_bundle(table_root, tables)
    bundle = load_poll_source_bundle(table_root)

    with pytest.raises(PollSourceContractError, match="ZIP CRC failed"):
        verify_poll_source_artifacts(bundle, project_root)


def test_tracked_current_poll_source_inventory() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    bundle = load_poll_source_bundle(repository_root / "data/raw/polls")

    assert len(bundle.source_documents) == 32
    assert len(bundle.poll_sample_documents) == 32
    assert len(bundle.poll_samples) == 26
    assert len(bundle.poll_readings) == 59
    assert len(bundle.poll_responses) == 260

    documents = {
        document.source_document_id: document
        for document in bundle.source_documents
    }
    samples = {sample.poll_sample_id: sample for sample in bundle.poll_samples}
    readings = {
        reading.poll_reading_id: reading for reading in bundle.poll_readings
    }
    readings_by_sample = {
        sample_id: [
            reading
            for reading in bundle.poll_readings
            if reading.poll_sample_id == sample_id
        ]
        for sample_id in samples
    }

    abacus_document = documents["abacus_2026-01-27_article"]
    assert abacus_document.retrieval_status == "access_pending"
    assert abacus_document.local_path is None
    assert samples["abacus-2026-01-27"].extraction_status == "blocked"
    assert readings_by_sample["abacus-2026-01-27"] == []

    citywide_samples = {
        sample_id: sample
        for sample_id, sample in samples.items()
        if sample.geography_type == "citywide"
    }
    recovered_citywide_ids = set(citywide_samples) - {"abacus-2026-01-27"}
    assert len(citywide_samples) == 20
    assert len(recovered_citywide_ids) == 19
    assert all(
        citywide_samples[sample_id].extraction_status == "extracted"
        for sample_id in recovered_citywide_ids
    )
    assert all(readings_by_sample[sample_id] for sample_id in recovered_citywide_ids)
    citywide_readings = [
        reading
        for reading in bundle.poll_readings
        if samples[reading.poll_sample_id].geography_type == "citywide"
    ]
    citywide_responses = [
        response
        for response in bundle.poll_responses
        if samples[readings[response.poll_reading_id].poll_sample_id].geography_type
        == "citywide"
    ]
    assert len(citywide_readings) == 46
    assert len(citywide_responses) == 211
    assert sum(
        reading.reading_purpose == "general_vote_intention"
        for reading in citywide_readings
    ) == 45
    assert readings["canadapulse_20251006_mayor_all"].reading_purpose == "context_only"
    assert len({reading.poll_sample_id for reading in bundle.poll_readings}) == 25
    expected_citywide_order = [
        "pallas-2025-06-07",
        "liaison-2025-07-06",
        "ipsos-2025-08-29",
        "forum-2025-09-04",
        "canadapulse-2025-10-06",
        "liaison-2025-10-23",
        "liaison-2025-12-21",
        "liaison-2026-02-02",
        "mainstreet-2026-02-22",
        "liaison-2026-03-08",
        "pallas-2026-03-08",
        "liaison-2026-04-13",
        "liaison-2026-05-11",
        "mainstreet-2026-06-18",
        "liaison-2026-06-30",
        "liaison-2026-07-26",
        "forum-2026-07-29",
        "liaison-2026-08-05",
        "liaison-2026-08-16",
    ]
    ordered_reading_samples = list(
        dict.fromkeys(reading.poll_sample_id for reading in citywide_readings)
    )
    ordered_response_samples = list(
        dict.fromkeys(
            readings[response.poll_reading_id].poll_sample_id
            for response in citywide_responses
        )
    )
    assert ordered_reading_samples == expected_citywide_order
    assert ordered_response_samples == expected_citywide_order

    canada_pulse = samples["canadapulse-2025-10-06"]
    assert canada_pulse.collection_mode == "online"
    assert canada_pulse.fieldwork_start.isoformat() == "2025-09-30"
    assert canada_pulse.fieldwork_end.isoformat() == "2025-10-06"
    assert canada_pulse.publication_date.isoformat() == "2025-10-21"
    canada_reading = readings["canadapulse_20251006_mayor_all"]
    assert canada_reading.unweighted_base == 406
    assert canada_reading.weighted_base == Decimal("406")
    assert canada_reading.denominator_type == "all_respondents"
    canada_responses = sorted(
        (
            response
            for response in bundle.poll_responses
            if response.poll_reading_id == canada_reading.poll_reading_id
        ),
        key=lambda response: response.option_order or 0,
    )
    assert [response.share for response in canada_responses] == [
        Decimal("0.27"),
        Decimal("0.24"),
        Decimal("0.08"),
        Decimal("0.02"),
        Decimal("0.33"),
        Decimal("0.06"),
    ]
    assert canada_responses[-1].response_kind == "would_not_vote"
    canada_link = next(
        link
        for link in bundle.poll_sample_documents
        if link.poll_sample_id == "canadapulse-2025-10-06"
        and link.source_document_id == "canadapulse_2025-10-06_tables"
    )
    assert canada_link.sample_locator == (
        "sheet Toronto Civic 10 25; mayoral block A333:C370"
    )

    forum_sample = samples["forum-2025-09-04"]
    forum_readings = readings_by_sample[forum_sample.poll_sample_id]
    assert forum_sample.recruited_sample_size is None
    assert "n=1,000" in (forum_sample.notes or "")
    assert "TOTAL (u/w)=1001" in (forum_sample.notes or "")
    assert len(forum_readings) == 4
    forum_head_to_heads = [
        readings["forum_20250904_mayor_chow_tory"],
        readings["forum_20250904_mayor_chow_bradford"],
        readings["forum_20250904_mayor_chow_bailao"],
    ]
    assert all(reading.unweighted_base == 1001 for reading in forum_head_to_heads)
    assert all(
        reading.weighted_base == Decimal("1001")
        for reading in forum_head_to_heads
    )

    liaison_june_all = readings["liaison_20260628_30_mayor_all"]
    liaison_june_decided = readings["liaison_20260628_30_mayor_decided"]
    assert liaison_june_all.poll_sample_id == liaison_june_decided.poll_sample_id
    assert liaison_june_all.denominator_type == "all_respondents"
    assert liaison_june_decided.denominator_type == "decided_respondents"
    assert liaison_june_all.unweighted_base == 1000
    assert liaison_june_decided.unweighted_base == 805
    assert liaison_june_decided.weighted_base == Decimal("801")
    liaison_june_decided_shares = {
        response.candidate_id or response.response_option_id: response.share
        for response in bundle.poll_responses
        if response.poll_reading_id == liaison_june_decided.poll_reading_id
    }
    assert liaison_june_decided_shares == {
        "chow": Decimal("0.49"),
        "bradford": Decimal("0.40"),
        "someone-else": Decimal("0.10"),
    }
    assert readings[
        "liaison_20260724_26_mayor_decided_leaning"
    ].denominator_type == "custom"
    assert readings[
        "liaison_20260804_05_mayor_decided_leaning"
    ].denominator_type == "custom"

    candidate_ids = {
        response.candidate_id
        for response in bundle.poll_responses
        if response.candidate_id is not None
    }
    assert "ford" not in candidate_ids
    michael_ford_rows = [
        response
        for response in bundle.poll_responses
        if response.candidate_id == "michael-ford"
    ]
    assert len(michael_ford_rows) == 4
    assert {
        response.response_option_id for response in michael_ford_rows
    } == {"candidate-michael-ford"}
    assert {response.candidate_name for response in michael_ford_rows} == {
        "Michael Ford"
    }
    bailao_rows = [
        response
        for response in bundle.poll_responses
        if response.candidate_id == "bailao"
    ]
    assert {response.candidate_name for response in bailao_rows} == {"Ana Bailão"}
    assert "Ana Bailao" in {
        response.response_label for response in bailao_rows
    }

    ward_11_readings = [
        reading
        for reading in bundle.poll_readings
        if reading.poll_sample_id == "forum_w11_20260812"
    ]
    assert len(ward_11_readings) == 3

    layton_reading = readings["forum_w11_20260812_council_layton"]
    assert layton_reading.unweighted_base == 385
    assert layton_reading.weighted_base == Decimal("386")
    assert layton_reading.denominator_type == "not_reported"
    assert layton_reading.denominator_text is None
    ward_mayor = readings["forum_w11_20260812_mayor"]
    assert ward_mayor.denominator_type == "not_reported"
    assert ward_mayor.denominator_text is None
    layton_responses = {
        response.candidate_id: response.share
        for response in bundle.poll_responses
        if response.poll_reading_id == layton_reading.poll_reading_id
        and response.response_kind == "candidate"
    }
    assert layton_responses["mike-layton"] == Decimal("0.44")
    assert layton_responses["dianne-saxe"] == Decimal("0.17")

    wong_tam = readings["forum_w13_20260622_23_wong_tam"]
    assert wong_tam.question_text_status == "not_reported"
    assert wong_tam.question_text is None
    assert "67% would vote for Kristyn Wong-Tam" in (wong_tam.notes or "")
    wong_tam_responses = [
        response
        for response in bundle.poll_responses
        if response.poll_reading_id == wong_tam.poll_reading_id
    ]
    assert {response.option_order for response in wong_tam_responses} == {None}
