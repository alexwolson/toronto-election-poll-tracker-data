# council_alignment.csv Schema

One row per councillor.

| Column | Type | Required | Description |
|---|---|---|---|
| `ward` | integer | yes | Ward number (1–25) |
| `councillor_name` | string | yes | Canonical name |
| `alignment_chow` | float | yes | Fraction of votes with Mayor Chow (0–1) |
| `alignment_tory` | float | yes | Fraction of votes with Mayor Tory (0–1) |
| `source_url` | string | no | City Hall Watcher URL |
| `last_updated` | YYYY-MM-DD | yes | Date scores were last updated |

## Validation rules
- `ward` must be an integer in 1–25
- `alignment_chow` and `alignment_tory` must be floats in [0, 1]
- No duplicate `ward` values
