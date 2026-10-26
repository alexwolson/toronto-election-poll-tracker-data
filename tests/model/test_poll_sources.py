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
    POLL_SAMPLE_COLUMNS,
    POLL_SAMPLE_DOCUMENT_COLUMNS,
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
        "denominator_semantics": "all_respondents",
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


def test_denominator_semantics_is_required_and_consistent(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["poll_readings.csv"][0]["denominator_semantics"] = "likely_voters"
    _write_bundle(tmp_path, tables)
    with pytest.raises(PollSourceContractError, match="denominator_semantics"):
        load_poll_source_bundle(tmp_path)

    tables = _valid_tables()
    # An all-respondents denominator cannot carry decided semantics.
    tables["poll_readings.csv"][0]["denominator_semantics"] = "decided_only"
    _write_bundle(tmp_path, tables)
    with pytest.raises(PollSourceContractError, match="denominator_semantics"):
        load_poll_source_bundle(tmp_path)

    _write_bundle(tmp_path, _valid_tables())
    bundle = load_poll_source_bundle(tmp_path)
    assert {r.denominator_semantics for r in bundle.poll_readings} == {
        "all_respondents"
    }


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

    with pytest.raises(
        PollSourceContractError, match="larger than its recruited sample"
    ):
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
        response
        for response in bundle.poll_responses
        if response.candidate_id == "layton"
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


def test_mainstreet_september_29_bases_and_five_candidate_field() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    bundle = load_poll_source_bundle(repository_root / "data/raw/polls")
    sample = next(
        sample
        for sample in bundle.poll_samples
        if sample.poll_sample_id == "mainstreet-2026-09-29"
    )
    assert sample.fieldwork_start.isoformat() == "2026-09-28"
    assert sample.fieldwork_end.isoformat() == "2026-09-29"
    assert sample.publication_date.isoformat() == "2026-10-02"
    assert sample.publication_at is None
    assert sample.evidence_available_at.isoformat() == "2026-10-03T00:00:00-04:00"
    readings = {
        reading.poll_reading_id: reading
        for reading in bundle.poll_readings
        if reading.poll_sample_id == sample.poll_sample_id
    }
    assert len(readings) == 3
    decided = readings["mainstreet_20260928_29_mayor_decided_leaning"]
    assert decided.denominator_semantics == "decided_plus_leaners"
    assert decided.unweighted_base == 850
    assert decided.weighted_base == Decimal("839.8")
    all_voters = readings["mainstreet_20260928_29_mayor_all"]
    assert all_voters.denominator_semantics == "all_respondents"
    assert (all_voters.unweighted_base, all_voters.weighted_base) == (
        1000,
        Decimal(1000),
    )
    head_to_head = readings["mainstreet_20260928_29_mayor_head_to_head_all"]
    assert head_to_head.scenario_label == "Brad Bradford and Olivia Chow only"
    candidates = {
        response.candidate_name
        for response in bundle.poll_responses
        if response.poll_reading_id == decided.poll_reading_id
        and response.response_kind == "candidate"
    }
    assert candidates == {
        "Brad Bradford",
        "Olivia Chow",
        "Chris Alexander",
        "Sarah McVie",
        "Odessa Paloma Parker",
    }
    # Both additional candidates keep the same identities in every Mainstreet wave.
    for name in ("Sarah McVie", "Odessa Paloma Parker"):
        samples = {
            response.poll_reading_id.split("_mayor_")[0]
            for response in bundle.poll_responses
            if response.candidate_name == name
            and not response.poll_reading_id.startswith("mainstreet_w")  # ward polls
        }
        assert samples == {
            "mainstreet_20260914",
            "mainstreet_20260928_29",
            "mainstreet_20261006_07",
            "mainstreet_20261016_18",
            "mainstreet_20261022_24",
        }


def test_tracked_current_poll_source_inventory() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    bundle = load_poll_source_bundle(repository_root / "data/raw/polls")

    assert len(bundle.source_documents) == 88
    assert len(bundle.poll_sample_documents) == 92
    assert len(bundle.poll_samples) == 72
    assert len(bundle.poll_readings) == 172
    assert len(bundle.poll_responses) == 772

    documents = {
        document.source_document_id: document for document in bundle.source_documents
    }
    samples = {sample.poll_sample_id: sample for sample in bundle.poll_samples}
    readings = {reading.poll_reading_id: reading for reading in bundle.poll_readings}
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
    assert len(citywide_samples) == 47
    assert len(recovered_citywide_ids) == 46
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
    assert len(citywide_readings) == 120
    assert len(citywide_responses) == 536
    assert (
        sum(
            reading.reading_purpose == "general_vote_intention"
            for reading in citywide_readings
        )
        == 111
    )
    assert readings["canadapulse_20251006_mayor_all"].reading_purpose == "context_only"
    assert len({reading.poll_sample_id for reading in bundle.poll_readings}) == 71
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
        "pallas-2026-08-21",
        "liaison-2026-09-05",
        "mainstreet-2026-09-14",
        "liaison-2026-09-20",
        "ipsos-2026-09-08",
        "forum-2026-09-23",
        "canadapulse-2026-09-24",
        "liaison-2026-09-27",
        "mainstreet-2026-09-29",
        "liaison-2026-10-04",
        "nanos-2026-10-04",
        "forum-2026-10-06",
        "scope-2026-10-06",
        "mainstreet-2026-10-07",
        "liaison-2026-10-09",
        "nanos-2026-10-10",
        "pallas-2026-10-14",
        "nanos-2026-10-18",
        "mainstreet-2026-10-18",
        "buildcanada-2026-10-16",
        "pollara-2026-10-19",
        "liaison-2026-10-19",
        "canadapulse-2026-10-21",
        "pollara-2026-10-21",
        "liaison-2026-10-25",
        "mainstreet-2026-10-24",
        "pallas-2026-10-24",
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

    latest_sample = samples["liaison-2026-09-20"]
    assert latest_sample.sponsor == "Toronto Star"
    assert latest_sample.fieldwork_start.isoformat() == "2026-09-19"
    assert latest_sample.fieldwork_end.isoformat() == "2026-09-20"
    assert latest_sample.publication_date.isoformat() == "2026-09-22"
    latest_all = readings["liaison_20260919_20_mayor_all"]
    latest_decided = readings["liaison_20260919_20_mayor_decided_leaning"]
    assert latest_all.unweighted_base == 1000
    assert latest_all.weighted_base == Decimal(1000)
    assert latest_decided.unweighted_base == 828
    assert latest_decided.weighted_base == Decimal(828)

    new_sample = samples["liaison-2026-09-27"]
    assert new_sample.fieldwork_start.isoformat() == "2026-09-26"
    assert new_sample.fieldwork_end.isoformat() == "2026-09-27"
    assert new_sample.publication_date.isoformat() == "2026-09-30"
    assert new_sample.evidence_available_at.isoformat() == "2026-09-30T05:00:22-04:00"
    new_all = readings["liaison_20260926_27_mayor_all"]
    new_decided = readings["liaison_20260926_27_mayor_decided_leaning"]
    assert (new_all.unweighted_base, new_all.weighted_base) == (1000, Decimal(1000))
    assert (new_decided.unweighted_base, new_decided.weighted_base) == (
        848,
        Decimal(847),
    )
    assert new_all.denominator_semantics == "all_respondents"
    assert new_decided.denominator_semantics == "decided_plus_leaners"

    # Mainstreet Oct 6-7: entirely post-suspension; Alexander is not offered.
    mainstreet = samples["mainstreet-2026-10-07"]
    assert mainstreet.fieldwork_start.isoformat() == "2026-10-06"
    assert mainstreet.fieldwork_end.isoformat() == "2026-10-07"
    assert mainstreet.evidence_available_at.isoformat() == "2026-10-09T05:02:32-04:00"
    mainstreet_decided = readings["mainstreet_20261006_07_mayor_decided_leaning"]
    assert (mainstreet_decided.unweighted_base, mainstreet_decided.weighted_base) == (
        864,
        Decimal("865.0"),
    )
    assert mainstreet_decided.denominator_semantics == "decided_plus_leaners"
    assert not any(
        response.candidate_id == "alexander"
        for response in bundle.poll_responses
        if readings[response.poll_reading_id].poll_sample_id == "mainstreet-2026-10-07"
    )

    # Liaison Oct 8-9: post-suspension; Alexander is not offered.
    liaison = samples["liaison-2026-10-09"]
    assert liaison.sponsor == "Toronto Star"
    assert liaison.fieldwork_start.isoformat() == "2026-10-08"
    assert liaison.fieldwork_end.isoformat() == "2026-10-09"
    assert liaison.evidence_available_at.isoformat() == "2026-10-13T05:00:00-04:00"
    liaison_all = readings["liaison_20261008_09_mayor_all"]
    liaison_decided = readings["liaison_20261008_09_mayor_decided_leaning"]
    assert (liaison_all.unweighted_base, liaison_all.weighted_base) == (
        1000,
        Decimal(1000),
    )
    assert (liaison_decided.unweighted_base, liaison_decided.weighted_base) == (
        837,
        Decimal(836),
    )
    assert liaison_all.denominator_semantics == "all_respondents"
    assert liaison_decided.denominator_semantics == "decided_plus_leaners"
    assert not any(
        response.candidate_id == "alexander"
        for response in bundle.poll_responses
        if readings[response.poll_reading_id].poll_sample_id == "liaison-2026-10-09"
    )

    # Nanos wave 2, Oct 8-10: post-suspension; Alexander removed from the questionnaire.
    nanos = samples["nanos-2026-10-10"]
    assert nanos.sponsor == "CP24 / CTV News Toronto"
    assert nanos.fieldwork_start.isoformat() == "2026-10-08"
    assert nanos.fieldwork_end.isoformat() == "2026-10-10"
    assert nanos.recruited_sample_size == 757
    assert nanos.evidence_available_at.isoformat() == "2026-10-13T07:00:29-04:00"
    nanos_decided = readings["nanos_20261008_10_mayor_decided_leaning"]
    assert (nanos_decided.unweighted_base, nanos_decided.weighted_base) == (
        668,
        Decimal(658),
    )
    assert nanos_decided.denominator_semantics == "decided_plus_leaners"
    nanos_all = readings["nanos_20261008_10_mayor_all"]
    assert (nanos_all.unweighted_base, nanos_all.weighted_base) == (757, Decimal(750))
    assert not any(
        response.candidate_id == "alexander"
        for response in bundle.poll_responses
        if readings[response.poll_reading_id].poll_sample_id == "nanos-2026-10-10"
    )

    # Pallas, Oct 14: single-day, post-suspension; Alexander not offered.
    pallas = samples["pallas-2026-10-14"]
    assert pallas.fieldwork_start.isoformat() == "2026-10-14"
    assert pallas.fieldwork_end.isoformat() == "2026-10-14"
    assert pallas.recruited_sample_size == 732
    assert pallas.evidence_available_at.isoformat() == "2026-10-16T09:34:02-04:00"
    pallas_decided = readings["pallas_20261014_mayor_decided_leaning"]
    assert (pallas_decided.unweighted_base, pallas_decided.weighted_base) == (
        686,
        Decimal(686),
    )
    assert pallas_decided.denominator_semantics == "decided_plus_leaners"
    assert not any(
        response.candidate_id == "alexander"
        for response in bundle.poll_responses
        if readings[response.poll_reading_id].poll_sample_id == "pallas-2026-10-14"
    )

    # Nanos wave 3, Oct 15-18: CTV published before the Nanos post; Alexander not offered.
    nanos3 = samples["nanos-2026-10-18"]
    assert nanos3.fieldwork_start.isoformat() == "2026-10-15"
    assert nanos3.fieldwork_end.isoformat() == "2026-10-18"
    assert nanos3.recruited_sample_size == 762
    assert nanos3.evidence_available_at.isoformat() == "2026-10-20T06:01:16-04:00"
    nanos3_decided = readings["nanos_20261015_18_mayor_decided_leaning"]
    assert (nanos3_decided.unweighted_base, nanos3_decided.weighted_base) == (
        682,
        Decimal(669),
    )
    assert nanos3_decided.denominator_semantics == "decided_plus_leaners"
    assert not any(
        response.candidate_id == "alexander"
        for response in bundle.poll_responses
        if readings[response.poll_reading_id].poll_sample_id == "nanos-2026-10-18"
    )

    # Mainstreet Oct 16-18: one combined reported-vote/intention question; decided only.
    ms18_decided = readings["mainstreet_20261016_18_mayor_decided"]
    assert (ms18_decided.unweighted_base, ms18_decided.weighted_base) == (
        903,
        Decimal(866),
    )
    assert ms18_decided.denominator_semantics == "decided_only"
    assert samples["mainstreet-2026-10-18"].evidence_available_at.isoformat() == (
        "2026-10-20T03:38:53-04:00"
    )

    # Two firms new this cycle: Build Canada (SMS-to-online) and Pollara (CUPE 416).
    build_canada = samples["buildcanada-2026-10-16"]
    assert build_canada.pollster == "Build Canada"
    assert build_canada.collection_mode == "online-sms-invitation"
    assert build_canada.recruited_sample_size == 991
    bc_decided = readings["buildcanada_20261011_16_mayor_decided_leaning"]
    assert (bc_decided.unweighted_base, bc_decided.weighted_base) == (
        820,
        Decimal("766.1"),
    )
    assert bc_decided.denominator_semantics == "decided_plus_leaners"
    pollara = samples["pollara-2026-10-19"]
    assert (pollara.pollster, pollara.sponsor) == (
        "Pollara Strategic Insights",
        "CUPE Local 416",
    )
    assert pollara.collection_mode == "mixed"
    pollara_decided = readings["pollara_20261013_19_mayor_decided_leaning"]
    assert (pollara_decided.unweighted_base, pollara_decided.weighted_base) == (
        919,
        Decimal(911),
    )
    assert pollara_decided.reported_share_precision == 0
    assert not any(
        response.candidate_id == "alexander"
        for response in bundle.poll_responses
        if readings[response.poll_reading_id].poll_sample_id
        in {"mainstreet-2026-10-18", "buildcanada-2026-10-16", "pollara-2026-10-19"}
    )

    # Liaison Oct 18-19: post-suspension; Alexander is not offered.
    liaison_oct19 = samples["liaison-2026-10-19"]
    assert liaison_oct19.sponsor == "Toronto Star"
    assert liaison_oct19.publication_date.isoformat() == "2026-10-21"
    assert liaison_oct19.evidence_available_at.isoformat() == (
        "2026-10-21T05:00:00-04:00"
    )
    assert liaison_oct19.collection_mode == "ivr"
    liaison_oct19_decided = readings["liaison_20261018_19_mayor_decided_leaning"]
    assert (
        liaison_oct19_decided.unweighted_base,
        liaison_oct19_decided.weighted_base,
    ) == (857, Decimal(859))
    assert {
        response.candidate_id: response.share
        for response in bundle.poll_responses
        if response.poll_reading_id == "liaison_20261018_19_mayor_decided_leaning"
        and response.candidate_id
    } == {"chow": Decimal("0.47"), "bradford": Decimal("0.49")}

    # Canada Pulse Oct 16-21 (Rogers CityNews): post-suspension; Alexander is not
    # offered. Its definite-voter tables are turnout-screened, so they rank below the
    # all-decided reading.
    canadapulse_oct21 = samples["canadapulse-2026-10-21"]
    assert canadapulse_oct21.sponsor == "Rogers CityNews"
    assert canadapulse_oct21.publication_date.isoformat() == "2026-10-23"
    assert canadapulse_oct21.evidence_available_at.isoformat() == (
        "2026-10-23T06:48:11-04:00"
    )
    assert canadapulse_oct21.collection_mode == "online"
    canadapulse_oct21_decided = readings[
        "canadapulse_20261016_21_mayor_decided_leaning"
    ]
    assert (
        canadapulse_oct21_decided.unweighted_base,
        canadapulse_oct21_decided.weighted_base,
    ) == (663, Decimal(700))
    assert {
        response.candidate_id: response.share
        for response in bundle.poll_responses
        if response.poll_reading_id == "canadapulse_20261016_21_mayor_decided_leaning"
        and response.candidate_id
    } == {"chow": Decimal("0.51"), "bradford": Decimal("0.46")}
    assert {
        readings[f"canadapulse_20261016_21_mayor_{suffix}"].denominator_semantics
        for suffix in ("definite_all", "definite_decided_leaning")
    } == {"other"}

    # Ipsos for the Star was released later than its older fieldwork.
    ipsos = samples["ipsos-2026-09-08"]
    assert ipsos.sponsor == "Toronto Star"
    assert ipsos.fieldwork_start.isoformat() == "2026-09-04"
    assert ipsos.fieldwork_end.isoformat() == "2026-09-08"
    assert ipsos.publication_date.isoformat() == "2026-09-23"
    assert ipsos.collection_mode == "online"
    ipsos_all = readings["ipsos_20260904_08_mayor_all"]
    ipsos_likely = readings["ipsos_20260904_08_mayor_extremely_likely"]
    assert ipsos_all.unweighted_base == 1006
    assert ipsos_all.weighted_base == Decimal(1006)
    assert ipsos_likely.unweighted_base == 584
    assert ipsos_likely.weighted_base == Decimal(578)
    assert ipsos_likely.turnout_screen == "custom"
    # The model's ranking key is data, entered at ingestion, not a text heuristic.
    assert ipsos_all.denominator_semantics == "all_respondents"
    assert ipsos_likely.denominator_semantics == "other"
    assert latest_decided.denominator_semantics == "decided_plus_leaners"
    assert latest_all.denominator_semantics == "all_respondents"
    assert (
        readings[
            "pallas_20260819_21_mayor_leaning_with_undecided"
        ].denominator_semantics
        == "all_respondents"
    )

    canada_pulse = samples["canadapulse-2025-10-06"]
    assert canada_pulse.collection_mode == "online"
    assert canada_pulse.fieldwork_start.isoformat() == "2025-09-30"
    assert canada_pulse.fieldwork_end.isoformat() == "2025-10-06"
    assert canada_pulse.publication_date.isoformat() == "2025-10-21"
    canada_reading = readings["canadapulse_20251006_mayor_all"]
    assert canada_reading.unweighted_base == 406
    assert canada_reading.weighted_base == Decimal(406)
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
        reading.weighted_base == Decimal(1001) for reading in forum_head_to_heads
    )

    liaison_june_all = readings["liaison_20260628_30_mayor_all"]
    liaison_june_decided = readings["liaison_20260628_30_mayor_decided"]
    assert liaison_june_all.poll_sample_id == liaison_june_decided.poll_sample_id
    assert liaison_june_all.denominator_type == "all_respondents"
    assert liaison_june_decided.denominator_type == "decided_respondents"
    assert liaison_june_all.unweighted_base == 1000
    assert liaison_june_decided.unweighted_base == 805
    assert liaison_june_decided.weighted_base == Decimal(801)
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
    assert (
        readings["liaison_20260724_26_mayor_decided_leaning"].denominator_type
        == "custom"
    )
    assert (
        readings["liaison_20260804_05_mayor_decided_leaning"].denominator_type
        == "custom"
    )

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
    assert {response.response_option_id for response in michael_ford_rows} == {
        "candidate-michael-ford"
    }
    assert {response.candidate_name for response in michael_ford_rows} == {
        "Michael Ford"
    }
    bailao_rows = [
        response
        for response in bundle.poll_responses
        if response.candidate_id == "bailao"
    ]
    assert {response.candidate_name for response in bailao_rows} == {"Ana Bailão"}
    assert "Ana Bailao" in {response.response_label for response in bailao_rows}

    ward_11_readings = [
        reading
        for reading in bundle.poll_readings
        if reading.poll_sample_id == "forum_w11_20260812"
    ]
    assert len(ward_11_readings) == 3

    ward_20_august = samples["forum_w20_20260818"]
    assert ward_20_august.recruited_sample_size == 269
    assert ward_20_august.publication_date.isoformat() == "2026-08-20"
    assert len(readings_by_sample[ward_20_august.poll_sample_id]) == 3
    tory_jr = readings["forum_w20_20260818_council_tory_jr"]
    assert tory_jr.unweighted_base == 211
    assert tory_jr.weighted_base == Decimal(207)
    tory_jr_shares = {
        response.candidate_id or response.response_option_id: response.share
        for response in bundle.poll_responses
        if response.poll_reading_id == tory_jr.poll_reading_id
    }
    assert tory_jr_shares == {
        "parthi-kandavel": Decimal("0.19"),
        "philip-mills": Decimal("0.03"),
        "kevin-rupasinghe": Decimal("0.24"),
        "mohammad-ali-reza": Decimal("0.02"),
        "john-tory-jr": Decimal("0.38"),
        "other": Decimal("0.13"),
    }

    layton_reading = readings["forum_w11_20260812_council_layton"]
    assert layton_reading.unweighted_base == 385
    assert layton_reading.weighted_base == Decimal(386)
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


