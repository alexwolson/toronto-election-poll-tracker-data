"""Strict loader for the model-neutral poll source contract.

The contract separates physical source artifacts, respondent samples, poll
readings, and response observations.  In particular, a reading is never an
independent sample: every reading with the same ``poll_sample_id`` is dependent
evidence from the same recruited respondents.

This module intentionally does not decide whether evidence is forecast-eligible.
It only rejects ambiguous, malformed, or relationally incomplete source data.
"""

from __future__ import annotations

import csv
import hashlib
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Final
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo


SOURCE_DOCUMENT_COLUMNS: Final = (
    "source_document_id",
    "document_role",
    "publisher_url",
    "retrieval_url",
    "retrieval_status",
    "retrieved_at",
    "media_type",
    "sha256",
    "local_path",
    "byte_size",
    "page_count",
    "sheet_count",
    "text_layer_status",
    "visual_qa_status",
    "access_class",
    "redistribution_status",
    "reuse_terms_url",
    "notes",
)

POLL_SAMPLE_DOCUMENT_COLUMNS: Final = (
    "poll_sample_id",
    "source_document_id",
    "sample_locator",
    "notes",
)

POLL_SAMPLE_COLUMNS: Final = (
    "poll_sample_id",
    "election_cycle_id",
    "pollster",
    "sponsor",
    "geography_type",
    "geography_id",
    "fieldwork_start",
    "fieldwork_end",
    "publication_date",
    "publication_at",
    "publication_time_precision",
    "evidence_available_at",
    "collection_mode",
    "recruited_sample_size",
    "extraction_status",
    "notes",
)

POLL_READING_COLUMNS: Final = (
    "poll_reading_id",
    "poll_sample_id",
    "source_document_id",
    "source_locator",
    "contest_type",
    "contest_id",
    "question_order_status",
    "question_order",
    "document_display_order",
    "question_text_status",
    "question_text",
    "scenario_label",
    "population",
    "turnout_screen",
    "turnout_screen_text",
    "denominator_type",
    "denominator_text",
    "unweighted_base_status",
    "unweighted_base",
    "weighted_base_status",
    "weighted_base",
    "reported_base_status",
    "reported_base",
    "tested_choice_set_status",
    "response_coverage",
    "reported_share_unit",
    "reported_share_precision",
    "notes",
    "reading_purpose",
)

POLL_RESPONSE_COLUMNS: Final = (
    "poll_reading_id",
    "response_option_id",
    "response_kind",
    "candidate_id",
    "candidate_name",
    "candidate_observation_status",
    "response_label",
    "option_order",
    "reported_value",
    "share",
    "notes",
)

_FILES: Final = {
    "source_documents.csv": SOURCE_DOCUMENT_COLUMNS,
    "poll_sample_documents.csv": POLL_SAMPLE_DOCUMENT_COLUMNS,
    "poll_samples.csv": POLL_SAMPLE_COLUMNS,
    "poll_readings.csv": POLL_READING_COLUMNS,
    "poll_responses.csv": POLL_RESPONSE_COLUMNS,
}

_DOCUMENT_ROLES: Final = frozenset(
    {"release", "article", "questionnaire", "tables", "methodology", "microdata", "other"}
)
_RETRIEVAL_STATUSES: Final = frozenset(
    {"retrieved", "not_retrieved", "access_pending", "dead_link", "corrupt"}
)
_TEXT_LAYER_STATUSES: Final = frozenset(
    {"present", "partial", "absent", "not_applicable"}
)
_VISUAL_QA_STATUSES: Final = frozenset(
    {"pending", "passed", "failed", "not_applicable"}
)
_ACCESS_CLASSES: Final = frozenset(
    {"public", "licensed", "institutional_restricted"}
)
_REDISTRIBUTION_STATUSES: Final = frozenset(
    {"permitted", "prohibited", "unknown"}
)
_GEOGRAPHY_TYPES: Final = frozenset({"citywide", "ward"})
_PUBLICATION_PRECISIONS: Final = frozenset({"exact", "date_only"})
_EXTRACTION_STATUSES: Final = frozenset(
    {"pending", "in_progress", "extracted", "blocked"}
)
_CONTEST_TYPES: Final = frozenset({"mayoral", "council"})
_QUESTION_ORDER_STATUSES: Final = frozenset({"reported", "not_reported"})
_QUESTION_TEXT_STATUSES: Final = frozenset({"reported", "not_reported"})
_TURNOUT_SCREENS: Final = frozenset(
    {
        "none",
        "eligible_voters",
        "registered_voters",
        "likely_voters",
        "past_voters",
        "custom",
        "not_reported",
    }
)
_DENOMINATOR_TYPES: Final = frozenset(
    {
        "all_respondents",
        "decided_respondents",
        "valid_responses",
        "custom",
        "not_reported",
    }
)
_BASE_STATUSES: Final = frozenset({"reported", "not_reported"})
_CHOICE_SET_STATUSES: Final = frozenset({"complete", "partial", "unknown"})
_RESPONSE_COVERAGES: Final = frozenset({"complete", "partial", "unknown"})
_REPORTED_SHARE_UNITS: Final = frozenset({"percent", "proportion"})
_READING_PURPOSES: Final = frozenset(
    {
        "general_vote_intention",
        "conditional_lean_followup",
        "routed_subgroup",
        "context_only",
    }
)
_RESPONSE_KINDS: Final = frozenset(
    {
        "candidate",
        "undecided",
        "other",
        "refusal",
        "dont_know",
        "would_not_vote",
        "none_of_the_above",
        "no_answer",
        "combined_residual",
    }
)
_CANDIDATE_OBSERVATION_STATUSES: Final = frozenset(
    {
        "individually_published",
        "offered_not_individually_published",
        "known_not_offered",
        "tested_ballot_unknown",
    }
)
_ID_RE: Final = re.compile(r"^[a-z0-9][a-z0-9._:-]*$")
_MEDIA_TYPE_RE: Final = re.compile(r"^[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+$")
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_TORONTO: Final = ZoneInfo("America/Toronto")
_SPREADSHEET_MEDIA_TYPES: Final = frozenset(
    {
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
)
_OOXML_ZIP_MEDIA_TYPES: Final = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)


