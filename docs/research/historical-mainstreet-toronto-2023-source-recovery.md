# Mainstreet 2023 Toronto mayoral source recovery

**Research date:** 2026-08-17  
**Scope:** the 19 unresolved Mainstreet Research entries in the 2023 Toronto
mayoral legacy inventory  
**Output boundary:** source-faithful promotion draft only; no shared canonical
CSV, crosswalk, schema, live input, test, or model file changed

## Outcome

Six of the 19 legacy respondent samples are recoverable from freely accessible
archived-original Mainstreet reports. The recovered corpus contains **nine PDF
editions, nine sample-document links, six distinct respondent samples, 12
dependent mayoral ballot readings, and 110 response rows**. Three April samples
have both a detailed and a shorter public edition; those paired documents are
two reports about one sample, not two polls.

The strict generic five-table draft is isolated at
`/private/tmp/mainstreet_2023/`. The nine raw reports are retained under the
gitignored path
`data/source_documents/historical_mayoral/mainstreet_2023/`. This was a public
archive recovery: it required no purchase, account, access-control bypass, or
direct request to Mainstreet.

The other **13 legacy entries remain unmatched**. Archived Mainstreet poll
pages and WordPress download routes survive for parts of that period, but no
source-grade PDF payload was recovered. A blocked or wrapper HTML capture is a
source lead, not a report, and has not been promoted.

## Recovered source inventory

Every retained file has a `%PDF-` signature, `application/pdf` media type, a
usable text layer, and a recorded byte size and SHA-256 digest in the draft
`source_documents.csv`. The table links to the exact archived payload used for
extraction.

