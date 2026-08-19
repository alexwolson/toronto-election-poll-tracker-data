"""Canonical historical Toronto mayoral evidence behind a non-live seam.

The legacy Wikipedia-derived poll CSV is useful for discovery, but it is not
model input.  This module exposes complete official election outcomes and only
the small set of poll readings that have been re-extracted from first-party
documents.  A crosswalk keeps every legacy row auditable without promoting its
normalized shares, proxy dates, or scenario IDs to canonical observations.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final, Literal
from zoneinfo import ZoneInfo

from backend.model.poll_sources import (
    PollReading as HistoricalPollReading,
)
from backend.model.poll_sources import (
    PollResponse as HistoricalPollResponse,
)
from backend.model.poll_sources import (
    PollSample as HistoricalPollSample,
)
from backend.model.poll_sources import (
    PollSampleDocument,
    SourceDocument,
    load_poll_source_bundle,
)

_TORONTO: Final = ZoneInfo("America/Toronto")

ELECTION_COLUMNS: Final = (
    "election_cycle_id",
    "election_date",
    "election_type",
    "nomination_close_date",
    "nomination_close_status",
    "final_ballot_known_by_date",
    "final_ballot_known_by_status",
    "ballot_timing_source_url",
    "source_document_id",
    "source_url",
    "source_locator",
    "source_sha256",
    "source_completeness",
    "notes",
)

OUTCOME_COLUMNS: Final = (
    "election_cycle_id",
    "candidate_id",
    "candidate_name",
    "candidate_name_as_reported",
    "votes",
    "valid_vote_total",
    "share",
    "is_winner",
    "source_document_id",
    "source_locator",
)

CROSSWALK_COLUMNS: Final = (
    "legacy_poll_id",
    "election_cycle_id",
    "legacy_sample_proxy_key",
    "poll_sample_id",
    "poll_reading_id",
    "disposition",
    "notes",
)

_LEGACY_POLL_COLUMNS: Final = (
    "election_id",
    "election_date",
    "poll_id",
    "firm",
    "date_published",
    "sample_size",
    "field_tested",
    "source_url",
    "candidate_id",
    "candidate_name",
    "share",
    "is_residual",
)

_OFFICIAL_2014_COLUMNS: Final = (
    "candidate_name",
    "votes",
    "is_winner",
    "source_document_id",
    "source_url",
    "source_locator",
    "source_sha256",
    "source_completeness",
)

_WARD_RESULT_COLUMNS: Final = ("year", "ward", "candidate", "votes")

_KNOWN_CANDIDATE_IDS: Final = {
    "ana bailao": "bailao",
    "bailao ana": "bailao",
    "blake acton": "acton",
    "acton blake": "acton",
    "brad bradford": "bradford",
    "bradford brad": "bradford",
    "chloe brown": "brown",
    "brown chloe": "brown",
    "brown chloe marie": "brown",
    "doug ford": "doug-ford",
    "gil penalosa": "penalosa",
    "penalosa gil": "penalosa",
    "jennifer keesmaat": "keesmaat",
    "keesmaat jennifer": "keesmaat",
    "john tory": "tory",
    "tory john": "tory",
    "josh matlow": "matlow",
    "matlow josh": "matlow",
    "mark saunders": "saunders",
    "saunders mark": "saunders",
    "mitzie hunter": "hunter",
    "hunter mitzie": "hunter",
    "olivia chow": "chow",
    "chow olivia": "chow",
    "anthony furey": "furey",
    "furey anthony": "furey",
    # 2010 field (candidates who also appear in the 2010 polls)
    "rob ford": "rob-ford",
    "ford rob": "rob-ford",
    "george smitherman": "smitherman",
    "smitherman george": "smitherman",
    "joe pantalone": "pantalone",
    "pantalone joe": "pantalone",
    "rocco rossi": "rossi",
    "rossi rocco": "rossi",
    "sarah thomson": "thomson",
    "thomson sarah": "thomson",
}

_KNOWN_CANDIDATE_NAMES: Final = {
    "acton": "Blake Acton",
    "bailao": "Ana Bailão",
    "bradford": "Brad Bradford",
    "brown": "Chloe Brown",
    "chow": "Olivia Chow",
    "doug-ford": "Doug Ford",
    "furey": "Anthony Furey",
    "hunter": "Mitzie Hunter",
    "keesmaat": "Jennifer Keesmaat",
    "matlow": "Josh Matlow",
    "penalosa": "Gil Peñalosa",
    "saunders": "Mark Saunders",
    "tory": "John Tory",
    "rob-ford": "Rob Ford",
    "smitherman": "George Smitherman",
    "pantalone": "Joe Pantalone",
    "rossi": "Rocco Rossi",
    "thomson": "Sarah Thomson",
}

_ELECTION_CONFIG: Final = {
    2010: (
        "toronto_2010",
        date(2010, 10, 25),
        "general",
        "toronto_open_data_2010_results",
        "https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/96d35404-44d9-49d8-95bb-fb1e5489240d/resource/6fbfaab0-bb84-442a-8e4b-1c14d4c10d6d/download/2010-results.zip",
        "2010 Poll-by-Poll Mayor workbook; 44 ward sheets aggregated citywide",
        "",
        "official_rows_complete_artifact_not_retained",
    ),
    2014: (
        "toronto_2014",
        date(2014, 10, 27),
        "general",
        "toronto_2014_official_declaration",
        "https://www.toronto.ca/wp-content/uploads/2017/08/9059-election-2014-clerksofficialdeclarationofresults.pdf",
        "PDF pages 2-3 (printed pages 1-2)",
        "007f5055da03ce1df17cb85c6c1871a1de822c55966e4518f845905fa4b12158",
        "complete_official_candidate_totals",
    ),
    2018: (
        "toronto_2018",
        date(2018, 10, 22),
        "general",
        "toronto_open_data_2018_results",
        "https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/96d35404-44d9-49d8-95bb-fb1e5489240d/resource/2fcd5f20-90f5-4dd0-88eb-22e978b9bf89/download/2018-results.zip",
        "Mayor workbook; 25 ward sheets aggregated citywide",
        "",
        "official_rows_complete_artifact_not_retained",
    ),
    2022: (
        "toronto_2022",
        date(2022, 10, 24),
        "general",
        "toronto_open_data_2022_results",
        "https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/96d35404-44d9-49d8-95bb-fb1e5489240d/resource/3ad371de-7c51-45d3-9ea4-0b4efac5fc2b/download/2022-results.zip",
        "Mayor workbook; 25 ward sheets aggregated citywide",
        "",
        "official_rows_complete_artifact_not_retained",
    ),
    2023: (
        "toronto_2023",
        date(2023, 6, 26),
        "by_election",
        "toronto_open_data_2023_mayoral_by_election",
        "https://open.toronto.ca/dataset/elections-official-by-election-results/",
        "2023 Office of the Mayor workbook; 25 ward sheets aggregated citywide",
        "",
        "official_rows_complete_artifact_not_retained",
    ),
}

_BALLOT_TIMING: Final = {
    2010: (
        date(2010, 9, 10),
        date(2010, 9, 10),
        "statutory_deadline",
        "https://en.wikipedia.org/wiki/2010_Toronto_mayoral_election",
    ),
    2014: (
        date(2014, 9, 12),
        date(2014, 9, 15),
        "statutory_deadline",
        "https://www.toronto.ca/wp-content/uploads/2017/07/96b9-2014-election-report.pdf",
    ),
    2018: (
        date(2018, 7, 27),
        date(2018, 7, 30),
        "certification_date_reported",
        "https://www.toronto.ca/wp-content/uploads/2019/07/96b2-2018-Election-Report.pdf",
    ),
    2022: (
        date(2022, 8, 19),
        date(2022, 8, 20),
        "publicly_announced",
        "https://www.toronto.ca/news/toronto-city-clerk-certifies-372-candidates-for-october-24-municipal-election/",
    ),
    2023: (
        date(2023, 5, 12),
        date(2023, 5, 12),
        "certification_date_reported",
        "https://www.toronto.ca/news/toronto-city-clerk-certifies-102-candidates-for-june-26-by-election-for-mayor/",
    ),
}

_BALLOT_TIMING_NOTES: Final = {
    2010: (
        "The nomination period closed September 10, 2010; names could not be "
        "removed afterward (Thomson and Rossi withdrew later but stayed on the "
        "ballot), so the Final Ballot was known by nomination close. Miller did "
        "not seek re-election, so this was an open race."
    ),
    2014: (
        "September 15 is the statutory certification deadline and is used only "
        "as the conservative Final Ballot classification boundary; no exact "
        "public-release instant is asserted. Nanos fieldwork began September 16."
    ),
    2018: (
        "The July 30 certification date establishes the Final Ballot known-by "
        "boundary. The 35 certified mayoral candidates were unchanged by the "
        "subsequent council/trustee boundary disruption."
    ),
    2022: (
        "The City release establishes that the Final Ballot was publicly known "
        "by August 20; the internal Clerk action date is not modelled."
    ),
    2023: (
        "The May 12 certification date establishes the Final Ballot known-by boundary."
    ),
}

_MAPPED_LEGACY_READINGS: Final = {
    # --- Forum 2013-01-25 head-to-heads (jan25 double-read extraction) ---
    "toronto_2014-2013-01-25-d2df21f9": (
        "forum_city_2013_01_25_n1099",
        "forum_2013_jan25_release__r1",
    ),
    "toronto_2014-2013-01-25-7682463f": (
        "forum_city_2013_01_25_n1099",
        "forum_2013_jan25_release__r3",
    ),
    "toronto_2014-2013-01-25-a556e530": (
        "forum_city_2013_01_25_n1099",
        "forum_2013_jan25_release__r6",
    ),
    "toronto_2014-2013-01-25-b9d08ec1": (
        "forum_city_2013_01_25_n1099",
        "forum_2013_jan25_release__r7",
    ),
    # --- Forum 2014-03-13 (mar13 double-read extraction) ---
    "toronto_2014-2014-03-13-b2122bbc": (
        "forum_city_2014_03_13_n1271",
        "forum_2014_mar13_release__r3",
    ),
    "toronto_2014-2014-03-13-cd5b72f3": (
        "forum_city_2014_03_13_n1271",
        "forum_2014_mar13_release__r1",
    ),
    # --- Mainstreet 2014: all-voter proxy -> r1, decided-voter proxy -> r2 ---
    "toronto_2014-2014-09-12-97920e4e": (
        "mainstreet_city_2014_09_12_n1054",
        "mainstreet_2014_sep13_report__r1",
    ),
    "toronto_2014-2014-09-12-0f52b317": (
        "mainstreet_city_2014_09_12_n1054",
        "mainstreet_2014_sep13_report__r2",
    ),
    "toronto_2014-2014-09-21-0b625aeb": (
        "mainstreet_city_2014_09_21_n2469",
        "mainstreet_2014_sep21_report__r1",
    ),
    "toronto_2014-2014-09-21-fc3831be": (
        "mainstreet_city_2014_09_21_n2469",
        "mainstreet_2014_sep21_report__r2",
    ),
    "toronto_2014-2014-09-28-03741d5a": (
        "mainstreet_city_2014_09_28_n2409",
        "mainstreet_2014_sep28_report__r1",
    ),
    "toronto_2014-2014-09-28-3ea61f3e": (
        "mainstreet_city_2014_09_28_n2409",
        "mainstreet_2014_sep28_report__r2",
    ),
    "toronto_2014-2014-10-05-b15e7c6a": (
        "mainstreet_city_2014_10_05_n2379",
        "mainstreet_2014_oct05_report__r1",
    ),
    "toronto_2014-2014-10-05-4e73e0b7": (
        "mainstreet_city_2014_10_05_n2379",
        "mainstreet_2014_oct05_report__r2",
    ),
    "toronto_2014-2014-10-23-402c55fc": (
        "mainstreet_city_2014_10_23_n3569",
        "mainstreet_2014_oct23_report__r1",
    ),
    "toronto_2014-2014-10-23-5e3b3a4f": (
        "mainstreet_city_2014_10_23_n3569",
        "mainstreet_2014_oct23_report__r2",
    ),
    # --- Mainstreet 2018: legacy recorded only the decided-voter field -> r2 ---
    "toronto_2018-2018-09-16-8259f99e": (
        "mainstreet_city_2018_09_16_n802",
        "mainstreet_2018_sep16_report__r2",
    ),
    "toronto_2018-2018-09-25-bd8a7f23": (
        "mainstreet_city_2018_09_25_n966",
        "mainstreet_2018_sep25_report__r2",
    ),
    # --- Pre-existing Forum backlog: audited samples that predate this session
    #     but were never retired. Matched by candidate set (09-22 stays
    #     unresolved: its two proxies are ambiguous/not source-equivalent). ---
    "toronto_2014-2013-08-29-10ac3a3c": (
        "forum_city_2013_08_29_n848",
        "forum_2013_aug29_release__r1",
    ),
    "toronto_2014-2013-08-29-056a657f": (
        "forum_city_2013_08_29_n848",
        "forum_2013_aug29_release__r2",
    ),
    "toronto_2014-2013-08-29-4d46f0e0": (
        "forum_city_2013_08_29_n848",
        "forum_2013_aug29_release__r3",
    ),
    "toronto_2014-2013-08-29-dcebef42": (
        "forum_city_2013_08_29_n848",
        "forum_2013_aug29_release__r4",
    ),
    "toronto_2014-2013-08-29-127e27bb": (
        "forum_city_2013_08_29_n848",
        "forum_2013_aug29_release__r5",
    ),
    "toronto_2014-2013-11-04-f846e0fb": (
        "forum_city_2013_11_04_n1393",
        "forum_2013_nov04_release__r1",
    ),
    "toronto_2014-2013-11-04-b90dc200": (
        "forum_city_2013_11_04_n1393",
        "forum_2013_nov04_release__r2",
    ),
    "toronto_2014-2013-11-04-ef100e47": (
        "forum_city_2013_11_04_n1393",
        "forum_2013_nov04_release__r3",
    ),
    "toronto_2014-2013-11-04-d0e9e15c": (
        "forum_city_2013_11_04_n1393",
        "forum_2013_nov04_release__r4",
    ),
    "toronto_2014-2014-01-22-17ee9410": (
        "forum_city_2014_01_22_n1063",
        "forum_2014_jan22_release__r7",
    ),
    "toronto_2014-2014-03-27-da2b1b5d": (
        "forum_city_2014_03_27_n634",
        "forum_2014_mar27_release__r1",
    ),
    "toronto_2014-2014-03-27-2d4bc707": (
        "forum_city_2014_03_27_n634",
        "forum_2014_mar27_release__r2",
    ),
    "toronto_2014-2014-09-08-dd81d126": (
        "forum_city_2014_09_08_n1069",
        "forum_2014_sep08_four_way_rob",
    ),
    # --- found-2014 batch, group 1 (first-party reports) ---
    # Forum 2014-02-24 already in the corpus (feb25 release); map by candidate set.
    "toronto_2014-2014-02-24-d2896f09": (
        "forum_city_2014_02_24_n1310",
        "forum_2014_feb24_ford_tory_chow",
    ),
    "toronto_2014-2014-02-24-59cb828a": (
        "forum_city_2014_02_24_n1310",
        "forum_2014_feb24_four_way_ford",
    ),
    "toronto_2014-2014-02-24-ebbbbd3a": (
        "forum_city_2014_02_24_n1310",
        "forum_2014_feb24_five_way",
    ),
    # Mainstreet 2014-10-17: all-voter -> r1, decided -> r2.
    "toronto_2014-2014-10-17-364251db": (
        "mainstreet_city_2014_10_16_n2265",
        "mainstreet_2014_oct17_report__r1",
    ),
    "toronto_2014-2014-10-17-c139fbc5": (
        "mainstreet_city_2014_10_16_n2265",
        "mainstreet_2014_oct17_report__r2",
    ),
    # Nanos 2014-08-31: legacy used Nanos's unprompted accessible ballot; the
    # first-party prompted first-ranked (r1) and decided (r2) readings supersede.
    "toronto_2014-2014-08-31-615d57f4": (
        "nanos_city_2014_08_31_n1000",
        "nanos_2014_aug31_report__r1",
    ),
    "toronto_2014-2014-08-31-0ebf8dc2": (
        "nanos_city_2014_08_31_n1000",
        "nanos_2014_aug31_report__r2",
    ),
    # Forum 2014-09-22: full current field from the horserace release (companion
    # to the Issues release already mapped). r1 = 3-way, r2 = Goldkind 4-way.
    "toronto_2014-2014-09-22-19782e6d": (
        "forum_city_2014_09_22_n1164",
        "forum_2014_sep22_horserace__r1",
    ),
    "toronto_2014-2014-09-22-19304bb9": (
        "forum_city_2014_09_22_n1164",
        "forum_2014_sep22_horserace__r2",
    ),
    # --- found-2014 batch, group 2 (news toplines; matched by candidate values) ---
    "toronto_2014-2013-03-21-fa96205a": (
        "forum_city_2013_03_19_n1045",
        "forum_2013_mar21_star__r1",
    ),
    "toronto_2014-2013-03-21-1d85c80b": (
        "forum_city_2013_03_19_n1045",
        "forum_2013_mar21_star__r2",
    ),
    "toronto_2014-2013-03-21-47574b99": (
        "forum_city_2013_03_19_n1045",
        "forum_2013_mar21_star__r3",
    ),
    "toronto_2014-2013-05-13-dc2249d8": (
        "forum_city_2013_05_10_n974",
        "forum_2013_may13_star__r1",
    ),
    "toronto_2014-2013-05-13-d3c182cc": (
        "forum_city_2013_05_10_n974",
        "forum_2013_may13_star__r2",
    ),
    "toronto_2014-2013-05-13-9b716dba": (
        "forum_city_2013_05_10_n974",
        "forum_2013_may13_star__r3",
    ),
    "toronto_2014-2013-05-13-586501f0": (
        "forum_city_2013_05_10_n974",
        "forum_2013_may13_star__r4",
    ),
    "toronto_2014-2013-11-24-3ace1d90": (
        "forum_city_2013_11_24_n1049",
        "forum_2013_nov24_sun__r1",
    ),
    "toronto_2014-2013-11-24-28fc3455": (
        "forum_city_2013_11_24_n1049",
        "forum_2013_nov24_sun__r5",
    ),
    "toronto_2014-2013-11-24-0434843b": (
        "forum_city_2013_11_24_n1049",
        "forum_2013_nov24_sun__r6",
    ),
    "toronto_2014-2014-02-09-dd29b723": (
        "forum_city_2014_02_06_n769",
        "forum_2014_feb09_sun__r1",
    ),
    "toronto_2014-2014-02-09-ad636993": (
        "forum_city_2014_02_06_n769",
        "forum_2014_feb09_sun__r4",
    ),
    # Mainstreet 2018-09-05: legacy recorded only the decided field -> r2.
    "toronto_2018-2018-09-05-7c405033": (
        "mainstreet_city_2018_09_05_n1178",
        "mainstreet_2018_sep06_report__r2",
    ),
    # --- 2023 by-election Mainstreet toplines (CP24 articles + public narratives) ---
    "toronto_2023-2023-04-03-c3a0fb42": (
        "mainstreet_city_2023_04_03_n1306",
        "mainstreet_2023_cp24_a__r1",
    ),
    "toronto_2023-2023-05-03-ce518d01": (
        "mainstreet_city_2023_05_03_n1056",
        "mainstreet_2023_may03_report__r1",
    ),
    "toronto_2023-2023-05-17-40ce4bce": (
        "mainstreet_city_2023_05_17_n1125",
        "mainstreet_2023_may19_report__r1",
    ),
    "toronto_2023-2023-06-15-d7599146": (
        "mainstreet_city_2023_06_15_n899",
        "mainstreet_2023_cp24_c__r1",
    ),
    "toronto_2023-2023-06-19-1629c424": (
        "mainstreet_city_2023_06_19_n552",
        "mainstreet_2023_jun20_report__r1",
    ),
    "toronto_2023-2023-06-22-40f3d792": (
        "mainstreet_city_2023_06_22_n1481",
        "mainstreet_2023_cp24_b__r1",
    ),
    "toronto_2014-2013-11-12-6a9b9d1e": (
        "ipsos_city_2013_11_08_12_n665",
        "ipsos_nov2013_scenario3",
    ),
    "toronto_2014-2013-11-12-7d87bc74": (
        "ipsos_city_2013_11_08_12_n665",
        "ipsos_nov2013_scenario2",
    ),
    "toronto_2014-2013-11-12-a25ac730": (
        "ipsos_city_2013_11_08_12_n665",
        "ipsos_nov2013_scenario1",
    ),
    "toronto_2014-2013-11-12-e5e824f2": (
        "ipsos_city_2013_11_08_12_n665",
        "ipsos_nov2013_scenario4",
    ),
    "toronto_2014-2014-07-05-8095cb7d": (
        "nanos_city_2014_07_02_05_n600",
        "nanos_jul_ballot",
    ),
    "toronto_2014-2014-07-30-68013cdd": (
        "maple_leaf_city_2014_07_28_30_n800",
        "maple_leaf_jul_decided",
    ),
    "toronto_2014-2014-07-30-c9871872": (
        "maple_leaf_city_2014_07_28_30_n800",
        "maple_leaf_jul_all",
    ),
    "toronto_2014-2014-09-16-2b8087b6": (
        "ipsos_city_2014_09_12_16_n596",
        "ipsos_sep16_decided",
    ),
    "toronto_2014-2014-09-20-149cf9eb": (
        "nanos_city_2014_09_16_20_n1000",
        "nanos_sep_all",
    ),
    "toronto_2014-2014-09-20-8da2bbf6": (
        "nanos_city_2014_09_16_20_n1000",
        "nanos_sep_decided",
    ),
    "toronto_2014-2014-09-26-ffa3584b": (
        "ipsos_city_2014_09_23_26_n1252",
        "ipsos_sep26_decided_leaners",
    ),
    "toronto_2014-2014-10-23-10ff6cd1": (
        "ipsos_city_2014_10_21_23_n1201",
        "ipsos_oct23_decided_leaners",
    ),
    "toronto_2018-2018-09-05-87b8c045": (
        "probit_city_2018_08_20_09_05_n1635",
        "probit_2018_undecideds_removed",
    ),
    "toronto_2018-2018-10-15-00471a65": (
        "dart_city_2018_10_12_15_n669",
        "dart_2018_head_to_head",
    ),
    "toronto_2022-2022-10-08-193526f0": (
        "forum_city_2022_10_07_08_n1017",
        "forum_2022_oct08_decided_leaning",
    ),
    "toronto_2023-2023-02-14-5a8ad8e6": (
        "forum_city_2023_02_13_n1042",
        "forum_2023_feb13_decided_leaning",
    ),
    "toronto_2023-2023-03-23-9ed06eb6": (
        "forum_city_2023_03_22_23_n1009",
        "forum_2023_mar23_decided_leaning",
    ),
    "toronto_2023-2023-04-22-99e92736": (
        "liaison_city_2023_04_21_22_n1264",
        "liaison_2023_04_21_22_decided",
    ),
    "toronto_2023-2023-04-26-60f8ec78": (
        "forum_city_2023_04_25_26_n1022",
        "forum_2023_apr26_decided_leaning",
    ),
    "toronto_2023-2023-04-29-27c4faed": (
        "liaison_city_2023_04_28_29_n1253",
        "liaison_2023_04_28_29_decided",
    ),
    "toronto_2023-2023-05-06-f56cccbb": (
        "liaison_city_2023_05_05_06_n1257",
        "liaison_2023_05_05_06_decided",
    ),
    "toronto_2023-2023-05-07-6f5a8760": (
        "forum_city_2023_05_06_07_n2000",
        "forum_2023_may07_decided_leaning",
    ),
    "toronto_2023-2023-05-13-fe817631": (
        "liaison_city_2023_05_12_13_n1318",
        "liaison_2023_05_12_13_decided",
    ),
    "toronto_2023-2023-05-14-f216820b": (
        "forum_city_2023_05_13_n1029",
        "forum_2023_may13_decided_leaning",
    ),
    "toronto_2023-2023-05-18-e960c650": (
        "liaison_city_2023_05_17_18_n1311",
        "liaison_2023_05_17_18_decided",
    ),
    "toronto_2023-2023-05-20-b403ec48": (
        "forum_city_2023_05_19_n1000",
        "forum_2023_may19_decided_leaning",
    ),
    "toronto_2023-2023-05-27-5af2e4a3": (
        "liaison_city_2023_05_26_27_n1305",
        "liaison_2023_05_26_27_decided",
    ),
    "toronto_2023-2023-05-27-ad718bff": (
        "forum_city_2023_05_26_n1007",
        "forum_2023_may26_decided_leaning",
    ),
    "toronto_2023-2023-06-02-5e744916": (
        "forum_city_2023_06_02_n1032",
        "forum_2023_jun02_decided_leaning",
    ),
    "toronto_2023-2023-06-02-85a96bf1": (
        "viewpoints_city_2023_06_01_02_n1004",
        "viewpoints_2023_06_02_decided",
    ),
    "toronto_2023-2023-06-04-35b1f370": (
        "liaison_city_2023_06_03_04_n1287",
        "liaison_2023_06_03_04_decided",
    ),
    "toronto_2023-2023-06-09-c2c4b67a": (
        "forum_city_2023_06_09_n1047",
        "forum_2023_jun09_decided_leaning",
    ),
    "toronto_2023-2023-06-11-427f06fa": (
        "liaison_city_2023_06_10_11_n1197",
        "liaison_2023_06_10_11_decided",
    ),
    "toronto_2023-2023-06-13-1d20c510": (
        "liaison_city_2023_06_12_13_n1156",
        "liaison_2023_06_12_13_decided",
    ),
    "toronto_2023-2023-06-13-a85f2b10": (
        "ipsos_city_2023_06_09_13_n1001",
        "ipsos_2023_total_repercentaged",
    ),
    "toronto_2023-2023-06-18-c78c5dae": (
        "liaison_city_2023_06_17_18_n1152",
        "liaison_2023_06_17_18_decided",
    ),
    "toronto_2023-2023-06-19-1521a447": (
        "viewpoints_city_2023_06_15_19_n1007",
        "viewpoints_jun19_leaning",
    ),
    "toronto_2023-2023-06-23-2c0221b3": (
        "liaison_city_2023_06_22_23_n1086",
        "liaison_2023_06_22_23_decided",
    ),
    "toronto_2023-2023-06-23-5253ec7d": (
        "forum_city_2023_06_23_n1037",
        "forum_2023_jun23_decided_leaning",
    ),
    "toronto_2014-2014-04-14-21adb36a": (
        "forum_city_2014_04_14_n882",
        "forum_2014_apr14_four_way_no_ford",
    ),
    "toronto_2014-2014-04-14-6b1c4967": (
        "forum_city_2014_04_14_n882",
        "forum_2014_apr14_five_way_rob",
    ),
    "toronto_2014-2014-04-14-6de26188": (
        "forum_city_2014_04_14_n882",
        "forum_2014_apr14_three_way",
    ),
    "toronto_2014-2014-05-01-63bee463": (
        "forum_city_2014_05_01_n888",
        "forum_2014_may01_five_way_rob",
    ),
    "toronto_2014-2014-05-01-e88f6159": (
        "forum_city_2014_05_01_n888",
        "forum_2014_may01_four_way_no_ford",
    ),
    "toronto_2014-2014-05-01-ef18a380": (
        "forum_city_2014_05_01_n888",
        "forum_2014_may01_three_way",
    ),
    "toronto_2014-2014-05-21-33505da6": (
        "forum_city_2014_05_21_n923",
        "forum_2014_may21_five_way_rob",
    ),
    "toronto_2014-2014-05-21-3fd183ff": (
        "forum_city_2014_05_21_n923",
        "forum_2014_may21_five_way_doug",
    ),
    "toronto_2014-2014-05-21-49c9ea8d": (
        "forum_city_2014_05_21_n923",
        "forum_2014_may21_four_way_no_ford",
    ),
    "toronto_2014-2014-05-21-5bacb559": (
        "forum_city_2014_05_21_n923",
        "forum_2014_may21_three_way_rob",
    ),
    "toronto_2014-2014-05-21-bc54549a": (
        "forum_city_2014_05_21_n923",
        "forum_2014_may21_three_way_doug",
    ),
    "toronto_2014-2014-05-21-f67470d1": (
        "forum_city_2014_05_21_n923",
        "forum_2014_may21_five_way_norm_kelly",
    ),
    "toronto_2014-2014-06-23-76b204a0": (
        "forum_city_2014_06_23_n890",
        "forum_2014_jun23_three_way_rob",
    ),
    "toronto_2014-2014-06-23-7e968ba6": (
        "forum_city_2014_06_23_n890",
        "forum_2014_jun23_five_way_rob",
    ),
    "toronto_2014-2014-06-23-9f6d6da3": (
        "forum_city_2014_06_23_n890",
        "forum_2014_jun23_two_way_tory_chow",
    ),
    "toronto_2014-2014-06-23-e45dd43a": (
        "forum_city_2014_06_23_n890",
        "forum_2014_jun23_four_way_no_ford",
    ),
    "toronto_2014-2014-07-02-30237a62": (
        "forum_city_2014_07_02_n1182",
        "forum_2014_jul02_two_way_tory_chow_trend",
    ),
    "toronto_2014-2014-07-02-7afc20a5": (
        "forum_city_2014_07_02_n1182",
        "forum_2014_jul02_three_way_rob_trend",
    ),
    "toronto_2014-2014-07-02-810c9dea": (
        "forum_city_2014_07_02_n1182",
        "forum_2014_jul02_five_way_rob",
    ),
    "toronto_2014-2014-07-02-f0332833": (
        "forum_city_2014_07_02_n1182",
        "forum_2014_jul02_four_way_no_ford_trend",
    ),
    "toronto_2014-2014-07-21-83f8db7a": (
        "forum_city_2014_07_21_n1063",
        "forum_2014_jul21_three_way_rob",
    ),
    "toronto_2014-2014-07-21-8e6e3f76": (
        "forum_city_2014_07_21_n1063",
        "forum_2014_jul21_five_way_rob",
    ),
    "toronto_2014-2014-08-06-52196426": (
        "forum_city_2014_08_05_06_n1268",
        "forum_2014_aug06_five_way_rob",
    ),
    "toronto_2014-2014-08-06-820ca818": (
        "forum_city_2014_08_05_06_n1268",
        "forum_2014_aug06_three_way_rob_trend",
    ),
    "toronto_2014-2014-08-26-066ea1b6": (
        "forum_city_2014_08_25_26_n1945",
        "forum_2014_aug26_four_way_rob",
    ),
    "toronto_2014-2014-08-26-82a7f606": (
        "forum_city_2014_08_25_26_n1945",
        "forum_2014_aug26_three_way_rob",
    ),
    "toronto_2014-2014-09-08-98eb25b6": (
        "forum_city_2014_09_08_n1069",
        "forum_2014_sep08_two_way_rob_tory",
    ),
    "toronto_2014-2014-09-08-b82e0bbf": (
        "forum_city_2014_09_08_n1069",
        "forum_2014_sep08_three_way_rob",
    ),
    "toronto_2014-2014-09-12-6d6a07d5": (
        "forum_city_2014_09_12_n1228",
        "forum_2014_sep12_three_way_doug",
    ),
    "toronto_2014-2014-09-29-8273cf08": (
        "forum_city_2014_09_29_n1202",
        "forum_2014_sep29_decided_leaning",
    ),
    "toronto_2014-2014-10-06-400594e6": (
        "forum_city_2014_10_06_n1218",
        "forum_2014_oct06_decided_leaning",
    ),
    "toronto_2014-2014-10-14-44ca18bc": (
        "forum_city_2014_10_15_n1241",
        "forum_2014_oct15_decided_leaning",
    ),
    "toronto_2014-2014-10-20-056adce9": (
        "forum_city_2014_10_20_n852",
        "forum_2014_oct20_decided_leaning",
    ),
    "toronto_2014-2014-10-25-2382a96c": (
        "forum_city_2014_10_25_n986",
        "forum_2014_oct25_decided_leaning",
    ),
    "toronto_2018-2018-07-27-4dbe1c75": (
        "forum_city_2018_07_27_n1328",
        "forum_2018_jul27_decided_leaning",
    ),
    "toronto_2018-2018-08-27-ab6de01e": (
        "forum_city_2018_08_27_n1242",
        "forum_2018_aug27_decided_leaning",
    ),
    "toronto_2018-2018-09-24-1e18acf4": (
        "forum_city_2018_09_20_24_n944",
        "forum_2018_sep24_decided_leaning",
    ),
    "toronto_2018-2018-10-05-34b8524e": (
        "forum_city_2018_10_03_05_n987",
        "forum_2018_oct05_decided_leaning",
    ),
    "toronto_2018-2018-10-10-1c17f752": (
        "forum_city_2018_10_09_10_n1206",
        "forum_2018_oct10_decided_leaning",
    ),
    "toronto_2023-2023-02-14-f879a53a": (
        "mainstreet_city_2023_02_13_14_n1947",
        "mainstreet_2023_feb14_all",
    ),
    "toronto_2023-2023-02-19-b354d774": (
        "mainstreet_city_2023_02_19_n1701",
        "mainstreet_2023_feb19_all",
    ),
    "toronto_2023-2023-03-19-1cb19f92": (
        "mainstreet_city_2023_03_17_19_n985",
        "mainstreet_2023_mar19_all",
    ),
    "toronto_2023-2023-04-13-431601a9": (
        "mainstreet_city_2023_04_12_13_n785",
        "mainstreet_2023_apr13_all",
    ),
    "toronto_2023-2023-04-20-3df69850": (
        "mainstreet_city_2023_04_17_19_n1082",
        "mainstreet_2023_apr20_decided",
    ),
    "toronto_2023-2023-04-26-a07c911c": (
        "mainstreet_city_2023_04_25_26_n996",
        "mainstreet_2023_apr26_decided",
    ),
}

_LEGACY_MAPPING_NOTES: Final = {
    "toronto_2014-2013-01-25-b9d08ec1": (
        "Mapped to the Ford / Carroll head-to-head; the legacy row kept only "
        "Rob Ford (0.45) and folded Shelley Carroll and Don't Know into a single "
        "0.55 residual. The first-party extraction supersedes that combined vector."
    ),
    "toronto_2018-2018-09-16-8259f99e": (
        "Mapped to the decided-voter reading. Mainstreet's 2018 legacy proxy "
        "recorded only the decided-voter field (Tory/Keesmaat), folding the minor "
        "candidates into a residual; the all-respondents field is a separate reading."
    ),
    "toronto_2014-2013-08-29-dcebef42": (
        "Mapped to the Ford / Minnan-Wong head-to-head; the legacy row kept only "
        "Rob Ford (0.39) and folded Denzil Minnan-Wong and Don't Know into a 0.61 "
        "residual. The first-party extraction supersedes that combined vector."
    ),
    "toronto_2014-2014-09-08-dd81d126": (
        "Mapped to the four-candidate reading (Tory 40, Rob Ford 28, Chow 21, "
        "Soknacki 6). The legacy row halved the named shares into a >0.5 residual; "
        "the first-party source values supersede that corrupted vector."
    ),
    "toronto_2014-2014-08-31-615d57f4": (
        "Nanos Aug 31 sample. The legacy row is Nanos's unprompted accessible-ballot "
        "question (a large 'unsure' residual); it is superseded by the first-party "
        "prompted first-ranked ballot (including Unsure) extracted from the report."
    ),
    "toronto_2014-2014-08-31-0ebf8dc2": (
        "Nanos Aug 31 sample, decided-voter reading. Legacy is the unprompted "
        "accessible ballot; the first-party decided-voter ballot supersedes it."
    ),
    "toronto_2014-2014-09-22-19782e6d": (
        "Mapped to the full three-way current field (Tory 38, Doug Ford 31, Chow 25) "
        "recovered from the Sep 22 horserace release. The legacy row halved the shares "
        "into a >0.5 residual; the first-party values supersede it."
    ),
    "toronto_2014-2014-07-05-8095cb7d": (
        "Mapped to the visually verified Nanos Ballot reading. The legacy "
        "scraper treated the source's 1.0% Soknacki value as 100% before "
        "normalizing the row; the canonical source values supersede that "
        "corrupted vector."
    ),
}

_NON_POLL_LEGACY_ID: Final = "toronto_2014-2010-10-25-6a933a5f"

# Proxies with no recoverable first-party or secondary source. Documented as
# unavailable so they do not block calibration as "unresolved" — the source was
# searched for and does not exist publicly (see docs/research/
# unresolved-proxy-source-hunt.md).
_NO_PUBLIC_SOURCE_LEGACY_IDS: Final = frozenset(
    {
        "toronto_2014-2014-01-06-f94510f4",
        "toronto_2023-2023-05-11-076ef4ef",
        "toronto_2023-2023-05-25-3a934378",
        "toronto_2023-2023-05-31-30f43af0",
        "toronto_2023-2023-06-08-1d2a2a3e",
        "toronto_2023-2023-06-11-2c161a34",
        "toronto_2023-2023-06-16-e57b0970",
        "toronto_2023-2023-06-24-7cdc9fdb",
        "toronto_2023-2023-06-25-c32aea31",
    }
)
_NO_PUBLIC_SOURCE_NOTES: Final = {
    "toronto_2014-2014-01-06-f94510f4": (
        "No surviving first-party release; the Jan 22 2014 Forum release only "
        "references this early-January wave. No public source located."
    ),
}
_NO_PUBLIC_SOURCE_DEFAULT_NOTE: Final = (
    "No public first-party or secondary source located; Mainstreet's premium tier "
    "does not include these 2023 by-election reports. Documented as unavailable."
)


class HistoricalMayoralDataError(ValueError):
    """Raised when historical evidence is malformed or relationally incomplete."""


@dataclass(frozen=True, slots=True)
class MayoralElection:
    election_cycle_id: str
    election_date: date
    election_type: Literal["general", "by_election"]
    nomination_close_date: date | None
    nomination_close_status: Literal["reported", "not_reconstructed"]
    final_ballot_known_by_date: date
    final_ballot_known_by_status: Literal[
        "certification_date_reported",
        "publicly_announced",
        "statutory_deadline",
    ]
    ballot_timing_source_url: str
    source_document_id: str
    source_url: str
    source_locator: str
    source_sha256: str | None
    source_completeness: str
    notes: str | None

    @property
    def final_ballot_evidence_available_at(self) -> datetime:
        """Earliest safe cutoff after a date-precision known-by boundary."""
        next_day = self.final_ballot_known_by_date + timedelta(days=1)
        return datetime(next_day.year, next_day.month, next_day.day, tzinfo=_TORONTO)


@dataclass(frozen=True, slots=True)
class MayoralOutcome:
    election_cycle_id: str
    candidate_id: str
    candidate_name: str
    candidate_name_as_reported: str
    votes: int
    valid_vote_total: int
    share: Decimal
    is_winner: bool
    source_document_id: str
    source_locator: str


@dataclass(frozen=True, slots=True)
class LegacyPollCrosswalk:
    legacy_poll_id: str
    election_cycle_id: str
    legacy_sample_proxy_key: str
    poll_sample_id: str | None
    poll_reading_id: str | None
    disposition: Literal["mapped", "non_poll", "unresolved", "no_public_source"]
    notes: str


@dataclass(frozen=True, slots=True)
class HistoricalMayoralCorpus:
    """Validated official outcomes plus source-verified historical poll readings."""

    elections: tuple[MayoralElection, ...]
    outcomes: tuple[MayoralOutcome, ...]
    poll_samples: tuple[HistoricalPollSample, ...]
    poll_readings: tuple[HistoricalPollReading, ...]
    poll_responses: tuple[HistoricalPollResponse, ...]
    legacy_crosswalk: tuple[LegacyPollCrosswalk, ...]
    source_documents: tuple[SourceDocument, ...] = ()
    poll_sample_documents: tuple[PollSampleDocument, ...] = ()

    def outcome_universe(self, election_cycle_id: str) -> tuple[MayoralOutcome, ...]:
        """Return the complete certified candidate outcome, ordered by candidate ID."""
        rows = tuple(
            row for row in self.outcomes if row.election_cycle_id == election_cycle_id
        )
        if not rows:
            raise KeyError(election_cycle_id)
        return rows

    def outcome_share_vector(
        self, election_cycle_id: str
    ) -> tuple[tuple[str, Decimal], ...]:
        """Return a complete candidate-id/share vector for evaluation adapters."""
        return tuple(
            (row.candidate_id, row.share)
            for row in self.outcome_universe(election_cycle_id)
        )

    def readings_for_sample(
        self, poll_sample_id: str
    ) -> tuple[HistoricalPollReading, ...]:
        return tuple(
            reading
            for reading in self.poll_readings
            if reading.poll_sample_id == poll_sample_id
        )

    def responses_for_reading(
        self, poll_reading_id: str
    ) -> tuple[HistoricalPollResponse, ...]:
        return tuple(
            response
            for response in self.poll_responses
            if response.poll_reading_id == poll_reading_id
        )


@dataclass(frozen=True, slots=True)
class HistoricalMayoralAudit:
    election_count: int
    outcome_candidate_count: int
    source_verified_sample_count: int
    source_verified_reading_count: int
    legacy_poll_id_count: int
    historical_sample_inventory_count: int
    unresolved_sample_proxy_count: int
    no_public_source_proxy_count: int
    blocker_codes: tuple[str, ...]


def load_historical_mayoral_corpus(project_root: str | Path) -> HistoricalMayoralCorpus:
    """Load the isolated canonical historical corpus rooted at ``project_root``.

    Source rows must carry completed extraction and visual-QA metadata, while
    rechecking the gitignored artifact bytes remains an explicit acquisition
    audit rather than a runtime dependency of the normalized evidence.
    """
    root = Path(project_root)
    elections = _load_elections(root / "data/raw/elections/mayoral_elections.csv")
    outcomes = _load_outcomes(root / "data/raw/elections/mayoral_outcomes.csv")
    crosswalk = _load_crosswalk(
        root / "data/raw/polls/legacy_historical_poll_crosswalk.csv"
    )
    poll_sources = load_poll_source_bundle(
        root / "data/raw/polls/historical_mayoral",
        require_audited_sources=True,
    )
    corpus = HistoricalMayoralCorpus(
        elections=elections,
        outcomes=outcomes,
        poll_samples=poll_sources.poll_samples,
        poll_readings=poll_sources.poll_readings,
        poll_responses=poll_sources.poll_responses,
        legacy_crosswalk=crosswalk,
        source_documents=poll_sources.source_documents,
        poll_sample_documents=poll_sources.poll_sample_documents,
    )
    _validate_corpus(corpus, root / "data/raw/polls/historical_mayoral_polls.csv")
    return corpus


def audit_historical_mayoral_corpus(
    corpus: HistoricalMayoralCorpus,
) -> HistoricalMayoralAudit:
    non_poll = {
        row.legacy_poll_id
        for row in corpus.legacy_crosswalk
        if row.disposition == "non_poll"
    }
    inventory_ids = {
        row.poll_sample_id
        for row in corpus.legacy_crosswalk
        if row.legacy_poll_id not in non_poll and row.poll_sample_id is not None
    }
    inventory_ids.update(sample.poll_sample_id for sample in corpus.poll_samples)
    unresolved_ids = {
        row.poll_sample_id
        for row in corpus.legacy_crosswalk
        if row.disposition == "unresolved" and row.poll_sample_id is not None
    }
    no_public_source_ids = {
        row.poll_sample_id
        for row in corpus.legacy_crosswalk
        if row.disposition == "no_public_source" and row.poll_sample_id is not None
    }
    blockers: list[str] = []
    if unresolved_ids:
        blockers.append("unresolved_legacy_poll_samples")
    return HistoricalMayoralAudit(
        election_count=len(corpus.elections),
        outcome_candidate_count=len(corpus.outcomes),
        source_verified_sample_count=len(corpus.poll_samples),
        source_verified_reading_count=len(corpus.poll_readings),
        legacy_poll_id_count=len(corpus.legacy_crosswalk),
        historical_sample_inventory_count=len(inventory_ids),
        unresolved_sample_proxy_count=len(unresolved_ids),
        no_public_source_proxy_count=len(no_public_source_ids),
        blocker_codes=tuple(blockers),
    )


def build_mayoral_election_rows() -> list[dict[str, str]]:
    """Build the four-cycle election/source manifest with explicit missingness."""
    rows: list[dict[str, str]] = []
    for year in sorted(_ELECTION_CONFIG):
        (
            cycle,
            election_date,
            election_type,
            source_id,
            source_url,
            source_locator,
            source_sha256,
            source_completeness,
        ) = _ELECTION_CONFIG[year]
        (
            nomination_close,
            final_ballot_known_by,
            final_ballot_status,
            timing_source_url,
        ) = _BALLOT_TIMING[year]
        rows.append(
            {
                "election_cycle_id": cycle,
                "election_date": election_date.isoformat(),
                "election_type": election_type,
                "nomination_close_date": nomination_close.isoformat(),
                "nomination_close_status": "reported",
                "final_ballot_known_by_date": final_ballot_known_by.isoformat(),
                "final_ballot_known_by_status": final_ballot_status,
                "ballot_timing_source_url": timing_source_url,
                "source_document_id": source_id,
                "source_url": source_url,
                "source_locator": source_locator,
                "source_sha256": source_sha256,
                "source_completeness": source_completeness,
                "notes": _BALLOT_TIMING_NOTES[year],
            }
        )
    return rows


def build_mayoral_outcome_rows(
    sidecar_paths: dict[int, str | Path], ward_results_path: str | Path
) -> list[dict[str, str]]:
    """Build complete official candidate outcomes for every cycle.

    Sidecar cycles carry candidate-total declarations from a per-year CSV — used
    where the ward geography is not the current 25 (2010's 44 wards) or the source
    is a candidate-level declaration (2014). The 25-ward cycles (2018/2022/2023)
    are aggregated from the shared ward-results file.
    """
    grouped: dict[int, dict[str, int]] = {}
    winners_by_year: dict[int, set[str]] = {}
    for year, path in sidecar_paths.items():
        source_rows = _read_csv(Path(path), _OFFICIAL_2014_COLUMNS)
        expected_source = {
            "source_document_id": _ELECTION_CONFIG[year][3],
            "source_url": _ELECTION_CONFIG[year][4],
            "source_locator": _ELECTION_CONFIG[year][5],
            "source_sha256": _ELECTION_CONFIG[year][6],
            "source_completeness": _ELECTION_CONFIG[year][7],
        }
        grouped[year] = {}
        winners_by_year[year] = set()
        for row in source_rows:
            for field, expected in expected_source.items():
                # Compare the raw declared value against the config; source_sha256
                # is legitimately blank when the artifact was not retained.
                if row.get(field, "") != expected:
                    raise HistoricalMayoralDataError(
                        f"{year} sidecar has unexpected {field}={row.get(field)!r}"
                    )
            name = _required(row, "candidate_name")
            if name in grouped[year]:
                raise HistoricalMayoralDataError(f"duplicate {year} candidate {name!r}")
            grouped[year][name] = _positive_int(row, "votes")
            if _boolean(row, "is_winner"):
                winners_by_year[year].add(name)
        if len(winners_by_year[year]) != 1:
            raise HistoricalMayoralDataError(
                f"{year} sidecar must identify exactly one official winner"
            )

    ward_rows = _read_csv(Path(ward_results_path), _WARD_RESULT_COLUMNS)
    wards_by_candidate: dict[tuple[int, str], set[int]] = defaultdict(set)
    for row in ward_rows:
        year = _positive_int(row, "year")
        if year not in {2018, 2022, 2023}:
            raise HistoricalMayoralDataError(f"unexpected mayoral result year {year}")
        ward = _positive_int(row, "ward")
        if not 1 <= ward <= 25:
            raise HistoricalMayoralDataError(f"invalid ward {ward} for {year}")
        name = _required(row, "candidate")
        grouped.setdefault(year, {})[name] = grouped.setdefault(year, {}).get(
            name, 0
        ) + _nonnegative_int(row, "votes")
        wards_by_candidate[(year, name)].add(ward)
    for (year, name), wards in wards_by_candidate.items():
        if wards != set(range(1, 26)):
            raise HistoricalMayoralDataError(
                f"{year} candidate {name!r} does not have all 25 ward totals"
            )

    expected_counts = {2010: 40, 2014: 65, 2018: 35, 2022: 31, 2023: 102}
    expected_totals = {
        2010: 813984,
        2014: 981054,
        2018: 755493,
        2022: 551890,
        2023: 724638,
    }
    rows: list[dict[str, str]] = []
    for year in sorted(expected_counts):
        candidates = grouped.get(year, {})
        total = sum(candidates.values())
        if len(candidates) != expected_counts[year] or total != expected_totals[year]:
            raise HistoricalMayoralDataError(
                f"{year} outcome expected {expected_counts[year]} candidates and "
                f"{expected_totals[year]} votes; got {len(candidates)} and {total}"
            )
        max_votes = max(candidates.values())
        source_id = _ELECTION_CONFIG[year][3]
        source_locator = _ELECTION_CONFIG[year][5]
        for name, votes in sorted(
            candidates.items(), key=lambda item: _candidate_id(year, item[0])
        ):
            candidate_id = _candidate_id(year, name)
            is_winner = (
                name in winners_by_year[year]
                if year in winners_by_year
                else votes == max_votes
            )
            rows.append(
                {
                    "election_cycle_id": _ELECTION_CONFIG[year][0],
                    "candidate_id": candidate_id,
                    "candidate_name": _KNOWN_CANDIDATE_NAMES.get(candidate_id, name),
                    "candidate_name_as_reported": name,
                    "votes": str(votes),
                    "valid_vote_total": str(total),
                    "share": format(Decimal(votes) / Decimal(total), ".18f"),
                    "is_winner": str(is_winner).lower(),
                    "source_document_id": source_id,
                    "source_locator": source_locator,
                }
            )
    return rows


def build_legacy_crosswalk_rows(legacy_poll_path: str | Path) -> list[dict[str, str]]:
    """Build a one-row-per-legacy-ID crosswalk without blessing staging values."""
    raw_rows = _read_csv(Path(legacy_poll_path), _LEGACY_POLL_COLUMNS)
    by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in raw_rows:
        by_id[_required(row, "poll_id")].append(row)
    rows: list[dict[str, str]] = []
    for legacy_id in sorted(by_id):
        group = by_id[legacy_id]
        first = group[0]
        invariant_fields = (
            "election_id",
            "firm",
            "date_published",
            "sample_size",
        )
        for field in invariant_fields:
            if {row[field] for row in group} != {first[field]}:
                raise HistoricalMayoralDataError(
                    f"legacy poll {legacy_id!r} disagrees on {field}"
                )
        election_id = _required(first, "election_id")
        firm = _required(first, "firm")
        legacy_date = _required(first, "date_published")
        sample_token = first["sample_size"] or "missing"
        firm_slug = _slug(firm)
        proxy_key = f"{election_id}|{firm_slug}|{legacy_date}|{sample_token}"
        staging_sample_id = (
            f"staging:{election_id}:{firm_slug}:{legacy_date}:n{sample_token}"
        )
        if legacy_id == _NON_POLL_LEGACY_ID:
            disposition = "non_poll"
            sample_id = ""
            reading_id = ""
            notes = "2010 election result incorrectly stored as a 2014 poll."
        elif legacy_id in _MAPPED_LEGACY_READINGS:
            disposition = "mapped"
            sample_id, reading_id = _MAPPED_LEGACY_READINGS[legacy_id]
            notes = _LEGACY_MAPPING_NOTES.get(
                legacy_id,
                "Mapped to a visually verified first-party document extraction.",
            )
        elif legacy_id in _NO_PUBLIC_SOURCE_LEGACY_IDS:
            disposition = "no_public_source"
            sample_id = staging_sample_id
            reading_id = ""
            notes = _NO_PUBLIC_SOURCE_NOTES.get(
                legacy_id, _NO_PUBLIC_SOURCE_DEFAULT_NOTE
            )
        else:
            disposition = "unresolved"
            sample_id = staging_sample_id
            reading_id = f"staging:{legacy_id}"
            notes = (
                "Discovery-only proxy. Legacy date is last polling-date proxy; "
                "shares were normalized and residual kinds combined; owning source "
                "and publication timing remain unresolved."
            )
        rows.append(
            {
                "legacy_poll_id": legacy_id,
                "election_cycle_id": election_id,
                "legacy_sample_proxy_key": proxy_key,
                "poll_sample_id": sample_id,
                "poll_reading_id": reading_id,
                "disposition": disposition,
                "notes": notes,
            }
        )
    return rows


def _load_elections(path: Path) -> tuple[MayoralElection, ...]:
    result: list[MayoralElection] = []
    for row in _read_csv(path, ELECTION_COLUMNS):
        final_ballot_status = _required(row, "final_ballot_known_by_status")
        if final_ballot_status not in {
            "certification_date_reported",
            "publicly_announced",
            "statutory_deadline",
        }:
            raise HistoricalMayoralDataError(
                f"invalid Final Ballot known-by status {final_ballot_status!r}"
            )
        final_ballot_known_by = _date(row, "final_ballot_known_by_date")
        nomination_status = _required(row, "nomination_close_status")
        if nomination_status not in {"reported", "not_reconstructed"}:
            raise HistoricalMayoralDataError(
                f"invalid nomination close status {nomination_status!r}"
            )
        nomination_close_date = _optional_date(row, "nomination_close_date")
        if (nomination_status == "reported") != (nomination_close_date is not None):
            raise HistoricalMayoralDataError(
                "nomination close date/status must be reported together"
            )
        election_date = _date(row, "election_date")
        if nomination_close_date is not None and not (
            nomination_close_date <= final_ballot_known_by <= election_date
        ):
            raise HistoricalMayoralDataError(
                "Final Ballot known-by date must fall between nomination close "
                "and election day"
            )
        election_type = _required(row, "election_type")
        if election_type not in {"general", "by_election"}:
            raise HistoricalMayoralDataError(f"invalid election type {election_type!r}")
        result.append(
            MayoralElection(
                election_cycle_id=_required(row, "election_cycle_id"),
                election_date=election_date,
                election_type=election_type,
                nomination_close_date=nomination_close_date,
                nomination_close_status=nomination_status,
                final_ballot_known_by_date=final_ballot_known_by,
                final_ballot_known_by_status=final_ballot_status,
                ballot_timing_source_url=_url(row, "ballot_timing_source_url"),
                source_document_id=_required(row, "source_document_id"),
                source_url=_url(row, "source_url"),
                source_locator=_required(row, "source_locator"),
                source_sha256=row["source_sha256"] or None,
                source_completeness=_required(row, "source_completeness"),
                notes=row["notes"] or None,
            )
        )
    if len({row.election_cycle_id for row in result}) != len(result):
        raise HistoricalMayoralDataError("duplicate election_cycle_id")
    return tuple(sorted(result, key=lambda row: row.election_date))


def _load_outcomes(path: Path) -> tuple[MayoralOutcome, ...]:
    result: list[MayoralOutcome] = []
    for row in _read_csv(path, OUTCOME_COLUMNS):
        result.append(
            MayoralOutcome(
                election_cycle_id=_required(row, "election_cycle_id"),
                candidate_id=_required(row, "candidate_id"),
                candidate_name=_required(row, "candidate_name"),
                candidate_name_as_reported=_required(row, "candidate_name_as_reported"),
                votes=_positive_int(row, "votes"),
                valid_vote_total=_positive_int(row, "valid_vote_total"),
                share=_share(row, "share"),
                is_winner=_boolean(row, "is_winner"),
                source_document_id=_required(row, "source_document_id"),
                source_locator=_required(row, "source_locator"),
            )
        )
    return tuple(
        sorted(result, key=lambda row: (row.election_cycle_id, row.candidate_id))
    )


def _load_crosswalk(path: Path) -> tuple[LegacyPollCrosswalk, ...]:
    result: list[LegacyPollCrosswalk] = []
    for row in _read_csv(path, CROSSWALK_COLUMNS):
        disposition = _required(row, "disposition")
        if disposition not in {"mapped", "non_poll", "unresolved", "no_public_source"}:
            raise HistoricalMayoralDataError(f"invalid disposition {disposition!r}")
        result.append(
            LegacyPollCrosswalk(
                legacy_poll_id=_required(row, "legacy_poll_id"),
                election_cycle_id=_required(row, "election_cycle_id"),
                legacy_sample_proxy_key=_required(row, "legacy_sample_proxy_key"),
                poll_sample_id=row["poll_sample_id"] or None,
                poll_reading_id=row["poll_reading_id"] or None,
                disposition=disposition,
                notes=_required(row, "notes"),
            )
        )
    if len({row.legacy_poll_id for row in result}) != len(result):
        raise HistoricalMayoralDataError("duplicate legacy_poll_id in crosswalk")
    return tuple(result)


def _validate_corpus(corpus: HistoricalMayoralCorpus, legacy_poll_path: Path) -> None:
    election_by_id = {row.election_cycle_id: row for row in corpus.elections}
    if set(election_by_id) != {
        "toronto_2010",
        "toronto_2014",
        "toronto_2018",
        "toronto_2022",
        "toronto_2023",
    }:
        raise HistoricalMayoralDataError("canonical corpus must contain five cycles")
    outcomes_by_cycle: dict[str, list[MayoralOutcome]] = defaultdict(list)
    canonical_names_by_id: dict[str, set[str]] = defaultdict(set)
    for outcome in corpus.outcomes:
        if outcome.election_cycle_id not in election_by_id:
            raise HistoricalMayoralDataError("outcome references unknown election")
        if (
            outcome.source_document_id
            != election_by_id[outcome.election_cycle_id].source_document_id
        ):
            raise HistoricalMayoralDataError(
                "outcome source does not match its election manifest"
            )
        outcomes_by_cycle[outcome.election_cycle_id].append(outcome)
        canonical_names_by_id[outcome.candidate_id].add(outcome.candidate_name)
    if any(len(names) != 1 for names in canonical_names_by_id.values()):
        raise HistoricalMayoralDataError(
            "a candidate ID maps to conflicting canonical outcome names"
        )
    expected_counts = {
        "toronto_2010": 40,
        "toronto_2014": 65,
        "toronto_2018": 35,
        "toronto_2022": 31,
        "toronto_2023": 102,
    }
    expected_totals = {
        "toronto_2010": 813984,
        "toronto_2014": 981054,
        "toronto_2018": 755493,
        "toronto_2022": 551890,
        "toronto_2023": 724638,
    }
    for cycle, expected_count in expected_counts.items():
        rows = outcomes_by_cycle.get(cycle, [])
        if len(rows) != expected_count:
            raise HistoricalMayoralDataError(f"wrong candidate count for {cycle}")
        if len({row.candidate_id for row in rows}) != len(rows):
            raise HistoricalMayoralDataError(f"duplicate candidate ID for {cycle}")
        total = expected_totals[cycle]
        if {row.valid_vote_total for row in rows} != {total}:
            raise HistoricalMayoralDataError(
                f"wrong valid-vote denominator for {cycle}"
            )
        if sum(row.votes for row in rows) != total:
            raise HistoricalMayoralDataError(f"votes do not sum for {cycle}")
        winners = [row for row in rows if row.is_winner]
        if len(winners) != 1 or winners[0].votes != max(row.votes for row in rows):
            raise HistoricalMayoralDataError(f"invalid winner for {cycle}")
        for row in rows:
            exact = Decimal(row.votes) / Decimal(total)
            if abs(row.share - exact) > Decimal("0.000000000000000001"):
                raise HistoricalMayoralDataError(
                    f"incorrect share for {cycle}/{row.candidate_id}"
                )

    samples = {row.poll_sample_id: row for row in corpus.poll_samples}
    readings = {row.poll_reading_id: row for row in corpus.poll_readings}
    if len(samples) != len(corpus.poll_samples):
        raise HistoricalMayoralDataError("duplicate historical poll sample ID")
    if len(readings) != len(corpus.poll_readings):
        raise HistoricalMayoralDataError("duplicate historical poll reading ID")
    for sample in corpus.poll_samples:
        if sample.election_cycle_id not in election_by_id:
            raise HistoricalMayoralDataError("sample references unknown election")
        if sample.geography_type != "citywide" or sample.geography_id != "toronto":
            raise HistoricalMayoralDataError(
                "historical mayoral samples must use the Toronto citywide geography"
            )
    for reading in corpus.poll_readings:
        if reading.poll_sample_id not in samples:
            raise HistoricalMayoralDataError("reading references unknown sample")
        sample = samples[reading.poll_sample_id]
        expected_contest_id = sample.election_cycle_id.replace(
            "toronto_", "toronto-mayor-"
        )
        if (
            reading.contest_type != "mayoral"
            or reading.contest_id != expected_contest_id
        ):
            raise HistoricalMayoralDataError(
                "historical mayoral reading identifies the wrong contest"
            )
    for crosswalk in corpus.legacy_crosswalk:
        if crosswalk.election_cycle_id not in election_by_id:
            raise HistoricalMayoralDataError("crosswalk references unknown election")
        if crosswalk.disposition == "mapped" and (
            crosswalk.poll_sample_id not in samples
            or crosswalk.poll_reading_id not in readings
        ):
            raise HistoricalMayoralDataError("mapped crosswalk target is missing")
        if (
            crosswalk.disposition == "mapped"
            and samples[crosswalk.poll_sample_id].election_cycle_id
            != crosswalk.election_cycle_id
        ):
            raise HistoricalMayoralDataError(
                "mapped crosswalk sample belongs to another election"
            )
        if crosswalk.disposition == "non_poll" and (
            crosswalk.poll_sample_id is not None
            or crosswalk.poll_reading_id is not None
        ):
            raise HistoricalMayoralDataError("non-poll crosswalk row has canonical IDs")

    legacy_rows = _read_csv(legacy_poll_path, _LEGACY_POLL_COLUMNS)
    legacy_ids = {row["poll_id"] for row in legacy_rows}
    if legacy_ids != {row.legacy_poll_id for row in corpus.legacy_crosswalk}:
        raise HistoricalMayoralDataError(
            "legacy crosswalk does not cover every poll ID"
        )


def _candidate_id(year: int, candidate_name: str) -> str:
    known = _KNOWN_CANDIDATE_IDS.get(_normalized_name(candidate_name))
    return (
        known or f"toronto_{year}:{_normalized_name(candidate_name).replace(' ', '-')}"
    )


def _normalized_name(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    )
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.casefold()).strip()


def _slug(value: str) -> str:
    return _normalized_name(value).replace(" ", "_")


def _read_csv(path: Path, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    rows = _read_dict_rows(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        actual = tuple(csv.DictReader(handle).fieldnames or ())
    if actual != expected_columns:
        raise HistoricalMayoralDataError(
            f"{path.name} header must be exactly {expected_columns!r}; got {actual!r}"
        )
    return rows


def _read_dict_rows(path: Path) -> list[dict[str, str]]:
    try:
        handle = path.open(encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise HistoricalMayoralDataError(f"cannot read {path}: {exc}") from exc
    with handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise HistoricalMayoralDataError(f"{path} has no header")
        rows: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise HistoricalMayoralDataError(
                    f"{path.name} row {row_number} is ragged"
                )
            if all(value == "" for value in row.values()):
                raise HistoricalMayoralDataError(
                    f"{path.name} row {row_number} is blank"
                )
            rows.append(row)
        return rows


def _required(row: dict[str, str], field: str) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise HistoricalMayoralDataError(f"required field {field!r} is blank")
    return value


def _date(row: dict[str, str], field: str) -> date:
    value = _required(row, field)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HistoricalMayoralDataError(f"invalid {field} {value!r}") from exc


def _optional_date(row: dict[str, str], field: str) -> date | None:
    return None if not row.get(field, "").strip() else _date(row, field)


def _positive_int(row: dict[str, str], field: str) -> int:
    value = _required(row, field)
    try:
        parsed = int(value)
    except ValueError as exc:
        raise HistoricalMayoralDataError(f"invalid integer {field}={value!r}") from exc
    if parsed <= 0:
        raise HistoricalMayoralDataError(f"{field} must be positive")
    return parsed


def _nonnegative_int(row: dict[str, str], field: str) -> int:
    value = _required(row, field)
    try:
        parsed = int(value)
    except ValueError as exc:
        raise HistoricalMayoralDataError(f"invalid integer {field}={value!r}") from exc
    if parsed < 0:
        raise HistoricalMayoralDataError(f"{field} must be non-negative")
    return parsed


def _optional_int(value: str) -> int | None:
    if not value.strip():
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise HistoricalMayoralDataError(f"invalid optional integer {value!r}") from exc
    if parsed <= 0:
        raise HistoricalMayoralDataError("optional integer must be positive")
    return parsed


def _decimal(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise HistoricalMayoralDataError(f"invalid decimal {value!r}") from exc
    if not parsed.is_finite():
        raise HistoricalMayoralDataError(f"decimal must be finite: {value!r}")
    return parsed


def _optional_decimal(value: str) -> Decimal | None:
    return None if not value.strip() else _decimal(value)


def _share(row: dict[str, str], field: str) -> Decimal:
    parsed = _decimal(_required(row, field))
    if not Decimal(0) <= parsed <= Decimal(1):
        raise HistoricalMayoralDataError(f"{field} must be in [0, 1]")
    return parsed


def _boolean(row: dict[str, str], field: str) -> bool:
    value = _required(row, field).casefold()
    if value not in {"true", "false"}:
        raise HistoricalMayoralDataError(f"invalid boolean {field}={value!r}")
    return value == "true"


def _url(row: dict[str, str], field: str) -> str:
    value = _required(row, field)
    if not value.startswith(("https://", "http://")):
        raise HistoricalMayoralDataError(f"{field} must be an HTTP(S) URL")
    return value
