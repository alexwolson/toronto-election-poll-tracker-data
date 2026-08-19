# Unresolved poll proxies — source hunt

**Purpose:** These are the historical Toronto mayoral polls the model still knows
only as *legacy proxies* (numbers scraped from Wikipedia), with no first-party
source recovered. Before any of them is marked "unavailable," this is the list to
hunt through. If you can find a first-party report for one, we can ingest it and
retire the proxy properly.

**How to use:** flip the **Found?** box from `[ ]` to `[X]` when you locate a
first-party report, then hand it to me (or drop the PDF under
`data/source_documents/historical_mayoral/`) and I'll extract + retire it.

**Status:** 15 of these were found and ingested (first-party reports where they
exist, else newspaper / CP24 toplines) and their proxies retired — [X] below.
**9 remain unresolved** ([ ]): Forum 2014-01-06 and 2023-06-16, plus seven
Mainstreet 2023 dates with no public source (premium did not include them).

## What counts as a usable source

A first-party **report or press release** (PDF, or a web page we can render) that
prints the actual mayoral horserace table — ideally the **all-respondents /
including-undecided** column, and the **decided-voter** column if shown. That's
the same standard everything else in the corpus meets.

The percentages in the tables below are the **Wikipedia-recorded** numbers. They
identify *which* poll to look for; they are not themselves admissible (they were
normalized and residuals were combined). So use them to confirm you've found the
right report, then we extract from the report itself.

## Where the recovered ones came from (what works)

