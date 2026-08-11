#!/usr/bin/env python3
"""Fetch Toronto mayoral polling/outcomes used for forecast backtesting.

The output is long-form and records the ballot offered by every row.  The
Wikimedia article URL is retained as the source for each observation; the
source tables themselves link through to the underlying pollster releases.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "polls"
USER_AGENT = "toronto-election-model/1.0 (historical forecast calibration)"

ELECTIONS = {
    "toronto_2014": {
        "page": "2014_Toronto_mayoral_election",
        "election_date": "2014-10-27",
        "poll_tables": [6, 7],
        "outcome_table": 3,
        "final_field": {"chow", "doug_ford", "tory"},
    },
    "toronto_2018": {
        "page": "2018_Toronto_mayoral_election",
        "election_date": "2018-10-22",
        "poll_tables": [5],
        "outcome_table": 7,
        "final_field": {"keesmaat", "tory"},
    },
    "toronto_2022": {
        "page": "2022_Toronto_mayoral_election",
        "election_date": "2022-10-24",
        "poll_tables": [4],
        "outcome_table": 5,
        "final_field": {"acton", "brown", "penalosa", "tory"},
    },
    "toronto_2023": {
        "page": "2023_Toronto_mayoral_by-election",
        "election_date": "2023-06-26",
        "poll_tables": [7, 8],
        "outcome_table": 9,
        "final_field": {
            "bailao", "bradford", "brown", "chow", "furey", "hunter", "matlow", "saunders"
        },
    },
}

NAME_IDS = {
    "ana bailao": "bailao",
    "ana bailão": "bailao",
    "blake acton": "acton",
    "brad bradford": "bradford",
    "chloe brown": "brown",
    "doug ford": "doug_ford",
    "d. ford": "doug_ford",
    "gil penalosa": "penalosa",
    "gil peñalosa": "penalosa",
    "jennifer keesmaat": "keesmaat",
    "keesmaat": "keesmaat",
    "john tory": "tory",
    "tory": "tory",
    "josh matlow": "matlow",
    "mark saunders": "saunders",
    "mitzie hunter": "hunter",
    "olivia chow": "chow",
    "chow": "chow",
    "rob ford": "rob_ford",
    "r. ford": "rob_ford",
    "anthony furey": "furey",
    "david soknacki": "soknacki",
    "soknacki": "soknacki",
    "karen stintz": "stintz",
    "stintz": "stintz",
}


def _plain(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return re.sub(r"\[[^]]+\]", "", text).strip()


def _slug(value: object) -> str:
    text = re.sub(r"\s+\(X\)$", "", _plain(value), flags=re.I)
    lower = text.lower()
    if lower in NAME_IDS:
        return NAME_IDS[lower]
    ascii_name = unicodedata.normalize("NFKD", lower).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", ascii_name).strip("_")


def _flatten(table: pd.DataFrame) -> pd.DataFrame:
    result = table.copy()
    if isinstance(result.columns, pd.MultiIndex):
        first_level = [str(column[0]) for column in result.columns]
        use_second = len(set(first_level)) == 1
        result.columns = [
            str(column[1] if use_second else column[0]) for column in result.columns
        ]
    return result


def _date(value: object) -> str | None:
    text = _plain(value).replace("—", "-")
    range_match = re.match(r"^([A-Za-z]+)\s+\d+\s*[–-]\s*(\d+),\s*(\d{4})$", text)
    if range_match:
        text = f"{range_match.group(1)} {range_match.group(2)}, {range_match.group(3)}"
    parsed = pd.to_datetime(text, errors="coerce")
    return None if pd.isna(parsed) else parsed.date().isoformat()


def _share(value: object) -> float | None:
    text = _plain(value).replace("−", "-").replace("–", "-")
    if not text or text in {"-", "—", "N/a", "nan"}:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%?", text)
    if not match:
        return None
    number = float(match.group(1))
    # Wikipedia tables sometimes encode tiny shares as "<1%". The percent
    # sign, not the numeric magnitude, determines the unit.
    return number / 100.0 if "%" in text or number > 1.0 else number


def _outcome_share(value: object) -> float | None:
    """Election-result tables always express their share column as percent."""
    text = _plain(value)
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return None if not match else float(match.group(1)) / 100.0


def _sample(value: object) -> int | None:
    text = re.sub(r"[^0-9]", "", _plain(value))
    return int(text) if text else None


def _table_columns(table: pd.DataFrame) -> tuple[str, str | None, str | None, list[str]]:
    columns = list(table.columns)
    firm = next(column for column in columns if "Polling firm" in column)
    date = next(column for column in columns if "date of poll" in column.lower() or "date of polling" in column.lower())
    sample = next((column for column in columns if "sample" in column.lower()), None)
    metadata = {firm, date, sample, "Link", "Source", "MoE", "MOE"}
    candidates = [column for column in columns if column not in metadata]
    return firm, date, sample, candidates


def _fetch_tables(page: str) -> tuple[list[pd.DataFrame], str]:
    source_url = f"https://en.wikipedia.org/wiki/{page}"
    api_url = f"https://en.wikipedia.org/api/rest_v1/page/html/{page}"
    response = requests.get(api_url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return pd.read_html(StringIO(response.text)), source_url


def build_history() -> tuple[pd.DataFrame, pd.DataFrame]:
    poll_rows: list[dict] = []
    outcome_rows: list[dict] = []
    for election_id, config in ELECTIONS.items():
        tables, source_url = _fetch_tables(str(config["page"]))
        for table_index in config["poll_tables"]:
            table = _flatten(tables[int(table_index)])
            firm_column, date_column, sample_column, candidate_columns = _table_columns(table)
            for row_number, row in table.iterrows():
                firm = _plain(row.get(firm_column))
                published = _date(row.get(date_column))
                if not firm or not published:
                    continue
                offered: list[tuple[str, str, float]] = []
                residual = 0.0
                for column in candidate_columns:
                    value = _share(row.get(column))
                    if value is None:
                        continue
                    if "other" in column.lower() or "don't know" in column.lower():
                        residual += value
                    else:
                        offered.append((_slug(column), _plain(column), value))
                if not offered:
                    continue
                # Published tables occasionally omit undecided; preserve the
                # full denominator by adding the unreported remainder.
                residual = max(residual, 1.0 - sum(value for _, _, value in offered))
                total = sum(value for _, _, value in offered) + residual
                if total <= 0:
                    continue
                # Published whole-number percentages can sum to 99%, 101%, or
                # 102% through rounding. Normalise the modelling view while
                # retaining the source values' relative proportions.
                offered = [
                    (candidate_id, candidate_name, value / total)
                    for candidate_id, candidate_name, value in offered
                ]
                residual /= total
                signature = ",".join(sorted(candidate_id for candidate_id, _, _ in offered))
                digest = hashlib.sha1(f"{firm}|{published}|{signature}|{row_number}".encode()).hexdigest()[:8]
                poll_id = f"{election_id}-{published}-{digest}"
                common = {
                    "election_id": election_id,
                    "election_date": config["election_date"],
                    "poll_id": poll_id,
                    "firm": firm,
                    "date_published": published,
                    "sample_size": _sample(row.get(sample_column)) if sample_column else None,
                    "field_tested": signature,
                    "source_url": source_url,
                }
                for candidate_id, candidate_name, value in offered:
                    poll_rows.append({
                        **common,
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "share": round(value, 4),
                        "is_residual": False,
                    })
                poll_rows.append({
                    **common,
                    "candidate_id": "residual",
                    "candidate_name": "Other / undecided",
                    "share": round(min(1.0, residual), 4),
                    "is_residual": True,
                })

        outcome = _flatten(tables[int(config["outcome_table"])])
        candidate_column = next(column for column in outcome.columns if "candidate" in column.lower())
        share_column = next(column for column in outcome.columns if "%" in column.lower() or "popular vote" in column.lower())
        final_field = set(config["final_field"])
        residual_share = 0.0
        for _, row in outcome.iterrows():
            candidate_name = _plain(row.get(candidate_column))
            share = _outcome_share(row.get(share_column))
            if not candidate_name or candidate_name.lower() == "total" or share is None:
                continue
            candidate_id = _slug(candidate_name)
            if candidate_id in final_field:
                outcome_rows.append({
                    "election_id": election_id,
                    "election_date": config["election_date"],
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "share": round(share, 4),
                    "is_residual": False,
                    "source_url": source_url,
                })
            else:
                residual_share += share
        outcome_rows.append({
            "election_id": election_id,
            "election_date": config["election_date"],
            "candidate_id": "residual",
            "candidate_name": "Other candidates",
            "share": round(residual_share, 4),
            "is_residual": True,
            "source_url": source_url,
        })

    polls = pd.DataFrame(poll_rows).sort_values(["election_id", "date_published", "poll_id", "candidate_id"])
    outcomes = pd.DataFrame(outcome_rows).sort_values(["election_id", "candidate_id"])
    return polls, outcomes


def main() -> None:
    polls, outcomes = build_history()
    RAW.mkdir(parents=True, exist_ok=True)
    polls.to_csv(RAW / "historical_mayoral_polls.csv", index=False)
    outcomes.to_csv(RAW / "historical_mayoral_outcomes.csv", index=False)
    print(f"Wrote {polls['poll_id'].nunique()} historical polls across {polls['election_id'].nunique()} elections")


if __name__ == "__main__":
    main()
