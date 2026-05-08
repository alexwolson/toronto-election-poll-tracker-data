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
import re
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

FIRM_DISPLAY_NAME: dict[str, str] = {
    "liaison": "Liaison Strategies",
    "pallas": "Pallas Data",
    "mainstreet": "Mainstreet Research",
    "canadapulse": "Canada Pulse Insights/CityNews",
    "forum": "Forum Research",
    "ipsos": "Ipsos",
    "abacus": "Abacus Data",
}

CANDIDATE_SLUG: dict[str, str] = {
    # Short-name form (used in test fixtures)
    "Bailão": "bailao",
    "Bradford": "bradford",
    "Chow": "chow",
    "Furey": "furey",
    "Ford": "ford",
    "Mendicino": "mendicino",
    "Tory": "tory",
    "Other": "other",
    "Undecided": "undecided",
    # Full-name form (used on live Wikipedia)
    "Ana Bailão": "bailao",
    "Brad Bradford": "bradford",
    "Olivia Chow": "chow",
    "Anthony Furey": "furey",
    "Michael Ford": "ford",
    "Marco Mendicino": "mendicino",
    "John Tory": "tory",
}

METADATA_COLS = [
    "poll_id", "firm", "date_conducted", "date_published",
    "sample_size", "methodology", "field_tested",
]
ALL_CANDIDATE_COLS = [
    "bailao", "bradford", "chow", "furey", "ford",
    "mendicino", "tory", "other", "undecided",
]
# Columns to skip when collecting candidate share columns — both fixture and live forms
_SKIP_COLS = frozenset({
    # Test fixture header names
    "Polling Firm", "Methodology", "Poll Date", "Sample Size", "MOE", "Lead",
    # Live Wikipedia header names
    "Polling firm", "Source", "Date of poll", "Sample size",
})
# Columns that indicate a header row — both fixture and live forms
_KNOWN_HEADER_COLS = frozenset({
    "Polling Firm", "Poll Date", "Sample Size", "Methodology",
    "Polling firm", "Date of poll", "Sample size", "Source",
})
# Maps header name → row_data key for firm column (case variants)
_FIRM_HEADER_VARIANTS = ("Polling Firm", "Polling firm")
# Maps header name → row_data key for date column (case variants)
_DATE_HEADER_VARIANTS = ("Poll Date", "Date of poll")
# Maps header name → row_data key for sample size column
_SAMPLE_HEADER_VARIANTS = ("Sample Size", "Sample size")
# Maps header name → row_data key for methodology column
_METHODOLOGY_HEADER_VARIANTS = ("Methodology", "Source")
# Sentinel texts in the Polling Firm column that identify non-data rows
_NON_DATA_FIRM_TEXTS = frozenset({"Polling firm", "Polling Firm"})


def _parse_date(s: str) -> str:
    """Convert 'April 13, 2026' or '13 April 2026' to '2026-04-13'."""
    s = s.strip()
    for fmt in ("%B %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError(f"Unparseable poll date: {s!r}")


def _parse_share(s: str) -> float | None:
    """Convert '46%' to 0.46; '—', '–', '—N/a', or '' to None."""
    s = s.strip()
    if not s:
        return None
    # em-dash / en-dash, with or without trailing text (e.g. '—N/a')
    if s.startswith(("—", "–")):
        return None
    s = s.rstrip("%").strip()
    if not s:
        return None
    try:
        return round(float(s) / 100, 4)
    except ValueError as exc:
        raise ValueError(f"Unparseable share value: {s!r}") from exc


def _cell_text(cell) -> str:
    """Extract plain text from a BeautifulSoup td/th cell, stripping footnote markers."""
    text = cell.get_text(strip=True)
    return re.sub(r"\[.*?\]", "", text).strip()


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
        if not h.strip():
            continue
        if h in _SKIP_COLS:
            continue
        result[h] = CANDIDATE_SLUG.get(h, h.lower().replace(" ", "_"))
    return result


def _is_polling_table(table) -> bool:
    """Return True if this wikitable contains polling data."""
    for tr in table.find_all("tr"):
        ths = tr.find_all("th")
        if not ths:
            continue
        headers = {_cell_text(th) for th in ths}
        if not (headers & _KNOWN_HEADER_COLS):
            continue  # colspan section header row — skip
        has_firm = bool(headers & set(_FIRM_HEADER_VARIANTS))
        has_date = bool(headers & set(_DATE_HEADER_VARIANTS))
        return has_firm and has_date
    return False


def _normalise_methodology(s: str) -> str:
    """Lowercase methodology; preserve IVR as uppercase acronym."""
    low = s.lower()
    return "IVR" if low == "ivr" else low


def _resolve_header(row_data: dict, variants: tuple[str, ...], default: str = "") -> str:
    """Return first matching value from row_data given a list of header name variants."""
    for v in variants:
        if v in row_data:
            return row_data[v]
    return default


def _parse_table(table) -> list[dict]:
    """Parse one polling wikitable into a list of poll row dicts."""
    # Extract headers from the first <tr> containing <th> elements
    headers: list[str] = []
    for tr in table.find_all("tr"):
        ths = tr.find_all("th")
        if ths:
            candidate_texts = [_cell_text(th) for th in ths]
            if any(t in _KNOWN_HEADER_COLS for t in candidate_texts):
                headers = candidate_texts
                break

    cand_map = _candidate_col_names(headers)
    is_head_to_head = len(cand_map) == 2

    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue  # header row or too short

        cell_texts = [_cell_text(c) for c in cells]
        if len(cell_texts) != len(headers):
            continue  # rowspan artifact — cell count doesn't match headers
        row_data = dict(zip(headers, cell_texts))

        firm = _resolve_header(row_data, _FIRM_HEADER_VARIANTS).strip()
        if not firm or firm in _NON_DATA_FIRM_TEXTS:
            continue

        slug = _firm_slug(firm)
        firm = FIRM_DISPLAY_NAME[slug]  # normalise to canonical display name
        date_str = _resolve_header(row_data, _DATE_HEADER_VARIANTS)
        date = _parse_date(date_str)

        shares: dict[str, float | None] = {}
        for h, cand_slug in cand_map.items():
            try:
                shares[cand_slug] = _parse_share(row_data.get(h, ""))
            except ValueError:
                shares[cand_slug] = None

        field_tested = ",".join(sorted(s for s, v in shares.items() if v is not None))

        if is_head_to_head:
            cand_slugs = sorted(shares.keys())
            poll_id = f"{slug}-{date}-{'-v-'.join(cand_slugs)}"
        else:
            poll_id = f"{slug}-{date}"

        raw_n = _resolve_header(row_data, _SAMPLE_HEADER_VARIANTS).replace(",", "").strip()
        sample_size = int(raw_n) if raw_n.isdigit() else None

        methodology_raw = _resolve_header(row_data, _METHODOLOGY_HEADER_VARIANTS).strip()

        rows.append({
            "poll_id": poll_id,
            "firm": firm,
            "date_conducted": date,
            "date_published": date,
            "sample_size": sample_size,
            "methodology": _normalise_methodology(methodology_raw),
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


def write_output(rows: list[dict], output_dir: Path) -> None:
    """Write polls.csv and polls.json sidecar to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

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
        json.dumps({"fetched_at": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n",
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
