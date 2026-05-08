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
_KNOWN_HEADER_COLS = frozenset({"Polling Firm", "Poll Date", "Sample Size", "Methodology"})


def _parse_date(s: str) -> str:
    """Convert 'April 13, 2026' to '2026-04-13'."""
    try:
        return datetime.strptime(s.strip(), "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Unparseable poll date: {s!r}") from exc


def _parse_share(s: str) -> float | None:
    """Convert '46%' to 0.46; '—' or '' to None."""
    s = s.strip()
    if not s or s in {"—", "–"}:  # U+2014 em-dash, U+2013 en-dash
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
        if ths:
            headers = {_cell_text(th) for th in ths}
            return "Polling Firm" in headers and "Poll Date" in headers
    return False


def _normalise_methodology(s: str) -> str:
    """Lowercase methodology; preserve IVR as uppercase acronym."""
    low = s.lower()
    return "IVR" if low == "ivr" else low


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

        firm = row_data.get("Polling Firm", "").strip()
        if not firm:
            continue

        slug = _firm_slug(firm)
        date = _parse_date(row_data["Poll Date"])

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

        raw_n = row_data.get("Sample Size", "").replace(",", "").strip()
        sample_size = int(raw_n) if raw_n.isdigit() else None

        rows.append({
            "poll_id": poll_id,
            "firm": firm,
            "date_conducted": date,
            "date_published": date,
            "sample_size": sample_size,
            "methodology": _normalise_methodology(row_data.get("Methodology", "").strip()),
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
