# Endorsement Expansion Design

**Date:** 2026-05-07  
**Context:** Based on feedback from Matt Elliott (City Hall Watcher). His 2022 Endorsement Matrix showed that total endorsement count tracked well with challenger strength. This change aligns the model with that finding.

---

## Summary of Changes

1. Drop `fundraising_tier` from `challengers.csv` (data not available until after e-day; agreed by both parties).
2. Drop `is_endorsed_by_departing` as an editorial CSV column; derive it programmatically at load time.
3. Add `endorsements` column to `challengers.csv`: a flat, pipe-separated list of named endorsers.
4. Add a per-endorsement logit strength boost (`ENDORSEMENT_WEIGHT`) that applies in all races.

---

## Section 1: Schema

### `data/raw/candidates/challengers.csv`

**Removed columns:**
- `fundraising_tier` — dropped entirely; not reliably available during campaign period
- `is_endorsed_by_departing` — derived programmatically (see Section 2)

**Added column:**
- `endorsements` — pipe-separated list of named endorsers, empty string if none

Example values:
- `""` — no known endorsements
- `"Josh Matlow"` — single endorser
- `"Josh Matlow|CUPE Local 79"` — multiple endorsers

All endorsement types (elected officials, unions, community orgs, etc.) go into this single flat field. No type distinction is tracked at this time.

### `data/raw/candidates/SCHEMA.md`

Updated to reflect removed and added columns. Validation rules updated accordingly.

### `validate_challengers()` in `backend/model/validate.py`

- Remove `fundraising_tier` and `is_endorsed_by_departing` from required columns list.
- Remove `fundraising_tier` value validation.
- Add `endorsements` as a required column; valid if non-null string (including empty string).

---

## Section 2: Data Loading

### `backend/model/run.py`

After loading both `ward_data` and `challengers`, a post-load step derives `is_endorsed_by_departing` as a computed boolean column on the challengers DataFrame:

1. For each ward where `ward_data.is_running == False`, look up the departing councillor's `councillor_name`.
2. For each challenger in that ward, check whether the departing councillor's name appears as a pipe-delimited token in the challenger's `endorsements` string.
3. Write the result into a new `is_endorsed_by_departing` column on the challengers DataFrame.
4. For all other wards (incumbent running), `is_endorsed_by_departing` defaults to `False`.

The fillna/defaults block for challengers without an editorial entry retains `"is_endorsed_by_departing": False` as a safe default. The `endorsements` default is `""`.

`simulation.py` is unchanged with respect to the open-seat departing-boost logic — it still reads `is_endorsed_by_departing` off the row as a boolean.

---

## Section 3: Simulation Strength Function

### `backend/model/simulation.py`

**`_compute_candidate_strength()`:**

- Remove the `fundraising_bonuses` dict and the `mu_tier += fundraising_bonuses[...]` line.
- Add a new named constant at module level:
  ```python
  ENDORSEMENT_WEIGHT = 0.3
  ```
- Add endorsement count term:
  ```python
  raw = str(cand.get("endorsements", ""))
  endorsement_count = len([e for e in raw.split("|") if e.strip()])
  mu_tier += ENDORSEMENT_WEIGHT * endorsement_count
  ```

**Effect:** 3–4 endorsements ≈ moving up one name-recognition tier (since tier spacing is 1.0). This is consistent with Matt's 2022 finding that endorsement count tracked with challenger quality. `ENDORSEMENT_WEIGHT` is an editorial parameter and can be tuned as more data becomes available.

**Scope:** The endorsement count boost applies in both incumbent contested races and open-seat races. The open-seat departing-councillor boost (`ENDORSEMENT_BOOST = 1.0`) is a separate parameter and remains unchanged — a departing councillor's endorsement represents a structural advantage (volunteer list, voter trust transfer) that merits its own weight distinct from the general endorsement signal.

---

## Files Touched

| File | Change |
|---|---|
| `data/raw/candidates/challengers.csv` | Remove `fundraising_tier`, `is_endorsed_by_departing`; add `endorsements` |
| `data/raw/candidates/SCHEMA.md` | Update column docs and validation rules |
| `backend/model/validate.py` | Update `validate_challengers()` |
| `backend/model/run.py` | Add post-load derivation of `is_endorsed_by_departing`; update defaults |
| `backend/model/simulation.py` | Remove fundraising bonus; add `ENDORSEMENT_WEIGHT` constant and count boost |

---

## Out of Scope

- `mayoral_alignment` is unchanged. Worth revisiting separately.
- Endorser type weighting (e.g. councillor > union) is not implemented. All endorsers count equally toward the total.
- The `data/processed/challengers.csv` output will update automatically when `process_all.py` is re-run.
