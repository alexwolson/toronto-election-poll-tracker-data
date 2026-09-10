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
from polling_data.release_bundle import (
    build_polling_release_bundle,
    publish_polling_release,
)


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
                "notes": "All respondents.",
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
