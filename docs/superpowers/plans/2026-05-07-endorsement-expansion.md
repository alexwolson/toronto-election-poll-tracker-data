# Endorsement Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `fundraising_tier` and the editorial `is_endorsed_by_departing` boolean in `challengers.csv` with a flat pipe-separated `endorsements` column of named endorsers, and apply a per-endorsement logit boost in the simulation.

**Architecture:** Four sequential tasks — validation, simulation strength function, data loading + derivation, then CSV/schema update. Each task is independently testable and committed. `is_endorsed_by_departing` is retained as a derived boolean column computed at load time, so `simulation.py`'s open-seat logic requires no structural changes.

**Tech Stack:** Python 3.12, pandas, pytest via `uv run pytest`

---

## File Map

| File | Change |
|---|---|
| `backend/model/validate.py` | Update `validate_challengers()` — swap `fundraising_tier`/`is_endorsed_by_departing` for `endorsements` |
| `backend/model/simulation.py` | Remove fundraising bonus; add `ENDORSEMENT_WEIGHT` constant and count-based boost |
| `backend/model/run.py` | Update `_ensure_generic_challenger()`; add `_derive_endorsed_by_departing()` called in `run_model()` |
| `tests/model/test_validate.py` | Replace fundraising tier tests with endorsements tests |
| `tests/model/test_simulation.py` | Update `_minimal_challenger` helper; add endorsement boost test |
| `tests/model/test_run.py` | Add `_derive_endorsed_by_departing` tests |
| `data/raw/candidates/challengers.csv` | Remove `fundraising_tier`, `is_endorsed_by_departing`; add `endorsements` |
| `data/raw/candidates/SCHEMA.md` | Update column docs and validation rules |

---

## Task 1: Update `validate_challengers()`

**Files:**
- Modify: `backend/model/validate.py:315-347`
- Modify: `tests/model/test_validate.py:1-48`

- [ ] **Step 1: Write failing tests**

Replace the three fundraising-tier tests in `tests/model/test_validate.py` with endorsements tests. The `_base_challengers_row` helper also needs updating. Replace the entire file content up to line 48 (keep everything after the mayor/councillor tests):

```python
"""Tests for input validation functions."""
import pandas as pd
import pytest
from backend.model.validate import (
    ValidationError,
    validate_challengers,
    validate_registered_mayors,
    validate_registered_councillors,
)


def _base_challengers_row(**overrides) -> dict:
    base = {
        "ward": 1,
        "candidate_name": "Test Candidate",
        "name_recognition_tier": "known",
        "mayoral_alignment": "unaligned",
        "endorsements": "",
        "last_updated": "2026-01-01",
    }
    base.update(overrides)
    return base


def test_validate_challengers_accepts_empty_endorsements():
    """Empty endorsements string is valid — candidate has no known endorsers."""
    df = pd.DataFrame([_base_challengers_row(endorsements="")])
    validate_challengers(df)


def test_validate_challengers_accepts_single_endorser():
    """A single named endorser is valid."""
    df = pd.DataFrame([_base_challengers_row(endorsements="Josh Matlow")])
    validate_challengers(df)


def test_validate_challengers_accepts_pipe_separated_endorsers():
    """Multiple endorsers separated by pipes are valid."""
    df = pd.DataFrame([_base_challengers_row(endorsements="Josh Matlow|CUPE Local 79")])
    validate_challengers(df)


def test_validate_challengers_rejects_missing_endorsements_column():
    """Missing endorsements column must raise ValidationError."""
    df = pd.DataFrame([{
        "ward": 1,
        "candidate_name": "Test Candidate",
        "name_recognition_tier": "known",
        "mayoral_alignment": "unaligned",
        "last_updated": "2026-01-01",
    }])
    with pytest.raises(ValidationError, match="endorsements"):
        validate_challengers(df)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd toronto-election-poll-tracker-data
uv run pytest tests/model/test_validate.py -v -k "endorsement"
```

Expected: FAIL — `validate_challengers` still requires `fundraising_tier`/`is_endorsed_by_departing` and has no `endorsements` logic.

- [ ] **Step 3: Update `validate_challengers()` in `backend/model/validate.py`**

Replace the `validate_challengers` function (lines 315–347):

