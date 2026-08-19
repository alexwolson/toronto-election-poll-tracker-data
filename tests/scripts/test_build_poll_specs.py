import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_poll_specs import build_multiwave_spec, build_spec, group_by_sample

from backend.model.poll_ingest import ingest_poll_source

TABLES = (
    "source_documents",
    "poll_sample_documents",
    "poll_samples",
    "poll_readings",
    "poll_responses",
)


def _meta(doc_id="test_forum_doc"):
    return {
        "doc_id": doc_id,
        "cycle": "toronto_2014",
        "firm": "Forum Research",
        "publisher_url": "https://example.org/x.pdf",
        "retrieval_url": "https://web.archive.org/web/2014id_/https://example.org/x.pdf",
        "local_path": f"data/source_documents/historical_mayoral/test/{doc_id}.pdf",
        "sha256": "b" * 64,
        "byte_size": 2000,
        "page_count": 3,
    }


def _reading(scenario, responses, base=900, loc="p.4 [All Respondents] Total column"):
    return {
        "scenario_label": scenario,
        "question_text": "If a mayoral election were held today ...?",
        "denominator": "all_respondents",
        "base": base,
        "source_locator": loc,
        "responses": responses,
    }


def _merged(readings, fieldwork="2014-01-05", n=900):
    return {
        "pollster": "Forum Research",
        "fieldwork_start": fieldwork,
        "fieldwork_end": fieldwork,
        "publication_date": "2014-01-06",
        "collection_mode": "ivr",
        "recruited_sample_size": n,
        "readings": readings,
        "trending": [],
    }


FORD_TORY = [
    {"label": "Rob Ford", "kind": "candidate", "value": 40},
    {"label": "John Tory", "kind": "candidate", "value": 50},
    {"label": "Don't know", "kind": "dont_know", "value": 10},
]
FORD_CHOW = [
    {"label": "Rob Ford", "kind": "candidate", "value": 42},
    {"label": "Olivia Chow", "kind": "candidate", "value": 48},
    {"label": "Don't know", "kind": "dont_know", "value": 10},
]


def _copy_bundle(tmp_path: Path) -> Path:
    dest = tmp_path / "bundle"
    dest.mkdir()
    for table in TABLES:
        shutil.copy(
            ROOT / "data/raw/polls/historical_mayoral" / f"{table}.csv",
            dest / f"{table}.csv",
        )
    return dest


def test_single_document_group_produces_an_ingestible_spec(tmp_path) -> None:
    group = [(_meta(), _merged([_reading("Ford / Tory", FORD_TORY)]))]
    spec, problems = build_spec(
        group, "toronto_2014", retrieved_at="2026-08-19T00:00:00Z"
    )
    assert problems == []
    assert set(spec) == set(TABLES)
    assert len(spec["poll_samples"]) == 1
    assert len(spec["source_documents"]) == 1
    counts = ingest_poll_source(spec, bundle_dir=_copy_bundle(tmp_path))
    assert counts["poll_samples"] >= 1


def test_build_spec_strips_candidate_titles_but_keeps_printed_label() -> None:
    # Early Forum head-to-heads label candidates with titles ("Mayor Rob Ford").
    # The canonical id lookup must strip the title; response_label keeps the print.
    titled = [
        {"label": "Mayor Rob Ford", "kind": "candidate", "value": 45},
        {"label": "Councillor Adam Vaughan", "kind": "candidate", "value": 43},
        {"label": "Don't know", "kind": "dont_know", "value": 12},
    ]
    group = [(_meta(), _merged([_reading("Ford / Vaughan", titled)]))]
    spec, problems = build_spec(group, "toronto_2014")
    assert problems == []
    by_label = {r.get("response_label"): r for r in spec["poll_responses"]}
    assert by_label["Mayor Rob Ford"]["candidate_id"] == "rob-ford"
    assert by_label["Councillor Adam Vaughan"]["candidate_id"] == "vaughan"


def test_build_spec_flags_unknown_candidate() -> None:
    responses = [
        {"label": "Some Newcomer", "kind": "candidate", "value": 50},
        {"label": "Rob Ford", "kind": "candidate", "value": 40},
        {"label": "Don't know", "kind": "dont_know", "value": 10},
    ]
    spec, problems = build_spec(
        [(_meta(), _merged([_reading("X", responses)]))], "toronto_2014"
    )
    assert problems and "Some Newcomer" in problems[0]
    assert "Some Newcomer" not in {
        r.get("candidate_name") for r in spec["poll_responses"]
    }


def test_shared_sample_two_docs_distinct_scenarios(tmp_path) -> None:
    # two documents, same fieldwork+n, different ballot scenarios -> one sample, two docs
    a = (_meta("forum_a"), _merged([_reading("Ford / Tory", FORD_TORY)]))
    b = (_meta("forum_b"), _merged([_reading("Ford / Chow", FORD_CHOW)]))
    spec, problems = build_spec([a, b], "toronto_2014")
    assert problems == []
    assert len(spec["poll_samples"]) == 1
    assert len(spec["source_documents"]) == 2
    assert len(spec["poll_sample_documents"]) == 2
    assert len(spec["poll_readings"]) == 2  # one per distinct scenario
    counts = ingest_poll_source(spec, bundle_dir=_copy_bundle(tmp_path))
    assert counts["source_documents"] >= 2


