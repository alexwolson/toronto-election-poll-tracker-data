from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from polling_data.deposit import INCLUDED, DepositError, build_polling_deposit

READINGS = [
    "poll_reading_id",
    "poll_sample_id",
    "source_document_id",
    "source_locator",
    "question_text_status",
    "question_text",
    "reported_share_precision",
]
RESPONSES = ["poll_reading_id", "response_label", "reported_value", "share"]
DOCUMENTS = [
    "source_document_id",
    "document_role",
    "publisher_url",
    "retrieval_url",
    "retrieval_status",
    "media_type",
    "local_path",
    "text_layer_status",
    "visual_qa_status",
    "access_class",
    "redistribution_status",
    "notes",
]
RULE = [
    "corpus",
    "poll_sample_id",
    "kept_reading_id",
    "source_document_id",
    "source_locator",
    "free_values",
    "basis",
]
FREE = [
    "source_document_id",
    "poll_sample_ids",
    "document_role",
    "publisher_url",
    "retrieval_url",
    "media_type",
    "notes",
]


def _write(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _reading(reading_id, sample, doc, text="Who would you vote for?", precision="1"):
    return {
        "poll_reading_id": reading_id,
        "poll_sample_id": sample,
        "source_document_id": doc,
        "source_locator": "page 3",
        "question_text_status": "reported",
        "question_text": text,
        "reported_share_precision": precision,
    }


def _doc(doc_id):
    row = {column: "" for column in DOCUMENTS}
    row.update(
        source_document_id=doc_id, local_path=f"data/source_documents/{doc_id}.pdf"
    )
    return row


@pytest.fixture
def release(tmp_path: Path) -> Path:
    root = tmp_path / "release"
    root.mkdir()
    current = {
        "poll_samples.csv": (
            ["poll_sample_id"],
            [{"poll_sample_id": "ms-1"}, {"poll_sample_id": "other-1"}],
        ),
        "poll_readings.csv": (
            READINGS,
            [
                _reading("ms-1-all", "ms-1", "ms-1-full"),
                _reading("ms-1-decided", "ms-1", "ms-1-full"),
                _reading("other-1-decided", "other-1", "other-1-doc"),
            ],
        ),
        "poll_responses.csv": (
            RESPONSES,
            [
                {
                    "poll_reading_id": "ms-1-all",
                    "response_label": "Chow",
                    "reported_value": "38.1%",
                    "share": "0.381",
                },
                {
                    "poll_reading_id": "ms-1-decided",
                    "response_label": "Chow",
                    "reported_value": "43.1%",
                    "share": "0.431",
                },
                {
                    "poll_reading_id": "ms-1-decided",
                    "response_label": "Undecided",
                    "reported_value": "",
                    "share": "",
                },
                {
                    "poll_reading_id": "other-1-decided",
                    "response_label": "Chow",
                    "reported_value": "50%",
                    "share": "0.50",
                },
            ],
        ),
        "poll_sample_documents.csv": (
            ["poll_sample_id", "source_document_id", "sample_locator", "notes"],
            [
                {
                    "poll_sample_id": "ms-1",
                    "source_document_id": "ms-1-full",
                    "sample_locator": "entire document",
                    "notes": "",
                }
            ],
        ),
        "source_documents.csv": (DOCUMENTS, [_doc("ms-1-full"), _doc("other-1-doc")]),
        "reading_classification.csv": (
            ["poll_reading_id", "scope"],
            [
                {"poll_reading_id": "ms-1-all", "scope": "citywide_mayoral"},
                {"poll_reading_id": "ms-1-decided", "scope": "citywide_mayoral"},
            ],
        ),
        "descriptive_poll_readings.csv": (
            ["poll_sample_id", "poll_reading_id"],
            [{"poll_sample_id": "ms-1", "poll_reading_id": "ms-1-all"}],
        ),
        "all_respondent_poll_readings.csv": (
            ["poll_sample_id", "poll_reading_id"],
            [{"poll_sample_id": "ms-1", "poll_reading_id": "ms-1-all"}],
        ),
        "model_exclusions.csv": (["poll_sample_id"], []),
        "ward_poll_readings.csv": (
            ["ward", "poll_id"],
            [{"ward": "4", "poll_id": "ms-w4"}],
        ),
    }
    historical = {
        "historical_mayoral_poll_samples.csv": (
            ["poll_sample_id"],
            [{"poll_sample_id": "h-1"}],
        ),
        "historical_mayoral_poll_readings.csv": (
            READINGS,
            [
                _reading("h-1-r1", "h-1", "h-1-report"),
                _reading("h-1-r2", "h-1", "h-1-report"),
            ],
        ),
        "historical_mayoral_poll_responses.csv": (
            RESPONSES,
            [
                {
                    "poll_reading_id": "h-1-r1",
                    "response_label": "Chow",
                    "reported_value": "30%",
                    "share": "0.30",
                },
                {
                    "poll_reading_id": "h-1-r2",
                    "response_label": "Chow",
                    "reported_value": "35%",
                    "share": "0.35",
                },
            ],
        ),
        "historical_mayoral_poll_sample_documents.csv": (
            ["poll_sample_id", "source_document_id", "sample_locator", "notes"],
            [],
        ),
        "historical_mayoral_source_documents.csv": (DOCUMENTS, [_doc("h-1-report")]),
        "historical_mayoral_reading_classification.csv": (
            ["poll_reading_id", "scope"],
            [
                {"poll_reading_id": "h-1-r1", "scope": "citywide_mayoral"},
                {"poll_reading_id": "h-1-r2", "scope": "citywide_mayoral"},
            ],
        ),
        "historical_mayoral_outcomes.csv": (["election_id", "candidate_id"], []),
    }
    tables = {**current, **historical}
    assert set(tables) == set(INCLUDED)
    for name, (columns, rows) in tables.items():
        _write(root / name, columns, rows)
    _write(root / "polls.csv", ["poll_id"], [{"poll_id": "ms-1"}])
    _write_manifest(root)
    return root


def _write_manifest(root: Path) -> None:
    assets = [
        {"filename": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(root.iterdir())
        if p.name != "release_manifest.json"
    ]
    (root / "release_manifest.json").write_text(
        json.dumps({"assets": assets, "source_commit": "abc", "repository": "repo"})
    )


@pytest.fixture
def rule(tmp_path: Path) -> tuple[Path, Path]:
    rule_path = tmp_path / "rule.csv"
    _write(
        rule_path,
        RULE,
        [
            {
                "corpus": "current",
                "poll_sample_id": "ms-1",
                "kept_reading_id": "ms-1-decided",
                "source_document_id": "ms-1-post",
                "source_locator": "post text",
                "free_values": "Chow=43%",
                "basis": "Free post gives whole percents.",
            },
            {
                "corpus": "historical",
                "poll_sample_id": "h-1",
                "kept_reading_id": "h-1-r2",
                "source_document_id": "",
                "source_locator": "",
                "free_values": "",
                "basis": "Report was free at release.",
            },
        ],
    )
    free_path = tmp_path / "free.csv"
    _write(
        free_path,
        FREE,
        [
            {
                "source_document_id": "ms-1-post",
                "poll_sample_ids": "ms-1",
                "document_role": "release",
                "publisher_url": "https://example.com/post",
                "retrieval_url": "https://example.com/post",
                "media_type": "text/html",
                "notes": "Free post.",
            },
        ],
    )
    return rule_path, free_path


def _build(release: Path, rule: tuple[Path, Path], out: Path) -> dict:
    return build_polling_deposit(
        release,
        out,
        release_tag="polling-test.1",
        rule_path=rule[0],
        free_sources_path=rule[1],
        generated_at="2026-10-28T00:00:00+00:00",
    )


def test_withholds_every_reading_but_the_kept_topline(release, rule, tmp_path):
    out = tmp_path / "deposit"
    manifest = _build(release, rule, out)

    readings = {r["poll_reading_id"]: r for r in _read(out / "poll_readings.csv")}
    assert set(readings) == {"ms-1-decided", "other-1-decided"}
    assert {r["poll_reading_id"] for r in _read(out / "poll_responses.csv")} == {
        "ms-1-decided",
        "other-1-decided",
    }
    assert [
        r["poll_reading_id"] for r in _read(out / "reading_classification.csv")
    ] == ["ms-1-decided"]
    assert _read(out / "all_respondent_poll_readings.csv") == []
    assert [
        r["poll_reading_id"]
        for r in _read(out / "historical_mayoral_poll_readings.csv")
    ] == ["h-1-r2"]
    withheld = _read(out / "withheld_readings.csv")
    assert {r["poll_reading_id"] for r in withheld} == {"ms-1-all", "h-1-r1"}
    assert manifest["counts"] == {
        "samples_under_rule": 2,
        "readings_kept_under_rule": 2,
        "readings_withheld": 2,
    }
    assert manifest["excluded_release_assets"][0] == "approval_ratings.csv"
    assert not (out / "polls.csv").exists()


def test_kept_reading_loses_question_text_and_cites_the_free_source(
    release, rule, tmp_path
):
    out = tmp_path / "deposit"
    _build(release, rule, out)

    kept = next(
        r
        for r in _read(out / "poll_readings.csv")
        if r["poll_reading_id"] == "ms-1-decided"
    )
    assert kept["question_text"] == ""
    assert kept["question_text_status"] == "withheld"
    assert kept["source_document_id"] == "ms-1-post"
    assert kept["source_locator"] == "post text"
    assert kept["reported_share_precision"] == "0"
    untouched = next(
        r
        for r in _read(out / "poll_readings.csv")
        if r["poll_reading_id"] == "other-1-decided"
    )
    assert untouched["question_text"] == "Who would you vote for?"

    documents = {
        r["source_document_id"]: r for r in _read(out / "source_documents.csv")
    }
    assert documents["ms-1-post"]["publisher_url"] == "https://example.com/post"
    assert all(r["local_path"] == "" for r in documents.values())
    links = {
        (r["poll_sample_id"], r["source_document_id"])
        for r in _read(out / "poll_sample_documents.csv")
    }
    assert ("ms-1", "ms-1-post") in links


def test_free_values_replace_the_recorded_precision(release, rule, tmp_path):
    out = tmp_path / "deposit"
    _build(release, rule, out)

    responses = [
        r
        for r in _read(out / "poll_responses.csv")
        if r["poll_reading_id"] == "ms-1-decided"
    ]
    chow = next(r for r in responses if r["response_label"] == "Chow")
    assert (chow["reported_value"], chow["share"]) == ("43%", "0.43")
    undecided = next(r for r in responses if r["response_label"] == "Undecided")
    assert undecided["reported_value"] == ""


def test_withheld_representative_reading_is_replaced_by_the_kept_one(
    release, rule, tmp_path
):
    out = tmp_path / "deposit"
    _build(release, rule, out)
    assert _read(out / "descriptive_poll_readings.csv") == [
        {"poll_sample_id": "ms-1", "poll_reading_id": "ms-1-decided"}
    ]


def test_manifest_hashes_every_deposited_file(release, rule, tmp_path):
    out = tmp_path / "deposit"
    manifest = _build(release, rule, out)
    for asset in manifest["assets"]:
        assert (
            hashlib.sha256((out / asset["filename"]).read_bytes()).hexdigest()
            == asset["sha256"]
        )
    assert {a["filename"] for a in manifest["assets"]} >= {
        "toplines_rule.csv",
        "free_sources.csv",
        "withheld_readings.csv",
    }


def test_refuses_a_kept_reading_from_another_sample(release, rule, tmp_path):
    rows = _read(rule[0])
    rows[0]["kept_reading_id"] = "other-1-decided"
    _write(rule[0], RULE, rows)
    with pytest.raises(DepositError, match="kept readings not in the sample"):
        _build(release, rule, tmp_path / "deposit")


def test_refuses_free_values_that_match_no_response(release, rule, tmp_path):
    rows = _read(rule[0])
    rows[0]["free_values"] = "Chow=43%;Tory=34%"
    _write(rule[0], RULE, rows)
    with pytest.raises(DepositError, match="free values match no response"):
        _build(release, rule, tmp_path / "deposit")


def test_refuses_a_release_asset_with_no_deposit_decision(release, rule, tmp_path):
    _write(release / "new_table.csv", ["x"], [{"x": "1"}])
    _write_manifest(release)
    with pytest.raises(DepositError, match="no deposit decision"):
        _build(release, rule, tmp_path / "deposit")


def test_refuses_a_release_that_does_not_match_its_manifest(release, rule, tmp_path):
    (release / "poll_samples.csv").write_text("poll_sample_id\nms-1\n")
    with pytest.raises(DepositError, match="does not match the release manifest"):
        _build(release, rule, tmp_path / "deposit")


def test_tracked_rule_keeps_one_reading_per_listed_sample_and_race():
    from polling_data.deposit import DEFAULT_RULE, load_rule

    rule = load_rule(DEFAULT_RULE)
    assert len(rule) == 24
    assert len({(r.corpus, r.poll_sample_id) for r in rule}) == 24
    assert all(r.basis for r in rule)
