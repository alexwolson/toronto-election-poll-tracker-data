from __future__ import annotations

import json
import math
from pathlib import Path
from numbers import Real
from typing import Any


def snapshot_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "data"
        / "processed"
        / "model_snapshot.json"
    )


def load_snapshot() -> dict[str, Any] | None:
    path = snapshot_path()
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        return json.load(f, parse_constant=lambda _value: None)


def _sanitize_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_for_json(v) for v in value)
    if isinstance(value, Real) and not isinstance(value, bool):
        numeric = float(value)
        if not math.isfinite(numeric):
            return None
    return value


def save_snapshot(result: dict[str, Any]) -> Path:
    path = snapshot_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(_sanitize_for_json(result), f, allow_nan=False)
    return path
