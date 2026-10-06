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

    assert len(rows) == 29
    assert "abacus-2026-01-27" not in rows
    assert "canadapulse-2025-10-06" not in rows
    assert not any("-v-" in poll_id for poll_id in rows)


def test_public_rows_state_their_denominator() -> None:
    rows = _rows_by_id()
    assert rows["liaison-2026-09-20"]["denominator"] == "Decided and leaning voters"
    assert rows["liaison-2026-09-27"]["denominator"] == "Decided and leaning voters"
    assert rows["liaison-2026-10-04"]["denominator"] == "Decided and leaning voters"
    assert rows["mainstreet-2026-09-14"]["denominator"] == "Decided and leaning voters"
    assert rows["pallas-2026-08-21"]["denominator"] == "Decided and leaning voters"
    assert rows["ipsos-2026-09-08"]["denominator"] == "All respondents"
    assert rows["ipsos-2025-08-29"]["denominator"] == "All respondents"
    assert rows["forum-2026-09-23"]["denominator"] == "Decided and leaning voters"
    # A reading whose denominator was never reported says so, rather than "Other".
    assert rows["liaison-2026-02-02"]["denominator"] == "Not stated"


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


def test_canada_pulse_archive_selects_one_decided_and_leaning_reading() -> None:
    rows = _rows_by_id()
    poll = rows["canadapulse-2026-09-24"]
    assert poll["date_conducted"] == "2026-09-24"
    assert poll["date_published"] == "2026-09-29"
    assert poll["sample_size"] == "510"
    assert poll["denominator"] == "Decided and leaning voters"
    assert {key: poll[key] for key in poll["field_tested"].split(",")} == {
        "alexander": "0.09",
        "bradford": "0.34",
        "chow": "0.51",
        "other": "0.06",
    }
    assert sum(row["poll_id"] == poll["poll_id"] for row in rows.values()) == 1


def test_all_respondent_view_preserves_source_shares_and_counts_samples_once() -> None:
    from polling_data.descriptive_polls import build_all_respondent_poll_rows

    rows = build_all_respondent_poll_rows(SOURCE)
    by_id = {row["poll_id"]: row for row in rows}
    assert len(rows) == len(by_id) == 24
    assert all(row["denominator"] == "All respondents" for row in rows)
    assert (
        len(
            [
                row
                for row in rows
                if row["date_conducted"] > "2026-08-21"
                and all(row.get(key) for key in ("chow", "bradford", "alexander"))
            ]
        )
        == 9
    )
    assert by_id["ipsos-2026-09-08"]["bradford"] == "0.21"
    assert by_id["canadapulse-2026-09-24"]["chow"] == "0.38"
    assert by_id["liaison-2026-09-27"]["chow"] == "0.41"
    assert by_id["liaison-2026-09-27"]["undecided"] == "0.15"
    mainstreet = by_id["mainstreet-2026-09-29"]
    assert mainstreet["poll_reading_id"] == "mainstreet_20260928_29_mayor_all"
    assert {key: mainstreet[key] for key in mainstreet["field_tested"].split(",")} == {
        "bradford": "0.322",
        "chow": "0.381",
        "alexander": "0.072",
        "sarah-mcvie": "0.02",
        "odessa-paloma-parker": "0.018",
        "other": "0.027",
        "undecided": "0.16",
    }
    newest = by_id["liaison-2026-10-04"]
    assert newest["poll_reading_id"] == "liaison_20261003_04_mayor_all"
    assert {key: newest[key] for key in newest["field_tested"].split(",")} == {
        "bradford": "0.33",
        "chow": "0.40",
        "alexander": "0.08",
        "other": "0.03",
        "undecided": "0.16",
    }
    assert (
        by_id["pallas-2026-03-08"]["poll_reading_id"]
        == "pallas_20260308_mayor_ford_all"
    )
    assert by_id["pallas-2026-08-21"]["chow"] == "0.413"
    assert "forum-2026-09-23" not in by_id


@pytest.mark.parametrize(
    "replacement",
    [
        "liaison_20250702_06_mayor_with_tory_decided",
        "liaison_20260904_05_mayor_all",
        None,
    ],
)
def test_all_respondent_selection_rejects_wrong_basis_sample_or_missing_sample(
    tmp_path: Path,
    replacement: str | None,
) -> None:
    from polling_data.descriptive_polls import build_all_respondent_poll_rows

    source = tmp_path / "polls"
    shutil.copytree(SOURCE, source)
    path = source / "all_respondent_poll_readings.csv"
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    if replacement is None:
        rows.pop(0)
    else:
        rows[0]["poll_reading_id"] = replacement
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["poll_sample_id", "poll_reading_id"]
        )
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(DescriptivePollContractError):
        build_all_respondent_poll_rows(source)


def test_nanos_views_preserve_distinct_published_readings() -> None:
    from polling_data.descriptive_polls import build_all_respondent_poll_rows

    archive = _rows_by_id()["nanos-2026-10-04"]
    all_voters = next(
        row
        for row in build_all_respondent_poll_rows(SOURCE)
        if row["poll_id"] == "nanos-2026-10-04"
    )
    assert archive["denominator"] == "Decided and leaning voters"
    assert {key: archive[key] for key in archive["field_tested"].split(",")} == {
        "alexander": "0.04",
        "bradford": "0.426",
        "chow": "0.524",
        "other": "0.01",
    }
    assert all_voters["poll_reading_id"] == "nanos_20260930_1004_mayor_all"
    assert {key: all_voters[key] for key in all_voters["field_tested"].split(",")} == {
        "alexander": "0.027",
        "bradford": "0.327",
        "chow": "0.419",
        "other": "0.008",
        "undecided": "0.218",
    }
    assert archive["sarah-mcvie"] == archive["odessa-paloma-parker"] == ""
    assert all_voters["sarah-mcvie"] == all_voters["odessa-paloma-parker"] == ""
