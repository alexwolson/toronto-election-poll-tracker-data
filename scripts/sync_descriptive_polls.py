#!/usr/bin/env python3
"""Regenerate the public mayoral poll archive from audited representative readings."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from polling_data.descriptive_polls import write_descriptive_polls

SOURCE = ROOT / "data" / "raw" / "polls"


if __name__ == "__main__":
    output = write_descriptive_polls(SOURCE, SOURCE / "polls.csv")
    print(f"descriptive mayoral polls written to {output}")
