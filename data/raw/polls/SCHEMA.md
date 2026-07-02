# polls.csv Schema

One row per published **citywide** mayoral poll. Ward-level subsamples do not
belong here (they would bias the citywide average toward that ward's lean) —
record them in `ward_polls.csv` and list their poll_id in `EXCLUDED_POLL_IDS`
in `scripts/fetch_polls.py` so the Wikipedia fetch doesn't re-add them.

## Fixed metadata columns

| Column | Type | Required | Description |
|---|---|---|---|
| `poll_id` | string | yes | Unique identifier, e.g. `liaison-2025-11-01` |
| `firm` | string | yes | Polling firm name |
| `date_conducted` | YYYY-MM-DD | yes | Date range end if a range was reported |
| `date_published` | YYYY-MM-DD | yes | Date the poll was publicly released |
| `sample_size` | integer | no | Blank if not reported |
| `methodology` | string | no | e.g. `online-panel`, `IVR`, `phone` |
| `field_tested` | string | yes | Comma-separated list of candidate keys tested in this poll (must match column names exactly) |
| `notes` | string | no | Anything noteworthy |

## Candidate share columns

Any numeric column not in the fixed metadata set above is treated as a candidate share column. Columns are added as candidates enter polling — there is no fixed set.

Use the candidate's short lowercase key as the column name (matching the key used in `field_tested`). For example: `chow`, `bradford`, `bailao`, `tory`, `doe`. Add `undecided` for the undecided share — it is treated as a share column like any other.

Older rows leave columns for candidates who weren't tested blank (empty cell, not `0`).

## Validation rules

- All share columns (candidate columns + `undecided`) per row must sum to ≤ 1.0
- Every key listed in `field_tested` must have a corresponding column in the CSV
- Every share column that has a value in a given row must be listed in `field_tested` for that row
- `date_conducted` must be ≤ `date_published`
- `sample_size` must be a positive integer if present
- `poll_id` must be unique across all rows

---

# ward_polls.csv Schema

One row per published **ward-level** councillor poll. Feeds the ward-level
polling override (model spec Part 6): the simulation blends `inc_win_share`
with the structural incumbent win probability, weighted by poll recency and
sample size.

| Column | Type | Required | Description |
|---|---|---|---|
| `ward` | integer | yes | Ward number, 1–25 |
| `poll_id` | string | yes | Unique identifier, e.g. `forum-ward13-2026-06-23` |
| `firm` | string | no | Polling firm name |
| `date_conducted` | YYYY-MM-DD | no | Date range end if a range was reported |
| `date_published` | YYYY-MM-DD | yes | Date the poll was publicly released |
| `sample_size` | integer | yes | Ward respondents |
| `methodology` | string | no | e.g. `IVR`, `online-panel` |
| `inc_win_share` | float | yes | Poll-implied P(incumbent wins), in [0, 1] — NOT the raw vote share. Derive via `scripts/derive_ward_poll_win_share.py` and record the derivation in `notes` |
| `notes` | string | no | Topline shares, derivation notes, anything noteworthy |

## Validation rules

- `ward` must be 1–25
- `inc_win_share` must be in [0, 1]
- `sample_size` must be a positive integer
- `date_conducted` must be ≤ `date_published`
- (`ward`, `poll_id`) pairs must be unique
