from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from backend.model.poll_sources import load_poll_source_bundle
from polling_data.descriptive_polls import (
    DescriptivePollContractError,
    build_descriptive_poll_rows,
    validate_descriptive_polls,
    write_descriptive_polls,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "polls"


def _rows_by_id() -> dict[str, dict[str, str]]:
    _, rows = build_descriptive_poll_rows(SOURCE)
    return {row["poll_id"]: row for row in rows}


def test_tracked_archive_matches_audited_representative_readings() -> None:
    validate_descriptive_polls(SOURCE, SOURCE / "polls.csv")
    rows = _rows_by_id()

    assert len(rows) == 20
    assert "abacus-2026-01-27" not in rows
    assert "canadapulse-2025-10-06" not in rows
    assert not any("-v-" in poll_id for poll_id in rows)


def test_generation_reproduces_the_tracked_archive_exactly(tmp_path: Path) -> None:
    generated = write_descriptive_polls(SOURCE, tmp_path / "polls.csv")

    assert generated.read_bytes() == (SOURCE / "polls.csv").read_bytes()


def test_pallas_publication_date_and_topline_come_from_first_party_evidence() -> None:
    pallas = _rows_by_id()["pallas-2026-08-21"]

    assert pallas["date_conducted"] == "2026-08-21"
    assert pallas["date_published"] == "2026-08-25"
    assert pallas["field_tested"] == "alexander,bradford,chow,other"
    assert {key: pallas[key] for key in pallas["field_tested"].split(",")} == {
        "alexander": "0.081",
        "bradford": "0.393",
        "chow": "0.501",
        "other": "0.026",
    }


def test_dependent_alternate_readings_remain_one_public_sample() -> None:
    bundle = load_poll_source_bundle(SOURCE)
    forum_readings = [
        reading
        for reading in bundle.poll_readings
        if reading.poll_sample_id == "forum-2026-07-29"
    ]
    pallas_readings = [
        reading
        for reading in bundle.poll_readings
        if reading.poll_sample_id == "pallas-2026-03-08"
    ]
    rows = _rows_by_id()

    assert len(forum_readings) == 2
    assert len(pallas_readings) == 4
    assert sum(row["poll_id"] == "forum-2026-07-29" for row in rows.values()) == 1
    assert sum(row["poll_id"] == "pallas-2026-03-08" for row in rows.values()) == 1


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("date_published", "2026-08-24"),
        ("chow", "0.49"),
        ("field_tested", "bradford,chow,other"),
    ],
)
def test_validation_rejects_date_share_and_field_drift(
    tmp_path: Path, field: str, replacement: str
) -> None:
    polls = tmp_path / "polls.csv"
    shutil.copy2(SOURCE / "polls.csv", polls)
    with polls.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or ())
        rows = list(reader)
    pallas = next(row for row in rows if row["poll_id"] == "pallas-2026-08-21")
    pallas[field] = replacement
    with polls.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(DescriptivePollContractError, match=field):
        validate_descriptive_polls(SOURCE, polls)
