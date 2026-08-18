import csv
import shutil
from pathlib import Path

import pytest

from backend.model.poll_ingest import IngestError, ingest_poll_source

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "data/raw/polls/historical_mayoral"
TABLES = (
    "source_documents",
    "poll_sample_documents",
    "poll_samples",
    "poll_readings",
    "poll_responses",
)


def _copy_bundle(tmp_path: Path) -> Path:
    dest = tmp_path / "bundle"
    dest.mkdir()
    for table in TABLES:
        shutil.copy(BUNDLE / f"{table}.csv", dest / f"{table}.csv")
    return dest


def _counts(bundle_dir: Path) -> dict[str, int]:
    return {
        table: sum(1 for _ in csv.DictReader(open(bundle_dir / f"{table}.csv")))
        for table in TABLES
    }


def _valid_spec() -> dict[str, list[dict[str, str]]]:
    doc = {
        "source_document_id": "test_doc_2014",
        "document_role": "release",
        "publisher_url": "https://example.org/test.pdf",
        "retrieval_url": "https://web.archive.org/web/2014id_/https://example.org/test.pdf",
        "retrieval_status": "retrieved",
        "retrieved_at": "2026-08-18T00:00:00Z",
        "media_type": "application/pdf",
        "sha256": "a" * 64,
        "local_path": "data/source_documents/historical_mayoral/test/test_doc_2014.pdf",
        "byte_size": "1000",
        "page_count": "2",
        "sheet_count": "",
        "text_layer_status": "present",
        "visual_qa_status": "passed",
        "access_class": "public",
        "redistribution_status": "unknown",
        "reuse_terms_url": "",
        "notes": "Test-only synthetic document.",
    }
    sample = {
        "poll_sample_id": "test_city_2014_01_01_n500",
        "election_cycle_id": "toronto_2014",
        "pollster": "Test Pollster",
        "sponsor": "",
        "geography_type": "citywide",
        "geography_id": "toronto",
        "fieldwork_start": "2014-01-01",
        "fieldwork_end": "2014-01-01",
        "publication_date": "2014-01-02",
        "publication_at": "",
        "publication_time_precision": "date_only",
        "evidence_available_at": "2014-01-03T00:00:00-05:00",
        "collection_mode": "ivr",
        "recruited_sample_size": "500",
        "extraction_status": "extracted",
        "notes": "Test-only synthetic sample.",
    }
    link = {
        "poll_sample_id": "test_city_2014_01_01_n500",
        "source_document_id": "test_doc_2014",
        "sample_locator": "entire document",
        "notes": "",
    }
    reading = {
        "poll_reading_id": "test_reading",
        "poll_sample_id": "test_city_2014_01_01_n500",
        "source_document_id": "test_doc_2014",
        "source_locator": "PDF p. 1",
        "contest_type": "mayoral",
        "contest_id": "toronto-mayor-2014",
        "question_order_status": "not_reported",
        "question_text_status": "not_reported",
        "population": "Toronto voters age 18+",
        "turnout_screen": "none",
        "denominator_type": "all_respondents",
        "denominator_text": "[All Respondents]",
        "unweighted_base_status": "not_reported",
        "weighted_base_status": "not_reported",
        "reported_base_status": "reported",
        "reported_base": "500",
        "tested_choice_set_status": "complete",
        "response_coverage": "complete",
        "reported_share_unit": "percent",
        "reported_share_precision": "0",
        "reading_purpose": "general_vote_intention",
        "notes": "",
    }

    def resp(oid, kind, value, share, **extra):
        row = {
            "poll_reading_id": "test_reading",
            "response_option_id": oid,
            "response_kind": kind,
            "option_order": extra.pop("order"),
            "reported_value": value,
            "share": share,
            "notes": "",
        }
        row.update(extra)
        return row

    responses = [
        resp(
            "tory",
            "candidate",
            "50",
            "0.5",
            order="1",
            candidate_id="tory",
            candidate_name="John Tory",
            candidate_observation_status="individually_published",
            response_label="John Tory",
        ),
        resp(
            "chow",
            "candidate",
            "40",
            "0.4",
            order="2",
            candidate_id="chow",
            candidate_name="Olivia Chow",
            candidate_observation_status="individually_published",
            response_label="Olivia Chow",
        ),
        resp(
            "dont-know",
            "dont_know",
            "10",
            "0.1",
            order="3",
            response_label="Don't know",
        ),
    ]
    return {
        "source_documents": [doc],
        "poll_sample_documents": [link],
        "poll_samples": [sample],
        "poll_readings": [reading],
        "poll_responses": responses,
    }


def test_valid_spec_appends_rows_and_passes_audited_validation(tmp_path) -> None:
    bundle = _copy_bundle(tmp_path)
    before = _counts(bundle)

    result = ingest_poll_source(_valid_spec(), bundle_dir=bundle)

    after = _counts(bundle)
    assert after["poll_samples"] == before["poll_samples"] + 1
    assert after["poll_readings"] == before["poll_readings"] + 1
    assert after["poll_responses"] == before["poll_responses"] + 3
    assert after["source_documents"] == before["source_documents"] + 1
    assert after["poll_sample_documents"] == before["poll_sample_documents"] + 1
    # the helper reports the new counts it validated
    assert result["poll_samples"] == after["poll_samples"]


def test_malformed_spec_is_rejected_and_rolls_back(tmp_path) -> None:
    bundle = _copy_bundle(tmp_path)
    before = _counts(bundle)
    spec = _valid_spec()
    # a reported denominator with no denominator_text violates the contract
    spec["poll_readings"][0]["denominator_text"] = ""

    with pytest.raises((IngestError, ValueError)):
        ingest_poll_source(spec, bundle_dir=bundle)

    assert _counts(bundle) == before  # every CSV restored unchanged