def test_canada_pulse_september_readings_keep_bases_and_subgroup_separate() -> None:
    root = Path(__file__).resolve().parents[2]
    bundle = load_poll_source_bundle(root / "data/raw/polls")
    sample = next(
        s for s in bundle.poll_samples if s.poll_sample_id == "canadapulse-2026-09-24"
    )
    readings = {
        r.poll_reading_id: r
        for r in bundle.poll_readings
        if r.poll_sample_id == sample.poll_sample_id
    }
    assert sample.recruited_sample_size == 510
    assert sample.collection_mode == "online"
    assert sample.sponsor == "Rogers CityNews"
    assert sample.fieldwork_start.isoformat() == "2026-09-14"
    assert sample.fieldwork_end.isoformat() == "2026-09-24"
    assert sample.publication_date.isoformat() == "2026-09-29"
    assert "decided-vote target" in sample.notes
    assert len(readings) == 3
    decided = readings["canadapulse_20260914_24_mayor_decided_leaning"]
    assert decided.denominator_semantics == "decided_plus_leaners"
    assert decided.unweighted_base == 380
    assert decided.weighted_base == Decimal(380)
    assert decided.reading_purpose == "general_vote_intention"
    all_voters = readings["canadapulse_20260914_24_mayor_all"]
    assert all_voters.denominator_semantics == "all_respondents"
    assert all_voters.weighted_base == Decimal(510)
    all_shares = {
        r.candidate_id or r.response_kind: r.share
        for r in bundle.poll_responses
        if r.poll_reading_id == all_voters.poll_reading_id
    }
    assert all_shares == {
        "chow": Decimal("0.38"),
        "bradford": Decimal("0.25"),
        "alexander": Decimal("0.07"),
        "other": Decimal("0.04"),
        "would_not_vote": Decimal("0.06"),
        "dont_know": Decimal("0.20"),
    }
    subgroup = readings["canadapulse_20260914_24_mayor_time_for_change"]
    assert subgroup.reading_purpose == "routed_subgroup"
    assert subgroup.unweighted_base == 275
    assert subgroup.weighted_base == Decimal(279)
    documents = [
        d
        for d in bundle.source_documents
        if d.source_document_id.startswith("canadapulse_2026-09-")
    ]
    assert {d.page_count for d in documents} == {4, 14}
    assert all(d.visual_qa_status == "passed" for d in documents)