class PollSourceContractError(ValueError):
    """Raised when source data does not satisfy the poll source contract."""


@dataclass(frozen=True, slots=True)
class SourceDocument:
    source_document_id: str
    document_role: str
    publisher_url: str
    retrieval_url: str | None
    retrieval_status: str
    retrieved_at: datetime | None
    media_type: str | None
    sha256: str | None
    local_path: PurePosixPath | None
    byte_size: int | None
    page_count: int | None
    sheet_count: int | None
    text_layer_status: str | None
    visual_qa_status: str
    access_class: str
    redistribution_status: str
    reuse_terms_url: str | None
    notes: str | None


@dataclass(frozen=True, slots=True)
class PollSampleDocument:
    poll_sample_id: str
    source_document_id: str
    sample_locator: str | None
    notes: str | None


@dataclass(frozen=True, slots=True)
class PollSample:
    poll_sample_id: str
    election_cycle_id: str
    pollster: str
    sponsor: str | None
    geography_type: str
    geography_id: str
    fieldwork_start: date
    fieldwork_end: date
    publication_date: date
    publication_at: datetime | None
    publication_time_precision: str
    evidence_available_at: datetime
    collection_mode: str
    recruited_sample_size: int | None
    extraction_status: str
    notes: str | None


@dataclass(frozen=True, slots=True)
class PollReading:
    poll_reading_id: str
    poll_sample_id: str
    source_document_id: str
    source_locator: str
    contest_type: str
    contest_id: str
    question_order_status: str
    question_order: int | None
    document_display_order: int | None
    question_text_status: str
    question_text: str | None
    scenario_label: str | None
    population: str
    turnout_screen: str
    turnout_screen_text: str | None
    denominator_type: str
    denominator_text: str | None
    unweighted_base_status: str
    unweighted_base: int | None
    weighted_base_status: str
    weighted_base: Decimal | None
    reported_base_status: str
    reported_base: Decimal | None
    tested_choice_set_status: str
    response_coverage: str
    reported_share_unit: str
    reported_share_precision: int
    notes: str | None
    reading_purpose: str = "general_vote_intention"


@dataclass(frozen=True, slots=True)
class PollResponse:
    poll_reading_id: str
    response_option_id: str
    response_kind: str
    candidate_id: str | None
    candidate_name: str | None
    candidate_observation_status: str | None
    response_label: str | None
    option_order: int | None
    reported_value: str | None
    share: Decimal | None
    notes: str | None


@dataclass(frozen=True, slots=True)
class PollSourceBundle:
    """A validated, immutable source bundle.

    ``poll_sample_id`` is the unit used to count Distinct Poll Samples.  The
    number of readings must never be substituted for the number of samples.
    """

    source_documents: tuple[SourceDocument, ...]
    poll_sample_documents: tuple[PollSampleDocument, ...]
    poll_samples: tuple[PollSample, ...]
    poll_readings: tuple[PollReading, ...]
    poll_responses: tuple[PollResponse, ...]


def load_poll_source_bundle(
    directory: str | Path, *, require_audited_sources: bool = False
) -> PollSourceBundle:
    """Load and validate the five CSVs in ``directory``.

    Files, headers, scalar values, enums, chronology, foreign keys, response
    semantics, and reading totals are all checked before anything is returned.
    The default manifest mode permits explicitly pending or blocked extraction.
    ``require_audited_sources=True`` additionally requires every sample to be
    fully extracted and every reading's source artifact to be retrieved and to
    have passed visual QA. It does not determine forecast eligibility. The
    function never silently drops or coerces a malformed row.
    """

    root = Path(directory)
    raw_tables = {
        filename: _read_rows(root / filename, columns)
        for filename, columns in _FILES.items()
    }

    documents = tuple(
        _parse_source_document(row, filename="source_documents.csv", row_number=row_number)
        for row_number, row in raw_tables["source_documents.csv"]
    )
    sample_documents = tuple(
        _parse_poll_sample_document(
            row, filename="poll_sample_documents.csv", row_number=row_number
        )
        for row_number, row in raw_tables["poll_sample_documents.csv"]
    )
    samples = tuple(
        _parse_poll_sample(row, filename="poll_samples.csv", row_number=row_number)
        for row_number, row in raw_tables["poll_samples.csv"]
    )
    readings = tuple(
        _parse_poll_reading(row, filename="poll_readings.csv", row_number=row_number)
        for row_number, row in raw_tables["poll_readings.csv"]
    )
    responses = tuple(
        _parse_poll_response(row, filename="poll_responses.csv", row_number=row_number)
        for row_number, row in raw_tables["poll_responses.csv"]
    )

    bundle = PollSourceBundle(documents, sample_documents, samples, readings, responses)
    _validate_relations(bundle, require_audited_sources=require_audited_sources)
    return bundle