```python
def validate_challengers(df: pd.DataFrame) -> None:
    """Validate a challengers DataFrame against the challengers.csv schema."""
    required = [
        "ward",
        "candidate_name",
        "name_recognition_tier",
        "mayoral_alignment",
        "endorsements",
        "last_updated",
    ]
    _check_required_columns(df, required, "challengers")

    # ward must be 1–25
    bad_ward = df[~df["ward"].between(1, 25)]
    if not bad_ward.empty:
        raise ValidationError(f"ward values outside 1–25: {bad_ward['ward'].tolist()}")

    # name_recognition_tier must be valid
    valid_recog = {"well-known", "known", "unknown"}
    bad_recog = df[~df["name_recognition_tier"].isin(valid_recog)]
    if not bad_recog.empty:
        raise ValidationError(
            f"Invalid name_recognition_tier in wards: {bad_recog['ward'].tolist()}"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/model/test_validate.py -v
```

Expected: All tests PASS (including existing mayor/councillor tests).

- [ ] **Step 5: Commit**

```bash
git add backend/model/validate.py tests/model/test_validate.py
git commit -m "feat: replace fundraising_tier/is_endorsed_by_departing with endorsements in validation"
```

---

## Task 2: Update simulation strength function

**Files:**
- Modify: `backend/model/simulation.py:24-122`
- Modify: `tests/model/test_simulation.py:25-37`

- [ ] **Step 1: Write failing test**

Add to `tests/model/test_simulation.py` after the existing `_minimal_challenger` helper. Also update `_minimal_challenger` to drop `fundraising_tier` and `is_endorsed_by_departing`, and add `endorsements`:

Replace `_minimal_challenger` (lines 25–37):

```python
def _minimal_challenger(ward: int, endorsements: str = "") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ward": ward,
                "candidate_name": "Challenger A",
                "name_recognition_tier": "known",
                "mayoral_alignment": "unaligned",
                "is_endorsed_by_departing": False,
                "endorsements": endorsements,
            }
        ]
    )
```

Then add this test at the end of the file:

```python
def test_endorsement_count_boosts_candidate_strength():
    """Each named endorser adds ENDORSEMENT_WEIGHT to the candidate's logit strength.

    A candidate with 3 endorsements should have a higher win probability than
    an identical candidate with 0 endorsements, all else equal.
    """
    from backend.model.simulation import ENDORSEMENT_WEIGHT
    ward = 5

    def _run_with_endorsements(endorsements: str) -> float:
        sim = WardSimulation(
            ward_data=_minimal_ward_data(ward, is_running=False),
            mayoral_averages=_minimal_mayoral_averages(),
            coattails=_empty_coattails(),
            challengers=_minimal_challenger(ward, endorsements=endorsements),
            leans=_empty_leans(),
            n_draws=2000,
            seed=42,
        )
        result = sim.run()
        return result["candidate_win_probabilities"][ward].get("Challenger A", 0.0)

    prob_none = _run_with_endorsements("")
    prob_three = _run_with_endorsements("Endorser A|Endorser B|Endorser C")

    assert prob_three > prob_none, (
        f"3-endorsement candidate ({prob_three:.3f}) should win more often than "
        f"0-endorsement candidate ({prob_none:.3f})"
    )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/model/test_simulation.py::test_endorsement_count_boosts_candidate_strength -v
```

Expected: FAIL — `_compute_candidate_strength` doesn't use `endorsements` yet, so both runs produce identical probabilities.

- [ ] **Step 3: Update `simulation.py`**

Add `ENDORSEMENT_WEIGHT` constant near the other constants at the top of the file (after `ENDORSEMENT_BOOST = 1.0`, around line 34):

```python
# Per-endorsement logit strength boost, applied in all races
ENDORSEMENT_WEIGHT = 0.3
```

Replace `_compute_candidate_strength` (lines 95–122):

```python
def _compute_candidate_strength(
    self, cand: pd.Series, mayoral_mood: dict[str, float], ward_num: int
) -> float:
    """Compute mu_j (Stage 2 strength)."""
    tier_baselines = {"well-known": 2.0, "known": 1.0, "unknown": 0.0}
    mu_tier = tier_baselines.get(cand["name_recognition_tier"], 0.0)

    raw_endorsements = str(cand.get("endorsements", ""))
    endorsement_count = len([e for e in raw_endorsements.split("|") if e.strip()])
    mu_tier += ENDORSEMENT_WEIGHT * endorsement_count

    w_a = 2.0
    alignment = cand["mayoral_alignment"]
    boost = 0.0
    if alignment != "unaligned":
        lean_row = self.leans[
            (self.leans["ward"] == ward_num)
            & (self.leans["candidate"] == alignment)
        ]
        if not lean_row.empty:
            lean = lean_row.iloc[0]["lean"]
            mood = mayoral_mood.get(alignment, 0.0)
            boost = w_a * (lean + (mood - 0.20))

    return mu_tier + boost
```