@pytest.mark.parametrize(
    "ward,recruited,council_base,mayor_base,council_shares,mayor_shares",
    [
        (
            3,
            535,
            (406, 416),
            (493, 487),
            {
                "Amber Morley": "0.40",
                "Ted Opitz": "0.27",
                "Mihaela Andrei": "0.07",
                "Anthony Internicola": "0.14",
                "Other": "0.12",
            },
            {
                "Olivia Chow": "0.36",
                "Brad Bradford": "0.43",
                "Chris Alexander": "0.14",
                "Other": "0.07",
            },
        ),
        (
            4,
            464,
            (307, 331),
            (433, 443),
            {
                "Nadia Guerrera": "0.23",
                "Debbie King": "0.37",
                "Diana Chan McNally": "0.18",
                "Vanessa Raponi": "0.06",
                "Other": "0.16",
            },
            {
                "Olivia Chow": "0.55",
                "Brad Bradford": "0.35",
                "Chris Alexander": "0.06",
                "Other": "0.04",
            },
        ),
        (
            13,
            519,
            (362, 370),
            (476, 446),
            {
                "Chris Moise": "0.29",
                "Curran Stikuts": "0.13",
                "Daniel Tate": "0.26",
                "Walied Khogali Ali": "0.08",
                "Other": "0.25",
            },
            {
                "Olivia Chow": "0.51",
                "Brad Bradford": "0.36",
                "Chris Alexander": "0.07",
                "Other": "0.05",
            },
        ),
        (
            19,
            474,
            (417, 395),
            (452, 440),
            {
                "James Dann": "0.06",
                "Nate Erskine-Smith": "0.52",
                "Natalie Johnson": "0.24",
                "Jennie Worden": "0.06",
                "Other": "0.12",
            },
            {
                "Olivia Chow": "0.52",
                "Brad Bradford": "0.30",
                "Chris Alexander": "0.14",
                "Other": "0.04",
            },
        ),
        (
            23,
            368,
            (298, 293),
            (329, 324),
            {
                "Han Dong": "0.12",
                "Kevin Li": "0.08",
                "Jamaal Myers": "0.31",
                "Shaun Chen": "0.37",
                "John-Mark Oleh": "0.06",
                "Other": "0.07",
            },
            {
                "Olivia Chow": "0.60",
                "Brad Bradford": "0.32",
                "Chris Alexander": "0.04",
                "Other": "0.04",
            },
        ),
    ],
)
def test_september_forum_ward_sources_preserve_bases_and_published_shares(
    ward, recruited, council_base, mayor_base, council_shares, mayor_shares
) -> None:
    from backend.model.council_race_card import load_ward_poll_readings

    root = Path(__file__).resolve().parents[2]
    bundle = load_poll_source_bundle(root / "data/raw/polls")
    sample_id = f"forum_w{ward:02d}_20260925_27"
    sample = next(s for s in bundle.poll_samples if s.poll_sample_id == sample_id)
    assert sample.geography_type == "ward"
    assert sample.geography_id == f"toronto-ward-{ward}"
    assert sample.recruited_sample_size == recruited
    assert sample.collection_mode == "ivr-online-panel"
    assert sample.fieldwork_start.isoformat() == "2026-09-25"
    assert sample.fieldwork_end.isoformat() == "2026-09-27"
    assert sample.publication_date.isoformat() == "2026-10-02"
    assert sample.evidence_available_at > sample.publication_at
    readings = [r for r in bundle.poll_readings if r.poll_sample_id == sample_id]
    assert len(readings) == 2  # council and mayor are dependent, not two polls
    for office, bases, shares in [
        ("council", council_base, council_shares),
        ("mayoral", mayor_base, mayor_shares),
    ]:
        reading = next(r for r in readings if r.contest_type == office)
        assert reading.denominator_semantics == "decided_plus_leaners"
        assert reading.denominator_text == "[Decided/ Leaning]"
        assert (reading.unweighted_base, reading.weighted_base) == bases
        assert reading.reported_base is None
        assert reading.question_order is None
        assert reading.tested_choice_set_status == "unknown"
        responses = [
            r
            for r in bundle.poll_responses
            if r.poll_reading_id == reading.poll_reading_id
        ]
        assert {r.candidate_name or r.response_label: r.share for r in responses} == {
            name: Decimal(value) for name, value in shares.items()
        }
        assert {r.response_kind for r in responses} == {"candidate", "other"}
        assert all(r.reported_value is not None for r in responses)
    document = next(
        d
        for d in bundle.source_documents
        if d.source_document_id == sample_id + "_release"
    )
    assert document.page_count == 3
    assert document.visual_qa_status == "passed"
    assert document.redistribution_status == "unknown"
    display = load_ward_poll_readings(root / "data/raw/polls/ward_poll_readings.csv")
    council = next(
        r for r in display[str(ward)] if r.poll_id == f"forum-ward{ward}-2026-09-27"
    )
    assert council.date_published == "2026-10-02"
    assert council.sample_size == recruited
    assert council.denominator == "decided and leaning voters"
    assert council.undecided_share is None
    assert council.ballot_status == "final_ballot_candidates"
    assert {c.candidate_name: Decimal(str(c.share)) for c in council.candidates} == {
        ("Other candidates" if name == "Other" else name): Decimal(value)
        for name, value in council_shares.items()
    }
    assert all(
        c.registration_status == "registered"
        for c in council.candidates
        if not c.is_residual
    )
    assert {c.candidate_name for c in council.candidates if c.is_incumbent} == {
        3: {"Amber Morley"},
        4: set(),
        13: {"Chris Moise"},
        19: set(),
        23: {"Jamaal Myers"},
    }[ward]


