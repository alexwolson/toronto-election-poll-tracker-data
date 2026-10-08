import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from backend.model.poll_sources import (
    POLL_READING_COLUMNS,
    POLL_RESPONSE_COLUMNS,
    POLL_SAMPLE_COLUMNS,
    POLL_SAMPLE_DOCUMENT_COLUMNS,
    SOURCE_DOCUMENT_COLUMNS,
)
from polling_data.descriptive_polls import write_descriptive_polls
from polling_data.release_bundle import (
    HISTORICAL_TABLES,
    build_polling_release_bundle,
    head_to_head_readings,
    head_to_head_selection,
    publish_polling_release,
)

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "data/raw/polls"
HISTORICAL = ROOT / "data/raw/polls/historical_mayoral"
EXCLUSION_HEADER = "poll_sample_id,decided_on,reasons,explanation,notes\n"


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
    (results / "person_aliases.json").write_text(json.dumps({"aliases": aliases}))
    (results / "mayoral_candidates.json").write_text(
        json.dumps(
            {
                "ballot_certified": True,
                "candidates": [
                    {"person_id": "per_chow"},
                    {"person_id": "per_bradford"},
                    {"person_id": "per_alexander"},
                ],
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
        source / "source_documents.csv",
        SOURCE_DOCUMENT_COLUMNS,
        [
            {
                "source_document_id": "document",
                "document_role": "release",
                "publisher_url": "https://example.test/release",
                "retrieval_url": "",
                "retrieval_status": "not_retrieved",
                "retrieved_at": "",
                "media_type": "",
                "sha256": "",
                "local_path": "",
                "byte_size": "",
                "page_count": "",
                "sheet_count": "",
                "text_layer_status": "",
                "visual_qa_status": "not_applicable",
                "access_class": "public",
                "redistribution_status": "unknown",
                "reuse_terms_url": "",
                "notes": "Synthetic test source is intentionally not retrieved.",
            }
        ],
    )
    _write_csv(
        source / "poll_sample_documents.csv",
        POLL_SAMPLE_DOCUMENT_COLUMNS,
        [
            {
                "poll_sample_id": "poll",
                "source_document_id": "document",
                "sample_locator": "",
                "notes": "",
            }
        ],
    )
    _write_csv(
        source / "poll_samples.csv",
        POLL_SAMPLE_COLUMNS,
        [
            {
                "poll_sample_id": "poll",
                "election_cycle_id": "toronto-2026",
                "pollster": "Pollster",
                "sponsor": "",
                "geography_type": "citywide",
                "geography_id": "toronto",
                "fieldwork_start": "2026-08-20",
                "fieldwork_end": "2026-08-20",
                "publication_date": "2026-08-21",
                "publication_at": "",
                "publication_time_precision": "date_only",
                "evidence_available_at": "2026-08-22T00:00:00-04:00",
                "collection_mode": "online",
                "recruited_sample_size": "500",
                "extraction_status": "extracted",
                "notes": "",
            }
        ],
    )
    _write_csv(
        source / "poll_readings.csv",
        POLL_READING_COLUMNS,
        [
            {
                "poll_reading_id": "reading",
                "poll_sample_id": "poll",
                "source_document_id": "document",
                "source_locator": "table 1",
                "contest_type": "mayoral",
                "contest_id": "toronto-mayor-2026",
                "question_order_status": "not_reported",
                "question_order": "",
                "document_display_order": "",
                "question_text_status": "reported",
                "question_text": "Who would you vote for?",
                "scenario_label": "",
                "population": "Toronto adults",
                "turnout_screen": "none",
                "turnout_screen_text": "",
                "denominator_type": "all_respondents",
                "denominator_text": "All respondents",
                "denominator_semantics": "all_respondents",
                "unweighted_base_status": "reported",
                "unweighted_base": "500",
                "weighted_base_status": "not_reported",
                "weighted_base": "",
                "reported_base_status": "not_reported",
                "reported_base": "",
                "tested_choice_set_status": "complete",
                "response_coverage": "complete",
                "reported_share_unit": "proportion",
                "reported_share_precision": "2",
                "notes": "",
                "reading_purpose": "general_vote_intention",
            }
        ],
    )
    normalized_responses = []
    for index, response in enumerate(responses, start=1):
        normalized_responses.append(
            {
                **response,
                "response_option_id": f"candidate-{index}",
                "candidate_observation_status": "individually_published",
                "response_label": response["candidate_name"],
                "option_order": str(index),
                "reported_value": "0.5",
                "notes": "",
            }
        )
    normalized_responses.append(
        {
            "poll_reading_id": "reading",
            "response_option_id": "other",
            "response_kind": "other",
            "candidate_id": "",
            "candidate_name": "",
            "candidate_observation_status": "",
            "response_label": "Other",
            "option_order": "2",
            "reported_value": "0.5",
            "share": "0.5",
            "notes": "",
        }
    )
    _write_csv(
        source / "poll_responses.csv",
        POLL_RESPONSE_COLUMNS,
        normalized_responses,
    )
    _write_csv(
        source / "descriptive_poll_readings.csv",
        ["poll_sample_id", "poll_reading_id"],
        [{"poll_sample_id": "poll", "poll_reading_id": "reading"}],
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
            "denominator",
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
                "denominator": "All respondents",
                "field_tested": field_tested,
                "chow": "0.5",
                "other": "0.5",
                "notes": "All respondents.",
            }
        ],
    )

    shutil.copy2(
        source / "descriptive_poll_readings.csv",
        source / "all_respondent_poll_readings.csv",
    )
    _write_csv(
        source / "reading_classification.csv",
        ["poll_reading_id", "scope", "measurement_class"],
        [
            {
                "poll_reading_id": "reading",
                "scope": "citywide_mayoral",
                "measurement_class": "campaign_vote_intention",
            }
        ],
    )
    (source / "model_exclusions.csv").write_text(EXCLUSION_HEADER)
    # The audited historical corpus and its classification ride in every release.
    shutil.copytree(HISTORICAL, source / "historical_mayoral")
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


