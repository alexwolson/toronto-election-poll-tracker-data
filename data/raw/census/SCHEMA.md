# ward_population.csv Schema

Ward-level total population from the Statistics Canada Census of Population,
extracted from Toronto Open Data's Ward Profiles (25-Ward Model) dataset.

Fetched by: `scripts/fetch_ward_profiles.py`
Source: https://open.toronto.ca/dataset/ward-profiles-25-ward-model/

## Columns

| Column | Type | Description |
|---|---|---|
| `ward` | integer | Ward number (1–25) |
| `pop_2016` | integer | Total population, 2016 census |
| `pop_2021` | integer | Total population, 2021 census |

## Derived value

`pop_growth_pct` is computed in `process_all.py` as:

    (pop_2021 - pop_2016) / pop_2016

This is used as the ward growth input to the defeatability score. It captures
the 2016→2021 growth trend as a proxy for post-2022 electorate change. A
more precise figure will be possible after the 2026 census or when the 2026
municipal voters list is published.
