# challengers.csv Schema

One row per viable challenger in a ward. Also-rans (those unlikely to be competitive) are excluded.

| Column | Type | Required | Description |
|---|---|---|---|
| `ward` | integer | yes | Ward number (1–25) |
| `candidate_name` | string | yes | Canonical name of the challenger |
| `name_recognition_tier` | string | yes | `well-known`, `known`, or `unknown` |
| `fundraising_tier` | string | yes | `high` or `low` (placeholder until filings are available) |
| `mayoral_alignment` | string | yes | Candidate key they are aligned with (e.g. `chow`, `bradford`, `unaligned`) |
| `is_endorsed_by_departing` | boolean | yes | `true` if endorsed by the departing councillor (for open seats) |
| `notes` | string | no | Context on the candidate |
| `last_updated` | YYYY-MM-DD | yes | Date this row was last updated |

## Validation rules
- `ward` must be 1–25
- `name_recognition_tier` must be one of: `well-known`, `known`, `unknown`
- `fundraising_tier` must be one of: `high`, `low`
- `mayoral_alignment` should ideally match a candidate key (or `unaligned`)
- `is_endorsed_by_departing` must be `true` or `false`
