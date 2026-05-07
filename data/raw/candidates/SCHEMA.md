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