def test_shared_sample_duplicate_scenario_is_deduped() -> None:
    a = (_meta("forum_a"), _merged([_reading("Ford / Tory", FORD_TORY)]))
    b = (
        _meta("forum_b"),
        _merged([_reading("Ford / Tory", FORD_TORY)]),
    )  # same scenario+values
    spec, problems = build_spec([a, b], "toronto_2014")
    assert problems == []
    assert len(spec["source_documents"]) == 2
    assert len(spec["poll_readings"]) == 1  # scenario kept once


def test_shared_sample_value_conflict_flags() -> None:
    conflicting = [
        {
            "label": "Rob Ford",
            "kind": "candidate",
            "value": 44,
        },  # differs from FORD_TORY
        {"label": "John Tory", "kind": "candidate", "value": 46},
        {"label": "Don't know", "kind": "dont_know", "value": 10},
    ]
    a = (_meta("forum_a"), _merged([_reading("Ford / Tory", FORD_TORY)]))
    b = (_meta("forum_b"), _merged([_reading("Ford / Tory", conflicting)]))
    _, problems = build_spec([a, b], "toronto_2014")
    assert problems and "differ" in problems[0].lower()


FORD_SOLO = [
    {"label": "Rob Ford", "kind": "candidate", "value": 55},
    {"label": "Don't know", "kind": "dont_know", "value": 45},
]


def test_build_multiwave_spec_splits_readings_by_base(tmp_path) -> None:
    # one document, readings from two fieldwork waves (base 1093 x2, base 1041 x1)
    readings = [
        _reading("Ford / Tory", FORD_TORY, base=1093),
        _reading("Ford / Chow", FORD_CHOW, base=1093),
        _reading("Ford declared", FORD_SOLO, base=1041),
    ]
    # synthetic in-cycle dates chosen so the derived sample ids do not collide
    # with the real bundle that _copy_bundle clones.
    merged = _merged(readings, fieldwork="2014-01-05", n=1093)
    merged["publication_date"] = "2014-01-07"
    waves = [
        {
            "fieldwork_start": "2014-01-05",
            "fieldwork_end": "2014-01-05",
            "n": 1093,
            "bases": [1093],
        },
        {
            "fieldwork_start": "2014-01-06",
            "fieldwork_end": "2014-01-06",
            "n": 1041,
            "bases": [1041],
        },
    ]
    spec, problems = build_multiwave_spec(
        _meta("forum_oct30"),
        merged,
        waves,
        "toronto_2014",
        retrieved_at="2026-08-19T00:00:00Z",
    )
    assert problems == []
    assert len(spec["source_documents"]) == 1  # one doc backs both samples
    assert len(spec["poll_samples"]) == 2
    assert len(spec["poll_sample_documents"]) == 2  # doc -> two samples (junction)
    assert len(spec["poll_readings"]) == 3
    per_sample = {}
    for r in spec["poll_readings"]:
        per_sample[r["poll_sample_id"]] = per_sample.get(r["poll_sample_id"], 0) + 1
    assert per_sample["forum_city_2014_01_05_n1093"] == 2
    assert per_sample["forum_city_2014_01_06_n1041"] == 1
    # reading ids stay unique across the split
    assert len({r["poll_reading_id"] for r in spec["poll_readings"]}) == 3
    counts = ingest_poll_source(spec, bundle_dir=_copy_bundle(tmp_path))
    assert counts["poll_samples"] >= 2


def test_build_multiwave_spec_flags_base_matching_no_wave() -> None:
    readings = [_reading("X", FORD_TORY, base=999)]
    merged = _merged(readings, fieldwork="2013-10-29", n=1093)
    waves = [
        {
            "fieldwork_start": "2013-10-29",
            "fieldwork_end": "2013-10-29",
            "n": 1093,
            "bases": [1093],
        }
    ]
    _, problems = build_multiwave_spec(_meta(), merged, waves, "toronto_2014")
    assert problems and "999" in problems[0]


def test_group_by_sample_groups_same_fieldwork_and_size() -> None:
    items = [
        (
            _meta("a"),
            _merged(
                [_reading("Ford / Tory", FORD_TORY)], fieldwork="2014-01-05", n=900
            ),
        ),
        (
            _meta("b"),
            _merged(
                [_reading("Ford / Chow", FORD_CHOW)], fieldwork="2014-01-05", n=900
            ),
        ),
        (
            _meta("c"),
            _merged(
                [_reading("Ford / Tory", FORD_TORY)], fieldwork="2014-02-02", n=800
            ),
        ),
    ]
    groups = group_by_sample(items)
    sizes = sorted(len(g) for g in groups)
    assert sizes == [1, 2]
