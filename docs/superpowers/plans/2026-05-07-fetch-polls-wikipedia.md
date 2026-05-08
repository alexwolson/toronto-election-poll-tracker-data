# fetch_polls.py — Wikipedia Poll Fetcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/fetch_polls.py` that fetches Toronto 2026 mayoral polling tables from Wikipedia via the Wikimedia REST API and writes a clean `data/raw/polls/polls.csv`, replacing the existing file entirely.

**Architecture:** Three pure parsing layers (date/share helpers → slug mapping + table detection → full HTML parse) topped by output writing and a thin HTTP fetch. Each layer is tested in isolation using fixture HTML — no HTTP calls in tests. Follows the `importlib.util` module-loading pattern used by `tests/model/test_fetch_candidates.py`.

**Tech Stack:** Python 3.12, requests, BeautifulSoup4 (lxml parser), pandas. All already in `pyproject.toml`.

---

## File Map

| File | Change |
|---|---|
| `scripts/fetch_polls.py` | Create — full script |
| `tests/scripts/__init__.py` | Create — empty, makes directory a package |
| `tests/scripts/test_fetch_polls.py` | Create — all tests |

---

## Task 1: Script skeleton + date/share parsing

**Context:** Establish the file layout, constants, and the two simplest pure functions. Everything in later tasks depends on these.

**Files:**
- Create: `scripts/fetch_polls.py`
- Create: `tests/scripts/__init__.py`
- Create: `tests/scripts/test_fetch_polls.py`

---

- [ ] **Step 1: Create the empty test package**

```bash
touch /Users/alex/code/projects/toronto-election/toronto-election-poll-tracker-data/tests/scripts/__init__.py
```

- [ ] **Step 2: Write failing tests for `_parse_date` and `_parse_share`**

Create `tests/scripts/test_fetch_polls.py`:

```python
"""Tests for fetch_polls.py parsing logic."""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def fp():
    path = _REPO_ROOT / "scripts" / "fetch_polls.py"
    spec = importlib.util.spec_from_file_location("scripts.fetch_polls", str(path))
    assert spec is not None, f"Could not load fetch_polls.py — expected at {path}"
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_parse_date_april(fp):
    assert fp._parse_date("April 13, 2026") == "2026-04-13"


def test_parse_date_march(fp):
    assert fp._parse_date("March 8, 2026") == "2026-03-08"


def test_parse_date_invalid(fp):
    with pytest.raises(ValueError, match="Unparseable poll date"):
        fp._parse_date("not-a-date")


def test_parse_share_percentage(fp):
    assert fp._parse_share("46%") == pytest.approx(0.46)


def test_parse_share_bold_stripped(fp):
    # get_text() strips bold tags, but share value may still have bold marker
    assert fp._parse_share("35%") == pytest.approx(0.35)


def test_parse_share_em_dash(fp):
    assert fp._parse_share("—") is None


def test_parse_share_empty(fp):
    assert fp._parse_share("") is None


def test_parse_share_small_value(fp):
    assert fp._parse_share("8%") == pytest.approx(0.08)
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/alex/code/projects/toronto-election/toronto-election-poll-tracker-data
uv run pytest tests/scripts/test_fetch_polls.py -v
```

Expected: FAIL — `scripts/fetch_polls.py` doesn't exist yet.

- [ ] **Step 4: Create `scripts/fetch_polls.py` with the skeleton and two functions**

```python
#!/usr/bin/env python3
"""Fetch Toronto 2026 mayoral election polls from Wikipedia.

Fetches polling tables from the Wikipedia article via the Wikimedia REST API
and writes a clean polls.csv to data/raw/polls/, replacing any existing file.
Wikipedia is treated as authoritative.

Outputs:
  data/raw/polls/polls.csv  -- all polls from Wikipedia
  data/raw/polls/polls.json -- sidecar with fetch timestamp

Run: uv run scripts/fetch_polls.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

WIKIPEDIA_URL = (
    "https://en.wikipedia.org/api/rest_v1/page/html/2026_Toronto_mayoral_election"
)
USER_AGENT = (
    "toronto-election-poll-tracker/1.0"
    " (https://github.com/alexwolson/toronto-election-poll-tracker-data)"
)

OUTPUT_DIR = Path("data/raw/polls")

FIRM_SLUG: dict[str, str] = {
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

CANDIDATE_SLUG: dict[str, str] = {
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

METADATA_COLS = [
    "poll_id", "firm", "date_conducted", "date_published",
    "sample_size", "methodology", "field_tested",
]
ALL_CANDIDATE_COLS = [
    "bailao", "bradford", "chow", "furey", "ford",
    "mendicino", "tory", "other", "undecided",
]
_SKIP_COLS = frozenset({"Polling Firm", "Methodology", "Poll Date", "Sample Size", "MOE", "Lead"})


def _parse_date(s: str) -> str:
    """Convert 'April 13, 2026' to '2026-04-13'."""
    try:
        return datetime.strptime(s.strip(), "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Unparseable poll date: {s!r}") from exc


def _parse_share(s: str) -> float | None:
    """Convert '46%' to 0.46; '—' or '' to None."""
    s = s.strip()
    if not s or s == "—" or s == "—":
        return None
    s = s.rstrip("%").strip()
    if not s:
        return None
    try:
        return round(float(s) / 100, 4)
    except ValueError as exc:
        raise ValueError(f"Unparseable share value: {s!r}") from exc
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/scripts/test_fetch_polls.py -v
```

