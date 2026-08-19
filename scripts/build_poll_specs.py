#!/usr/bin/env python3
"""Bridge reconciled vision extraction -> 5-table ingest spec -> audited ingest.

Reads the double-read workflow's reconcile output (JSON array) and the prep
meta.json files, groups the CLEAN documents by shared sample identity (same
fieldwork_end and recruited_sample_size), and for each sample builds the
source-contract spec via the pure ``build_spec`` and ingests it through the
tested ``ingest_poll_source`` core plus artifact verification.

One sample may be backed by several documents (e.g. a Forum trial-heats release
plus a same-fieldwork summary): readings are merged across the group's documents
and deduped by candidate set; a candidate set that recurs with different values
is flagged rather than silently kept. Candidate-label canonicalization is
explicit: any label not in ``CANDIDATES`` flags the document for review rather
than minting an id silently.

Forum-oriented (pollster/sponsor/sample id); generalize CANDIDATES and the
sample identity when extending to other firms.

Usage:  uv run scripts/build_poll_specs.py <workflow_results.json>
"""

import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.poll_ingest import IngestError, ingest_poll_source
from backend.model.poll_sources import (
    load_poll_source_bundle,
    verify_poll_source_artifacts,
)

BUNDLE = ROOT / "data/raw/polls/historical_mayoral"
TORONTO = ZoneInfo("America/Toronto")

CANDIDATES = {
    "rob ford": ("rob-ford", "Rob Ford"),
    "doug ford": ("doug-ford", "Doug Ford"),
    "john tory": ("tory", "John Tory"),
    "olivia chow": ("chow", "Olivia Chow"),
    "karen stintz": ("stintz", "Karen Stintz"),
    "david soknacki": ("soknacki", "David Soknacki"),
    "denzil minnan-wong": ("minnan-wong", "Denzil Minnan-Wong"),
    "adam giambrone": ("giambrone", "Adam Giambrone"),
}
DK = {"don't know", "dont know", "dk", "undecided/don't know"}


def _evidence_available_at(pub_date: str) -> str:
    d = date.fromisoformat(pub_date) + timedelta(days=1)
    dt = datetime(d.year, d.month, d.day, tzinfo=TORONTO)
    z = dt.strftime("%z")
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + z[:3] + ":" + z[3:]


def _candidate_key(responses) -> tuple:
    return tuple(
        sorted(
            str(r["label"]).strip().lower()
            for r in responses
            if r.get("kind") == "candidate"
            and str(r["label"]).strip().lower() not in DK
        )
    )


def _value_map(responses) -> dict:
    return {str(r["label"]).strip().lower(): int(r["value"]) for r in responses}


def _document_row(meta, retrieved_at) -> dict:
    return {
        "source_document_id": meta["doc_id"],
        "document_role": "release",
        "publisher_url": meta["publisher_url"],
        "retrieval_url": meta["retrieval_url"],
        "retrieval_status": "retrieved",
        "retrieved_at": retrieved_at,
        "media_type": "application/pdf",
        "sha256": meta["sha256"],
        "local_path": meta["local_path"],
        "byte_size": str(meta["byte_size"]),
        "page_count": str(meta["page_count"]),
        "sheet_count": "",
        "text_layer_status": "present",
        "visual_qa_status": "passed",
        "access_class": "public",
        "redistribution_status": "unknown",
        "reuse_terms_url": "",
        "notes": (
            "First-party Forum PDF recovered through an archived-original Wayback replay. "
            "All pages were rendered and visually inspected by two independent vision reads; "
            "the text layer is present and readable, and every [All Respondents] Total column "
            "used for extraction agreed across both reads. Public availability is not an "
            "affirmative reuse licence, so redistribution status remains unknown."
        ),
    }


