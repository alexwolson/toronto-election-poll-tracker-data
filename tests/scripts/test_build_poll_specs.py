import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_poll_specs import build_spec

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
        "local_path": "data/source_documents/historical_mayoral/test/x.pdf",
        "sha256": "b" * 64,
        "byte_size": 2000,
        "page_count": 3,
    }


def _merged(candidate_label="John Tory"):
    return {
        "pollster": "Forum Research",
        "fieldwork_start": "2014-01-05",
        "fieldwork_end": "2014-01-05",
        "publication_date": "2014-01-06",
        "collection_mode": "ivr",
        "recruited_sample_size": 900,
        "readings": [
            {
                "scenario_label": "Ford / Tory",
                "question_text": "If a mayoral election were held today ...?",
                "denominator": "all_respondents",
                "base": 900,
                "source_locator": "p.4 [All Respondents] Total column",
                "responses": [
                    {"label": "Rob Ford", "kind": "candidate", "value": 40},
                    {"label": candidate_label, "kind": "candidate", "value": 50},
                    {"label": "Don't know", "kind": "dont_know", "value": 10},
                ],
            }
        ],
        "trending": [],
    }


def _copy_bundle(tmp_path: Path) -> Path:
    dest = tmp_path / "bundle"
    dest.mkdir()
    for table in TABLES:
        shutil.copy(
            ROOT / "data/raw/polls/historical_mayoral" / f"{table}.csv",
            dest / f"{table}.csv",
        )
    return dest


def test_build_spec_produces_an_ingestible_spec(tmp_path) -> None:
    spec, problems = build_spec(
        _meta(), _merged(), "toronto_2014", retrieved_at="2026-08-18T00:00:00Z"
    )
    assert problems == []
    assert set(spec) == set(TABLES)
    ids = {
        r["candidate_id"]
        for r in spec["poll_responses"]
        if r["response_kind"] == "candidate"
    }
    assert ids == {"rob-ford", "tory"}
    # the spec passes the audited contract when ingested into a copy of the bundle
    bundle = _copy_bundle(tmp_path)
    counts = ingest_poll_source(spec, bundle_dir=bundle)
    assert counts["poll_samples"] >= 1


def test_build_spec_flags_unknown_candidate() -> None:
    spec, problems = build_spec(
        _meta(), _merged(candidate_label="Some Newcomer"), "toronto_2014"
    )
    assert problems and "Some Newcomer" in problems[0]
    labels = {r.get("candidate_name") for r in spec["poll_responses"]}
    assert "Some Newcomer" not in labels  # never silently minted