Expected: 8 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/fetch_polls.py tests/scripts/__init__.py tests/scripts/test_fetch_polls.py
git commit -m "feat: add fetch_polls skeleton with date/share parsing (TDD)"
```

---

## Task 2: Slug mapping + table detection

**Context:** Add the functions that map firm names and candidate column headers to slugs, and detect which wikitables contain polling data. These are tested using small BeautifulSoup objects constructed from inline HTML strings.

**Files:**
- Modify: `scripts/fetch_polls.py` (append functions after `_parse_share`)
- Modify: `tests/scripts/test_fetch_polls.py` (append tests)

---

- [ ] **Step 1: Write failing tests**

Append to `tests/scripts/test_fetch_polls.py`:

```python
from bs4 import BeautifulSoup


def test_firm_slug_known(fp):
    assert fp._firm_slug("Liaison Strategies") == "liaison"


def test_firm_slug_variant(fp):
    assert fp._firm_slug("Pallas") == "pallas"


def test_firm_slug_unknown(fp):
    with pytest.raises(ValueError, match="Unknown polling firm"):
        fp._firm_slug("Mystery Pollsters Inc.")


def test_candidate_col_names_maps_known(fp):
    headers = ["Polling Firm", "Methodology", "Poll Date", "Sample Size", "MOE",
               "Bradford", "Chow", "Lead"]
    result = fp._candidate_col_names(headers)
    assert result == {"Bradford": "bradford", "Chow": "chow"}


def test_candidate_col_names_skips_metadata(fp):
    headers = ["Polling Firm", "Poll Date", "MOE", "Lead"]
    assert fp._candidate_col_names(headers) == {}


def _make_table(headers: list[str]) -> "BeautifulSoup":
    ths = "".join(f"<th>{h}</th>" for h in headers)
    html = f"<table class='wikitable'><tbody><tr>{ths}</tr></tbody></table>"
    return BeautifulSoup(html, "lxml").find("table")


def test_is_polling_table_true(fp):
    table = _make_table(["Polling Firm", "Methodology", "Poll Date", "Sample Size"])
    assert fp._is_polling_table(table) is True


def test_is_polling_table_false_missing_poll_date(fp):
    table = _make_table(["Polling Firm", "Methodology", "Sample Size"])
    assert fp._is_polling_table(table) is False


def test_is_polling_table_false_non_polling(fp):
    table = _make_table(["Candidate", "Party", "Status"])
    assert fp._is_polling_table(table) is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/scripts/test_fetch_polls.py -v
```

Expected: 8 passed (Task 1), ~7 new FAIL.

- [ ] **Step 3: Implement the three functions**

Append to `scripts/fetch_polls.py` after `_parse_share`:

```python
def _cell_text(cell) -> str:
    """Extract plain text from a BeautifulSoup td/th cell."""
    return cell.get_text(strip=True)


def _firm_slug(firm: str) -> str:
    """Map a Wikipedia firm name to its poll_id slug."""
    firm = firm.strip()
    if firm not in FIRM_SLUG:
        raise ValueError(
            f"Unknown polling firm: {firm!r}. Add it to FIRM_SLUG in fetch_polls.py."
        )
    return FIRM_SLUG[firm]


def _candidate_col_names(headers: list[str]) -> dict[str, str]:
    """Return {header_name: candidate_slug} for all candidate share columns.

    Skips metadata and non-share columns (Polling Firm, MOE, Lead, etc.).
    Falls back to lowercased slug for names not in CANDIDATE_SLUG.
    """
    result: dict[str, str] = {}
    for h in headers:
        if h in _SKIP_COLS:
            continue
        result[h] = CANDIDATE_SLUG.get(h, h.lower().replace(" ", "_"))
    return result


