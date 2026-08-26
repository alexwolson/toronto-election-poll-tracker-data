import csv
import hashlib
import json

from polling_data.release_bundle import build_polling_release_bundle


def _write_csv(path, columns, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_polling_release_uses_results_keys_and_pins_results(tmp_path):
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
                "aliases": [
                    {
                        "normalized_name": "olivia chow",
                        "person_id": "per_chow",
                        "is_unambiguous": True,
                    }
                ]
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
        [
            {
                "poll_reading_id": "reading",
                "response_kind": "candidate",
                "candidate_id": "chow",
                "candidate_name": "Olivia Chow",
                "share": "0.5",
            },
            {
                "poll_reading_id": "reading",
                "response_kind": "candidate",
                "candidate_id": "unknown",
                "candidate_name": "Unresolved Person",
                "share": "0.1",
            },
        ],
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
                "field_tested": "chow",
                "chow": "0.5",
                "other": "0.5",
                "notes": "",
            }
        ],
    )

    output = build_polling_release_bundle(
        source,
        results,
        tmp_path / "dist",
        results_release="results-v1",
        source_commit="pollsha",
        dirty=False,
        generated_at="2026-08-26T12:00:00Z",
    )

    with (output / "poll_readings.csv").open(newline="") as handle:
        reading = next(csv.DictReader(handle))
    assert reading["contest_id"] == "con_mayor"
    assert reading["source_contest_id"] == "toronto-mayor-2026"
    with (output / "poll_responses.csv").open(newline="") as handle:
        responses = list(csv.DictReader(handle))
    assert responses[0]["person_id"] == "per_chow"
    assert responses[0]["source_candidate_id"] == "chow"
    assert responses[1]["person_id"] == ""
    assert "candidate_id" not in responses[0]
    polling = json.loads((output / "mayoral_polling.json").read_text())
    assert polling["schema_version"] == 2
    assert polling["latest"]["shares"] == {"per_chow": 0.5, "response:other": 0.5}
    assert polling["latest"]["field_tested"] == ["per_chow"]

    manifest = json.loads((output / "release_manifest.json").read_text())
    dependency = manifest["dependencies"]["results"]
    assert dependency["release"] == "results-v1"
    assert dependency["source_commit"] == "resultsha"
    assert (
        dependency["manifest_sha256"]
        == hashlib.sha256((results / "release_manifest.json").read_bytes()).hexdigest()
    )