def test_liaison_october_6_preserves_both_denominators_and_reading_bases() -> None:
    bundle = load_poll_source_bundle(
        Path(__file__).resolve().parents[2] / "data/raw/polls"
    )
    sample = next(
        s for s in bundle.poll_samples if s.poll_sample_id == "liaison-2026-10-04"
    )
    assert sample.fieldwork_start.isoformat() == "2026-10-03"
    assert sample.fieldwork_end.isoformat() == "2026-10-04"
    assert sample.publication_date.isoformat() == "2026-10-06"
    assert sample.evidence_available_at.isoformat() == "2026-10-06T05:00:15-04:00"
    assert sample.recruited_sample_size == 1000
    readings = {
        r.denominator_semantics: r
        for r in bundle.poll_readings
        if r.poll_sample_id == sample.poll_sample_id
    }
    assert set(readings) == {"all_respondents", "decided_plus_leaners"}
    all_voters = readings["all_respondents"]
    decided = readings["decided_plus_leaners"]
    assert (all_voters.unweighted_base, all_voters.weighted_base) == (
        1000,
        Decimal(1000),
    )
    assert (decided.unweighted_base, decided.weighted_base) == (840, Decimal(841))
    assert all_voters.question_text_status == "not_reported"
    assert decided.question_text == (
        "If an election were held today, for whom would you cast your vote for mayor?"
    )
    for reading, expected in [
        (
            all_voters,
            {
                "candidate-chow": "0.40",
                "candidate-bradford": "0.33",
                "candidate-alexander": "0.08",
                "someone-else": "0.03",
                "undecided": "0.16",
            },
        ),
        (
            decided,
            {
                "candidate-chow": "0.48",
                "candidate-bradford": "0.40",
                "candidate-alexander": "0.09",
                "someone-else": "0.03",
            },
        ),
    ]:
        actual = {
            r.response_option_id: r.share
            for r in bundle.poll_responses
            if r.poll_reading_id == reading.poll_reading_id
        }
        assert actual == {key: Decimal(value) for key, value in expected.items()}