def _is_polling_table(table) -> bool:
    """Return True if this wikitable contains polling data."""
    headers = {_cell_text(th) for th in table.find_all("th")}
    return "Polling Firm" in headers and "Poll Date" in headers
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/scripts/test_fetch_polls.py -v
```

Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_polls.py tests/scripts/test_fetch_polls.py
git commit -m "feat: add firm/candidate slug mapping and table detection"
```

---

## Task 3: Full HTML parsing (`_parse_table` + `parse_polls`)

**Context:** Parse complete wikitables into poll row dicts. Tested against a minimal fixture HTML string that mimics the Wikipedia page structure: one main multi-candidate table, one head-to-head table, and one non-polling table (to verify it is skipped).

**Files:**
- Modify: `scripts/fetch_polls.py` (append functions)
- Modify: `tests/scripts/test_fetch_polls.py` (append tests + fixture)

---

- [ ] **Step 1: Write failing tests**

Append to `tests/scripts/test_fetch_polls.py`:

```python
FIXTURE_HTML = """
<html><body>
<table class="wikitable">
<tbody>
<tr>
<th>Polling Firm</th><th>Methodology</th><th>Poll Date</th>
<th>Sample Size</th><th>MOE</th>
<th>Bradford</th><th>Chow</th><th>Furey</th><th>Lead</th>
</tr>
<tr>
<td>Liaison Strategies</td><td>IVR</td><td>April 13, 2026</td>
<td>1000</td><td>±3.1%</td>
<td>35%</td><td>46%</td><td>11%</td><td>11</td>
</tr>
<tr>
<td>Pallas Data</td><td>IVR</td><td>March 8, 2026</td>
<td>735</td><td>±3.6%</td>
<td>26%</td><td>44%</td><td>—</td><td>18</td>
</tr>
</tbody>
</table>
<table class="wikitable">
<tbody>
<tr>
<th>Polling Firm</th><th>Methodology</th><th>Poll Date</th>
<th>Sample Size</th><th>MOE</th>
<th>Bradford</th><th>Chow</th><th>Lead</th>
</tr>
<tr>
<td>Pallas Data</td><td>IVR</td><td>March 8, 2026</td>
<td>735</td><td>±3.6%</td>
<td>38%</td><td>47%</td><td>9</td>
</tr>
</tbody>
</table>
<table class="wikitable">
<tbody>
<tr><th>Candidate</th><th>Party</th></tr>
<tr><td>Someone</td><td>Independent</td></tr>
</tbody>
</table>
</body></html>
"""

DUPLICATE_HTML = """
<html><body>
<table class="wikitable">
<tbody>
<tr>
<th>Polling Firm</th><th>Methodology</th><th>Poll Date</th>
<th>Sample Size</th><th>MOE</th><th>Bradford</th><th>Chow</th><th>Lead</th>
</tr>
<tr>
<td>Liaison Strategies</td><td>IVR</td><td>April 13, 2026</td>
<td>1000</td><td>±3.1%</td><td>35%</td><td>46%</td><td>11</td>
</tr>
<tr>
<td>Liaison Strategies</td><td>IVR</td><td>April 13, 2026</td>
<td>1000</td><td>±3.1%</td><td>35%</td><td>46%</td><td>11</td>
</tr>
</tbody>
</table>
</body></html>
"""

EMPTY_HTML = "<html><body><p>No tables here.</p></body></html>"


def test_parse_polls_multi_candidate_count(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    main_rows = [r for r in rows if "v" not in r["poll_id"].split("-", 2)[-1]]
    assert len(main_rows) == 2


def test_parse_polls_multi_candidate_poll_id(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    ids = [r["poll_id"] for r in rows]
    assert "liaison-2026-04-13" in ids


def test_parse_polls_multi_candidate_shares(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if r["poll_id"] == "liaison-2026-04-13")
    assert row["chow"] == pytest.approx(0.46)
    assert row["bradford"] == pytest.approx(0.35)
    assert row["furey"] == pytest.approx(0.11)


def test_parse_polls_multi_candidate_missing_share(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if r["poll_id"] == "pallas-2026-03-08")
    assert row["furey"] is None


def test_parse_polls_multi_candidate_field_tested(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if r["poll_id"] == "liaison-2026-04-13")
    # field_tested should be sorted comma-joined slugs with values
    assert row["field_tested"] == "bradford,chow,furey"


def test_parse_polls_multi_candidate_sample_size(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if r["poll_id"] == "liaison-2026-04-13")
    assert row["sample_size"] == 1000


def test_parse_polls_head_to_head_poll_id(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    ids = [r["poll_id"] for r in rows]
    assert "pallas-2026-03-08-bradford-v-chow" in ids


def test_parse_polls_head_to_head_shares(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if "bradford-v-chow" in r["poll_id"])
    assert row["bradford"] == pytest.approx(0.38)
    assert row["chow"] == pytest.approx(0.47)


def test_parse_polls_skips_non_polling_table(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    assert len(rows) == 3  # 2 main + 1 head-to-head


def test_parse_polls_duplicate_id_raises(fp):
    with pytest.raises(ValueError, match="Duplicate poll_id"):
        fp.parse_polls(DUPLICATE_HTML)


def test_parse_polls_no_tables_raises(fp):
    with pytest.raises(RuntimeError, match="No polling tables found"):
        fp.parse_polls(EMPTY_HTML)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/scripts/test_fetch_polls.py -v
```