- [ ] **Step 4: Run all simulation tests**

```bash
uv run pytest tests/model/test_simulation.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/model/simulation.py tests/model/test_simulation.py
git commit -m "feat: add per-endorsement logit boost, remove fundraising strength term"
```

---

## Task 3: Update data loading and add `_derive_endorsed_by_departing`

**Files:**
- Modify: `backend/model/run.py:62-110`
- Modify: `tests/model/test_run.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/model/test_run.py`:

```python
import pandas as pd
from backend.model.run import _derive_endorsed_by_departing


def _ward_data(ward: int, councillor_name: str, is_running: bool) -> pd.DataFrame:
    return pd.DataFrame([{
        "ward": ward,
        "councillor_name": councillor_name,
        "is_running": is_running,
        "defeatability_score": 20,
    }])


def test_derive_endorsed_by_departing_detects_match():
    """Challenger whose endorsements include the departing councillor's name
    should have is_endorsed_by_departing=True."""
    ward_data = _ward_data(5, "Paula Fletcher", is_running=False)
    challengers = pd.DataFrame([{
        "ward": 5,
        "candidate_name": "Challenger A",
        "endorsements": "Paula Fletcher|CUPE Local 79",
    }])

    result = _derive_endorsed_by_departing(challengers, ward_data)

    assert result.loc[0, "is_endorsed_by_departing"] is True or \
           result.loc[0, "is_endorsed_by_departing"] == True


def test_derive_endorsed_by_departing_no_match():
    """Challenger without the departing councillor in endorsements gets False."""
    ward_data = _ward_data(5, "Paula Fletcher", is_running=False)
    challengers = pd.DataFrame([{
        "ward": 5,
        "candidate_name": "Challenger A",
        "endorsements": "CUPE Local 79",
    }])

    result = _derive_endorsed_by_departing(challengers, ward_data)

    assert result.loc[0, "is_endorsed_by_departing"] == False


def test_derive_endorsed_by_departing_incumbent_ward_is_false():
    """Wards where the incumbent is running have no departing councillor;
    is_endorsed_by_departing must be False."""
    ward_data = _ward_data(3, "Mike Colle", is_running=True)
    challengers = pd.DataFrame([{
        "ward": 3,
        "candidate_name": "Challenger B",
        "endorsements": "Mike Colle",
    }])

    result = _derive_endorsed_by_departing(challengers, ward_data)

    assert result.loc[0, "is_endorsed_by_departing"] == False


def test_derive_endorsed_by_departing_empty_endorsements():
    """Empty endorsements string yields False even for open seats."""
    ward_data = _ward_data(7, "Michael Thompson", is_running=False)
    challengers = pd.DataFrame([{
        "ward": 7,
        "candidate_name": "Challenger C",
        "endorsements": "",
    }])

    result = _derive_endorsed_by_departing(challengers, ward_data)

    assert result.loc[0, "is_endorsed_by_departing"] == False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/model/test_run.py -v -k "derive"
```

Expected: FAIL — `_derive_endorsed_by_departing` does not exist yet.

- [ ] **Step 3: Implement `_derive_endorsed_by_departing` and update `_ensure_generic_challenger` in `run.py`**

Add `_derive_endorsed_by_departing` as a new function before `_ensure_generic_challenger`:

```python
def _derive_endorsed_by_departing(
    challengers: pd.DataFrame, ward_data: pd.DataFrame
) -> pd.DataFrame:
    """Derive is_endorsed_by_departing from the named endorsements list.

    For open-seat wards (is_running=False), checks whether the departing
    councillor's name appears as a token in the challenger's endorsements field.
    All other wards get False.
    """
    departing = (
        ward_data[~ward_data["is_running"].astype(bool)][["ward", "councillor_name"]]
        .set_index("ward")["councillor_name"]
        .to_dict()
    )

    def _check(row: pd.Series) -> bool:
        departing_name = departing.get(int(row["ward"]))
        if not departing_name:
            return False
        tokens = [e.strip() for e in str(row.get("endorsements", "")).split("|")]
        return departing_name in tokens

    result = challengers.copy()
    result["is_endorsed_by_departing"] = result.apply(_check, axis=1)
    return result
```

