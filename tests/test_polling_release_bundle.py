import csv
import hashlib
import json

import pytest

from polling_data.release_bundle import build_polling_release_bundle


def _write_csv(path, columns, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _release_inputs(tmp_path, *, aliases, responses, field_tested="chow,other"):
    results = tmp_path / "results"
    results.mkdir()
    (results / "release_manifest.json").write_text(
        json.dumps(
            {
                "repository": "alexwolson/toronto-election-results",
                "source_commit": "resultsha",
            }
        )
    )
    (results / "person_aliases.json").write_text(
        json.dumps(
            {
                "aliases": aliases
            }
        )
    )
    _write_csv(
        results / "election_results.csv",
        [
            "election_year",
            "represented_body",
            "result_status",
            "office_type",
            "official_district_id",
            "contest_id",
        ],
        [
            {
                "election_year": "2026",
                "represented_body": "toronto_city_council",
                "result_status": "pending",
                "office_type": "mayor",
                "official_district_id": "city",
                "contest_id": "con_mayor",
            }
        ],
    )
    source = tmp_path / "polls"
    source.mkdir()
    _write_csv(
        source / "poll_readings.csv",
        ["poll_reading_id", "contest_id"],
        [{"poll_reading_id": "reading", "contest_id": "toronto-mayor-2026"}],
    )
    _write_csv(
        source / "poll_responses.csv",
        ["poll_reading_id", "response_kind", "candidate_id", "candidate_name", "share"],
        responses,
    )
    _write_csv(
        source / "polls.csv",
        [
            "poll_id",
            "firm",
            "date_conducted",
            "date_published",
            "sample_size",
            "methodology",
            "field_tested",
            "chow",
            "other",
            "notes",
        ],
        [
            {
                "poll_id": "poll",
                "firm": "Pollster",
                "date_conducted": "2026-08-20",
                "date_published": "2026-08-21",
                "sample_size": "500",
                "methodology": "online",
                "field_tested": field_tested,
                "chow": "0.5",
                "other": "0.5",
                "notes": "",
            }
        ],
    )

    return source, results


def _build(tmp_path, *, aliases, responses, field_tested="chow,other"):
    source, results = _release_inputs(
        tmp_path,
        aliases=aliases,
        responses=responses,
        field_tested=field_tested,
    )
    return build_polling_release_bundle(
        source,
        results,
        tmp_path / "dist",
        results_release="results-v1",
        source_commit="pollsha",
        dirty=False,
        generated_at="2026-08-26T12:00:00Z",
    )


def _candidate_response(name="Olivia Chow", candidate_id="chow", reading="reading"):
    return {
        "poll_reading_id": reading,
        "response_kind": "candidate",
        "candidate_id": candidate_id,
        "candidate_name": name,
        "share": "0.5",
    }


def test_polling_release_uses_results_keys_and_pins_results(tmp_path):
    output = _build(
        tmp_path,
        aliases=[
            {
                "normalized_name": "olivia chow",
                "person_id": "per_chow",
                "is_unambiguous": True,
            }
        ],
        responses=[_candidate_response()],
    )

    with (output / "poll_readings.csv").open(newline="") as handle:
        reading = next(csv.DictReader(handle))
    assert reading["contest_id"] == "con_mayor"
    assert reading["source_contest_id"] == "toronto-mayor-2026"
    with (output / "poll_responses.csv").open(newline="") as handle:
        responses = list(csv.DictReader(handle))
    assert responses[0]["person_id"] == "per_chow"
    assert responses[0]["source_candidate_id"] == "chow"
    assert "candidate_id" not in responses[0]
    polling = json.loads((output / "mayoral_polling.json").read_text())
    assert polling["schema_version"] == 2
    assert polling["latest"]["shares"] == {"per_chow": 0.5, "response:other": 0.5}
    assert polling["latest"]["field_tested"] == ["per_chow", "response:other"]
    assert set(polling["latest"]["field_tested"]) == set(
        polling["latest"]["shares"]
    )

    manifest = json.loads((output / "release_manifest.json").read_text())
    dependency = manifest["dependencies"]["results"]
    assert dependency["release"] == "results-v1"
    assert dependency["source_commit"] == "resultsha"
    assert (
        dependency["manifest_sha256"]
        == hashlib.sha256(
            (tmp_path / "results" / "release_manifest.json").read_bytes()
        ).hexdigest()
    )


def test_polling_release_rejects_absent_candidate_identity(tmp_path):
    with pytest.raises(
        ValueError,
        match=(
            "absent.*poll_reading_id='reading-unknown'.*"
            "source_candidate_id='unknown'.*candidate_name='Unresolved Person'"
        ),
    ):
        _build(
            tmp_path,
            aliases=[],
            responses=[
                _candidate_response(
                    "Unresolved Person", "unknown", "reading-unknown"
                )
            ],
        )


def test_polling_release_reports_every_unresolved_candidate_identity(tmp_path):
    with pytest.raises(ValueError) as error:
        _build(
            tmp_path,
            aliases=[],
            responses=[
                _candidate_response("First Missing", "first", "reading-one"),
                _candidate_response("Second Missing", "second", "reading-two"),
            ],
        )

    message = str(error.value)
    assert "poll_reading_id='reading-one'" in message
    assert "source_candidate_id='first'" in message
    assert "candidate_name='First Missing'" in message
    assert "poll_reading_id='reading-two'" in message
    assert "source_candidate_id='second'" in message
    assert "candidate_name='Second Missing'" in message


def test_polling_release_rejects_ambiguous_candidate_identity(tmp_path):
    with pytest.raises(
        ValueError,
        match=(
            "ambiguous.*poll_reading_id='reading-ambiguous'.*"
            "source_candidate_id='ambiguous'.*candidate_name='Ambiguous Person'"
        ),
    ):
        _build(
            tmp_path,
            aliases=[
                {
                    "normalized_name": "ambiguous person",
                    "person_id": None,
                    "is_unambiguous": False,
                }
            ],
            responses=[
                _candidate_response(
                    "Ambiguous Person", "ambiguous", "reading-ambiguous"
                )
            ],
        )


def test_polling_release_rejects_field_tested_share_mismatch(tmp_path):
    with pytest.raises(
        ValueError,
        match="poll field_tested/share key mismatch.*response:other",
    ):
        _build(
            tmp_path,
            aliases=[
                {
                    "normalized_name": "olivia chow",
                    "person_id": "per_chow",
                    "is_unambiguous": True,
                }
            ],
            responses=[_candidate_response()],
            field_tested="chow",
        )