def test_nanos_october_6_keeps_leaners_bases_and_subgroups_dependent() -> None:
    bundle = load_poll_source_bundle(
        Path(__file__).resolve().parents[2] / "data/raw/polls"
    )
    sample = next(
        s for s in bundle.poll_samples if s.poll_sample_id == "nanos-2026-10-04"
    )
    assert sample.recruited_sample_size == 755
    assert sample.collection_mode == "mixed"
    assert sample.fieldwork_start.isoformat() == "2026-09-30"
    assert sample.fieldwork_end.isoformat() == "2026-10-04"
    assert sample.publication_date.isoformat() == "2026-10-06"
    assert (
        sample.evidence_available_at.isoformat() == "2026-10-06T06:02:56.736000-04:00"
    )
    readings = {
        r.poll_reading_id: r
        for r in bundle.poll_readings
        if r.poll_sample_id == sample.poll_sample_id
    }
    assert len(readings) == 7
    decided = readings["nanos_20260930_1004_mayor_decided_leaning"]
    initial = readings["nanos_20260930_1004_mayor_all"]
    followup = readings["nanos_20260930_1004_mayor_lean_followup"]
    assert decided.denominator_semantics == "decided_plus_leaners"
    assert decided.denominator_text == "Ballot – Decided Voters Only"
    assert (decided.unweighted_base, decided.weighted_base) == (648, Decimal(632))
    assert initial.denominator_semantics == "all_respondents"
    assert (initial.unweighted_base, initial.weighted_base) == (755, Decimal(750))
    assert followup.reading_purpose == "conditional_lean_followup"
    assert (followup.unweighted_base, followup.weighted_base) == (151, Decimal(162))
    assert all(
        r.denominator_semantics == "other"
        for key, r in readings.items()
        if key not in {initial.poll_reading_id, decided.poll_reading_id}
    )
    for reading, expected in [
        (
            decided,
            {
                "candidate-chow": "0.524",
                "candidate-bradford": "0.426",
                "candidate-alexander": "0.04",
                "rest": "0.01",
            },
        ),
        (
            initial,
            {
                "candidate-chow": "0.419",
                "candidate-bradford": "0.327",
                "candidate-alexander": "0.027",
                "undecided": "0.218",
                "rest": "0.008",
            },
        ),
    ]:
        actual = {
            r.response_option_id: r.share
            for r in bundle.poll_responses
            if r.poll_reading_id == reading.poll_reading_id
        }
        assert actual == {key: Decimal(value) for key, value in expected.items()}
    assert sum(
        r.share
        for r in bundle.poll_responses
        if r.poll_reading_id == initial.poll_reading_id
    ) == Decimal("0.999")
    document = next(
        d
        for d in bundle.source_documents
        if d.source_document_id == "nanos_2026-10-04_tables"
    )
    assert document.retrieval_status == "access_pending"
    assert document.local_path is None
    assert document.visual_qa_status == "not_applicable"


