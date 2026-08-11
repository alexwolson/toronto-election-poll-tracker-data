"""Single source of truth for the public 2026 mayoral field."""

from __future__ import annotations

from datetime import UTC, datetime

TARGET_FIELD = ("chow", "bradford", "alexander")
INCUMBENT_CANDIDATE = "chow"
RESIDUAL_ID = "residual"
RESIDUAL_LABEL = "Other / undecided"
ELECTION_DATE = "2026-10-26"
FORECAST_MODEL_VERSION = "choice_set_v1"
SNAPSHOT_SCHEMA_VERSION = 2
NOMINATION_CLOSE = datetime(2026, 8, 21, 18, 0, tzinfo=UTC)
