"""Build the public mayoral poll archive from audited representative readings."""

from __future__ import annotations

import csv
import os
import tempfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from backend.model.poll_sources import (
    PollReading,
    PollResponse,
    PollSample,
    PollSourceBundle,
    load_poll_source_bundle,
)

SELECTION_FILENAME = "descriptive_poll_readings.csv"
SELECTION_COLUMNS = ("poll_sample_id", "poll_reading_id")
METADATA_COLUMNS = (
    "poll_id",
    "firm",
    "date_conducted",
    "date_published",
    "sample_size",
    "methodology",
    "field_tested",
)


class DescriptivePollContractError(ValueError):
    """Raised when the descriptive archive diverges from audited source evidence."""


def _load_selections(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != SELECTION_COLUMNS:
            raise DescriptivePollContractError(
                f"{path.name} must have exact columns {list(SELECTION_COLUMNS)!r}"
            )
        selections: dict[str, str] = {}
        reading_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            sample_id = row["poll_sample_id"].strip()
            reading_id = row["poll_reading_id"].strip()
            if not sample_id or not reading_id:
                raise DescriptivePollContractError(
                    f"{path.name}:{row_number}: selection identifiers cannot be blank"
                )
            if sample_id in selections:
                raise DescriptivePollContractError(
                    f"{path.name}:{row_number}: duplicate sample selection {sample_id!r}"
                )
            if reading_id in reading_ids:
                raise DescriptivePollContractError(
                    f"{path.name}:{row_number}: duplicate reading selection {reading_id!r}"
                )
            selections[sample_id] = reading_id
            reading_ids.add(reading_id)
    return selections


def _eligible_readings(bundle: PollSourceBundle) -> dict[str, list[PollReading]]:
    samples = {
        sample.poll_sample_id
        for sample in bundle.poll_samples
        if sample.election_cycle_id == "toronto-2026"
        and sample.geography_type == "citywide"
        and sample.geography_id == "toronto"
        and sample.extraction_status == "extracted"
    }
    eligible: dict[str, list[PollReading]] = defaultdict(list)
    for reading in bundle.poll_readings:
        if (
            reading.poll_sample_id in samples
            and reading.contest_type == "mayoral"
            and reading.reading_purpose == "general_vote_intention"
        ):
            eligible[reading.poll_sample_id].append(reading)
    return eligible


def _selection_rows(
    bundle: PollSourceBundle, selections: dict[str, str]
) -> list[tuple[PollSample, PollReading, dict[str, Decimal]]]:
    eligible = _eligible_readings(bundle)
    if set(selections) != set(eligible):
        missing = sorted(set(eligible) - set(selections))
        extra = sorted(set(selections) - set(eligible))
        raise DescriptivePollContractError(
            "representative reading selections do not cover the eligible citywide samples: "
            f"missing={missing!r}, extra={extra!r}"
        )
    samples = {sample.poll_sample_id: sample for sample in bundle.poll_samples}
    readings = {reading.poll_reading_id: reading for reading in bundle.poll_readings}
    responses: dict[str, list[PollResponse]] = defaultdict(list)
    for response in bundle.poll_responses:
        responses[response.poll_reading_id].append(response)

    selected = []
    for sample_id, reading_id in selections.items():
        reading = readings.get(reading_id)
        if reading is None or reading.poll_sample_id != sample_id:
            raise DescriptivePollContractError(
                f"representative reading {reading_id!r} does not belong to sample {sample_id!r}"
            )
        if (
            reading not in eligible[sample_id]
            or reading.response_coverage != "complete"
        ):
            raise DescriptivePollContractError(
                f"representative reading {reading_id!r} must be a complete general vote-intention reading"
            )
        shares: dict[str, Decimal] = {}
        for response in responses[reading_id]:
            if response.share is None:
                continue
            key = (
                response.candidate_id
                if response.response_kind == "candidate"
                else response.response_kind
            )
            if not key or key in shares:
                raise DescriptivePollContractError(
                    f"representative reading {reading_id!r} has duplicate public response key {key!r}"
                )
            shares[key] = response.share
        if not shares:
            raise DescriptivePollContractError(
                f"representative reading {reading_id!r} has no published numeric responses"
            )
        selected.append((samples[sample_id], reading, shares))
    return selected


def _public_note(reading: PollReading, shares: dict[str, Decimal]) -> str:
    parts: list[str] = []
    if reading.scenario_label:
        parts.append(reading.scenario_label.rstrip("."))
    if reading.denominator_text:
        denominator = reading.denominator_text.strip().strip("[]").strip()
        if denominator and denominator.casefold() not in {
            part.casefold() for part in parts
        }:
            parts.append(denominator.rstrip("."))
    total = sum(shares.values(), Decimal())
    if total > Decimal(1):
        percent = format((total * 100).normalize(), "f")
        parts.append(f"published shares total {percent}% due to source rounding")
    note = "; ".join(parts)
    return f"{note[:1].upper()}{note[1:]}." if note else ""


def build_descriptive_poll_rows(
    source_dir: str | Path,
) -> tuple[list[str], list[dict[str, str]]]:
    """Create one public row per explicitly selected, audited citywide sample."""

    source = Path(source_dir)
    bundle = load_poll_source_bundle(source)
    selections = _load_selections(source / SELECTION_FILENAME)
    selected = _selection_rows(bundle, selections)
    share_columns = sorted({key for _, _, shares in selected for key in shares})
    columns = [*METADATA_COLUMNS, *share_columns, "notes"]
    rows = []
    for sample, reading, shares in selected:
        row = {column: "" for column in columns}
        row.update(
            {
                "poll_id": sample.poll_sample_id,
                "firm": sample.pollster,
                "date_conducted": sample.fieldwork_end.isoformat(),
                "date_published": sample.publication_date.isoformat(),
                "sample_size": str(sample.recruited_sample_size or ""),
                "methodology": sample.collection_mode,
                "field_tested": ",".join(sorted(shares)),
                "notes": _public_note(reading, shares),
            }
        )
        for key, share in shares.items():
            row[key] = format(share, "f")
        rows.append(row)
    rows.sort(key=lambda row: (row["date_published"], row["poll_id"]), reverse=True)
    return columns, rows


def write_descriptive_polls(source_dir: str | Path, destination: str | Path) -> Path:
    """Atomically regenerate ``polls.csv`` from audited selections."""

    target = Path(destination)
    columns, rows = build_descriptive_poll_rows(source_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", newline="", encoding="utf-8", dir=target.parent, delete=False
        ) as handle:
            temporary_name = handle.name
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_name, target)
    finally:
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()
    return target