def test_scope_october_6_is_one_all_respondent_reading_without_alexander() -> None:
    bundle = load_poll_source_bundle(
        Path(__file__).resolve().parents[2] / "data/raw/polls"
    )
    sample = next(
        s for s in bundle.poll_samples if s.poll_sample_id == "scope-2026-10-06"
    )
    assert sample.pollster == "Scope Research"
    assert sample.sponsor in (None, "")
    assert sample.fieldwork_start.isoformat() == "2026-10-06"
    assert sample.fieldwork_end.isoformat() == "2026-10-06"
    assert sample.publication_date.isoformat() == "2026-10-08"
    assert sample.evidence_available_at.isoformat() == "2026-10-08T06:02:53-04:00"
    assert sample.recruited_sample_size == 3100
    readings = [
        r for r in bundle.poll_readings if r.poll_sample_id == sample.poll_sample_id
    ]
    assert len(readings) == 1
    (reading,) = readings
    assert reading.denominator_semantics == "all_respondents"
    assert reading.reported_base == Decimal(3100)
    assert reading.unweighted_base is None and reading.weighted_base is None
    actual = {
        (r.response_kind, r.response_option_id): r.share
        for r in bundle.poll_responses
        if r.poll_reading_id == reading.poll_reading_id
    }
    assert actual == {
        ("candidate", "candidate-bradford"): Decimal("0.41"),
        ("candidate", "candidate-chow"): Decimal("0.44"),
        ("other", "other"): Decimal("0.03"),
        ("undecided", "undecided"): Decimal("0.11"),
        ("would_not_vote", "would-not-vote"): Decimal("0.02"),
    }


@pytest.mark.parametrize(
    "ward,end,recruited,council_base,mayor_base,council_shares,mayor_shares,incumbents",
    [
        (
            4,
            "18",
            594,
            (541, 542),
            (576, 577),
            {
                "Nadia Guerrera": "0.32",
                "Debbie King": "0.16",
                "Diana Chan McNally": "0.29",
                "Vanessa Raponi": "0.17",
                "Other": "0.06",
            },
            {"Olivia Chow": "0.51", "Brad Bradford": "0.46", "Other": "0.03"},
            set(),
        ),
        (
            5,
            "18",
            543,
            (469, 477),
            (509, 515),
            {
                "Chiara Padovani": "0.28",
                "Daniel Di Giorgio": "0.30",
                "Frances Nunziata": "0.34",
                "Other": "0.07",
            },
            {"Olivia Chow": "0.51", "Brad Bradford": "0.44", "Other": "0.05"},
            {"Frances Nunziata"},
        ),
        (
            13,
            "18",
            648,
            (556, 583),
            (626, 628),
            {
                "Chris Moise": "0.34",
                "Curran Stikuts": "0.25",
                "Daniel Tate": "0.30",
                "Other": "0.11",
            },
            {"Olivia Chow": "0.58", "Brad Bradford": "0.40", "Other": "0.02"},
            {"Chris Moise"},
        ),
        (
            14,
            "18",
            604,
            (495, 473),
            (556, 541),
            {
                "Dianne Saxe": "0.22",
                "Mary Fragedakis": "0.26",
                "Sara Ehrhardt": "0.40",
                "Other": "0.12",
            },
            {"Olivia Chow": "0.60", "Brad Bradford": "0.34", "Other": "0.05"},
            set(),
        ),
        (
            19,
            "20",
            1084,
            (997, 990),
            (1045, 1044),
            {
                "James Dann": "0.21",
                "Nate Erskine-Smith": "0.32",
                "Natalie Johnson": "0.26",
                "Jennie Worden": "0.16",
                "Other": "0.04",
            },
            {"Olivia Chow": "0.60", "Brad Bradford": "0.37", "Other": "0.03"},
            set(),
        ),
        (
            20,
            "18",
            538,
            (447, 464),
            (515, 515),
            {
                "Parthi Kandavel": "0.41",
                "Kevin Rupasinghe": "0.38",
                "Other": "0.21",
            },
            {"Olivia Chow": "0.50", "Brad Bradford": "0.47", "Other": "0.04"},
            {"Parthi Kandavel"},
        ),
        (
            23,
            "18",
            512,
            (472, 476),
            (496, 496),
            {
                "Jamaal Myers": "0.34",
                "Shaun Chen": "0.42",
                "Han Dong": "0.12",
                "Other": "0.12",
            },
            {"Olivia Chow": "0.62", "Brad Bradford": "0.32", "Other": "0.06"},
            {"Jamaal Myers"},
        ),
    ],
)
def test_october_forum_ward_sources_preserve_bases_and_published_shares(
    ward,
    end,
    recruited,
    council_base,
    mayor_base,
    council_shares,
    mayor_shares,
    incumbents,
) -> None:
    from backend.model.council_race_card import load_ward_poll_readings

    root = Path(__file__).resolve().parents[2]
    bundle = load_poll_source_bundle(root / "data/raw/polls")
    sample_id = f"forum_w{ward:02d}_20261015_{end}"
    sample = next(s for s in bundle.poll_samples if s.poll_sample_id == sample_id)
    assert sample.geography_type == "ward"
    assert sample.geography_id == f"toronto-ward-{ward}"
    assert sample.recruited_sample_size == recruited
    assert sample.collection_mode == "ivr-online-panel"
    assert sample.fieldwork_start.isoformat() == "2026-10-15"
    assert sample.fieldwork_end.isoformat() == f"2026-10-{end}"
    assert sample.publication_date.isoformat() == "2026-10-22"
    assert sample.evidence_available_at > sample.publication_at
    readings = [r for r in bundle.poll_readings if r.poll_sample_id == sample_id]
    assert len(readings) == 2  # council and mayor are dependent, not two polls
    for office, bases, shares in [
        ("council", council_base, council_shares),
        ("mayoral", mayor_base, mayor_shares),
    ]:
        reading = next(r for r in readings if r.contest_type == office)
        assert reading.denominator_semantics == "decided_plus_leaners"
        assert reading.denominator_text == "[Decided/ Leaning]"
        assert (reading.unweighted_base, reading.weighted_base) == bases
        assert reading.reported_base is None
        assert reading.tested_choice_set_status == "unknown"
        responses = [
            r
            for r in bundle.poll_responses
            if r.poll_reading_id == reading.poll_reading_id
        ]
        assert {r.candidate_name or r.response_label: r.share for r in responses} == {
            name: Decimal(value) for name, value in shares.items()
        }
        assert {r.response_kind for r in responses} == {"candidate", "other"}
    document = next(
        d
        for d in bundle.source_documents
        if d.source_document_id == sample_id + "_release"
    )
    assert document.page_count == 3
    assert document.visual_qa_status == "passed"
    display = load_ward_poll_readings(root / "data/raw/polls/ward_poll_readings.csv")
    council = next(
        r for r in display[str(ward)] if r.poll_id == f"forum-ward{ward}-2026-10-{end}"
    )
    assert council.date_published == "2026-10-22"
    assert council.sample_size == recruited
    assert council.denominator == "decided and leaning voters"
    assert council.undecided_share is None
    assert council.ballot_status == "final_ballot_candidates"
    assert {c.candidate_name: Decimal(str(c.share)) for c in council.candidates} == {
        ("Other candidates" if name == "Other" else name): Decimal(value)
        for name, value in council_shares.items()
    }
    assert {c.candidate_name for c in council.candidates if c.is_incumbent} == (
        incumbents
    )


