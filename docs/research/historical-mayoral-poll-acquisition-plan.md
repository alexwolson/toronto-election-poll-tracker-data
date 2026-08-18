# Historical mayoral poll acquisition plan

**Research date:** 2026-08-17

**Scope:** the 95 unresolved respondent-sample proxies in
[`legacy_historical_poll_crosswalk.csv`](../../data/raw/polls/legacy_historical_poll_crosswalk.csv)

**Purpose:** turn the existing availability audit into a small, executable retrieval queue. This note does not authorize publication or redistribution of restricted respondent data.

## Decision

Do not treat this as a hunt for 95 PDFs. The 95 unresolved samples are represented by 149 legacy poll/scenario IDs, and **71 samples already have an exact full-document lead**. Two more have source-grade first-party toplines or a factum. Only 22 currently lack an exact full-document lead; they may remain unavailable without blocking the project.

Use three acquisition lanes, in this order:

1. retrieve the small, deterministic public queue now;
2. use the three already-requested Borealis datasets as the preferred route for pre-2019 Forum data once access is approved;
3. consider paid access only when its catalogue can be shown to contain the exact missing material and its terms permit internal analytical use.

Direct requests to pollsters are out of scope. When public and verified purchasable routes are exhausted, the source is recorded as unavailable; neither model readiness nor publication may depend on a pollster replying to an unsolicited request.

Full demographic crosstabs are useful but are not required for the mayoral model. Stop searching once a source establishes the sample lineage, fieldwork and availability dates, target population, question and denominator, complete published response distribution, method, and usable sample/base size. A source-exact topline may therefore be admissible even when no table book survives; it must remain labelled as such.

## Reconciled inventory

These counts are respondent-sample proxies, not questions, scenarios, readings, releases, or files.

| Firm | Unresolved samples | Best acquisition route | Detail and access | Hard minimum currently identified |
|---|---:|---|---|---:|
| Forum Research | 45 | Borealis for the 33 pre-2019 proxies; Forum originals and Wayback for all years | Restricted respondent tables plus public codebooks; public archived full releases | 39 exact full-release leads; six weaker cases. Borealis overlaps these leads and is not additional coverage. |
| Mainstreet | 28 | Wayback/Scribd, then a verified paid archive if one exists | Public or archived full reports for some; no proven historical coverage from the current subscription | 13 exact full-report leads; 15 currently unavailable full-detail cases |
| Liaison Strategies | 11 | First-party releases plus Liaison's Scribd publisher records; paid viewer access only if needed and useful | Every first-party release is public; 11 full-report viewer records are public but durable download is awkward | 11 exact full-report leads |
| Ipsos | 5 | Direct first-party table PDFs | Public full tables | 5 exact full-table leads |
| Nanos Research | 2 | Direct report; then subscriber archive only if the exact missing report is listed | One live full report; one known dead path | 1 exact full-report lead; 1 currently unavailable case |
| Maple Leaf Strategies | 1 | Archived first-party PDF | Public complete release, without demographic crosstabs | 1 complete-release lead |
| Viewpoints Research | 1 | Direct WordPress media PDF | Public full marginals report | 1 exact full-report lead |
| DART | 1 | Archived first-party factum | Complete questionnaire/factum toplines; the only detailed-table capture is truncated | 1 source-grade factum, not a full table book |
| Probit | 1 | First-party X post and original images | Public all-voter and decided-voter charts | 1 source-grade chart pair, not a full table book |
| **Total** | **95** |  |  | **71 full-document leads + 2 source-grade toplines/facta + 22 full-detail tasks** |

The 2014 file creates most of the apparent duplication: Forum has 71 legacy scenario IDs but 28 respondent samples. All/decided results, alternate candidate fields, a release and its table attachment, and public/full editions remain dependent readings or documents from one sample.

## Lane 1: smallest public first wave

Retrieve and source-audit these **11 artifacts representing 10 unresolved respondent samples** first. They are live or have a verified archived-original replay and cover three election cycles without any account or purchase:

1. Five Ipsos table attachments: [November 2013](https://www.ipsos.com/sites/default/files/publication/2013-11/6317-tb1.pdf), [September 16, 2014](https://www.ipsos.com/sites/default/files/publication/2014-09/6599-tb1.pdf), [September 26, 2014](https://www.ipsos.com/sites/default/files/publication/2014-09/6609-tb1.pdf), [October 23, 2014](https://www.ipsos.com/sites/default/files/publication/2014-10/6648-tb1.pdf), and [June 2023](https://www.ipsos.com/sites/default/files/ct/news/documents/2023-06/Toronto%20Mayoral%20Race%20Tables%202.pdf). The September 26 artifact is a one-page excerpt and October 23 is a four-page selected-table attachment, not a full table book; both still contain the required published result table.
2. The remaining unresolved [Viewpoints June 1–2, 2023 marginals report](https://viewpoints.ca/wp-content/uploads/2023/06/Toronto-Mayoral-By-Election-Marginals-Report-20230608-1.pdf).
3. The [Nanos July 3–5, 2014 report with tables](https://nanos.co/wp-content/uploads/2017/07/2014-541-OCSA-Report-FINAL-w-tabs-R-1.pdf).
4. The [Maple Leaf Strategies July 2014 archived release](https://web.archive.org/web/20140808050914id_/http://mapleleafstrategies.com/wp-content/uploads/2014/07/Tory-Leads-Ford-No-Growth-Room.pdf).
5. The [DART 2018 factum](https://web.archive.org/web/20181023234340id_/http://dartincom.ca/wp-content/uploads/2018/10/Sun-Toronto-Election-Factum-1-Oct-2018.pdf). Do not accept the companion 32-page capture as complete: its replay stops at exactly 1,048,576 bytes.
6. The Probit 2018 [decided-voter](https://pbs.twimg.com/media/Dmg-TobW4AEnYm2.jpg:large) and [all-voter](https://pbs.twimg.com/media/Dmg-TpGXcAU_j3-.jpg:large) originals, linked from the [pollster's post](https://x.com/ProbitInc/status/1038148223423184896).

Also retrieve one high-leverage corroborating artifact: Forum's [June 24, 2023 final release](https://web.archive.org/web/20230726065606id_/https://poll.forumresearch.com/data/cb12c41a-8453-40e6-90f1-7558d098f7e1Chow%20lead%20narrowing%20in%20final%20days%20of%20campaign_June%2024%202023.pdf). It gives full tables for the June 23 sample and a decided/leaning trend table for nine Forum waves from April 25–26 through June 23. The eight earlier trend columns are useful cross-checks, not substitutes for their sample-specific release metadata.

This first wave is deliberately small. It tests the extraction path and adds source-correct evidence before any large archive download.

## Lane 2: Forum through Borealis

The University of Toronto Map & Data Library says its Forum collection contains Toronto municipal polling from 2013 onward and is downloadable by Ontario-university students, staff and faculty; other researchers may request access. The user's requests for these three datasets are already pending:

| Dataset | DOI | Public codebooks | Restricted respondent tables | Maximum matching unresolved proxies |
|---|---|---:|---:|---:|
| Toronto Municipal 2013 | [10.5683/SP3/2ANYFR](https://doi.org/10.5683/SP3/2ANYFR) | 12 | 12 | part of the 28 Forum 2013–14 proxies |
| Toronto Municipal 2014 | [10.5683/SP3/IM2A0R](https://doi.org/10.5683/SP3/IM2A0R) | 15 | 15 | part of the 28 Forum 2013–14 proxies |
| Toronto Municipal 2018 | [10.5683/SP2/QCPM89](https://doi.org/10.5683/SP2/QCPM89) | 10 | 10 | 5 Forum 2018 proxies |

The 37 respondent files are broader than the 33 unresolved pre-2019 Forum proxies and must be date/question matched. They do **not** count as 37 extra polls.

Public metadata and file IDs are available without authentication:

```bash
curl -sS 'https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi:10.5683/SP3/2ANYFR'
curl -sS 'https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi:10.5683/SP3/IM2A0R'
curl -sS 'https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi:10.5683/SP2/QCPM89'
```

After approval, create an API token in Borealis account settings and keep it out of chat, shell history, and the repository. Probe one respondent file from each dataset before downloading bundles:

```bash
curl -L -H "X-Dataverse-key:$BOREALIS_API_TOKEN" \
  'https://borealisdata.ca/api/access/datafile/8650' \
  -o FO1C_DATA_20131219.tab

curl -L -H "X-Dataverse-key:$BOREALIS_API_TOKEN" \
  'https://borealisdata.ca/api/access/datafile/9120' \
  -o FO4M_DATA_20140311.tab

curl -L -H "X-Dataverse-key:$BOREALIS_API_TOKEN" \
  'https://borealisdata.ca/api/access/datafile/72462' \
  -o Toronto_August_2018.tab
```

If labels, question text, weights, and cases are usable, download each approved dataset bundle using Dataverse's documented Data Access API:

```bash
curl -L -O -J -H "X-Dataverse-key:$BOREALIS_API_TOKEN" \
  'https://borealisdata.ca/api/access/dataset/:persistentId/?persistentId=doi:10.5683/SP3/2ANYFR'
```

Repeat with the other two DOIs. Inspect `MANIFEST.TXT` because a bundle can succeed while silently omitting inaccessible files. Do not publish or redistribute respondent files until their licence and access terms have been checked.

If Borealis access is denied or its variables are unusable, enumerate archived Forum PDFs instead:

```bash
curl -sS \
  'https://web.archive.org/cdx/search/cdx?url=poll.forumresearch.com/data/*&output=json&filter=statuscode:200&filter=mimetype:application/pdf&fl=timestamp,original,statuscode,digest&collapse=digest'
```

That endpoint was live on the research date and returned 1,391 unique Forum PDF captures across all subjects. Match exact Toronto titles/dates before replaying any file. The old Forum host itself currently returns a maintenance page, so a stored original URL is only a lead until its Wayback bytes are verified.

## Lane 3: Mainstreet and Liaison public or paid archives

### Mainstreet

The 28 unresolved Mainstreet samples divide into 13 exact full-report leads and 15 cases currently lacking a verified public or purchasable archive. The batchable 2023 first-party directory currently yields six respondent samples (plus a public/full duplicate):

```bash
curl -sS \
  'https://web.archive.org/cdx/search/cdx?url=www.mainstreetresearch.ca/2023_Polls/Toronto/*&output=json&fl=timestamp,original,statuscode,mimetype,length,digest&filter=statuscode:200&collapse=digest'
```

Those six are February 14, February 19, March 19, April 13, April 20, and April 26. Exact older full-report leads are:

- 2014 September 12: [archived first-party PDF](https://web.archive.org/web/20140913214848/http://mainstreetzone.mainstreettechno.netdna-cdn.com/mainstreet/wp-content/uploads/2014/09/Mainstreet-Toronto-Mayoral-and-Ward-2-September-13.pdf); September 21: [Scribd 240548385](https://www.scribd.com/document/240548385); September 28: [241314474](https://www.scribd.com/document/241314474); October 5: [242035582](https://www.scribd.com/document/242035582); October 23: [244228439](https://www.scribd.com/document/244228439).
- 2018 September 16: [Scribd 388824269](https://www.scribd.com/document/388824269); September 25: [389471142](https://www.scribd.com/document/389471142).

Do not spend hours reconstructing the remaining 15 individually. The exact missing dates are 2014 October 17; 2018 September 5; and 2023 April 3, May 3, May 11, May 17, May 25, May 31, June 8, June 11, June 15, June 19, June 22, June 24, and June 25. No evidence found in this audit shows that Mainstreet's current subscription includes these historical reports. Do not purchase it for this purpose unless a public catalogue or product description first establishes that coverage and permits durable internal analytical use. Otherwise record these cases as unavailable in full detail while retaining any source-grade public toplines.

### Liaison

All 11 first-party press releases remain enumerable from [Liaison's sitemap](https://press.liaisonstrategies.ca/sitemap-posts.xml), and all publish fieldwork, parent sample size, method, all-voter results, and decided-voter results. Liaison's own Scribd publisher records identify a full report for every sample:

| Fieldwork end | Scribd document |
|---|---|
| 2023-04-22 | [640520195](https://www.scribd.com/document/640520195) |
| 2023-04-29 | [641979949](https://www.scribd.com/document/641979949) |
| 2023-05-06 | [643701013](https://www.scribd.com/document/643701013) |
| 2023-05-13 | [645478285](https://www.scribd.com/document/645478285) |
| 2023-05-18 | [646880402](https://www.scribd.com/document/646880402) |
| 2023-05-27 | [649083839](https://www.scribd.com/document/649083839) |
| 2023-06-04 | [651023358](https://www.scribd.com/document/651023358) |
| 2023-06-11 | [652661765](https://www.scribd.com/document/652661765) |
| 2023-06-13 | [653169044](https://www.scribd.com/document/653169044) |
| 2023-06-18 | [654274535](https://www.scribd.com/document/654274535) |
| 2023-06-23 | [655112063](https://www.scribd.com/document/655112063) |

Several migrated Ghost posts embed the wrong May 29 document, so match on report title and fieldwork rather than trusting the current embed. Use the public releases as source-grade toplines wherever a durable full report cannot be obtained. A paid Scribd route may be considered only if it demonstrably unlocks the identified documents and its terms permit the intended internal use; do not scrape around access controls.

## Remaining one-off cases

- **Nanos:** the July report is public, while the known August path returns 404. The [2014 reports page](https://nanos.co/2014-reports/) is subscriber-only, but there is no evidence yet that it contains this specific file. Buy access only if the exact report can first be verified in the subscriber catalogue; otherwise mark it unavailable.
- **Forum post-2019:** Borealis has no identified Toronto municipal datasets after 2019. Use exact Forum/Wayback releases for the 2022 sample and ten of eleven 2023 samples. Treat the unmatched 2023 wave or a failed replay as unavailable after the public archive pass.
- **DART and Probit:** the recovered factum/charts may already meet the model's historical topline rule. If the canonical admissibility check finds a missing essential field and no public or verified paid source exists, mark the richer document unavailable.

## User actions and stop conditions

The only immediate user-dependent step is to wait for the three Borealis access decisions. When approval arrives:

1. generate an API token privately;
2. test the three single-file commands above;
3. confirm whether the files have labels, weights, and the mayoral ballot questions;
4. then authorize the three bundle downloads.

No direct pollster outreach is part of the workflow. A purchase decision should be presented to the user only with evidence that the exact missing documents are included, the price is known, and the intended internal analytical use is permitted.

Stop the search when every sample is either source-audited, explicitly admissible as a source-grade topline, or explicitly unavailable after its public and verified purchasable routes. The model should carry those distinctions rather than making completeness a precondition for starting.

## Verification record

On 2026-08-17:

- all five Ipsos PDFs, the remaining Viewpoints PDF, the Nanos July PDF, the Maple Leaf replay, the DART factum, and both Probit images returned successful first-party or archived-original bytes;
- the DART detailed-table replay returned exactly 1,048,576 bytes and remains classified as truncated;
- all 11 Liaison Scribd records returned public viewer pages;
- the Forum CDX endpoint returned 1,391 unique PDF captures, while the old Forum host returned a maintenance response;
- Borealis public metadata listed 12, 15, and 10 restricted respondent tables for 2013, 2014, and 2018 respectively; a public codebook returned HTTP 200 and a restricted table returned HTTP 403 without authorization;
- the [University of Toronto collection page](https://mdl.library.utoronto.ca/collections/numeric-data/microdata/forum-research-political-polls) states the institutional access condition; and
- the bundle and token commands above follow the official [Dataverse Data Access API](https://guides.dataverse.org/en/latest/api/dataaccess.html).