def validate_descriptive_polls(source_dir: str | Path, polls_path: str | Path) -> None:
    """Fail with the first field whose public value differs from audited evidence."""

    expected_columns, expected_rows = build_descriptive_poll_rows(source_dir)
    path = Path(polls_path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        actual_columns = list(reader.fieldnames or ())
        actual_rows = list(reader)
    if actual_columns != expected_columns:
        raise DescriptivePollContractError(
            f"descriptive poll columns drifted: expected={expected_columns!r}, actual={actual_columns!r}"
        )
    expected = {row["poll_id"]: row for row in expected_rows}
    actual = {row["poll_id"]: row for row in actual_rows}
    if len(actual) != len(actual_rows) or set(actual) != set(expected):
        raise DescriptivePollContractError(
            "descriptive poll sample inventory drifted: "
            f"missing={sorted(set(expected) - set(actual))!r}, "
            f"extra={sorted(set(actual) - set(expected))!r}"
        )
    for poll_id, expected_row in expected.items():
        actual_row = actual[poll_id]
        for field in expected_columns:
            expected_value = expected_row[field]
            actual_value = actual_row[field].strip()
            if field not in {*METADATA_COLUMNS, "notes"} and actual_value:
                try:
                    matches = Decimal(actual_value) == Decimal(expected_value)
                except InvalidOperation:
                    matches = False
            else:
                matches = actual_value == expected_value
            if not matches:
                raise DescriptivePollContractError(
                    f"descriptive poll drift for {poll_id!r} field {field!r}: "
                    f"expected {expected_value!r}, found {actual_value!r}"
                )