def test_di_giorgio_keeps_one_ballot_identity_across_forum_misprints() -> None:
    bundle = load_poll_source_bundle(
        Path(__file__).resolve().parents[2] / "data/raw/polls"
    )
    rows = [r for r in bundle.poll_responses if "iorgio" in r.response_label]
    # Mainstreet (Oct 23) prints the ballot spelling itself.
    assert {r.response_label for r in rows} == {
        "David DiGiorgio",
        "Daniel DiGiorgio",
        "Daniel Di Giorgio",
    }
    assert {(r.candidate_id, r.candidate_name) for r in rows} == {
        ("daniel-di-giorgio", "Daniel Di Giorgio")
    }


_MAINSTREET_WARD_COUNCIL = {
    4: {
        "Nadia Guerrera": "0.352",
        "Debbie King": "0.033",
        "Diana Chan McNally": "0.292",
        "Bridget Ogundipe": "0.004",
        "Adam Pham": "0.155",
        "Vanessa Raponi": "0.034",
        "Holly Weber": "0.034",
        "No preferred candidate": "0.095",
    },
    10: {
        "Ian Cunningham": "0.376",
        "Xue Ding": "0.016",
        "Andi Hoàng-Lefranc": "0.007",
        "Bashar Kassir": "0.016",
        "Ausma Malik": "0.391",
        "Paul Nash": "0.029",
        "Husain Neemuchwala": "0.032",
        "No preferred candidate": "0.134",
    },
    25: {
        "Shawn Allen": "0.371",
        "Dharshan Casinathen": "0.057",
        "Jannette Lumley": "0.013",
        "Zakir Patel": "0.116",
        "Neethan Shan": "0.294",
        "Another candidate": "0.150",
    },
}


@pytest.mark.parametrize(
    "ward,base,mayor_shares,undecided,incumbents",
    [
        (4, 262, ("0.625", "0.337", "0.023", "0.000", "0.015"), "0.095", set()),
        (
            10,
            292,
            ("0.542", "0.451", "0.000", "0.000", "0.007"),
            "0.134",
            {"Ausma Malik"},
        ),
        (
            25,
            340,
            ("0.424", "0.532", "0.006", "0.006", "0.031"),
            None,
            {"Neethan Shan"},
        ),
    ],
)
def test_mainstreet_october_ward_sources_keep_vote_intention_as_printed(
    ward, base, mayor_shares, undecided, incumbents
) -> None:
    from backend.model.council_race_card import load_ward_poll_readings

    root = Path(__file__).resolve().parents[2]
    bundle = load_poll_source_bundle(root / "data/raw/polls")
    sample_id = f"mainstreet_w{ward:02d}_20261014_16"
    sample = next(s for s in bundle.poll_samples if s.poll_sample_id == sample_id)
    assert sample.geography_type == "ward"
    assert sample.geography_id == f"toronto-ward-{ward}"
    assert sample.recruited_sample_size == base
    assert sample.collection_mode == "ivr"
    assert sample.fieldwork_start.isoformat() == "2026-10-14"
    assert sample.fieldwork_end.isoformat() == "2026-10-16"
    assert sample.publication_date.isoformat() == "2026-10-22"
    links = [
        link
        for link in bundle.poll_sample_documents
        if link.poll_sample_id == sample_id
    ]
    assert [link.source_document_id for link in links] == [
        "mainstreet_2026-10-22_wards_tables"
    ]
    readings = [r for r in bundle.poll_readings if r.poll_sample_id == sample_id]
    assert len(readings) == 2  # council and mayor are dependent, not two polls
    expected = {
        "council": _MAINSTREET_WARD_COUNCIL[ward],
        "mayoral": dict(
            zip(
                [
                    "Olivia Chow",
                    "Brad Bradford",
                    "Odessa Paloma Parker",
                    "Sarah McVie",
                    "Someone else",
                ],
                mayor_shares,
                strict=True,
            )
        ),
    }
    for office, shares in expected.items():
        reading = next(r for r in readings if r.contest_type == office)
        assert reading.denominator_semantics == "all_respondents"
        assert reading.reading_purpose == "general_vote_intention"
        assert (reading.unweighted_base, reading.weighted_base) == (base, base)
        responses = [
            r
            for r in bundle.poll_responses
            if r.poll_reading_id == reading.poll_reading_id
        ]
        assert {r.candidate_name or r.response_label: r.share for r in responses} == {
            name: Decimal(value) for name, value in shares.items()
        }
    document = next(
        d
        for d in bundle.source_documents
        if d.source_document_id == "mainstreet_2026-10-22_wards_tables"
    )
    assert document.page_count == 35
    display = load_ward_poll_readings(root / "data/raw/polls/ward_poll_readings.csv")
    council = next(
        r
        for r in display[str(ward)]
        if r.poll_id == f"mainstreet-ward{ward}-2026-10-16"
    )
    assert council.firm == "Mainstreet Research"
    assert council.date_conducted == "2026-10-16"
    assert council.date_published == "2026-10-22"
    assert council.sample_size == base
    assert council.denominator == "all respondents"
    assert council.ballot_status == "final_ballot_candidates"
    assert council.undecided_share == (float(undecided) if undecided else None)
    assert {c.candidate_name: Decimal(str(c.share)) for c in council.candidates} == {
        ("Other candidates" if name == "Another candidate" else name): Decimal(value)
        for name, value in _MAINSTREET_WARD_COUNCIL[ward].items()
        if name != "No preferred candidate"
    }
    assert {c.candidate_name for c in council.candidates if c.is_incumbent} == (
        incumbents
    )