def verify_poll_source_artifacts(
    bundle: PollSourceBundle, project_root: str | Path
) -> None:
    """Verify retrieved local artifacts against their tracked manifest metadata.

    Existence, containment below ``data/source_documents``, byte size, SHA-256,
    and practical file signatures are checked. Acquisition gaps are skipped
    because they intentionally have no complete local artifact.
    """

    root = Path(project_root).resolve()
    corpus_root = (root / "data" / "source_documents").resolve()
    for document in bundle.source_documents:
        if document.retrieval_status != "retrieved":
            continue

        if (
            document.local_path is None
            or document.byte_size is None
            or document.sha256 is None
            or document.media_type is None
        ):
            raise PollSourceContractError(
                f"retrieved source document {document.source_document_id!r} has "
                "incomplete artifact metadata"
            )

        artifact = (root / Path(*document.local_path.parts)).resolve()
        if not artifact.is_relative_to(corpus_root):
            raise PollSourceContractError(
                f"source document {document.source_document_id!r} resolves outside "
                "data/source_documents"
            )
        if not artifact.is_file():
            raise PollSourceContractError(
                f"source document {document.source_document_id!r} artifact does not exist"
            )
        if artifact.stat().st_size != document.byte_size:
            raise PollSourceContractError(
                f"source document {document.source_document_id!r} byte_size mismatch"
            )

        digest = hashlib.sha256()
        with artifact.open("rb") as handle:
            prefix = handle.read(4096)
            digest.update(prefix)
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        if digest.hexdigest() != document.sha256:
            raise PollSourceContractError(
                f"source document {document.source_document_id!r} sha256 mismatch"
            )
        _verify_media_signature(document, prefix)
        if document.media_type in _OOXML_ZIP_MEDIA_TYPES:
            _verify_ooxml_archive(document, artifact)


def _verify_media_signature(document: SourceDocument, prefix: bytes) -> None:
    assert document.media_type is not None
    media_type = document.media_type
    signature_matches = True
    if media_type == "application/pdf":
        signature_matches = prefix.startswith(b"%PDF-")
    elif media_type in _OOXML_ZIP_MEDIA_TYPES:
        signature_matches = prefix.startswith(b"PK\x03\x04")
    elif media_type == "application/vnd.ms-excel":
        signature_matches = prefix.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    elif media_type == "text/html":
        lowered = prefix.lstrip(b"\xef\xbb\xbf\x00\t\r\n ").lower()
        signature_matches = lowered.startswith(b"<!doctype html") or b"<html" in lowered

    if not signature_matches:
        raise PollSourceContractError(
            f"source document {document.source_document_id!r} bytes do not match "
            f"media_type {media_type!r}"
        )


def _verify_ooxml_archive(document: SourceDocument, artifact: Path) -> None:
    assert document.media_type is not None
    required_entries = {"[Content_Types].xml"}
    if document.media_type.endswith("wordprocessingml.document"):
        required_entries.add("word/document.xml")
    elif document.media_type.endswith("spreadsheetml.sheet"):
        required_entries.add("xl/workbook.xml")

    try:
        with zipfile.ZipFile(artifact) as archive:
            bad_entry = archive.testzip()
            archive_entries = set(archive.namelist())
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise PollSourceContractError(
            f"source document {document.source_document_id!r} OOXML ZIP "
            f"integrity check failed: {exc}"
        ) from exc

    if bad_entry is not None:
        raise PollSourceContractError(
            f"source document {document.source_document_id!r} OOXML ZIP CRC "
            f"failed for {bad_entry!r}"
        )
    missing = sorted(required_entries - archive_entries)
    if missing:
        raise PollSourceContractError(
            f"source document {document.source_document_id!r} OOXML archive "
            f"is missing required entries {missing!r}"
        )