def _publication_bundle(tmp_path, head):
    project = tmp_path / "project"
    bundle = project / "dist"
    bundle.mkdir(parents=True)
    asset = bundle / "mayoral_polling.json"
    asset.write_text('{"schema_version":2}\n')
    manifest = {
        "schema_version": 1,
        "repository": "alexwolson/toronto-election-poll-tracker-data",
        "source_commit": head,
        "source_dirty": False,
        "dependencies": {
            "results": {
                "repository": "alexwolson/toronto-election-results",
                "release": "results-2026-09-09.2",
                "source_commit": "b" * 40,
                "manifest_sha256": "c" * 64,
            }
        },
        "assets": [
            {
                "filename": asset.name,
                "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
            }
        ],
    }
    (bundle / "release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return project, bundle


def _publication_runner(
    bundle,
    head,
    *,
    remote_head=None,
    tag_exists=False,
    release_exists=False,
    mutate_download=None,
):
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        if command == ["git", "status", "--porcelain"]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(
                command, 0, stdout=f"{head}\n", stderr=""
            )
        if command == ["git", "ls-remote", "origin", "refs/heads/main"]:
            resolved = remote_head or head
            return subprocess.CompletedProcess(
                command, 0, stdout=f"{resolved}\trefs/heads/main\n", stderr=""
            )
        if command[:4] == ["git", "ls-remote", "--tags", "origin"]:
            output = f"{'d' * 40}\t{command[-1]}\n" if tag_exists else ""
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")
        if command[:3] == ["gh", "release", "view"]:
            if release_exists:
                return subprocess.CompletedProcess(
                    command, 0, stdout='{"tagName":"existing"}\n', stderr=""
                )
            return subprocess.CompletedProcess(
                command, 1, stdout="", stderr="release not found\n"
            )
        if command[:3] == ["gh", "release", "create"]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command[:3] == ["gh", "release", "download"]:
            destination = Path(command[command.index("--dir") + 1])
            shutil.copytree(bundle, destination, dirs_exist_ok=True)
            if mutate_download:
                mutate_download(destination)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    return calls, runner


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
    assert len(polling["all_respondents"]) == 1
    assert polling["all_respondents"][0]["poll_reading_id"] == "reading"
    assert polling["all_respondents"][0]["shares"] == polling["polls"][0]["shares"]
    assert polling["latest"]["shares"] == {"per_chow": 0.5, "response:other": 0.5}
    assert polling["latest"]["field_tested"] == ["per_chow", "response:other"]
    assert set(polling["latest"]["field_tested"]) == set(polling["latest"]["shares"])

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
                _candidate_response("Unresolved Person", "unknown", "reading-unknown")
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
        match="descriptive poll drift.*field_tested.*chow,other",
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


def test_publish_rejects_malformed_tag_before_running_commands(tmp_path):
    def unexpected_runner(command, **kwargs):
        raise AssertionError(f"should not run {command} with {kwargs}")

    with pytest.raises(ValueError, match="polling-YYYY-MM-DD.N"):
        publish_polling_release(
            "polling-latest", tmp_path / "dist", root=tmp_path, runner=unexpected_runner
        )


def test_publish_targets_remote_main_and_verifies_download(tmp_path, capsys):
    head = "a" * 40
    project, bundle = _publication_bundle(tmp_path, head)
    calls, runner = _publication_runner(bundle, head)

    publish_polling_release("polling-2026-09-10.1", bundle, root=project, runner=runner)

    create = next(
        command for command in calls if command[:3] == ["gh", "release", "create"]
    )
    assert create[create.index("--target") + 1] == head
    assert any(command[:3] == ["gh", "release", "download"] for command in calls)
    assert "published and verified polling release" in capsys.readouterr().out


@pytest.mark.parametrize("existing_kind", ["tag", "release"])
def test_publish_rejects_an_existing_tag_or_release(tmp_path, existing_kind):
    head = "a" * 40
    project, bundle = _publication_bundle(tmp_path, head)
    calls, runner = _publication_runner(
        bundle,
        head,
        tag_exists=existing_kind == "tag",
        release_exists=existing_kind == "release",
    )

    with pytest.raises(RuntimeError, match="already exists"):
        publish_polling_release(
            "polling-2026-09-10.1", bundle, root=project, runner=runner
        )

    assert not any(command[:3] == ["gh", "release", "create"] for command in calls)


def test_publish_rejects_a_source_commit_other_than_remote_main(tmp_path):
    head = "a" * 40
    project, bundle = _publication_bundle(tmp_path, head)
    calls, runner = _publication_runner(bundle, head, remote_head="d" * 40)

    with pytest.raises(RuntimeError, match="not the current remote main commit"):
        publish_polling_release(
            "polling-2026-09-10.1", bundle, root=project, runner=runner
        )

    assert not any(command[:3] == ["gh", "release", "create"] for command in calls)


def test_publish_reports_a_corrupt_download_as_a_consumed_tag(tmp_path):
    head = "a" * 40
    project, bundle = _publication_bundle(tmp_path, head)

    def corrupt_asset(destination):
        (destination / "mayoral_polling.json").write_text("corrupt\n")

    _, runner = _publication_runner(bundle, head, mutate_download=corrupt_asset)

    with pytest.raises(
        RuntimeError,
        match="checksum mismatch.*never reuse this tag",
    ):
        publish_polling_release(
            "polling-2026-09-10.1", bundle, root=project, runner=runner
        )


def test_publish_verifies_the_downloaded_results_pin(tmp_path):
    head = "a" * 40
    project, bundle = _publication_bundle(tmp_path, head)

    def change_results_pin(destination):
        path = destination / "release_manifest.json"
        manifest = json.loads(path.read_text())
        manifest["dependencies"]["results"]["release"] = "results-2026-09-10.9"
        path.write_text(json.dumps(manifest))

    _, runner = _publication_runner(bundle, head, mutate_download=change_results_pin)

    with pytest.raises(
        RuntimeError,
        match="Results pin changed after upload.*never reuse this tag",
    ):
        publish_polling_release(
            "polling-2026-09-10.1", bundle, root=project, runner=runner
        )


def test_polling_release_carries_the_historical_corpus_verbatim(tmp_path):
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

    manifest = json.loads((output / "release_manifest.json").read_text())
    assets = {record["filename"] for record in manifest["assets"]}
    assert set(HISTORICAL_TABLES) == {
        "source_documents",
        "poll_sample_documents",
        "poll_samples",
        "poll_readings",
        "poll_responses",
        "reading_classification",
    }
    for table in HISTORICAL_TABLES:
        released = f"historical_mayoral_{table}.csv"
        assert (output / released).read_bytes() == (
            HISTORICAL / f"{table}.csv"
        ).read_bytes()
        assert manifest["tables"][f"historical_mayoral_{table}"] == released
        assert released in assets


def test_historical_classification_covers_exactly_the_corpus_readings() -> None:
    with (HISTORICAL / "poll_readings.csv").open(newline="") as handle:
        readings = [row["poll_reading_id"] for row in csv.DictReader(handle)]
    with (HISTORICAL / "reading_classification.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == ["poll_reading_id", "scope", "measurement_class"]
    assert sorted(row["poll_reading_id"] for row in rows) == sorted(readings)
    assert {row["measurement_class"] for row in rows} >= {
        "campaign_vote_intention",
        "alternative_ballot",
    }


@pytest.mark.parametrize("change", ["missing", "extra"])
def test_polling_release_rejects_a_classification_that_does_not_match_the_corpus(
    tmp_path, change
):
    source, results = _release_inputs(
        tmp_path, aliases=[], responses=[_candidate_response()]
    )
    path = source / "historical_mayoral" / "reading_classification.csv"
    lines = path.read_text().splitlines(keepends=True)
    if change == "missing":
        path.write_text("".join(lines[:-1]))
    else:
        path.write_text(
            "".join(lines) + "no_such_reading,citywide_mayoral,alternative_ballot\n"
        )
    with pytest.raises(ValueError, match="classification"):
        build_polling_release_bundle(
            source,
            results,
            tmp_path / "dist",
            results_release="results-v1",
            source_commit="pollsha",
            dirty=False,
            generated_at="2026-08-26T12:00:00Z",
        )


# --- 2026 reading classification and Head-to-Head Readings ---------------------


def _rebuild(source, results, tmp_path):
    return build_polling_release_bundle(
        source,
        results,
        tmp_path / "dist",
        results_release="results-v1",
        source_commit="pollsha",
        dirty=False,
        generated_at="2026-08-26T12:00:00Z",
    )


def _current_mayoral_reading_ids():
    with (CURRENT / "poll_samples.csv").open(newline="") as handle:
        samples = {
            row["poll_sample_id"]
            for row in csv.DictReader(handle)
            if row["election_cycle_id"] == "toronto-2026"
            and row["geography_type"] == "citywide"
        }
    with (CURRENT / "poll_readings.csv").open(newline="") as handle:
        return [
            row["poll_reading_id"]
            for row in csv.DictReader(handle)
            if row["poll_sample_id"] in samples and row["contest_type"] == "mayoral"
        ]


def test_current_classification_covers_exactly_the_2026_mayoral_readings() -> None:
    with (CURRENT / "reading_classification.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == ["poll_reading_id", "scope", "measurement_class"]
    assert sorted(row["poll_reading_id"] for row in rows) == sorted(
        _current_mayoral_reading_ids()
    )
    assert {row["scope"] for row in rows} == {"citywide_mayoral"}
    classes = {row["poll_reading_id"]: row["measurement_class"] for row in rows}
    for reading in (
        "mainstreet_20260928_29_mayor_head_to_head_all",
        "mainstreet_20260618_mayor_forced_two_way",
        "forum_20250904_mayor_chow_tory",
        "forum_20250904_mayor_chow_bradford",
        "forum_20250904_mayor_chow_bailao",
    ):
        assert classes[reading] == "alternative_ballot"
    assert classes["forum_20261006_mayor"] == "campaign_vote_intention"


@pytest.mark.parametrize("change", ["missing", "duplicate", "unknown", "bad_class"])
def test_polling_release_rejects_a_current_classification_that_does_not_cover_the_readings(
    tmp_path, change
):
    source, results = _release_inputs(
        tmp_path, aliases=[], responses=[_candidate_response()]
    )
    path = source / "reading_classification.csv"
    header, row = path.read_text().splitlines(keepends=True)
    if change == "missing":
        path.write_text(header)
    elif change == "duplicate":
        path.write_text(header + row + row)
    elif change == "unknown":
        path.write_text(
            header + row + "no_such_reading,citywide_mayoral,alternative_ballot\n"
        )
    else:
        path.write_text(header + "reading,citywide_mayoral,two_way\n")
    with pytest.raises(ValueError, match="2026 reading classification"):
        _rebuild(source, results, tmp_path)


def test_polling_release_ships_the_current_classification_beside_the_historical(
    tmp_path,
):
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
    source = tmp_path / "polls"
    assert (output / "reading_classification.csv").read_bytes() == (
        source / "reading_classification.csv"
    ).read_bytes()
    manifest = json.loads((output / "release_manifest.json").read_text())
    assert manifest["tables"]["reading_classification"] == "reading_classification.csv"
    assert "reading_classification.csv" in {
        record["filename"] for record in manifest["assets"]
    }


def test_polling_release_requires_a_certified_final_ballot(tmp_path):
    source, results = _release_inputs(
        tmp_path, aliases=[], responses=[_candidate_response()]
    )
    path = results / "mayoral_candidates.json"
    path.write_text(
        json.dumps({**json.loads(path.read_text()), "ballot_certified": False})
    )
    with pytest.raises(ValueError, match="certified Final Ballot"):
        _rebuild(source, results, tmp_path)


def _response(reading, kind, person_id=""):
    return {"poll_reading_id": reading, "response_kind": kind, "person_id": person_id}


FINAL_BALLOT = frozenset({"per_chow", "per_bradford", "per_alexander"})


@pytest.mark.parametrize(
    ("measurement_class", "people", "residuals", "qualifies"),
    [
        ("alternative_ballot", ["per_chow", "per_bradford"], ["undecided"], True),
        ("alternative_ballot", ["per_chow", "per_bradford"], [], True),
        # Not an alternative ballot: an ordinary campaign question.
        ("campaign_vote_intention", ["per_chow", "per_bradford"], [], False),
        # Three named candidates, or only one.
        (
            "alternative_ballot",
            ["per_chow", "per_bradford", "per_alexander"],
            [],
            False,
        ),
        ("alternative_ballot", ["per_chow"], ["undecided"], False),
        # One of the two is not on the Final Ballot (Chow-Tory).
        ("alternative_ballot", ["per_chow", "per_tory"], ["undecided"], False),
        # Two names plus "someone else" is not a Head-to-Head Reading.
        ("alternative_ballot", ["per_chow", "per_bradford"], ["other"], False),
    ],
)
def test_head_to_head_reading_rule(measurement_class, people, residuals, qualifies):
    responses = [_response("r", "candidate", person) for person in people] + [
        _response("r", kind) for kind in residuals
    ]
    found = head_to_head_readings({"r": measurement_class}, responses, FINAL_BALLOT)
    assert found == ({"r"} if qualifies else set())


def test_head_to_head_selection_flags_a_representative_reading_on_its_poll():
    array, flagged = head_to_head_selection(
        {"rep_h2h", "alt_h2h"},
        reading_samples={"rep_h2h": "poll-a", "alt_h2h": "poll-b"},
        representative={"poll-a": "rep_h2h", "poll-b": "full_field"},
    )
    assert array == ["alt_h2h"]
    assert flagged == {"poll-a"}


def test_head_to_head_selection_allows_at_most_one_reading_per_poll():
    with pytest.raises(ValueError, match="at most one Head-to-Head Reading per poll"):
        head_to_head_selection(
            {"first", "second"},
            reading_samples={"first": "poll", "second": "poll"},
            representative={"poll": "full_field"},
        )


def _real_results_bundle(tmp_path):
    """A Results bundle resolving every real 2026 poll name and contest.

    Person IDs are synthetic (``per_<source id>``). The Final Ballot holds the poll
    candidates certified in results-2026-09-30.2: Chow, Bradford, Alexander, McVie
    and Parker; Tory, Bailão, Furey, Mendicino and Michael Ford are not on it.
    """
    results = tmp_path / "results"
    results.mkdir()
    (results / "release_manifest.json").write_text(
        json.dumps(
            {"repository": "alexwolson/toronto-election-results", "source_commit": "r"}
        )
    )
    with (CURRENT / "poll_responses.csv").open(newline="") as handle:
        names = {
            row["candidate_name"]: row["candidate_id"]
            for row in csv.DictReader(handle)
            if row["response_kind"] == "candidate"
        }
    aliases = [
        {"normalized_name": name, "person_id": f"per_{slug}", "is_unambiguous": True}
        for name, slug in names.items()
    ]
    (results / "person_aliases.json").write_text(json.dumps({"aliases": aliases}))
    final_ballot = [
        "chow",
        "bradford",
        "alexander",
        "sarah-mcvie",
        "odessa-paloma-parker",
    ]
    (results / "mayoral_candidates.json").write_text(
        json.dumps(
            {
                "ballot_certified": True,
                "candidates": [{"person_id": f"per_{slug}"} for slug in final_ballot],
            }
        )
    )
    with (CURRENT / "poll_readings.csv").open(newline="") as handle:
        contests = {row["contest_id"] for row in csv.DictReader(handle)}
    rows = []
    for contest in sorted(contests):
        office, district = (
            ("mayor", "city")
            if contest == "toronto-mayor-2026"
            else ("councillor", f"ward-{contest.split('-')[2]}")
        )
        rows.append(
            {
                "election_year": "2026",
                "represented_body": "toronto_city_council",
                "result_status": "pending",
                "office_type": office,
                "official_district_id": district,
                "contest_id": f"con_{contest}",
            }
        )
    _write_csv(results / "election_results.csv", list(rows[0]), rows)
    return results


def test_real_polling_feed_derives_the_three_head_to_head_readings(tmp_path):
    output = _rebuild(CURRENT, _real_results_bundle(tmp_path), tmp_path)
    polling = json.loads((output / "mayoral_polling.json").read_text())

    assert polling["schema_version"] == 2
    entries = {entry["poll_reading_id"]: entry for entry in polling["head_to_head"]}
    assert sorted(entries) == [
        "forum_20250904_mayor_chow_bradford",
        "mainstreet_20260618_mayor_forced_two_way",
        "mainstreet_20260928_29_mayor_head_to_head_all",
    ]
    assert entries["mainstreet_20260928_29_mayor_head_to_head_all"]["shares"] == {
        "per_chow": 0.471,
        "per_bradford": 0.409,
        "response:undecided": 0.12,
    }
    assert entries["forum_20250904_mayor_chow_bradford"]["shares"] == {
        "per_chow": 0.4,
        "per_bradford": 0.42,
        "response:undecided": 0.18,
    }
    assert entries["mainstreet_20260618_mayor_forced_two_way"]["shares"] == {
        "per_chow": 0.481,
        "per_bradford": 0.519,
    }
    assert entries["mainstreet_20260928_29_mayor_head_to_head_all"]["denominator"] == (
        "All respondents"
    )

    polls = {poll["poll_id"]: poll for poll in polling["polls"]}
    for entry in entries.values():
        assert entry["head_to_head"] is True
        assert set(entry["field_tested"]) == set(entry["shares"])
        assert set(entry["shares"]) <= set(polling["candidates"])
        parent = polls[entry["poll_id"]]
        for field in (
            "firm",
            "date_conducted",
            "date_published",
            "sample_size",
            "methodology",
        ):
            assert entry[field] == parent[field]
    # No representative reading is a Head-to-Head Reading today.
    assert not any("head_to_head" in poll for poll in polling["polls"])
    # trend and latest ignore the array: one Chow point per poll record, from it.
    assert polling["latest"] == polling["polls"][0]
    assert sorted(
        (point["poll_id"], point["share"]) for point in polling["trend"]["per_chow"]
    ) == sorted(
        (poll["poll_id"], poll["shares"]["per_chow"])
        for poll in polling["polls"]
        if "per_chow" in poll["shares"]
    )


def _rewrite_responses(source, rows):
    _write_csv(
        source / "poll_responses.csv",
        POLL_RESPONSE_COLUMNS,
        [
            {
                "poll_reading_id": "reading",
                "response_option_id": f"option-{index}",
                "response_kind": kind,
                "candidate_id": slug,
                "candidate_name": name,
                "candidate_observation_status": "individually_published"
                if slug
                else "",
                "response_label": name or kind.title(),
                "option_order": str(index),
                "reported_value": share,
                "share": share,
                "notes": "",
            }
            for index, (kind, slug, name, share) in enumerate(rows, start=1)
        ],
    )


def test_a_representative_head_to_head_reading_flags_its_poll_record(tmp_path):
    aliases = [
        {
            "normalized_name": "olivia chow",
            "person_id": "per_chow",
            "is_unambiguous": True,
        },
        {
            "normalized_name": "brad bradford",
            "person_id": "per_bradford",
            "is_unambiguous": True,
        },
    ]
    source, results = _release_inputs(
        tmp_path, aliases=aliases, responses=[_candidate_response()]
    )
    # A post-exit poll that asks only Chow or Bradford.
    _rewrite_responses(
        source,
        [
            ("candidate", "chow", "Olivia Chow", "0.5"),
            ("candidate", "bradford", "Brad Bradford", "0.4"),
            ("undecided", "", "", "0.1"),
        ],
    )
    write_descriptive_polls(source, source / "polls.csv")
    (source / "reading_classification.csv").write_text(
        "poll_reading_id,scope,measurement_class\n"
        "reading,citywide_mayoral,alternative_ballot\n"
    )

    polling = json.loads(
        (_rebuild(source, results, tmp_path) / "mayoral_polling.json").read_text()
    )

    assert polling["schema_version"] == 2
    assert polling["polls"][0]["head_to_head"] is True
    assert polling["latest"]["head_to_head"] is True
    # The representative reading is the poll itself, not an extra entry.
    assert polling["head_to_head"] == []
    assert polling["trend"]["per_chow"] == [
        {"date_conducted": "2026-08-20", "poll_id": "poll", "share": 0.5}
    ]


def test_an_ordinary_poll_record_carries_no_head_to_head_flag(tmp_path):
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
    polling = json.loads((output / "mayoral_polling.json").read_text())
    assert "head_to_head" not in polling["polls"][0]
    assert polling["head_to_head"] == []


def _add_head_to_head_reading(source, residual_kind):
    """A dependent Chow-or-Bradford reading beside the fixture's full-field one."""
    with (source / "poll_readings.csv").open(newline="") as handle:
        base = next(csv.DictReader(handle))
    with (source / "poll_readings.csv").open("a", newline="") as handle:
        csv.DictWriter(handle, fieldnames=POLL_READING_COLUMNS).writerow(
            {
                **base,
                "poll_reading_id": "h2h",
                "scenario_label": "Chow and Bradford only",
            }
        )
    rows = [
        ("candidate", "chow", "Olivia Chow", "0.5"),
        ("candidate", "bradford", "Brad Bradford", "0.4"),
        (residual_kind, "", "", "0.1"),
    ]
    with (source / "poll_responses.csv").open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=POLL_RESPONSE_COLUMNS)
        for index, (kind, slug, name, share) in enumerate(rows, start=1):
            writer.writerow(
                {
                    "poll_reading_id": "h2h",
                    "response_option_id": f"h2h-{index}",
                    "response_kind": kind,
                    "candidate_id": slug,
                    "candidate_name": name,
                    "candidate_observation_status": "individually_published"
                    if slug
                    else "",
                    "response_label": name or kind.title(),
                    "option_order": str(index),
                    "reported_value": share,
                    "share": share,
                    "notes": "",
                }
            )
    with (source / "reading_classification.csv").open("a") as handle:
        handle.write("h2h,citywide_mayoral,alternative_ballot\n")


@pytest.mark.parametrize("residual_kind", ["undecided", "refusal"])
def test_a_head_to_head_entry_allows_only_undecided_beside_the_two_candidates(
    tmp_path, residual_kind
):
    aliases = [
        {
            "normalized_name": "olivia chow",
            "person_id": "per_chow",
            "is_unambiguous": True,
        },
        {
            "normalized_name": "brad bradford",
            "person_id": "per_bradford",
            "is_unambiguous": True,
        },
    ]
    source, results = _release_inputs(
        tmp_path, aliases=aliases, responses=[_candidate_response()]
    )
    _add_head_to_head_reading(source, residual_kind)

    if residual_kind == "undecided":
        polling = json.loads(
            (_rebuild(source, results, tmp_path) / "mayoral_polling.json").read_text()
        )
        assert [entry["poll_reading_id"] for entry in polling["head_to_head"]] == [
            "h2h"
        ]
        return
    with pytest.raises(ValueError, match="'h2h'.*'response:refusal'"):
        _rebuild(source, results, tmp_path)


def _alias_chow():
    return [
        {
            "normalized_name": "olivia chow",
            "person_id": "per_chow",
            "is_unambiguous": True,
        }
    ]


def _exclude(source, row):
    (source / "model_exclusions.csv").write_text(EXCLUSION_HEADER + row + "\n")


EXCLUDE_POLL = (
    "poll,2026-10-08,methodology_confidence;insufficient_track_record,"
    "Listed for the record only.,"
)


def test_an_excluded_poll_carries_its_exclusion_in_the_feed(tmp_path):
    source, results = _release_inputs(
        tmp_path, aliases=_alias_chow(), responses=[_candidate_response()]
    )
    _exclude(source, EXCLUDE_POLL)
    output = _rebuild(source, results, tmp_path)
    polling = json.loads((output / "mayoral_polling.json").read_text())

    expected = {
        "decided_on": "2026-10-08",
        "reasons": ["methodology_confidence", "insufficient_track_record"],
        "explanation": "Listed for the record only.",
    }
    assert polling["polls"][0]["model_exclusion"] == expected
    assert polling["all_respondents"][0]["model_exclusion"] == expected
    manifest = json.loads((output / "release_manifest.json").read_text())
    assert manifest["tables"]["model_exclusions"] == "model_exclusions.csv"
    assert manifest["table_versions"]["model_exclusions"] == 1
    assert (output / "model_exclusions.csv").read_bytes() == (
        source / "model_exclusions.csv"
    ).read_bytes()


def test_a_poll_without_an_exclusion_carries_no_exclusion_field(tmp_path):
    output = _build(tmp_path, aliases=_alias_chow(), responses=[_candidate_response()])
    polling = json.loads((output / "mayoral_polling.json").read_text())
    assert "model_exclusion" not in polling["polls"][0]
    assert "model_exclusion" not in polling["all_respondents"][0]


@pytest.mark.parametrize(
    "row",
    [
        "no_such_sample,2026-10-08,methodology_confidence,Why.,",
        "poll,2026-10-08,house_dislike,Why.,",
        "poll,2026-10-08,,Why.,",
        "poll,2026-10-08,methodology_confidence,,",
        "poll,08/10/2026,methodology_confidence,Why.,",
        (
            "poll,2026-10-08,methodology_confidence,Why.,\n"
            "poll,2026-10-08,not_cric_member,Again.,"
        ),
    ],
    ids=[
        "unknown_sample",
        "unknown_reason",
        "no_reason",
        "no_explanation",
        "bad_date",
        "duplicate",
    ],
)
def test_polling_release_rejects_an_invalid_model_exclusion(tmp_path, row):
    source, results = _release_inputs(
        tmp_path, aliases=_alias_chow(), responses=[_candidate_response()]
    )
    _exclude(source, row)
    with pytest.raises(ValueError, match="model exclusion"):
        _rebuild(source, results, tmp_path)


def test_polling_release_requires_the_model_exclusions_table(tmp_path):
    source, results = _release_inputs(
        tmp_path, aliases=_alias_chow(), responses=[_candidate_response()]
    )
    (source / "model_exclusions.csv").unlink()
    with pytest.raises(FileNotFoundError, match="model exclusions"):
        _rebuild(source, results, tmp_path)


def test_scope_is_the_only_excluded_poll_and_says_why() -> None:
    with (CURRENT / "model_exclusions.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["poll_sample_id"] for row in rows] == ["scope-2026-10-06"]
    (scope,) = rows
    assert scope["decided_on"] == "2026-10-08"
    assert scope["reasons"].split(";") == [
        "methodology_confidence",
        "insufficient_track_record",
        "not_cric_member",
    ]
    assert "Canadian Research Insights Council" in scope["explanation"]


def test_real_polling_feed_marks_only_scope_as_excluded(tmp_path):
    output = _rebuild(CURRENT, _real_results_bundle(tmp_path), tmp_path)
    polling = json.loads((output / "mayoral_polling.json").read_text())
    for view in ("polls", "all_respondents"):
        excluded = [p["poll_id"] for p in polling[view] if "model_exclusion" in p]
        assert excluded == ["scope-2026-10-06"]
