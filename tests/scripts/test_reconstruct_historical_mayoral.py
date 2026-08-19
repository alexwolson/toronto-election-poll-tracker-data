from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_reconstruction_script_checks_committed_tables_and_reports_blockers() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/reconstruct_historical_mayoral.py", "--check"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    audit = json.loads(result.stdout)
    assert audit["outcome_candidate_count"] == 233
    assert audit["source_verified_sample_count"] == 83
    assert audit["source_verified_reading_count"] == 202
    assert audit["historical_sample_inventory_count"] == 107
    assert audit["unresolved_sample_proxy_count"] == 24
    assert audit["blocker_codes"] == [
        "unresolved_legacy_poll_samples",
    ]