def _read_rows(
    path: Path, expected_columns: tuple[str, ...]
) -> list[tuple[int, dict[str, str]]]:
    try:
        handle = path.open(encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise PollSourceContractError(f"cannot read required file {path}: {exc}") from exc

    with handle:
        reader = csv.DictReader(handle)
        actual = tuple(reader.fieldnames or ())
        if actual != expected_columns:
            raise PollSourceContractError(
                f"{path.name} header must be exactly {expected_columns!r}; got {actual!r}"
            )

        rows: list[tuple[int, dict[str, str]]] = []
        try:
            for row_number, row in enumerate(reader, start=2):
                if None in row:
                    raise PollSourceContractError(
                        f"{path.name} row {row_number} has more values than columns"
                    )
                if all(value == "" for value in row.values()):
                    raise PollSourceContractError(
                        f"{path.name} row {row_number} is blank"
                    )
                rows.append((row_number, row))
        except csv.Error as exc:
            raise PollSourceContractError(f"invalid CSV in {path}: {exc}") from exc
        return rows


def _parse_source_document(
    row: dict[str, str], *, filename: str, row_number: int
) -> SourceDocument:
    location = _location(filename, row_number)
    retrieval_status = _enum(
        row, "retrieval_status", _RETRIEVAL_STATUSES, location
    )
    access_class = _enum(row, "access_class", _ACCESS_CLASSES, location)
    redistribution_status = _enum(
        row, "redistribution_status", _REDISTRIBUTION_STATUSES, location
    )
    notes = _optional(row, "notes")
    if (
        retrieval_status != "retrieved"
        or access_class != "public"
        or redistribution_status != "permitted"
    ) and not notes:
        raise PollSourceContractError(
            f"{location}: notes are required for gaps, non-public, or "
            "non-redistributable material"
        )

    retrieval_url = _optional_url(row, "retrieval_url", location)
    retrieved_at = _optional_datetime(row, "retrieved_at", location)
    media_type = _optional(row, "media_type")
    if media_type is not None and not _MEDIA_TYPE_RE.fullmatch(media_type):
        raise PollSourceContractError(f"{location}: invalid media_type {media_type!r}")

    digest = _optional(row, "sha256")
    if digest is not None and not _SHA256_RE.fullmatch(digest):
        raise PollSourceContractError(f"{location}: sha256 must be 64 lowercase hex digits")

    local_path_text = _optional(row, "local_path")
    local_path = None
    if local_path_text is not None:
        local_path = PurePosixPath(local_path_text)
        if (
            local_path.is_absolute()
            or ".." in local_path.parts
            or local_path.parts[:2] != ("data", "source_documents")
        ):
            raise PollSourceContractError(
                f"{location}: local_path must be a safe path below data/source_documents"
            )

    byte_size = _optional_positive_int(row, "byte_size", location)
    page_count = _optional_positive_int(row, "page_count", location)
    sheet_count = _optional_positive_int(row, "sheet_count", location)
    text_layer_status = _optional_enum(
        row, "text_layer_status", _TEXT_LAYER_STATUSES, location
    )
    visual_qa_status = _enum(
        row, "visual_qa_status", _VISUAL_QA_STATUSES, location
    )

    if retrieval_status == "retrieved":
        required_artifact_fields = {
            "retrieval_url": retrieval_url,
            "retrieved_at": retrieved_at,
            "media_type": media_type,
            "sha256": digest,
            "local_path": local_path,
            "byte_size": byte_size,
            "text_layer_status": text_layer_status,
        }
        missing = [field for field, value in required_artifact_fields.items() if value is None]
        if missing:
            raise PollSourceContractError(
                f"{location}: retrieved artifact is missing {missing!r}"
            )
        if media_type == "application/pdf":
            if page_count is None or sheet_count is not None:
                raise PollSourceContractError(
                    f"{location}: retrieved PDF requires page_count and blank sheet_count"
                )
            if text_layer_status == "not_applicable":
                raise PollSourceContractError(
                    f"{location}: retrieved PDF requires an inspected text-layer status"
                )
            if visual_qa_status == "not_applicable":
                raise PollSourceContractError(
                    f"{location}: retrieved PDF requires pending, passed, or failed visual QA"
                )
        elif media_type in _SPREADSHEET_MEDIA_TYPES:
            if sheet_count is None or page_count is not None:
                raise PollSourceContractError(
                    f"{location}: retrieved spreadsheet requires sheet_count and blank page_count"
                )
            if text_layer_status != "not_applicable":
                raise PollSourceContractError(
                    f"{location}: spreadsheet text_layer_status must be not_applicable"
                )
    elif retrieval_status == "corrupt" and visual_qa_status not in {
        "failed",
        "not_applicable",
    }:
        raise PollSourceContractError(
            f"{location}: corrupt artifact visual_qa_status must be failed or "
            "not_applicable"
        )
    elif retrieval_status != "corrupt" and visual_qa_status != "not_applicable":
        raise PollSourceContractError(
            f"{location}: unretrieved artifact visual_qa_status must be not_applicable"
        )
    if visual_qa_status == "failed" and not notes:
        raise PollSourceContractError(
            f"{location}: failed visual QA requires notes"
        )

    return SourceDocument(
        source_document_id=_identifier(row, "source_document_id", location),
        document_role=_enum(row, "document_role", _DOCUMENT_ROLES, location),
        publisher_url=_url(row, "publisher_url", location),
        retrieval_url=retrieval_url,
        retrieval_status=retrieval_status,
        retrieved_at=retrieved_at,
        media_type=media_type,
        sha256=digest,
        local_path=local_path,
        byte_size=byte_size,
        page_count=page_count,
        sheet_count=sheet_count,
        text_layer_status=text_layer_status,
        visual_qa_status=visual_qa_status,
        access_class=access_class,
        redistribution_status=redistribution_status,
        reuse_terms_url=_optional_url(row, "reuse_terms_url", location),
        notes=notes,
    )


def _parse_poll_sample_document(
    row: dict[str, str], *, filename: str, row_number: int
) -> PollSampleDocument:
    location = _location(filename, row_number)
    return PollSampleDocument(
        poll_sample_id=_identifier(row, "poll_sample_id", location),
        source_document_id=_identifier(row, "source_document_id", location),
        sample_locator=_optional(row, "sample_locator"),
        notes=_optional(row, "notes"),
    )


def _parse_poll_sample(
    row: dict[str, str], *, filename: str, row_number: int
) -> PollSample:
    location = _location(filename, row_number)
    start = _date(row, "fieldwork_start", location)
    end = _date(row, "fieldwork_end", location)
    publication_date = _date(row, "publication_date", location)
    if start > end:
        raise PollSourceContractError(f"{location}: fieldwork_start follows fieldwork_end")
    if end > publication_date:
        raise PollSourceContractError(
            f"{location}: fieldwork_end follows publication_date"
        )

    precision = _enum(
        row, "publication_time_precision", _PUBLICATION_PRECISIONS, location
    )
    publication_at = _optional_datetime(row, "publication_at", location)
    evidence_at = _datetime(row, "evidence_available_at", location)
    if precision == "exact":
        if publication_at is None:
            raise PollSourceContractError(
                f"{location}: exact publication time requires publication_at"
            )
        if publication_at.astimezone(_TORONTO).date() != publication_date:
            raise PollSourceContractError(
                f"{location}: publication_at does not fall on publication_date in Toronto"
            )
        if evidence_at < publication_at:
            raise PollSourceContractError(
                f"{location}: evidence_available_at precedes publication_at"
            )
    else:
        if publication_at is not None:
            raise PollSourceContractError(
                f"{location}: date_only publication must leave publication_at blank"
            )
        if evidence_at.astimezone(_TORONTO).date() <= publication_date:
            raise PollSourceContractError(
                f"{location}: date_only evidence must be eligible no earlier "
                "than the next Toronto day"
            )

    collection_mode = _required(row, "collection_mode", location)
    if not _ID_RE.fullmatch(collection_mode):
        raise PollSourceContractError(
            f"{location}: collection_mode must be a normalized identifier"
        )

    return PollSample(
        poll_sample_id=_identifier(row, "poll_sample_id", location),
        election_cycle_id=_identifier(row, "election_cycle_id", location),
        pollster=_required(row, "pollster", location),
        sponsor=_optional(row, "sponsor"),
        geography_type=_enum(row, "geography_type", _GEOGRAPHY_TYPES, location),
        geography_id=_identifier(row, "geography_id", location),
        fieldwork_start=start,
        fieldwork_end=end,
        publication_date=publication_date,
        publication_at=publication_at,
        publication_time_precision=precision,
        evidence_available_at=evidence_at,
        collection_mode=collection_mode,
        recruited_sample_size=_optional_positive_int(
            row, "recruited_sample_size", location
        ),
        extraction_status=_enum(
            row, "extraction_status", _EXTRACTION_STATUSES, location
        ),
        notes=_optional(row, "notes"),
    )


def _parse_poll_reading(
    row: dict[str, str], *, filename: str, row_number: int
) -> PollReading:
    location = _location(filename, row_number)
    question_order_status = _enum(
        row, "question_order_status", _QUESTION_ORDER_STATUSES, location
    )
    question_order = _optional_positive_int(row, "question_order", location)
    _validate_reported_value(
        status=question_order_status,
        value=question_order,
        field="question_order",
        location=location,
    )
    question_text_status = _enum(
        row, "question_text_status", _QUESTION_TEXT_STATUSES, location
    )
    question_text = _optional(row, "question_text")
    _validate_reported_value(
        status=question_text_status,
        value=question_text,
        field="question_text",
        location=location,
    )

    turnout_screen = _enum(row, "turnout_screen", _TURNOUT_SCREENS, location)
    turnout_screen_text = _optional(row, "turnout_screen_text")
    if turnout_screen == "custom" and not turnout_screen_text:
        raise PollSourceContractError(
            f"{location}: custom turnout_screen requires turnout_screen_text"
        )

    denominator_type = _enum(
        row, "denominator_type", _DENOMINATOR_TYPES, location
    )
    denominator_text = _optional(row, "denominator_text")
    if denominator_type == "not_reported" and denominator_text:
        raise PollSourceContractError(
            f"{location}: not_reported denominator must leave denominator_text blank"
        )
    if denominator_type != "not_reported" and not denominator_text:
        raise PollSourceContractError(
            f"{location}: reported denominator requires denominator_text"
        )

    unweighted_status = _enum(
        row, "unweighted_base_status", _BASE_STATUSES, location
    )
    unweighted_base = _optional_positive_int(row, "unweighted_base", location)
    _validate_reported_value(
        status=unweighted_status,
        value=unweighted_base,
        field="unweighted_base",
        location=location,
    )

    weighted_status = _enum(row, "weighted_base_status", _BASE_STATUSES, location)
    weighted_base = _optional_positive_decimal(row, "weighted_base", location)
    _validate_reported_value(
        status=weighted_status,
        value=weighted_base,
        field="weighted_base",
        location=location,
    )

    reported_status = _enum(row, "reported_base_status", _BASE_STATUSES, location)
    reported_base = _optional_positive_decimal(row, "reported_base", location)
    _validate_reported_value(
        status=reported_status,
        value=reported_base,
        field="reported_base",
        location=location,
    )

    return PollReading(
        poll_reading_id=_identifier(row, "poll_reading_id", location),
        poll_sample_id=_identifier(row, "poll_sample_id", location),
        source_document_id=_identifier(row, "source_document_id", location),
        source_locator=_required(row, "source_locator", location),
        contest_type=_enum(row, "contest_type", _CONTEST_TYPES, location),
        contest_id=_identifier(row, "contest_id", location),
        question_order_status=question_order_status,
        question_order=question_order,
        document_display_order=_optional_positive_int(
            row, "document_display_order", location
        ),
        question_text_status=question_text_status,
        question_text=question_text,
        scenario_label=_optional(row, "scenario_label"),
        population=_required(row, "population", location),
        turnout_screen=turnout_screen,
        turnout_screen_text=turnout_screen_text,
        denominator_type=denominator_type,
        denominator_text=denominator_text,
        unweighted_base_status=unweighted_status,
        unweighted_base=unweighted_base,
        weighted_base_status=weighted_status,
        weighted_base=weighted_base,
        reported_base_status=reported_status,
        reported_base=reported_base,
        tested_choice_set_status=_enum(
            row, "tested_choice_set_status", _CHOICE_SET_STATUSES, location
        ),
        response_coverage=_enum(
            row, "response_coverage", _RESPONSE_COVERAGES, location
        ),
        reported_share_unit=_enum(
            row, "reported_share_unit", _REPORTED_SHARE_UNITS, location
        ),
        reported_share_precision=_nonnegative_int(
            row, "reported_share_precision", location
        ),
        notes=_optional(row, "notes"),
        reading_purpose=_enum(
            row, "reading_purpose", _READING_PURPOSES, location
        ),
    )


def _parse_poll_response(
    row: dict[str, str], *, filename: str, row_number: int
) -> PollResponse:
    location = _location(filename, row_number)
    response_kind = _enum(row, "response_kind", _RESPONSE_KINDS, location)
    candidate_id = _optional_identifier(row, "candidate_id", location)
    candidate_name = _optional(row, "candidate_name")
    status_text = _optional(row, "candidate_observation_status")
    response_label = _optional(row, "response_label")
    option_order = _optional_positive_int(row, "option_order", location)
    reported_value = _optional(row, "reported_value")
    share = _optional_share(row, "share", location)

    if response_kind == "candidate":
        if not candidate_id or not candidate_name or not status_text:
            raise PollSourceContractError(
                f"{location}: candidate response requires candidate identity "
                "and observation status"
            )
        if status_text not in _CANDIDATE_OBSERVATION_STATUSES:
            raise PollSourceContractError(
                f"{location}: unknown candidate_observation_status {status_text!r}"
            )
        if status_text == "individually_published":
            if share is None or not response_label or reported_value is None:
                raise PollSourceContractError(
                    f"{location}: individually published candidate requires label, "
                    "reported_value, and share"
                )
        elif status_text == "offered_not_individually_published":
            if share is not None or reported_value is not None or not response_label:
                raise PollSourceContractError(
                    f"{location}: offered but unpublished candidate requires a label "
                    "and blank value/share"
                )
        elif (
            share is not None
            or reported_value is not None
            or response_label is not None
            or option_order is not None
        ):
            raise PollSourceContractError(
                f"{location}: unoffered or unknown-ballot candidate cannot have option data"
            )
    else:
        if candidate_id or candidate_name or status_text:
            raise PollSourceContractError(
                f"{location}: non-candidate response cannot contain candidate fields"
            )
        if share is None or reported_value is None or not response_label:
            raise PollSourceContractError(
                f"{location}: published non-candidate response requires label, "
                "reported_value, and share"
            )

    return PollResponse(
        poll_reading_id=_identifier(row, "poll_reading_id", location),
        response_option_id=_identifier(row, "response_option_id", location),
        response_kind=response_kind,
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        candidate_observation_status=status_text,
        response_label=response_label,
        option_order=option_order,
        reported_value=reported_value,
        share=share,
        notes=_optional(row, "notes"),
    )


def _validate_relations(
    bundle: PollSourceBundle, *, require_audited_sources: bool
) -> None:
    documents = _unique_index(
        bundle.source_documents, "source_document_id", "source document"
    )
    samples = _unique_index(bundle.poll_samples, "poll_sample_id", "poll sample")
    readings = _unique_index(bundle.poll_readings, "poll_reading_id", "poll reading")

    document_links: set[tuple[str, str]] = set()
    documents_by_sample: dict[str, int] = {sample_id: 0 for sample_id in samples}
    samples_by_document: dict[str, list[PollSample]] = {
        document_id: [] for document_id in documents
    }
    for link in bundle.poll_sample_documents:
        key = (link.poll_sample_id, link.source_document_id)
        if key in document_links:
            raise PollSourceContractError(
                f"duplicate poll sample/source document link {key!r}"
            )
        document_links.add(key)
        sample = samples.get(link.poll_sample_id)
        if sample is None:
            raise PollSourceContractError(
                f"sample/document link references unknown poll sample "
                f"{link.poll_sample_id!r}"
            )
        if link.source_document_id not in documents:
            raise PollSourceContractError(
                f"sample/document link references unknown source document "
                f"{link.source_document_id!r}"
            )
        documents_by_sample[link.poll_sample_id] += 1
        samples_by_document[link.source_document_id].append(sample)

    for sample_id, count in documents_by_sample.items():
        if count == 0:
            raise PollSourceContractError(
                f"poll sample {sample_id!r} has no source document"
            )
    for document_id, linked_samples in samples_by_document.items():
        if not linked_samples:
            raise PollSourceContractError(
                f"source document {document_id!r} is not linked to a poll sample"
            )

    readings_by_sample: dict[str, int] = {sample_id: 0 for sample_id in samples}
    for reading in bundle.poll_readings:
        if reading.poll_sample_id not in samples:
            raise PollSourceContractError(
                f"poll reading {reading.poll_reading_id!r} references unknown "
                f"poll sample {reading.poll_sample_id!r}"
            )
        document = documents.get(reading.source_document_id)
        if document is None:
            raise PollSourceContractError(
                f"poll reading {reading.poll_reading_id!r} references unknown source "
                f"document {reading.source_document_id!r}"
            )
        if (reading.poll_sample_id, reading.source_document_id) not in document_links:
            raise PollSourceContractError(
                f"poll reading {reading.poll_reading_id!r} uses source document "
                f"{reading.source_document_id!r} without a sample/document link"
            )
        if require_audited_sources and document.retrieval_status != "retrieved":
            raise PollSourceContractError(
                f"audited-source reading {reading.poll_reading_id!r} uses an "
                f"unretrieved source document"
            )
        if require_audited_sources and document.visual_qa_status != "passed":
            raise PollSourceContractError(
                f"audited-source reading {reading.poll_reading_id!r} uses a source "
                f"document whose visual QA has not passed"
            )
        readings_by_sample[reading.poll_sample_id] += 1

        sample = samples[reading.poll_sample_id]
        if (
            reading.unweighted_base is not None
            and sample.recruited_sample_size is not None
            and reading.unweighted_base > sample.recruited_sample_size
        ):
            raise PollSourceContractError(
                f"poll reading {reading.poll_reading_id!r} has an unweighted base larger "
                "than its recruited sample"
            )

    for sample_id, sample in samples.items():
        reading_count = readings_by_sample[sample_id]
        if sample.extraction_status == "pending" and reading_count:
            raise PollSourceContractError(
                f"poll sample {sample_id!r} is pending extraction but has readings"
            )
        if sample.extraction_status == "extracted" and reading_count == 0:
            raise PollSourceContractError(
                f"poll sample {sample_id!r} is extracted but has no poll reading"
            )
        if require_audited_sources and sample.extraction_status != "extracted":
            raise PollSourceContractError(
                f"poll sample {sample_id!r} is not source-audited: "
                f"extraction_status is {sample.extraction_status!r}"
            )

    path_metadata: dict[PurePosixPath, tuple[str, str]] = {}
    for document in bundle.source_documents:
        if document.local_path is not None:
            metadata = (document.sha256 or "", document.media_type or "")
            previous = path_metadata.setdefault(document.local_path, metadata)
            if previous != metadata:
                raise PollSourceContractError(
                    f"local artifact {str(document.local_path)!r} has conflicting "
                    "checksum or media type"
                )

        if document.retrieved_at is not None:
            for sample in samples_by_document[document.source_document_id]:
                if sample.publication_at is not None:
                    retrieved_too_early = document.retrieved_at < sample.publication_at
                else:
                    retrieved_too_early = (
                        document.retrieved_at.astimezone(_TORONTO).date()
                        < sample.publication_date
                    )
                if retrieved_too_early:
                    raise PollSourceContractError(
                        f"source document {document.source_document_id!r} was "
                        f"retrieved before sample {sample.poll_sample_id!r} publication"
                    )

    responses_by_reading: dict[str, list[PollResponse]] = {
        reading_id: [] for reading_id in readings
    }
    seen_response_keys: set[tuple[str, str]] = set()
    candidate_names: dict[str, str] = {}
    for response in bundle.poll_responses:
        if response.poll_reading_id not in readings:
            raise PollSourceContractError(
                f"response {response.response_option_id!r} references unknown poll "
                f"reading {response.poll_reading_id!r}"
            )
        key = (response.poll_reading_id, response.response_option_id)
        if key in seen_response_keys:
            raise PollSourceContractError(
                f"duplicate response_option_id {response.response_option_id!r} in "
                f"poll reading {response.poll_reading_id!r}"
            )
        seen_response_keys.add(key)

        if response.candidate_id is not None:
            candidate_name = response.candidate_name or ""
            previous_name = candidate_names.setdefault(
                response.candidate_id, candidate_name
            )
            if previous_name != candidate_name:
                raise PollSourceContractError(
                    f"candidate_id {response.candidate_id!r} maps to conflicting "
                    f"candidate_name values {previous_name!r} and {candidate_name!r}"
                )

        responses_by_reading[response.poll_reading_id].append(response)

    for reading_id, reading_responses in responses_by_reading.items():
        if not reading_responses:
            raise PollSourceContractError(f"poll reading {reading_id!r} has no responses")
        _validate_reading_responses(readings[reading_id], reading_responses)


def _validate_reading_responses(
    reading: PollReading, responses: list[PollResponse]
) -> None:
    candidates = [response for response in responses if response.response_kind == "candidate"]
    if not candidates:
        raise PollSourceContractError(
            f"poll reading {reading.poll_reading_id!r} has no candidate observations"
        )

    candidate_ids = [response.candidate_id for response in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise PollSourceContractError(
            f"poll reading {reading.poll_reading_id!r} has duplicate candidate observations"
        )

    ordered = [response.option_order for response in responses if response.option_order]
    if len(ordered) != len(set(ordered)):
        raise PollSourceContractError(
            f"poll reading {reading.poll_reading_id!r} has duplicate option_order values"
        )

    if reading.tested_choice_set_status == "complete" and any(
        response.candidate_observation_status == "tested_ballot_unknown"
        for response in candidates
    ):
        raise PollSourceContractError(
            f"poll reading {reading.poll_reading_id!r} claims a complete choice set "
            "but has a tested-ballot-unknown candidate"
        )

    if reading.response_coverage == "complete" and any(
        response.candidate_observation_status
        == "offered_not_individually_published"
        for response in candidates
    ):
        raise PollSourceContractError(
            f"poll reading {reading.poll_reading_id!r} claims complete response coverage "
            "but has an unpublished offered candidate"
        )

    published = [response for response in responses if response.share is not None]
    for response in published:
        if response.reported_value is None:
            raise PollSourceContractError(
                f"poll reading {reading.poll_reading_id!r} response "
                f"{response.response_option_id!r} has a share without reported_value"
            )
        normalized, decimal_places = _normalize_reported_value(
            response.reported_value,
            unit=reading.reported_share_unit,
            reading_id=reading.poll_reading_id,
            response_option_id=response.response_option_id,
        )
        if decimal_places > reading.reported_share_precision:
            raise PollSourceContractError(
                f"poll reading {reading.poll_reading_id!r} response "
                f"{response.response_option_id!r} exceeds reported_share_precision"
            )
        if normalized != response.share:
            raise PollSourceContractError(
                f"poll reading {reading.poll_reading_id!r} response "
                f"{response.response_option_id!r} share does not match reported_value"
            )

    published_sum = sum(
        (response.share for response in published if response.share is not None),
        start=Decimal(0),
    )
    rounding_tolerance = _reported_rounding_tolerance(reading, len(published))
    if published_sum > Decimal(1) + rounding_tolerance:
        raise PollSourceContractError(
            f"poll reading {reading.poll_reading_id!r} published shares exceed one"
        )
    if (
        reading.response_coverage == "complete"
        and abs(published_sum - Decimal(1)) > rounding_tolerance
    ):
        raise PollSourceContractError(
            f"poll reading {reading.poll_reading_id!r} claims complete response coverage "
            "but published shares do not sum to one"
        )


def _normalize_reported_value(
    value: str, *, unit: str, reading_id: str, response_option_id: str
) -> tuple[Decimal, int]:
    numeric_text = value
    if unit == "percent" and value.endswith("%"):
        numeric_text = value[:-1]
    elif unit == "proportion" and value.endswith("%"):
        raise PollSourceContractError(
            f"poll reading {reading_id!r} response {response_option_id!r} uses a "
            "percent sign with proportion units"
        )

    reported = _decimal(
        numeric_text,
        field=f"reported_value for {response_option_id}",
        location=f"poll reading {reading_id}",
    )
    if reported < 0:
        raise PollSourceContractError(
            f"poll reading {reading_id!r} response {response_option_id!r} has a "
            "negative reported value"
        )
    normalized = reported / Decimal(100) if unit == "percent" else reported
    if normalized > 1:
        raise PollSourceContractError(
            f"poll reading {reading_id!r} response {response_option_id!r} has a "
            "reported value above one"
        )
    decimal_places = max(0, -reported.as_tuple().exponent)
    return normalized, decimal_places


def _reported_rounding_tolerance(reading: PollReading, published_count: int) -> Decimal:
    reported_increment = Decimal(10) ** (-reading.reported_share_precision)
    normalized_increment = (
        reported_increment / Decimal(100)
        if reading.reported_share_unit == "percent"
        else reported_increment
    )
    return normalized_increment * published_count / Decimal(2)


def _unique_index(items: tuple[object, ...], field: str, label: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for item in items:
        key = getattr(item, field)
        if key in result:
            raise PollSourceContractError(f"duplicate {label} identifier {key!r}")
        result[key] = item
    return result


def _validate_reported_value(
    *, status: str, value: object | None, field: str, location: str
) -> None:
    if status == "reported" and value is None:
        raise PollSourceContractError(f"{location}: reported {field} requires a value")
    if status == "not_reported" and value is not None:
        raise PollSourceContractError(
            f"{location}: not_reported {field} must leave its value blank"
        )


def _location(filename: str, row_number: int) -> str:
    return f"{filename} row {row_number}"


def _required(row: dict[str, str], field: str, location: str) -> str:
    value = row[field]
    if value == "":
        raise PollSourceContractError(f"{location}: {field} is required")
    return value


def _optional(row: dict[str, str], field: str) -> str | None:
    return row[field] or None


def _identifier(row: dict[str, str], field: str, location: str) -> str:
    value = _required(row, field, location)
    if not _ID_RE.fullmatch(value):
        raise PollSourceContractError(
            f"{location}: {field} must be a normalized identifier"
        )
    return value


def _optional_identifier(
    row: dict[str, str], field: str, location: str
) -> str | None:
    value = _optional(row, field)
    if value is not None and not _ID_RE.fullmatch(value):
        raise PollSourceContractError(
            f"{location}: {field} must be a normalized identifier"
        )
    return value


def _enum(
    row: dict[str, str], field: str, allowed: frozenset[str], location: str
) -> str:
    value = _required(row, field, location)
    if value not in allowed:
        raise PollSourceContractError(
            f"{location}: unknown {field} {value!r}; expected one of {sorted(allowed)!r}"
        )
    return value


def _optional_enum(
    row: dict[str, str], field: str, allowed: frozenset[str], location: str
) -> str | None:
    value = _optional(row, field)
    if value is not None and value not in allowed:
        raise PollSourceContractError(
            f"{location}: unknown {field} {value!r}; expected one of {sorted(allowed)!r}"
        )
    return value


def _date(row: dict[str, str], field: str, location: str) -> date:
    value = _required(row, field, location)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise PollSourceContractError(
            f"{location}: {field} must be YYYY-MM-DD"
        ) from exc
    if parsed.isoformat() != value:
        raise PollSourceContractError(f"{location}: {field} must be YYYY-MM-DD")
    return parsed


def _datetime(row: dict[str, str], field: str, location: str) -> datetime:
    value = _required(row, field, location)
    return _parse_datetime(value, field=field, location=location)


def _optional_datetime(
    row: dict[str, str], field: str, location: str
) -> datetime | None:
    value = _optional(row, field)
    return None if value is None else _parse_datetime(value, field=field, location=location)


def _parse_datetime(value: str, *, field: str, location: str) -> datetime:
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise PollSourceContractError(
            f"{location}: {field} must be an ISO 8601 timestamp with an offset"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PollSourceContractError(
            f"{location}: {field} must include a UTC offset"
        )
    return parsed


def _positive_int(row: dict[str, str], field: str, location: str) -> int:
    value = _required(row, field, location)
    if not re.fullmatch(r"[1-9][0-9]*", value):
        raise PollSourceContractError(f"{location}: {field} must be a positive integer")
    return int(value)


def _nonnegative_int(row: dict[str, str], field: str, location: str) -> int:
    value = _required(row, field, location)
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise PollSourceContractError(
            f"{location}: {field} must be a non-negative integer"
        )
    return int(value)


def _optional_positive_int(
    row: dict[str, str], field: str, location: str
) -> int | None:
    value = _optional(row, field)
    if value is None:
        return None
    if not re.fullmatch(r"[1-9][0-9]*", value):
        raise PollSourceContractError(f"{location}: {field} must be a positive integer")
    return int(value)


def _optional_positive_decimal(
    row: dict[str, str], field: str, location: str
) -> Decimal | None:
    value = _optional(row, field)
    if value is None:
        return None
    parsed = _decimal(value, field=field, location=location)
    if parsed <= 0:
        raise PollSourceContractError(f"{location}: {field} must be positive")
    return parsed


def _optional_share(
    row: dict[str, str], field: str, location: str
) -> Decimal | None:
    value = _optional(row, field)
    if value is None:
        return None
    parsed = _decimal(value, field=field, location=location)
    if not Decimal(0) <= parsed <= Decimal(1):
        raise PollSourceContractError(f"{location}: {field} must be in [0, 1]")
    return parsed


def _decimal(value: str, *, field: str, location: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise PollSourceContractError(f"{location}: {field} must be numeric") from exc
    if not parsed.is_finite():
        raise PollSourceContractError(f"{location}: {field} must be finite")
    return parsed


def _url(row: dict[str, str], field: str, location: str) -> str:
    value = _required(row, field, location)
    _validate_url(value, field=field, location=location)
    return value


def _optional_url(row: dict[str, str], field: str, location: str) -> str | None:
    value = _optional(row, field)
    if value is not None:
        _validate_url(value, field=field, location=location)
    return value


def _validate_url(value: str, *, field: str, location: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PollSourceContractError(
            f"{location}: {field} must be an absolute HTTP(S) URL"
        )
