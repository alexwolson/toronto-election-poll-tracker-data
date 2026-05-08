# fetch_polls.py — Wikipedia Poll Fetcher Design Spec

## Goal

Add `scripts/fetch_polls.py` — a script that fetches the Toronto 2026 mayoral election polling tables from Wikipedia via the Wikimedia REST API and writes the result as a clean `data/raw/polls/polls.csv`, replacing the manually-maintained file entirely. Wikipedia is treated as authoritative.

---

## Fetch

Use the Wikimedia REST API:

```
GET https://en.wikipedia.org/api/rest_v1/page/html/2026_Toronto_mayoral_election
```

Include a `User-Agent` header identifying the client:
```
User-Agent: toronto-election-poll-tracker/1.0 (https://github.com/alexwolson/toronto-election-poll-tracker-data)
```

Raise on HTTP errors (`response.raise_for_status()`). Pass the response text to BeautifulSoup with the `lxml` parser (already a project dependency).

---

## Table Discovery

Find all `<table class="wikitable ...">` elements. Identify polling tables by checking whether the header row contains both `"Polling Firm"` and `"Poll Date"`. Non-polling tables (candidates, results, etc.) are skipped.

Each polling table is classified by the number of candidate columns it contains:
- **Two candidate columns** → head-to-head matchup table
- **Three or more candidate columns** → main multi-candidate table

Both are parsed with the same row-parsing logic; only `poll_id` generation differs.

---

## Column Mapping

Wikipedia columns and how they map to `polls.csv`:

| Wikipedia column | `polls.csv` field | Notes |
|---|---|---|
| Polling Firm | `firm` | Used as-is; also used to derive `firm_slug` |
| Poll Date | `date_conducted`, `date_published` | Both set to the same value; parsed from e.g. `"April 13, 2026"` → `"2026-04-13"` |
| Sample Size | `sample_size` | Strip commas; blank if `"N/A"` or `"—"` |
| Methodology | `methodology` | Lower-cased; `"IVR"` stays `"IVR"`, `"Online"` → `"online"` |
| MOE | — | Discarded |
| Lead | — | Discarded |
| Candidate % columns | per-candidate share column | `"—"` → empty; percentages divided by 100; bold markers stripped |

**Candidate column names** are normalised to lowercase ASCII slugs matching the existing `polls.csv` convention:

```python
CANDIDATE_SLUG = {
    "Bailão": "bailao",
    "Bradford": "bradford",
    "Chow": "chow",
    "Furey": "furey",
    "Ford": "ford",
    "Mendicino": "mendicino",
    "Tory": "tory",
    "Other": "other",
    "Undecided": "undecided",
}
```

Any candidate column not in this map is slugified with `name.lower().replace(" ", "_")` as a fallback.

---

## Firm Slug Map

Used for `poll_id` generation:

```python
FIRM_SLUG = {
    "Liaison Strategies": "liaison",
    "Pallas Data": "pallas",
    "Pallas": "pallas",
    "Mainstreet Research": "mainstreet",
    "Canada Pulse Insights": "canadapulse",
    "Canada Pulse Insights/CityNews": "canadapulse",
    "Forum Research": "forum",
    "Ipsos": "ipsos",
    "Abacus Data": "abacus",
    "Abacus": "abacus",
}
```

If a firm name is not in the map, raise a descriptive `ValueError` so new firms are never silently dropped.

---

## poll_id Generation

**Main multi-candidate polls:**
```
{firm_slug}-{YYYY-MM-DD}
```
Example: `liaison-2026-04-13`

**Head-to-head matchups:**
```
{firm_slug}-{YYYY-MM-DD}-{cand1}-v-{cand2}
```
Candidates are sorted alphabetically so the suffix is stable regardless of table column order.
Example: `pallas-2026-03-08-bradford-v-chow`

If two rows from different tables would produce the same `poll_id`, a `ValueError` is raised (the existing data has no such collision, and this guards against future ones).

---

## field_tested Derivation

For each row, `field_tested` is the comma-joined sorted list of candidate slug columns that have a non-empty value in that row. Example: `"bradford,chow,furey"`.

---

## Output

**`data/raw/polls/polls.csv`** — full replacement. Column order:

```
poll_id, firm, date_conducted, date_published, sample_size, methodology, field_tested,
bailao, bradford, chow, furey, ford, mendicino, tory, other, undecided, notes
```

The `notes` column is always written (all empty) to preserve the schema for future manual annotations. Any candidate columns not seen in the current Wikipedia data are omitted — they will appear when a new candidate column is added to Wikipedia.

**`data/raw/polls/polls.json`** — sidecar with fetch timestamp, matching the pattern used by all other fetch scripts:

```json
{"fetched_at": "2026-05-07T18:00:00+00:00"}
```

---

## Error Handling

- HTTP error from Wikipedia API → raise immediately with status code
- Unknown firm name → raise `ValueError` with the firm name
- Unparseable date → raise `ValueError` with the raw string
- No polling tables found → raise `RuntimeError` (page structure changed)
- Duplicate `poll_id` → raise `ValueError`

---

## CI Integration

Not added to the daily CI workflow. The script is run manually:

```bash
uv run scripts/fetch_polls.py
```

Polls require editorial review before they are committed and used in the model.

---

## Files

| File | Change |
|---|---|
| `scripts/fetch_polls.py` | New script |
| `data/raw/polls/polls.csv` | Replaced on each run |
| `data/raw/polls/polls.json` | Created/updated on each run |
| `tests/scripts/test_fetch_polls.py` | New test file |