def build_spec(group, cycle, *, retrieved_at=None):
    """A group of documents sharing one sample -> (5-table spec, problems).

    ``group`` is a non-empty list of (meta, merged) that share a sample identity
    (same fieldwork_end and recruited_sample_size). Produces one sample linked to
    every document, with readings merged across documents and deduped by candidate
    set; a recurring candidate set with different values is flagged.
    """
    retrieved_at = retrieved_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    problems: list[str] = []
    _, base = group[0]
    fw_end = base["fieldwork_end"]
    n = base["recruited_sample_size"]
    for _, md in group:
        if (md["fieldwork_end"], md["recruited_sample_size"]) != (fw_end, n):
            raise IngestError(
                "build_spec group does not share a single sample identity"
            )
    sample_id = f"forum_city_{fw_end.replace('-', '_')}_n{n}"
    year = cycle.split("_")[1]

    sample = {
        "poll_sample_id": sample_id,
        "election_cycle_id": cycle,
        "pollster": "Forum Research",
        "sponsor": "Forum Research Inc.",
        "geography_type": "citywide",
        "geography_id": "toronto",
        "fieldwork_start": base.get("fieldwork_start") or fw_end,
        "fieldwork_end": fw_end,
        "publication_date": base["publication_date"],
        "publication_at": "",
        "publication_time_precision": "date_only",
        "evidence_available_at": _evidence_available_at(base["publication_date"]),
        "collection_mode": base.get("collection_mode", "ivr"),
        "recruited_sample_size": str(n),
        "extraction_status": "extracted",
        "notes": "Toronto voters age 18+.",
    }

    docs, links, readings, responses = [], [], [], []
    seen: dict[tuple, dict] = {}
    for meta, md in group:
        did = meta["doc_id"]
        docs.append(_document_row(meta, retrieved_at))
        links.append(
            {
                "poll_sample_id": sample_id,
                "source_document_id": did,
                "sample_locator": "entire document",
                "notes": "First-party release for this respondent sample.",
            }
        )
        for i, r in enumerate(md["readings"], start=1):
            key = _candidate_key(r["responses"])
            values = _value_map(r["responses"])
            if key in seen:
                if seen[key] != values:
                    problems.append(
                        f"scenario {r['scenario_label']!r} differs across documents "
                        f"in sample {sample_id}"
                    )
                continue
            seen[key] = values
            rid = f"{did}__r{i}"
            readings.append(
                {
                    "poll_reading_id": rid,
                    "poll_sample_id": sample_id,
                    "source_document_id": did,
                    "source_locator": r["source_locator"],
                    "contest_type": "mayoral",
                    "contest_id": f"toronto-mayor-{year}",
                    "question_order_status": "not_reported",
                    "question_text_status": "reported"
                    if r.get("question_text")
                    else "not_reported",
                    "question_text": r.get("question_text", ""),
                    "scenario_label": r["scenario_label"],
                    "document_display_order": str(i),
                    "population": "Toronto voters age 18+",
                    "turnout_screen": "none",
                    "denominator_type": "all_respondents",
                    "denominator_text": "[All Respondents]",
                    "unweighted_base_status": "not_reported",
                    "weighted_base_status": "not_reported",
                    "reported_base_status": "reported",
                    "reported_base": str(r["base"]),
                    "tested_choice_set_status": "complete",
                    "response_coverage": "complete",
                    "reported_share_unit": "percent",
                    "reported_share_precision": "0",
                    "reading_purpose": "general_vote_intention",
                    "notes": "Extracted from the [All Respondents] Total column; agreed across two independent vision reads.",
                }
            )
            for j, resp in enumerate(r["responses"], start=1):
                label = str(resp["label"]).strip()
                low = label.lower()
                row = {
                    "poll_reading_id": rid,
                    "response_option_id": "",
                    "option_order": str(j),
                    "reported_value": str(int(resp["value"])),
                    "share": str(round(int(resp["value"]) / 100, 2)),
                    "notes": "Source-published token preserved; agreed across two reads.",
                }
                if resp.get("kind") == "dont_know" or low in DK:
                    row.update(
                        response_option_id="dont-know",
                        response_kind="dont_know",
                        response_label=label or "Don't know",
                    )
                elif low in CANDIDATES:
                    cid, cname = CANDIDATES[low]
                    row.update(
                        response_option_id=cid,
                        response_kind="candidate",
                        candidate_id=cid,
                        candidate_name=cname,
                        candidate_observation_status="individually_published",
                        response_label=label,
                    )
                else:
                    problems.append(
                        f"unknown candidate label {label!r} (add to CANDIDATES)"
                    )
                    continue
                responses.append(row)

    spec = {
        "source_documents": docs,
        "poll_sample_documents": links,
        "poll_samples": [sample],
        "poll_readings": readings,
        "poll_responses": responses,
    }
    return spec, problems


def group_by_sample(items):
    """Group (meta, merged) items by shared sample identity (fieldwork_end, size)."""
    groups: dict[tuple, list] = {}
    for meta, md in items:
        key = (md["fieldwork_end"], md["recruited_sample_size"])
        groups.setdefault(key, []).append((meta, md))
    return list(groups.values())


def main() -> None:
    results = json.loads(Path(sys.argv[1]).read_text())
    metas = {
        p.parent.name: json.loads(p.read_text())
        for p in (ROOT / "tmp/ingest_staging").glob("*/meta.json")
    }
    clean = []
    for res in results:
        if res.get("clean"):
            clean.append((metas[res["doc_id"]], res["merged"]))
        else:
            print(f"\n=== {res['doc_id']} FLAGGED — not ingested ===")
            for f in res.get("flags", []):
                print("   -", f)

    for group in group_by_sample(clean):
        cycle = group[0][0]["cycle"]
        dids = [m["doc_id"] for m, _ in group]
        print(f"\n=== sample from {dids} ===")
        spec, problems = build_spec(group, cycle)
        if problems:
            print("  PROBLEMS — not ingested:")
            for p in problems:
                print("   -", p)
            continue
        counts = ingest_poll_source(spec, bundle_dir=BUNDLE)
        verify_poll_source_artifacts(
            load_poll_source_bundle(str(BUNDLE), require_audited_sources=True), ROOT
        )
        print(
            f"  INGESTED {len(spec['poll_readings'])} readings from "
            f"{len(spec['source_documents'])} doc(s) -> samples={counts['poll_samples']} "
            f"readings={counts['poll_readings']}"
        )


if __name__ == "__main__":
    main()