Expected: 15 passed (Tasks 1–2), ~11 new FAIL.

- [ ] **Step 3: Implement `_parse_table` and `parse_polls`**

Append to `scripts/fetch_polls.py` after `_is_polling_table`:

```python
def _parse_table(table) -> list[dict]:
    """Parse one polling wikitable into a list of poll row dicts."""
    all_th = table.find_all("th")
    headers = [_cell_text(th) for th in all_th]

    cand_map = _candidate_col_names(headers)
    is_head_to_head = len(cand_map) == 2

    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue  # header row or too short to be a data row

        row_data = dict(zip(headers, [_cell_text(c) for c in cells]))

        firm = row_data.get("Polling Firm", "").strip()
        if not firm:
            continue

        slug = _firm_slug(firm)
        date = _parse_date(row_data["Poll Date"])

        shares: dict[str, float | None] = {}
        for h, cand_slug in cand_map.items():
            shares[cand_slug] = _parse_share(row_data.get(h, ""))

        field_tested = ",".join(sorted(s for s, v in shares.items() if v is not None))

        if is_head_to_head:
            cand_slugs = sorted(shares.keys())
            poll_id = f"{slug}-{date}-{'-v-'.join(cand_slugs)}"
        else:
            poll_id = f"{slug}-{date}"

        raw_n = row_data.get("Sample Size", "").replace(",", "").strip()
        sample_size = int(raw_n) if raw_n.isdigit() else None

        rows.append({
            "poll_id": poll_id,
            "firm": firm,
            "date_conducted": date,
            "date_published": date,
            "sample_size": sample_size,
            "methodology": row_data.get("Methodology", "").strip(),
            "field_tested": field_tested,
            **shares,
            "notes": "",
        })

    return rows


def parse_polls(html: str) -> list[dict]:
    """Parse all polling tables from Wikipedia HTML. Returns list of poll dicts."""
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)

    all_rows: list[dict] = []
    seen_ids: set[str] = set()

    for table in tables:
        if not _is_polling_table(table):
            continue
        for row in _parse_table(table):
            if row["poll_id"] in seen_ids:
                raise ValueError(
                    f"Duplicate poll_id: {row['poll_id']!r} — "
                    "two tables produced the same ID."
                )
            seen_ids.add(row["poll_id"])
            all_rows.append(row)

    if not all_rows:
        raise RuntimeError(
            "No polling tables found — the Wikipedia page structure may have changed."
        )

    return all_rows
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/scripts/test_fetch_polls.py -v
```

Expected: 26 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_polls.py tests/scripts/test_fetch_polls.py
git commit -m "feat: implement full Wikipedia polling table parser"
```

---

## Task 4: Output writing + HTTP fetch + `main()`

**Context:** Write the DataFrame to CSV with canonical column ordering and a JSON sidecar, following the exact pattern used by all other fetch scripts. Add a thin `fetch_html()` wrapper and a `main()` entry point. Test output writing using pytest's built-in `tmp_path` fixture.

**Files:**
- Modify: `scripts/fetch_polls.py` (append functions + `if __name__ == "__main__"` block)
- Modify: `tests/scripts/test_fetch_polls.py` (append output tests)

---

- [ ] **Step 1: Write failing tests**

Append to `tests/scripts/test_fetch_polls.py`:

```python
import json
import pandas as pd