_MAINSTREET_OCT23_COUNCIL = {
    3: {
        "Mihaela Andrei": "0.069",
        "Anthony Internicola": "0.023",
        "Amber Morley": "0.321",
        "Ted Opitz": "0.464",
        "No preferred candidate": "0.123",
    },
    5: {
        "Sharmarke Ali": "0.007",
        "Matthew Boateng": "0.032",
        "Daniel Di Giorgio": "0.196",
        "Ahmed Mawel": "0.081",
        "Frances Nunziata": "0.385",
        "Nekpen Obasogie": "0.018",
        "Chiara Padovani": "0.207",
        "Sileen Phillips": "0.007",
        "No preferred candidate": "0.068",
    },
    13: {
        "Joe Cadeau": "0.044",
        "Victoria Davis": "0.009",
        "Walied Khogali Ali": "0.026",
        "Chris Moise": "0.438",
        "Curran Stikuts": "0.158",
        "Daniel Tate": "0.169",
        "Nicki Ward": "0.043",
        "No preferred candidate": "0.115",
    },
}


@pytest.mark.parametrize(
    "ward,base,mayor_shares,undecided,incumbents,choice_set",
    [
        (
            3,
            342,
            ("0.337", "0.623", "0.000", "0.006", "0.034"),
            "0.123",
            {"Amber Morley"},
            "complete",
        ),
        (
            5,
            328,
            ("0.416", "0.393", "0.007", "0.037", "0.147"),
            "0.068",
            {"Frances Nunziata"},
            "partial",
        ),
        (
            13,
            348,
            ("0.572", "0.344", "0.000", "0.000", "0.083"),
            "0.115",
            {"Chris Moise"},
            "partial",
        ),
    ],
)
def test_mainstreet_october_23_ward_sources_keep_vote_intention_as_printed(
    ward, base, mayor_shares, undecided, incumbents, choice_set
) -> None:
    from backend.model.council_race_card import load_ward_poll_readings

    root = Path(__file__).resolve().parents[2]
    bundle = load_poll_source_bundle(root / "data/raw/polls")
    sample_id = f"mainstreet_w{ward:02d}_20261014_16"
    sample = next(s for s in bundle.poll_samples if s.poll_sample_id == sample_id)
    assert sample.geography_id == f"toronto-ward-{ward}"
    assert sample.recruited_sample_size == base
    assert sample.collection_mode == "ivr"
    assert sample.fieldwork_end.isoformat() == "2026-10-16"
    assert sample.publication_date.isoformat() == "2026-10-23"
    links = [l for l in bundle.poll_sample_documents if l.poll_sample_id == sample_id]
    assert [l.source_document_id for l in links] == [
        "mainstreet_2026-10-23_wards_tables"
    ]
    readings = [r for r in bundle.poll_readings if r.poll_sample_id == sample_id]
    assert len(readings) == 2
    names = [
        "Olivia Chow",
        "Brad Bradford",
        "Odessa Paloma Parker",
        "Sarah McVie",
        "Someone else",
    ]
    expected = {
        "council": _MAINSTREET_OCT23_COUNCIL[ward],
        "mayoral": dict(zip(names, mayor_shares, strict=True)),
    }
    for office, shares in expected.items():
        reading = next(r for r in readings if r.contest_type == office)
        assert reading.denominator_semantics == "all_respondents"
        assert (reading.unweighted_base, reading.weighted_base) == (base, base)
        responses = [
            r
            for r in bundle.poll_responses
            if r.poll_reading_id == reading.poll_reading_id
        ]
        assert {r.candidate_name or r.response_label: r.share for r in responses} == {
            name: Decimal(value) for name, value in shares.items()
        }
    council = next(r for r in readings if r.contest_type == "council")
    assert council.tested_choice_set_status == choice_set
    document = next(
        d
        for d in bundle.source_documents
        if d.source_document_id == "mainstreet_2026-10-23_wards_tables"
    )
    assert document.page_count == 33
    display = load_ward_poll_readings(root / "data/raw/polls/ward_poll_readings.csv")
    card = next(
        r
        for r in display[str(ward)]
        if r.poll_id == f"mainstreet-ward{ward}-2026-10-16"
    )
    assert card.date_published == "2026-10-23"
    assert card.denominator == "all respondents"
    assert card.undecided_share == float(undecided)
    assert {c.candidate_name: Decimal(str(c.share)) for c in card.candidates} == {
        name: Decimal(value)
        for name, value in _MAINSTREET_OCT23_COUNCIL[ward].items()
        if name != "No preferred candidate"
    }
    assert {c.candidate_name for c in card.candidates if c.is_incumbent} == incumbents