Replace `_ensure_generic_challenger` (lines 62–101) to remove `fundraising_tier` and `is_endorsed_by_departing` from the required columns and defaults, and add `endorsements`:

```python
def _ensure_generic_challenger(
    challengers: pd.DataFrame, ward_data: pd.DataFrame
) -> pd.DataFrame:
    required_cols = [
        "ward",
        "candidate_name",
        "name_recognition_tier",
        "mayoral_alignment",
        "endorsements",
        "is_endorsed_by_departing",
    ]
    out = challengers.copy()
    for col in required_cols:
        if col not in out.columns:
            out[col] = None

    rows = []
    wards_with_challengers = (
        set(out["ward"].dropna().astype(int).tolist()) if not out.empty else set()
    )
    for _, row in ward_data.iterrows():
        ward = int(row["ward"])
        if not bool(row.get("is_running", True)):
            continue
        if ward not in wards_with_challengers:
            rows.append(
                {
                    "ward": ward,
                    "candidate_name": "Generic Challenger",
                    "name_recognition_tier": "unknown",
                    "mayoral_alignment": "unaligned",
                    "endorsements": "",
                    "is_endorsed_by_departing": False,
                }
            )

    if rows:
        out = pd.concat([out, pd.DataFrame(rows)], ignore_index=True)

    return out
```

Then in `run_model()`, call `_derive_endorsed_by_departing` immediately after `_ensure_generic_challenger`. The relevant section currently reads:

```python
data["challengers"] = _ensure_generic_challenger(
    data["challengers"], data["defeatability"]
)
```

Update it to:

```python
data["challengers"] = _ensure_generic_challenger(
    data["challengers"], data["defeatability"]
)
data["challengers"] = _derive_endorsed_by_departing(
    data["challengers"], data["defeatability"]
)
```

- [ ] **Step 4: Run all run/validate tests**

```bash
uv run pytest tests/model/test_run.py tests/model/test_validate.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/model/run.py tests/model/test_run.py
git commit -m "feat: derive is_endorsed_by_departing from named endorsements at load time"
```

---

## Task 4: Update CSV and schema docs

**Files:**
- Modify: `data/raw/candidates/challengers.csv`
- Modify: `data/raw/candidates/SCHEMA.md`

- [ ] **Step 1: Rewrite `challengers.csv`**

Replace the file contents with the new schema (one data row for Ward 5, Chiara Padovani — no known endorsements yet):

```
ward,candidate_name,name_recognition_tier,mayoral_alignment,endorsements,notes,last_updated
5,Chiara Padovani,well-known,unaligned,,2026-05-03
```

- [ ] **Step 2: Rewrite `SCHEMA.md`**

Replace the file contents:

```markdown
# challengers.csv Schema

One row per viable challenger in a ward. Also-rans (those unlikely to be competitive) are excluded.

| Column | Type | Required | Description |
|---|---|---|---|
| `ward` | integer | yes | Ward number (1–25) |
| `candidate_name` | string | yes | Canonical name of the challenger |
| `name_recognition_tier` | string | yes | `well-known`, `known`, or `unknown` |
| `mayoral_alignment` | string | yes | Candidate key they are aligned with (e.g. `chow`, `bradford`, `unaligned`) |
| `endorsements` | string | yes | Pipe-separated list of named endorsers; empty string if none (e.g. `Josh Matlow\|CUPE Local 79`) |
| `notes` | string | no | Context on the candidate |
| `last_updated` | YYYY-MM-DD | yes | Date this row was last updated |

## Validation rules
- `ward` must be 1–25
- `name_recognition_tier` must be one of: `well-known`, `known`, `unknown`
- `endorsements` must be a non-null string (empty string is valid)

## Derived fields (not in CSV)
- `is_endorsed_by_departing` — computed at model load time; `True` if the departing councillor's name appears as a token in `endorsements` for an open-seat ward
```

- [ ] **Step 3: Run the full test suite**

```bash
uv run pytest -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add data/raw/candidates/challengers.csv data/raw/candidates/SCHEMA.md
git commit -m "feat: update challengers.csv schema — endorsements replaces fundraising_tier and is_endorsed_by_departing"
```

---

## Final Verification

- [ ] Run the full pipeline end-to-end to confirm no runtime errors:

```bash
uv run scripts/process_all.py && uv run scripts/build_snapshot.py
```

Expected: Both scripts complete without errors. `data/processed/model_snapshot.json` is regenerated.
