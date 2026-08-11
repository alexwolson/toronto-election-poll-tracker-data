# polls.csv Schema

One row per published **citywide** mayoral poll. Ward-level subsamples do not
belong here (they would bias the citywide average toward that ward's lean) —
record their reported response options in `ward_poll_readings.csv` and list
their poll_id in `EXCLUDED_POLL_IDS`
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

# ward_poll_readings.csv Schema (current)

One row per response option in a published ward-level councillor poll. This is
the only ward-poll input used by Council snapshot schema v3. It preserves the
source's candidate field and denominator; an absent candidate is unobserved,
not zero, and residual and undecided responses remain explicit.

Required fields are `ward`, `poll_id`, `firm`, `date_conducted`,
`date_published`, `sample_size`, `methodology`, `denominator`, `ballot_status`,
`candidate_id`, `candidate_name`, `share`, `is_incumbent`, `is_residual`,
`registration_status`, and `undecided_share`. Optional `source_url` and `notes`
fields preserve provenance and qualifications. Shares must be finite
proportions in `[0, 1]`; candidate IDs must be unique within a poll;
candidate/residual shares must sum to the stated denominator within tolerance;
and `undecided_share` must agree across every row for the poll.

---

# ward_polls.csv Schema (legacy, not consumed by v3)

This synthetic input is retained only to preserve repository history. Do not
add new records or use it for public forecasts. Converting vote intention into
an editorial `inc_win_share` was retired in Council schema v3.

One row per published **ward-level** councillor poll. Feeds the ward-level
polling override in the superseded v0.2 specification.

| Column | Type | Required | Description |
|---|---|---|---|
| `ward` | integer | yes | Ward number, 1–25 |
| `poll_id` | string | yes | Unique identifier, e.g. `forum-ward13-2026-06-23` |
| `firm` | string | no | Polling firm name |
| `date_conducted` | YYYY-MM-DD | no | Date range end if a range was reported |
| `date_published` | YYYY-MM-DD | yes | Date the poll was publicly released |
| `sample_size` | integer | yes | Ward respondents |
| `methodology` | string | no | e.g. `IVR`, `online-panel` |
| `inc_win_share` | float | yes | Retired synthetic probability used only by the superseded model; do not derive new values |
| `notes` | string | no | Topline shares, derivation notes, anything noteworthy |

## Validation rules

- `ward` must be 1–25
- `inc_win_share` must be in [0, 1]
- `sample_size` must be a positive integer
- `date_conducted` must be ≤ `date_published`
- (`ward`, `poll_id`) pairs must be unique

---

# approval_ratings.csv Schema

One row per published mayoral approval reading. Required columns are `date`,
`source`, `approve`, `disapprove`, and `not_sure`; `methodology` is optional.
The three response shares must be finite proportions in `[0, 1]` and sum to
`1 ± 0.01`. Source/date pairs must be unique. Approval is contextual evidence
and is never an input to candidate vote shares or win probabilities.

# historical_mayoral_polls.csv Schema

Long-form polling observations for Toronto mayoral forecast calibration. Each
poll/candidate row records `election_id`, `election_date`, `poll_id`, `firm`,
`date_published`, `sample_size`, `field_tested`, `candidate_id`,
`candidate_name`, `share`, `is_residual`, and `source_url`. A candidate absent
from `field_tested` is unobserved, not a zero.

# historical_mayoral_outcomes.csv Schema

Long-form final results keyed by election and candidate. Minor candidates are
combined into one explicit residual row so the calibration denominator remains
complete.
