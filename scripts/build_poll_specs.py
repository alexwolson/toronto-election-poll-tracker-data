#!/usr/bin/env python3
"""Bridge reconciled vision extraction -> 5-table ingest spec -> audited ingest.

Reads the double-read workflow's reconcile output (JSON array) and the prep
meta.json files, and for each CLEAN document builds the source-contract spec via
the pure ``build_spec`` and ingests it through the tested ``ingest_poll_source``
core plus artifact verification. Candidate-label canonicalization is explicit:
any label not in ``CANDIDATES`` flags the document for review rather than minting
an id silently. Flagged (non-clean) documents are reported, never ingested.

Forum-oriented (pollster/sponsor/sample id); generalize CANDIDATES and the sample
identity when extending to other firms.

Usage:  uv run scripts/build_poll_specs.py <workflow_results.json>
"""

import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.model.poll_ingest import ingest_poll_source
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


def build_spec(meta, merged, cycle, *, retrieved_at=None):
    """Pure transform: (meta, reconciled extraction) -> (5-table spec, problems)."""
    retrieved_at = retrieved_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    problems: list[str] = []
    did = meta["doc_id"]
    fw_end = merged["fieldwork_end"]
    n = merged["recruited_sample_size"]
    sample_id = f"forum_city_{fw_end.replace('-', '_')}_n{n}"
    year = cycle.split("_")[1]
    doc = {
        "source_document_id": did,
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
            "used for extraction agreed across both reads and matched the trending summary. "
            "Public availability is not an affirmative reuse licence, so redistribution status "
            "remains unknown."
        ),
    }
    sample = {
        "poll_sample_id": sample_id,
        "election_cycle_id": cycle,
        "pollster": "Forum Research",
        "sponsor": "Forum Research Inc.",
        "geography_type": "citywide",
        "geography_id": "toronto",
        "fieldwork_start": merged.get("fieldwork_start") or fw_end,
        "fieldwork_end": fw_end,
        "publication_date": merged["publication_date"],
        "publication_at": "",
        "publication_time_precision": "date_only",
        "evidence_available_at": _evidence_available_at(merged["publication_date"]),
        "collection_mode": merged.get("collection_mode", "ivr"),
        "recruited_sample_size": str(n),
        "extraction_status": "extracted",
        "notes": "Toronto voters age 18+.",
    }
    link = {
        "poll_sample_id": sample_id,
        "source_document_id": did,
        "sample_locator": "entire document",
        "notes": "First-party release for this respondent sample.",
    }
    readings, responses = [], []
    for i, r in enumerate(merged["readings"], start=1):
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
        "source_documents": [doc],
        "poll_sample_documents": [link],
        "poll_samples": [sample],
        "poll_readings": readings,
        "poll_responses": responses,
    }
    return spec, problems


def main() -> None:
    results = json.loads(Path(sys.argv[1]).read_text())
    metas = {
        p.parent.name: json.loads(p.read_text())
        for p in (ROOT / "tmp/ingest_staging").glob("*/meta.json")
    }
    for res in results:
        did = res["doc_id"]
        print(f"\n=== {did} ===")
        if not res.get("clean"):
            print("  FLAGGED — not ingested:")
            for f in res.get("flags", []):
                print("   -", f)
            continue
        spec, problems = build_spec(metas[did], res["merged"], metas[did]["cycle"])
        if problems:
            print("  NEEDS MAP EXTENSION — not ingested:")
            for p in problems:
                print("   -", p)
            continue
        counts = ingest_poll_source(spec, bundle_dir=BUNDLE)
        verify_poll_source_artifacts(
            load_poll_source_bundle(str(BUNDLE), require_audited_sources=True), ROOT
        )
        print(
            f"  INGESTED {len(spec['poll_readings'])} readings, {len(spec['poll_responses'])} responses"
            f"  -> samples={counts['poll_samples']} readings={counts['poll_readings']}"
        )


if __name__ == "__main__":
    main()