| Fieldwork | Respondents | Archived-original report | Edition | Pages | Bytes |
|---|---:|---|---|---:|---:|
| Feb. 13-14 | 1,947 | [Mainstreet February report](https://web.archive.org/web/20230313205132id_/https://www.mainstreetresearch.ca/2023_Polls/Toronto/Toronto_Early_Feb_2023_QP-1.pdf?_t=1677786735) | full | 38 | 1,179,196 |
| Feb. 19 | 1,701 | [Mainstreet late-February report](https://web.archive.org/web/20230315221852id_/https://www.mainstreetresearch.ca/2023_Polls/Toronto/Toronto_Late_Feb_2023_QP-1.pdf?_t=1677823873) | full | 62 | 1,280,804 |
| Mar. 17-19 | 985 | [Mainstreet March report](https://web.archive.org/web/20230426201843id_/https://www.mainstreetresearch.ca/2023_Polls/Toronto/Toronto_Mar_17_2023.pdf) | full | 42 | 1,209,913 |
| Apr. 12-13 | 785 | [Mainstreet detailed report](https://web.archive.org/web/20230605231252id_/https://www.mainstreetresearch.ca/2023_Polls/Toronto/Toronto_2_April_12_2023.pdf) | detailed | 30 | 1,181,949 |
| Apr. 12-13 | 785 | [QP Briefing/iPolitics-hosted Mainstreet report](https://web.archive.org/web/20230415051420id_/https://old.ipolitics.ca/wp-content/uploads/2023/04/Toronto_2_April_12_2023_Public.pdf) | public | 20 | 1,134,083 |
| Apr. 17-19 | 1,082 | [Mainstreet detailed report](https://web.archive.org/web/20230421154737id_/https://www.mainstreetresearch.ca/2023_Polls/Toronto/Toronto_April_18_2023.pdf) | detailed | 14 | 1,090,586 |
| Apr. 17-19 | 1,082 | [QP Briefing/iPolitics-hosted Mainstreet report](https://web.archive.org/web/20250219225455id_/https://old.ipolitics.ca/wp-content/uploads/2023/03/Toronto_April_18_2023_Public.pdf) | public | 10 | 1,070,989 |
| Apr. 25-26 | 996 | [Mainstreet detailed report](https://web.archive.org/web/20230428125957id_/https://www.mainstreetresearch.ca/2023_Polls/Toronto/Toronto_April_26_2023.pdf) | detailed | 17 | 1,104,374 |
| Apr. 25-26 | 996 | [Mainstreet public report](https://web.archive.org/web/20230505182317id_/https://www.mainstreetresearch.ca/2023_Polls/Toronto/Toronto_April_26_2023_Public.pdf) | public | 12 | 1,079,877 |

All **245 physical pages** were rendered to PNG and visually inspected. No
page was corrupt, clipped, unexpectedly blank, or unreadable, and every
reported Total-column value used in the extraction was legible in the rendered
page. Public availability is not a redistribution licence: each report
expressly prohibits reproduction without written authorization, so the files
remain in the gitignored internal audit corpus and the draft records
redistribution as prohibited.

## Respondent-sample and reading lineage

Mainstreet's reports describe Smart IVR interviews with Toronto adults age 18
or older using landlines and cellphones. The February reports say interviews
were available in English and Mandarin; the four later reports say English.
The reports describe an intended voting population but do not document an
eligibility or turnout screen, so the extraction records `turnout_screen=none`
rather than inferring one.

The sample is the unit of independent evidence. Alternate fields, routed
questions, and all/decided products from the same respondents are dependent
readings:

| Parent sample | Retained ballot readings | Source-reported bases | Lineage boundary |
|---|---|---|---|
| Feb. 13-14, `n=1,947` | all voters | 1,947 | One complete all-respondent ballot. |
| Feb. 19, `n=1,701` | all voters | 1,701 | One complete all-respondent ballot. |
| Mar. 17-19, `n=985` | unrestricted all-voter ballot; restricted named-field all-voter ballot | 985; 985 | Two candidate fields from the same sample, not two polls. |
| Apr. 12-13, `n=785` | main all-voter ballot; no-Chow alternate ballot among preceding Chow voters | 785; 112 | The no-Chow denominator is the routed subgroup, despite the report's chart suffix saying “All voters.” |
| Apr. 17-19, `n=1,082` | all voters; source-labelled “Decided and Undecided”; decided voters | 1,082; 1,082; 763 | The first two products are numerically identical as published. Both are retained as dependent source objects without assuming or silently correcting an error. |
| Apr. 25-26, `n=996` | all voters; source-labelled “Decided and Undecided”; decided voters | 996; 996; 794 | Three dependent products from one sample. |

Only contest-preference questions are retained. Issue-priority and leader-trust
questions remain outside the ballot-reading bundle. Exact question text,
scenario labels, denominator wording, reported bases, response kinds, source
candidate labels, canonical candidate identities, and document locations are
preserved. The reports do not establish questionnaire order, so display order
is not presented as questionnaire order. Published one-decimal shares remain
exactly as printed, including columns that sum to 99.9% or 100.1% through
rounding; nothing is renormalized and no residual is invented.

The March restricted-field reading and April no-Chow reading matter for
historical learning, but they must never be counted as extra independent
polls. Likewise, the April public editions corroborate the preferred detailed
reports; they do not add readings or sample weight.

## Publication and evidence timing

Publication timing is source-specific rather than copied from the legacy
field-end proxy:

- The Feb. 13-14 sample is sponsored by QP Briefing. QP Briefing's owning
  article records machine-readable `publishedAt`
  **2023-02-17T22:45:19.612Z**, or **5:45:19 p.m. EST**, which is used as both
  publication and first-evidence time ([QP Briefing article](https://www.qpbriefing.com/news/torontonians-undecided-on-who-should-succeed-john-tory-poll)).
  The page visibly renders `10:45 p.m.`, but the first Wayback capture already
  existed at 8:39:09 p.m. EST; that visible hour therefore cannot be the
  literal release time. The machine-readable timestamp controls and the
  discrepancy remains explicit.
- No clean release-page body survives for the Feb. 19 sample. Its report's
  embedded creation date, Feb. 21, is retained only as a date-level publication
  proxy; the first verified archived-original payload capture, Mar. 7 at
  10:07:21 a.m. Toronto time, controls `evidence_available_at`. This explicitly
  avoids claiming that PDF creation proves public release.
- Mainstreet's clean archived March page reports `datePublished`
  **2023-03-20T15:00:46Z** ([archived first-party release](https://web.archive.org/web/20230322183201id_/https://www.mainstreetresearch.ca/poll/toronto-polling-march-2023/)).
- The clean archived Apr. 12-13 page reports `datePublished`
  **2023-04-14T23:24:15Z** ([archived first-party release](https://web.archive.org/web/20240204024557id_/https://www.mainstreetresearch.ca/poll/toronto-april-polling/)).
- The Apr. 17-19 release page survives only as a blocked archive replay. The
  detailed first-party PDF was captured on Apr. 21, so the draft preserves an
  Apr. 21 date-level publication estimate and makes it eligible at the next
  Toronto midnight instead of inventing a release time.
- The clean archived Apr. 25-26 page reports `datePublished`
  **2023-04-28T08:00:14Z** ([archived first-party release](https://web.archive.org/web/20230507073018id_/https://www.mainstreetresearch.ca/poll/toronto-final-april-poll/)).

These distinctions are only as fine-grained as needed to prevent look-ahead in
a historical evaluation. They do not claim unknowable precision.

## Legacy reconciliation

The six matched legacy sample sizes contain a consistent factor-of-ten parsing
error: `19470`, `17010`, `9850`, `7850`, `10820`, and `9960` correspond to
source-reported `n=1,947`, `1,701`, `985`, `785`, `1,082`, and `996`. Source
sample sizes supersede those values.

The legacy vectors are also transformed rather than raw report readings. The
following mappings identify the underlying source objects; they do not preserve
the legacy transformations:

| Legacy poll ID | Proposed sample / canonical reading | Reconciliation |
|---|---|---|
| `toronto_2023-2023-02-14-f879a53a` | `mainstreet_city_2023_02_13_14_n1947` / `mainstreet_2023_feb14_all` | Legacy values remove/merge residual kinds and round a subset; the complete raw all-voter reading supersedes them. |
| `toronto_2023-2023-02-19-b354d774` | `mainstreet_city_2023_02_19_n1701` / `mainstreet_2023_feb19_all` | Same factor-of-ten sample error and transformed-vector problem; use the complete raw all-voter reading. |
| `toronto_2023-2023-03-19-1cb19f92` | `mainstreet_city_2023_03_17_19_n985` / `mainstreet_2023_mar19_all` | Legacy values correspond to the unrestricted ballot after removing undecided and rounding, not the dependent restricted-field ballot. |
| `toronto_2023-2023-04-13-431601a9` | `mainstreet_city_2023_04_12_13_n785` / `mainstreet_2023_apr13_all` | Legacy values correspond to the main ballot after removing undecided and would-not-vote, not the routed no-Chow reading. |
| `toronto_2023-2023-04-20-3df69850` | `mainstreet_city_2023_04_17_19_n1082` / `mainstreet_2023_apr20_decided` | Legacy whole-number vector corresponds to the source's decided-voter product. |
| `toronto_2023-2023-04-26-a07c911c` | `mainstreet_city_2023_04_25_26_n996` / `mainstreet_2023_apr26_decided` | Legacy normalized whole-number values correspond to the decided product; the source's one-decimal values supersede them. |

The exact raw all-voter products remain available alongside these proposed
canonical mappings. Selecting one reading for compatibility does not discard
the dependent source readings or make them independent observations.

## Clean payloads versus blocked archive captures

The archive search covered Mainstreet's Toronto poll pages, its WordPress
`download/*` routes, the first-party `2023_Polls/Toronto/` directory, and the
QP Briefing/iPolitics media mirror. The [first-party Toronto poll-page CDX
index](https://web.archive.org/cdx/search/cdx?url=www.mainstreetresearch.ca/poll/toronto*&output=json&fl=timestamp,original,statuscode,mimetype,length,digest&filter=statuscode:200&collapse=urlkey&limit=1000)
and [first-party download-route CDX index](https://web.archive.org/cdx/search/cdx?url=www.mainstreetresearch.ca/download/*&output=json&fl=timestamp,original,statuscode,mimetype,length,digest&filter=statuscode:200&collapse=urlkey&limit=1000)
were used as inventories, not as substitutes for report content.

The nine admitted artifacts are clean static PDF payloads: their bytes,
signatures, media types, text layers, hashes, physical pages, and visible
tables all agree. By contrast, later Mainstreet captures fall into two
non-source-grade classes:

1. roughly 596-621-byte WordPress/Incapsula/Imperva block or error bodies, many
   sharing the same archive digest (`Z546DIFW65RQMCSSNCDESTNQWGZOAU5X`);
2. ordinary roughly 12 KB WordPress wrapper pages that expose download-manager
   IDs, while the matching archived download endpoint still replays HTML rather
   than a PDF payload.

Neither class contains report tables, methodology, exact question wording, or
respondent lineage. Relabelling an HTML block page as a PDF would obscure the
absence of evidence, so no such capture is in the five-table bundle. No access
control was probed or bypassed.

## Unmatched inventory

No clean first-party or archived-original report payload was found for these
13 legacy entries:

| Legacy poll ID | Legacy field-end proxy | Legacy `n` proxy | Status |
|---|---|---:|---|
| `toronto_2023-2023-04-03-c3a0fb42` | Apr. 3 | 13,060 | unmatched; no report payload |
| `toronto_2023-2023-05-03-ce518d01` | May 3 | 10,560 | unmatched; no report payload |
| `toronto_2023-2023-05-11-076ef4ef` | May 11 | 12,050 | unmatched; no report payload |
| `toronto_2023-2023-05-17-40ce4bce` | May 17 | 11,250 | unmatched; no report payload |
| `toronto_2023-2023-05-25-3a934378` | May 25 | 8,380 | unmatched; no report payload |
| `toronto_2023-2023-05-31-30f43af0` | May 31 | 11,100 | unmatched; no report payload |
| `toronto_2023-2023-06-08-1d2a2a3e` | June 8 | 7,060 | unmatched; no report payload |
| `toronto_2023-2023-06-11-2c161a34` | June 11 | 8,330 | unmatched; no report payload |
| `toronto_2023-2023-06-15-d7599146` | June 15 | 8,990 | unmatched; no report payload |
| `toronto_2023-2023-06-19-1629c424` | June 19 | 5,520 | unmatched; no report payload |
| `toronto_2023-2023-06-22-40f3d792` | June 22 | 14,810 | unmatched; no report payload |
| `toronto_2023-2023-06-24-7cdc9fdb` | June 24 | 9,400 | unmatched; no report payload |
| `toronto_2023-2023-06-25-c32aea31` | June 25 | 10,300 | unmatched; no report payload |

The legacy values remain useful discovery leads, but secondary toplines alone
cannot establish the question, denominator, bases, sample lineage, exact
candidate offer, response coverage, or publication timing required for an
audited source sample. These entries should remain unresolved rather than be
mapped by resemblance.

## Validation and recommendation

The generic strict loader and local artifact verifier both pass the isolated
draft:

```text
source_documents: 9
poll_sample_documents: 9
poll_samples: 6
poll_readings: 12
poll_responses: 110
rendered and visually inspected PDF pages: 245
```

A temporary in-memory append to the then-current historical generic tables
passed strict relational validation without writing them. Aggregate merged
counts are omitted because other historical recovery waves are being promoted
concurrently. An independent promotion audit also confirmed that this bundle
contains only `toronto_2023` / `toronto-mayor-2023` records and has no sample,
reading, or document IDs overlapping the current-cycle generic bundle.
Candidate identities, response-kind constraints,
sample/document/readings foreign keys, reported-value/share agreement,
artifact byte sizes, SHA-256 hashes, and PDF signatures all validate.

The proportionate next step is to promote the six recovered samples and the
six proposed legacy mappings mechanically, preserve all dependent readings,
and leave the other 13 entries explicitly unresolved. The archive evidence
does not currently justify paying for access: it shows that the obstacle is
missing historical payload capture, not a clearly purchasable current archive.
If a first-party or archived-original report later appears, it can be audited
against the same five-table contract without changing the model boundary.