- **Forum:** archived first-party PDFs on the Wayback Machine. Query the CDX API
  for `forumresearch.com` / `poll.forumresearch.com` PDFs (not WebFetch — it
  can't reach web.archive.org). Files live under `forms/News Archives/News
  Releases/` and `.../In The News/`, and later under `poll.forumresearch.com/data/`.
- **Mainstreet:** Scribd documents (need a login/download) and the
  `mainstreetresearch.ca/2023_Polls/Toronto/` directory on Wayback.
- **Nanos:** first-party reports were on `nanos.co` / `nanosresearch.com`; some
  waves surfaced only via CTV/CP24 media coverage.

---

## Leads worth trying first

- **2014-02-24 (Forum)** — very likely the **same poll as the `forum_2014_feb25`
  report already in the corpus** (fieldwork Feb 24, released Feb 25). If its
  readings match these toplines (Tory 39 / Ford 33 / Stintz 15), this is a quick
  *map*, not a hunt. Check before searching.
- **2014-09-22 (Forum)** — partial source already exists: the corpus has the
  `forum_2014_sep22` sample (binary tables + a trend row). Forum *omitted* the
  full current-field crosstab in that release, so these two proxies were left
  unresolved as not source-equivalent. A different Forum release that reprints
  the Sep 22 full field would resolve it.
- **2014-10-17 (Mainstreet)** — the one missing weekly *between* Oct 5 and Oct 23,
  both of which we have. Almost certainly a Scribd report like its neighbours;
  search Scribd for "Mainstreet Toronto Mayoral October 17 2014."
- **Nanos 2014-08-31** — the corpus has Nanos July and September 2014; this is the
  late-August wave. Look in a Nanos report archive or the CTV/CP24 coverage.
- **Mainstreet 2023 (13 dates)** — the by-election tracker. Only 6 of the 2023
  waves were on the public `2023_Polls/Toronto/` directory; these 13 may be
  behind Mainstreet's subscription, on Scribd, or in the sponsor's coverage
  (QP Briefing / iPolitics). Their sample sizes below are the Wikipedia field
  divided by 10 (it was stored ×10), shown as ≈.

---

### 2014 cycle

| Found? | Date | Firm | n | Known toplines (Wikipedia-recorded %) |
|:---:|---|---|---|---|
| [X] | 2013-03-21 | Forum | not recorded | Chow 43, R. Ford 32, Other / undecided 25 <br> Chow 47, R. Ford 32, Other / undecided 21 <br> Chow 60, R. Ford 33, Other / undecided 7 |
| [X] | 2013-05-13 | Forum | not recorded | Chow 44, R. Ford 27, Tory 25, Other / undecided 4 <br> Tory 50, R. Ford 33, Other / undecided 17 <br> R. Ford 35, Chow 34, Stintz 11, Other / undecided 20 <br> Chow 57, R. Ford 36, Other / undecided 7 |
| [X] | 2013-11-24 | Forum | not recorded | Chow 33.7, R. Ford 30.7, Tory 19.8, Stintz 6.9, Soknacki 3.0, Other / undecided 5.9 <br> Chow 33.7, R. Ford 30.7, Tory 21.8, Stintz 6.9, Soknacki 4.0, Other / undecided 3.0 <br> Stintz 40, R. Ford 35, Soknacki 13, Other / undecided 12 |
| [ ] | 2014-01-06 | Forum | not recorded | R. Ford 35, Chow 30, Tory 22, Stintz 5, Soknacki 3, Other / undecided 5 |
| [X] | 2014-02-09 | Forum | not recorded | Chow 35, R. Ford 30, Tory 22, Stintz 6, Soknacki 3, Other / undecided 4 <br> R. Ford 35, Stintz 35, Soknacki 16, Other / undecided 14 |
| [X] | 2014-02-24 | Forum | not recorded | Tory 39, R. Ford 33, Stintz 15, Soknacki 5, Other / undecided 8 <br> Tory 33, Chow 32, R. Ford 32, Other / undecided 3 <br> Chow 31, R. Ford 31, Tory 27, Stintz 6, Soknacki 2, Other / undecided 3 |
| [X] | 2014-08-31 | Nanos | not recorded | Tory 21.1, R. Ford 14.1, Chow 13.1, Soknacki 1.5, Other / undecided 50.2 <br> Tory 17.2, R. Ford 11.6, Chow 10.6, Soknacki 1.5, Other / undecided 59.1 |
| [X] | 2014-09-22 | Forum | not recorded | Tory 38, D. Ford 30, Chow 24, Other / undecided 8 <br> Tory 19.2, D. Ford 15.7, Chow 12.6, Other / undecided 52.5 |
| [X] | 2014-10-17 | Mainstreet | not recorded | Tory 38, D. Ford 29, Chow 22, Other / undecided 11 <br> Tory 42.2, D. Ford 31.4, Chow 23.5, Other / undecided 2.9 |

### 2018 cycle

| Found? | Date | Firm | n | Known toplines (Wikipedia-recorded %) |
|:---:|---|---|---|---|
| [X] | 2018-09-05 | Mainstreet | not recorded | Tory 62.4, Keesmaat 27.7, Other / undecided 9.9 |

### 2023 by-election

| Found? | Date | Firm | n | Known toplines (Wikipedia-recorded %) |
|:---:|---|---|---|---|
| [X] | 2023-04-03 | Mainstreet | ≈1306 | Olivia Chow 24, Ana Bailão 23, Mark Saunders 13, Josh Matlow 9, Brad Bradford 8, Mitzie Hunter 7, Other / undecided 16 |
| [X] | 2023-05-03 | Mainstreet | ≈1056 | Olivia Chow 30.7, Ana Bailão 16.8, Josh Matlow 14.8, Mark Saunders 11.9, Mitzie Hunter 8.9, Brad Bradford 5.9, Other / undecided 10.9 |
| [ ] | 2023-05-11 | Mainstreet | ≈1205 | Olivia Chow 31, Ana Bailão 15, Mark Saunders 12, Josh Matlow 10, Mitzie Hunter 9, Anthony Furey 7, Brad Bradford 6, Chloe Brown 5, Other / undecided 5 |
| [X] | 2023-05-17 | Mainstreet | ≈1125 | Olivia Chow 30, Ana Bailão 21, Josh Matlow 14, Mark Saunders 10, Mitzie Hunter 9, Anthony Furey 7, Brad Bradford 4, Chloe Brown 2, Other / undecided 3 |
| [ ] | 2023-05-25 | Mainstreet | ≈838 | Olivia Chow 35, Ana Bailão 16, Mark Saunders 12, Josh Matlow 10, Anthony Furey 9, Brad Bradford 6, Mitzie Hunter 5, Chloe Brown 2, Other / undecided 5 |
| [ ] | 2023-05-31 | Mainstreet | ≈1110 | Olivia Chow 32, Ana Bailão 16, Mark Saunders 12, Josh Matlow 10, Anthony Furey 9, Mitzie Hunter 7, Brad Bradford 4, Chloe Brown 4, Other / undecided 6 |
| [ ] | 2023-06-08 | Mainstreet | ≈706 | Olivia Chow 28.4, Ana Bailão 19.6, Mark Saunders 12.8, Josh Matlow 10.8, Anthony Furey 8.8, Mitzie Hunter 8.8, Brad Bradford 3.9, Chloe Brown 2.9, Other / undecided 3.9 |
| [ ] | 2023-06-11 | Mainstreet | ≈833 | Olivia Chow 32.7, Ana Bailão 16.8, Mark Saunders 13.9, Anthony Furey 8.9, Mitzie Hunter 7.9, Josh Matlow 5.9, Chloe Brown 5.0, Brad Bradford 3.0, Other / undecided 5.9 |
| [X] | 2023-06-15 | Mainstreet | ≈899 | Olivia Chow 31, Ana Bailão 14, Mark Saunders 13, Josh Matlow 12, Anthony Furey 11, Mitzie Hunter 6, Chloe Brown 5, Brad Bradford 4, Other / undecided 4 |
| [ ] | 2023-06-16 | Forum | ≈1006 | Olivia Chow 31.4, Mark Saunders 14.7, Ana Bailão 12.8, Anthony Furey 12.8, Josh Matlow 8.8, Mitzie Hunter 5.9, Brad Bradford 3.9, Other / undecided 9.8 |
| [X] | 2023-06-19 | Mainstreet | ≈552 | Olivia Chow 36, Ana Bailão 13, Mark Saunders 13, Josh Matlow 12, Anthony Furey 7, Mitzie Hunter 7, Chloe Brown 4, Brad Bradford 3, Other / undecided 5 |
| [X] | 2023-06-22 | Mainstreet | ≈1481 | Olivia Chow 30, Ana Bailão 22, Anthony Furey 13, Mark Saunders 12, Josh Matlow 9, Mitzie Hunter 5, Brad Bradford 2, Chloe Brown 2, Other / undecided 5 |
| [ ] | 2023-06-24 | Mainstreet | ≈940 | Olivia Chow 34, Ana Bailão 25, Mark Saunders 11, Anthony Furey 10, Josh Matlow 7, Mitzie Hunter 5, Chloe Brown 2, Brad Bradford 1, Other / undecided 5 |
| [ ] | 2023-06-25 | Mainstreet | ≈1030 | Olivia Chow 35.6, Ana Bailão 29.7, Mark Saunders 8.9, Anthony Furey 7.9, Josh Matlow 7.9, Mitzie Hunter 5.0, Brad Bradford 1.0, Chloe Brown 1.0, Other / undecided 3.0 |

---

## After a source is found

Hand me the report (or a link / the PDF placed under
`data/source_documents/historical_mayoral/`) and I'll run it through the
double-read extraction + ingest, then retire its proxy in the crosswalk — same
flow as the Forum and Mainstreet batches.

Anything that stays genuinely unrecoverable will get an explicit
`no_public_source` disposition so the calibration blocker can clear.