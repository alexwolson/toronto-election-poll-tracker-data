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
    if not s or s in {"—", "–"}:  # U+2014 em-dash, U+2013 en-dash
        return None
    s = s.rstrip("%").strip()
    if not s:
        return None
    try:
        return round(float(s) / 100, 4)
    except ValueError as exc:
        raise ValueError(f"Unparseable share value: {s!r}") from exc
