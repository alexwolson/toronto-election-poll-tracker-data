# polls.csv Schema

One row per published poll.

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