MINIMAL_ROWS = [
    {
        "poll_id": "liaison-2026-04-13",
        "firm": "Liaison Strategies",
        "date_conducted": "2026-04-13",
        "date_published": "2026-04-13",
        "sample_size": 1000,
        "methodology": "IVR",
        "field_tested": "bradford,chow,furey",
        "bradford": 0.35,
        "chow": 0.46,
        "furey": 0.11,
        "notes": "",
    }
]


def test_write_output_creates_csv(fp, tmp_path):
    fp.write_output(MINIMAL_ROWS, tmp_path)
    assert (tmp_path / "polls.csv").exists()


def test_write_output_csv_content(fp, tmp_path):
    fp.write_output(MINIMAL_ROWS, tmp_path)
    df = pd.read_csv(tmp_path / "polls.csv")
    assert len(df) == 1
    assert df.iloc[0]["poll_id"] == "liaison-2026-04-13"
    assert df.iloc[0]["chow"] == pytest.approx(0.46)


def test_write_output_csv_has_notes_column(fp, tmp_path):
    fp.write_output(MINIMAL_ROWS, tmp_path)
    df = pd.read_csv(tmp_path / "polls.csv")
    assert "notes" in df.columns


def test_write_output_sidecar_created(fp, tmp_path):
    fp.write_output(MINIMAL_ROWS, tmp_path)
    assert (tmp_path / "polls.json").exists()


def test_write_output_sidecar_has_fetched_at(fp, tmp_path):
    fp.write_output(MINIMAL_ROWS, tmp_path)
    data = json.loads((tmp_path / "polls.json").read_text())
    assert "fetched_at" in data


def test_write_output_column_order(fp, tmp_path):
    fp.write_output(MINIMAL_ROWS, tmp_path)
    df = pd.read_csv(tmp_path / "polls.csv")
    cols = list(df.columns)
    assert cols[0] == "poll_id"
    assert cols[1] == "firm"
    # notes is last
    assert cols[-1] == "notes"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/scripts/test_fetch_polls.py -v
```

Expected: 26 passed (Tasks 1–3), ~7 new FAIL.

- [ ] **Step 3: Implement `write_output`, `fetch_html`, and `main`**

Append to `scripts/fetch_polls.py` after `parse_polls`:

```python
def write_output(rows: list[dict], output_dir: Path) -> None:
    """Write polls.csv and polls.json sidecar to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all candidate columns seen across all rows, in canonical order first
    seen_cands = {c for row in rows for c in row if c not in set(METADATA_COLS + ["notes"])}
    ordered_cands = [c for c in ALL_CANDIDATE_COLS if c in seen_cands]
    extra_cands = sorted(c for c in seen_cands if c not in ALL_CANDIDATE_COLS)
    cols = METADATA_COLS + ordered_cands + extra_cands + ["notes"]

    df = pd.DataFrame(rows, columns=cols)
    csv_path = output_dir / "polls.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Written: {csv_path} ({len(df)} rows)")

    sidecar_path = output_dir / "polls.json"
    sidecar_path.write_text(
        json.dumps({"fetched_at": datetime.now(timezone.utc).isoformat()}, indent=2),
        encoding="utf-8",
    )
    print(f"  Written: {sidecar_path}")


def fetch_html() -> str:
    """Fetch Wikipedia page HTML via the Wikimedia REST API."""
    r = requests.get(
        WIKIPEDIA_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    r.raise_for_status()
    return r.text


def main() -> None:
    print("Fetching Wikipedia polling page...")
    html = fetch_html()
    print("Parsing polling tables...")
    rows = parse_polls(html)
    print(f"Found {len(rows)} polls")
    write_output(rows, OUTPUT_DIR)
    print("Done.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
uv run pytest tests/scripts/test_fetch_polls.py -v
```

Expected: 33 passed.

- [ ] **Step 5: Run the full test suite to confirm no regressions**

```bash
uv run pytest -v
```

Expected: all existing tests still pass.

- [ ] **Step 6: Smoke test — run the script against live Wikipedia**

```bash
uv run scripts/fetch_polls.py
```

Expected output:
```
Fetching Wikipedia polling page...
Parsing polling tables...
Found N polls
  Written: data/raw/polls/polls.csv (N rows)
  Written: data/raw/polls/polls.json
Done.
```

Inspect `data/raw/polls/polls.csv` — verify the row count and spot-check a few values against the live Wikipedia page.

- [ ] **Step 7: Commit**

```bash
git add scripts/fetch_polls.py tests/scripts/test_fetch_polls.py data/raw/polls/polls.csv data/raw/polls/polls.json
git commit -m "feat: implement fetch_polls.py — Wikipedia poll fetcher"
```
