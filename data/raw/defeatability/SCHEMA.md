# ward_defeatability.csv Schema

One row per ward where an incumbent is seeking re-election. Open seats (no incumbent) are excluded.

This file is hand-maintained from publicly available data:
- **Vote share and electorate share**: Toronto Open Data election results (2022 general election, or the relevant by-election for mid-term incumbents)
- **Ward population growth**: City of Toronto ward population estimates and census data

## Columns

| Column | Type | Required | Description |
|---|---|---|---|
| `ward` | integer | yes | Ward number (1–25) |
| `councillor_name` | string | yes | Canonical name of the incumbent |
| `election_year` | integer | yes | Year of the election used for vote share and electorate share (2022 for general-election incumbents; by-election year for mid-term incumbents) |
| `is_byelection_incumbent` | boolean | yes | `true` if the councillor was elected in a mid-term by-election rather than the 2022 general election |
| `vote_share` | float | yes | Incumbent's vote share in the reference election as a decimal (e.g. 0.58 for 58%). For by-election incumbents, this is their by-election vote share. |
| `electorate_share` | float | yes | Incumbent's votes as a fraction of all eligible voters in the ward (not just those who turned out) in the reference election. Computed as: incumbent votes / total registered electors. |
| `source_url` | string | no | URL to the data source for vote/electorate figures |
| `notes` | string | no | Any context, e.g. "by-election turnout was unusually low" |
| `last_updated` | YYYY-MM-DD | yes | Date this row was last reviewed or updated |

## Validation rules

- `ward` must be an integer in 1–25
- No duplicate `ward` values
- `election_year` must be a positive integer (typically 2022 or a by-election year)
- `vote_share` must be a float in (0, 1] — strictly positive (an incumbent with 0% did not win)
- `electorate_share` must be a float in (0, 1] — strictly positive
- `is_byelection_incumbent` must be `true` or `false`
- `last_updated` must be a parseable date

> **Note:** `pop_growth_pct` is not stored in this file. It is computed automatically in `process_all.py` from `data/raw/census/ward_population.csv` (2016→2021 Statistics Canada census data) and merged into the processed output.

## By-election incumbents

Several current councillors were elected in mid-term by-elections:
- **Ward 21** (Scarborough Centre): Parthi Kandavel, elected 2023 by-election
- **Ward 24** (Scarborough-Guildwood): Stephanie Shan, elected 2023 by-election
- **Ward 15** (Don Valley West): seat vacant following Jaye Robinson's death; incumbent TBD

For these wards, `is_byelection_incumbent` is `true`, and `vote_share`, `electorate_share`, and `pop_growth_pct` are based on the by-election figures rather than 2022 figures. By-election electorate shares are typically lower due to reduced turnout, making them noisier proxies. This is flagged in the model's output.

## Notes on electorate share

Electorate share differs from turnout-adjusted vote share. Specifically:

- `vote_share` = incumbent votes / total valid votes cast in ward
- `electorate_share` = incumbent votes / total registered electors in ward

A councillor who won with 60% of a 30% turnout has a vote_share of 0.60 but an electorate_share of approximately 0.18. The electorate_share is the lower figure and is the one used in the defeatability score, as it captures how thinly spread the incumbent's actual support base is across the whole ward population.
