# Availability of detailed documents for the Toronto polling corpus

**Research date:** 2026-08-17  
**Scope:** the repository's historical mayoral polls, current-cycle mayoral polls, the six previously identified 2022 Council polls, and every current-cycle Council poll found in first-party archives  
**Purpose:** estimate acquisition difficulty before deciding how much detailed-document coverage the rebuilt models should require. This note does not set a model, publication, licensing, or purchase policy. The subsequently settled project policy is public retrieval first, verified purchasable access second, and explicit unavailability after those routes; direct pollster requests are out of scope.

## Bottom line

Getting a **useful validation corpus** is feasible. Getting a **perfect PDF for every row currently called a poll** is not: some rows came from HTML releases, client news stories, X posts, or access-gated commentary, and a PDF may never have been public.

The acquisition problem is smaller than the raw row count but larger than the current repository implies:

- `historical_mayoral_polls.csv` contains 153 `poll_id` values. Grouping same-firm, same-date, same-size scenarios gives **98 Distinct Poll Sample proxies**: 43 for the 2014 file, 10 for 2018, one for 2022, and 44 for 2023. The 2014 file contains 55 additional scenario rows from the same samples, not 55 additional samples.
- That apparent total contains one non-poll: the 2010 election result is stored as a 2014 polling observation. Conversely, the current public 2023 source table has a third Viewpoints survey that the parser omitted. Correcting those two errors leaves **98 actual historical mayoral sample proxies**.
- `polls.csv` contains 22 current mayoral rows but only **19 sample proxies**: the three Forum ballot scenarios of September 2025 share one sample, as do the two Pallas scenarios of March 2026.
- The previous Council research found **six historical 2022 ward samples**. Forum's new first-party archive exposes **six current Council samples**, although `ward_poll_readings.csv` contains only one of them.

The resulting source-gap inventory is therefore about **129 respondent samples**: 98 historical mayoral, 19 current mayoral, six historical Council, and six current Council. Each sample may contain several questions, denominators, or ballot scenarios.

For historical mayoral validation, approximately **80–85 of the 98 samples have an identifiable full-document lead**—a direct PDF, a first-party report attachment, or a Scribd document. That is not a recovery count. Many old Mainstreet links now return 404, old Forum is intermittently unavailable, Scribd is awkward to batch-download, and several Wayback captures still need verification.

The current mayoral side is much easier: **18 of 19 sample proxies already have public full-detail sources**, counting Canada Pulse's machine-readable workbook alongside PDFs. The only current sample without a downloadable table book is Abacus January 2026; its first-party release is now identified, but it is access-gated and publishes only ballot results.

The practical workloads are:

| Scope | Retrieval and provenance | Structured extraction and visual QA | Expected result |
|---|---:|---:|---|
| **A. Full corpus:** about 129 samples | 4–7 focused person-days | 5–8 person-days | A broad archive with a small explicit set of unrecoverable or topline-only samples; not guaranteed 100% PDF coverage |
| **B. Minimum canonical validation set:** roughly 52–56 post-Final historical mayoral samples plus six 2022 Council samples | 1–3 person-days | 3–5 person-days | Enough to learn whether the proposed post-Final gates can be evaluated without first solving every early hypothetical poll |

Those estimates assume a scripted manifest, batch downloads where possible, OCR only where necessary, and human verification of every extracted vote-intention table. They exclude waiting time for access requests. The project owner works at the University of Toronto, and the official Forum collection page expressly permits downloads by Ontario-university students, staff and faculty. Authenticated access still needs to be tested, but this makes the U of T collection—not one-PDF-at-a-time Wayback searching—the likely first acquisition route. A verified purchasable historical archive could reduce both workloads further, but none is assumed.

If the restricted Forum `.tab` files download cleanly with usable labels and weights, both retrieval and extraction should move toward the low end of those ranges. They still need to be mapped to public releases and proxy dates; institutional access is not itself proof that a record belongs in the historical corpus.

## Classification used

The requested availability classes are used as follows:

- **Full tables/questionnaire available:** a first-party or archived-original document exposes the relevant question, response rows and sample/method details. It need not contain respondent microdata.
- **Release/topline only:** a first-party or commissioning-client release gives results but no recoverable complete table book or questionnaire.
- **Dead link:** the recorded document endpoint no longer serves the document and no archived original was verified during this pass.
- **Access-restricted/paywalled:** the artifact exists behind a login, subscription, institutional restriction, or viewer that does not provide a durable public download.
- **Source identity unresolved:** the corpus cannot yet identify the owning source document or stable sample lineage.

Some entries have two statuses. For example, a public release may be available while the corresponding full tables are access-restricted. A URL labelled as a PDF in an old index is only a **document lead** until the bytes, page count, contents, retrieval date and checksum have been verified.

## Corpus defects discovered before document retrieval

Detailed-document work is already necessary to repair the sample inventory itself:

1. **The historical parser discarded the row source URLs.** Every row in `historical_mayoral_polls.csv` points only to one of four Wikipedia election articles. The underlying table still links the pollster or commissioning-client source, but the repository does not preserve it.
2. **The 2010 result is not a poll.** `toronto_2014-2010-10-25-6a933a5f` is an election result used as if it were a 2014 polling observation.
3. **One 2023 Viewpoints sample is missing from the repository.** The Apr. 29–May 2 survey and its first-party report are public, but the historical date parser cannot parse a range spanning two months.
4. **Historical sample sizes are frequently ten times too large.** Values such as `1,007.0` are converted by removing non-digits, producing `10070`. This affects the 2022 and 2023 files, including both imported Viewpoints samples.
5. **Current source URLs are absent.** `polls.csv` has no `source_url` column, even where the pollster publishes a stable report attachment.
6. **Current Council coverage is incomplete.** Only Ward 13 is present. The first-party Forum archive exposes Ward 5, Ward 11, Ward 13, Ward 19 twice, and Ward 20.
7. **Release dates are not always publication timestamps.** Four Forum ward releases carry a `newsDate` of June 24 but API `createdDate`/`goLiveDateTimeUTC` values on June 29. The source may have appeared through a client earlier, but that cannot be assumed from the dated PDF alone.

These are not modelling details. They determine how many samples exist and when their evidence was public.

## Historical mayoral inventory

### Counts by election and firm

| Election file | Firm | Poll-row proxies | Distinct Poll Sample proxies | Source-document situation |
|---|---|---:|---:|---|
| 2014 | Forum Research | 71 | 28 | 23 rows link a Forum PDF endpoint; five point to client/HTML releases. Old Forum hosting is unreliable, but search indexes and archived originals preserve many documents. Forum microdata may offer a second route. |
| 2014 | Mainstreet Technologies | 12 | 6 | Direct PDF or Scribd report leads exist for five samples; the Oct. 17 source is an archived first-party release. Several documents require manual Scribd/Wayback work. |
| 2014 | Ipsos-Reid | 7 | 4 | **Four of four full.** All four first-party release/table sets remain live. |
| 2014 | Nanos Research | 5 | 3 | **Two of three full.** July and September reports with tables are live. The August release's exact first-party path is known but returns 404 and no complete capture was found. |
| 2014 | Maple Leaf Strategies | 2 | 1 | **One of one complete release recovered.** The archived two-page PDF has method, exact ballot question, all/decided results and secondary toplines, but no demographic crosstabs. |
| 2014 | `2010 Election` | 1 | 1 | **Not a poll.** Remove from the polling corpus. |
| 2018 | Forum Research | 5 | 5 | Five full-release PDF leads. One was already labelled a permanent dead link; archived-original and restricted-data routes need verification. |
| 2018 | Mainstreet Research | 3 | 3 | The original site pages now return 404. Two full reports are readily discoverable on Scribd; the third remains a migrated-link recovery task. |
| 2018 | Probit Inc. | 1 | 1 | **First-party chart/topline only.** The X post and both original result images survive; no questionnaire or table book was located. |
| 2018 | DART Insight and Communications | 1 | 1 | **Factum/questionnaire toplines recovered.** Wayback has the five-page original. A separate 32-page detailed-table URL exists, but its only capture is truncated and corrupt. |
| 2022 | Forum Research | 1 | 1 | Full-release PDF lead; Forum/Wayback or restricted archive retrieval. |
| 2023 | Mainstreet Research | 19 | 19 | Fourteen rows point to a first-party report/download path; most old paths now return 404. Wayback enumeration found at least six clean report files for the 19 dates; the later download-manager era remains a deeper recovery task. |
| 2023 | Forum Research | 11 | 11 | Full Forum releases are search-indexed and the final release contains a same-firm trend table. Exact original filenames were found for 10 of 11 repository dates; June 18 remains unmatched. |
| 2023 | Liaison Strategies | 11 | 11 | All 11 first-party press posts are still public. Scribd full-report embeds exist for most, but several migrated posts point to the wrong May 29 document and need manual reconciliation. |
| 2023 | Viewpoints Research | 2 imported / 3 public | 2 imported / 3 public | **Three of three recovered.** All three first-party marginals reports are public, including the Apr. 29–May 2 sample omitted by the parser. |
| 2023 | Ipsos | 1 | 1 | **One of one full.** First-party factum and detailed tables are public. Combined with 2014, historical Ipsos coverage is five of five. |

The counts above come from the repository files and are independently checked against the owning source indexes. They describe sample proxies, not guaranteed statistical independence.

### Repository proxy-date manifest

The date manifest below makes the 98 repository proxies auditable without repeating 153 scenario rows. Each comma-separated date is one `(election, firm, stored date, stored sample size)` proxy; scenarios from the same firm/date/sample are collapsed. Historical sample sizes are omitted here because the parser defect described above makes many of them unsafe. The repository has not retained the original row-level source links: every 2014 row points to the [2014 Wikipedia article](https://en.wikipedia.org/wiki/2014_Toronto_mayoral_election), every 2018 row to the [2018 article](https://en.wikipedia.org/wiki/2018_Toronto_mayoral_election), the 2022 row to the [2022 article](https://en.wikipedia.org/wiki/2022_Toronto_mayoral_election), and every 2023 row to the [2023 by-election article](https://en.wikipedia.org/wiki/2023_Toronto_mayoral_by-election). Those are discovery indexes, not source documents.

| Election | Firm | Distinct Poll Sample proxy dates in the repository |
|---|---|---|
| 2014 | `2010 Election` | 2010-10-25 (**non-poll**) |
| 2014 | Forum Research | 2013-01-25, 2013-03-21, 2013-05-13, 2013-08-29, 2013-11-04, 2013-11-24, 2014-01-06, 2014-01-22, 2014-02-09, 2014-02-24, 2014-03-13, 2014-03-27, 2014-04-14, 2014-05-01, 2014-05-21, 2014-06-23, 2014-07-02, 2014-07-21, 2014-08-06, 2014-08-26, 2014-09-08, 2014-09-12, 2014-09-22, 2014-09-29, 2014-10-06, 2014-10-14, 2014-10-20, 2014-10-25 |
| 2014 | Ipsos-Reid | 2013-11-12, 2014-09-16, 2014-09-26, 2014-10-23 |
| 2014 | Mainstreet Technologies | 2014-09-12, 2014-09-21, 2014-09-28, 2014-10-05, 2014-10-17, 2014-10-23 |
| 2014 | Maple Leaf Strategies | 2014-07-30 |
| 2014 | Nanos Research | 2014-07-05, 2014-08-31, 2014-09-20 |
| 2018 | DART Insight and Communications | 2018-10-15 |
| 2018 | Forum Research | 2018-07-27, 2018-08-27, 2018-09-24, 2018-10-05, 2018-10-10 |
| 2018 | Mainstreet Research | 2018-09-05, 2018-09-16, 2018-09-25 |
| 2018 | Probit Inc. | 2018-09-05 |
| 2022 | Forum Research | 2022-10-08 |
| 2023 | Forum Research | 2023-02-14, 2023-03-23, 2023-04-26, 2023-05-07, 2023-05-14, 2023-05-20, 2023-05-27, 2023-06-02, 2023-06-09, 2023-06-16, 2023-06-23 |
| 2023 | Ipsos | 2023-06-13 |
| 2023 | Liaison Strategies | 2023-04-22, 2023-04-29, 2023-05-06, 2023-05-13, 2023-05-18, 2023-05-27, 2023-06-04, 2023-06-11, 2023-06-13, 2023-06-18, 2023-06-23 |
| 2023 | Mainstreet Research | 2023-02-14, 2023-02-19, 2023-03-19, 2023-04-03, 2023-04-13, 2023-04-20, 2023-04-26, 2023-05-03, 2023-05-11, 2023-05-17, 2023-05-25, 2023-05-31, 2023-06-08, 2023-06-11, 2023-06-15, 2023-06-19, 2023-06-22, 2023-06-24, 2023-06-25 |
| 2023 | Viewpoints Research | 2023-06-02, 2023-06-19; omitted public sample: 2023-04-29 to 2023-05-02 |

The omitted Viewpoints sample replaces the invalid 2010 row in the actual-sample total; it does not create a 99th historical sample. Reconstructing exact source-document identity and fieldwork timestamps for every date remains part of the acquisition manifest, not something the current CSV can answer.

### First-party and archived source routes

The most useful source routes, grouped by owner, are:

- **Forum Research:** [old Toronto release index](https://poll.forumresearch.com/m/category/3/toronto/), [archived release index](https://web.archive.org/web/20241003173026id_/https://poll.forumresearch.com/m/category/3/toronto/), [transparency statement](https://poll.forumresearch.com/m/transparency/), and the [University of Toronto Forum-poll collection](https://mdl.library.utoronto.ca/collections/numeric-data/microdata/forum-research-political-polls). The old index has 25 paginated pages, and a [Wayback CDX query over original Forum PDFs](https://web.archive.org/cdx/search/cdx?url=poll.forumresearch.com/data/*&output=json&filter=statuscode:200&filter=mimetype:application/pdf&fl=timestamp,original,statuscode,digest&collapse=digest) exposes a batch-recovery route. It yielded about 1,391 unique archived PDF records across Forum's full polling archive; date/title matching is still needed. At least 16 of the 28 Forum 2013–14 proxy dates already have exact `TO*` document matches. The U of T collection says it covers federal, provincial and Toronto municipal polling from 2013 onward and explicitly permits Ontario-university students, staff and faculty to download it; other researchers may request Dataverse access. Because the project owner is U of T staff, authenticated institutional retrieval is likely the highest-leverage first route, subject to confirming coverage and reuse terms.

The public Borealis metadata makes that institutional route unusually concrete:

| Forum Borealis dataset | Restricted respondent files | Public codebooks | Relationship to repository |
|---|---:|---:|---|
| [Toronto Municipal 2013, DOI 10.5683/SP3/2ANYFR](https://doi.org/10.5683/SP3/2ANYFR) | 12 `.tab` files | 12 | Together with 2014, nearly matches the 28 Forum 2013–14 sample proxies. |
| [Toronto Municipal 2014, DOI 10.5683/SP3/IM2A0R](https://doi.org/10.5683/SP3/IM2A0R) | 15 `.tab` files | 15 | 2013 + 2014 exposes 27 survey/codebook pairs; exact date matching is still required. |
| [Toronto Municipal 2018, DOI 10.5683/SP2/QCPM89](https://doi.org/10.5683/SP2/QCPM89) | 10 `.tab` files | 10 | The repository has only five Forum 2018 mayoral proxies, so this collection is broader than the current corpus or exposes missing samples. |

No post-2019 Toronto municipal dataset appeared in the collection's public search during this audit. The restricted `.tab` files may be more useful than PDFs because respondent-level data can preserve question/scenario structure and denominators, but they are not assumed to map one-to-one to repository rows. Coverage, labels/weights, confidentiality, redistribution and model-audit rights must be checked after authenticated download.
- **Representative Forum originals:** [2014 Oct. 25 release](http://poll.forumresearch.com/data/TO%20Horserace%20News%20Release%20(2014%2010%2026)%20Forum%20Research.pdf), [2018 July release](https://poll.forumresearch.com/data/417633c5-894a-4f17-a9ec-46da194ea51bNews%20Release%20from%20Forum%20Research_Toronto%20Issues_July%2027%202018.pdf), [2022 mayoral release](https://poll.forumresearch.com/data/d8c2ba39-b222-4066-a9c4-5b2421fb82abGeneral%20Mayoral%20News%20Release%20Final.pdf), [2023 final release and trend table](https://poll.forumresearch.com/data/cb12c41a-8453-40e6-90f1-7558d098f7e1Chow%20lead%20narrowing%20in%20final%20days%20of%20campaign_June%2024%202023.pdf). On the research date, the old Forum host returned maintenance responses, so these are document leads rather than proof of immediate downloadability.
- **Nanos Research:** the archived [first-party reports catalogue](https://web.archive.org/web/20210730210750id_/https://nanos.co/reports-2/) identifies all three 2014 samples. The [July report with tables](https://nanos.co/wp-content/uploads/2017/07/2014-541-OCSA-Report-FINAL-w-tabs-R-1.pdf) and [September report with tables](https://nanos.co/wp-content/uploads/2017/07/2014-566B-CTV-Globe-Toronto-Mayoral-Wave-2-report-w-tabs-R.pdf) are live. The exact [August release path](https://nanos.co/wp-content/uploads/2017/07/Sep-3-Tory-leads-comfortably-in-Toronto-Mayoral-race.pdf) returns 404 and has no complete PDF capture. Nanos's current [2014 reports page](https://nanos.co/2014-reports/) advertises subscriber access to historical proprietary research; confirm this specific missing municipal file before purchasing access.
- **Ipsos:** all five historical samples have live first-party full tables: [November 2013 page](https://www.ipsos.com/en-ca/rob-fords-road-re-election-long-and-bumpy-prospects-another-victory-look-bleak) and [tables](https://www.ipsos.com/sites/default/files/publication/2013-11/6317-tb1.pdf); [September 16, 2014 release](https://www.ipsos.com/sites/default/files/publication/2014-09/6599.pdf) and [tables](https://www.ipsos.com/sites/default/files/publication/2014-09/6599-tb1.pdf); [September 26 page](https://www.ipsos.com/en-ca/four-weeks-left-until-toronto-mayoral-vote-tory-48-soars-while-chow-26-ford-26-sputter) and [tables](https://www.ipsos.com/sites/default/files/publication/2014-09/6609-tb1.pdf); [October 23 page](https://www.ipsos.com/en-ca/john-tory-42-headed-toronto-mayors-chain-office-over-ford-31-chow-25) and [tables](https://www.ipsos.com/sites/default/files/publication/2014-10/6648-tb1.pdf); and the [2023 factum](https://www.ipsos.com/sites/default/files/ct/news/documents/2023-06/22-003004-01%20GN%20Media%20Release%20%283%29.pdf) with [detailed tables](https://www.ipsos.com/sites/default/files/ct/news/documents/2023-06/Toronto%20Mayoral%20Race%20Tables%202.pdf). Ipsos is comparatively easy to enumerate.
- **Liaison Strategies:** [first-party post sitemap](https://press.liaisonstrategies.ca/sitemap-posts.xml) and [Scribd publisher profile](https://www.scribd.com/user/665180330/Liaison-Strategies). The sitemap makes the press releases batch-enumerable; Scribd makes durable automated acquisition less straightforward. Examples are [April 21–22 tables](https://www.scribd.com/document/640520195/Toronto-Poll-April-24-2023) and the [June 22–23 report](https://www.scribd.com/document/655112063/Toronto-Poll-June-24).
- **Mainstreet Research:** old first-party paths are largely broken after a site migration. A CDX pass over the stable `2023_Polls/Toronto/` prefix found at least six clean reports: early February, late February, March 17, April 12, April 18 and April 26. Verified examples include [Feb. 14](https://web.archive.org/web/20230313205132/https://www.mainstreetresearch.ca/2023_Polls/Toronto/Toronto_Early_Feb_2023_QP-1.pdf?_t=1677786735), [Feb. 19](https://web.archive.org/web/20230315221852/https://www.mainstreetresearch.ca/2023_Polls/Toronto/Toronto_Late_Feb_2023_QP-1.pdf?_t=1677823873), and [Apr. 12–13](https://web.archive.org/web/20230415051420/https://old.ipolitics.ca/wp-content/uploads/2023/04/Toronto_2_April_12_2023_Public.pdf). Fourteen later poll pages and 15 download endpoints are visible in Wayback, but many archived bodies are Incapsula blocks rather than PDFs. The remaining dates require deeper download-manager recovery, Scribd matching or a pollster archive export.
- **Viewpoints Research:** WordPress's [first-party search API](https://www.viewpoints.ca/wp-json/wp/v2/search?search=Toronto&per_page=100) exposes all three samples. They are the [Apr. 29–May 2 release](https://www.viewpoints.ca/2023/05/chow-leads-mayoral-race-in-new-viewpoints-poll/) and [PDF](https://www.viewpoints.ca/wp-content/uploads/2023/05/Toronto-Mayoral-By-Election-Marginals-Report1.pdf), [June 1–2 release](https://viewpoints.ca/2023/06/chows-lead-grows-in-new-viewpoints-poll/) and [PDF](https://viewpoints.ca/wp-content/uploads/2023/06/Toronto-Mayoral-By-Election-Marginals-Report-20230608-1.pdf), and [June 15–19 release](https://viewpoints.ca/2023/06/final-viewpoints-poll-reinforces-chows-lead/) and [PDF](https://viewpoints.ca/wp-content/uploads/2023/06/Toronto-Mayoral-By-Election-Marginals-Tracking-Report-20230622.pdf). These are concise marginals reports with exact questions, bases, method and weighting, not demographic crosstab books.
- **2014 smaller-firm originals:** the [Maple Leaf Strategies archived release](https://web.archive.org/web/20140808050914id_/http://mapleleafstrategies.com/wp-content/uploads/2014/07/Tory-Leads-Ford-No-Growth-Room.pdf) is fully retrievable but has no demographic crosstabs. Representative Mainstreet Scribd reports survive for [Sept. 21](https://www.scribd.com/doc/240548385/Mainstreet-Toronto-Mayoral-Poll-September-22), [Sept. 28](https://www.scribd.com/doc/241314474/Toronto-Mayoral-Poll-September-29), [Oct. 5](https://www.scribd.com/doc/242035582/Toronto-October-6-Mayoral-Poll), and [Oct. 23](https://www.scribd.com/doc/244228439/Mainstreet-Toronto-Mayoral-Poll-October-23).
- **2018 smaller-firm originals:** [Mainstreet Sept. 16 Scribd report](https://www.scribd.com/document/388824269/Mainstreet-Toronto-17sept2018) and [Sept. 25 report](https://www.scribd.com/document/389471142/Mainstreet-Toronto-26sept2018) are full documents. Probit survives only as a [first-party X post](https://x.com/ProbitInc/status/1038148223423184896) plus the original [decided-voter](https://pbs.twimg.com/media/Dmg-TobW4AEnYm2.jpg:large) and [all-voter](https://pbs.twimg.com/media/Dmg-TpGXcAU_j3-.jpg:large) charts. DART's [five-page factum](https://web.archive.org/web/20181023234340id_/http://dartincom.ca/wp-content/uploads/2018/10/Sun-Toronto-Election-Factum-1-Oct-2018.pdf) is fully recoverable, but the only capture of its companion [32-page detailed tables](https://web.archive.org/web/20201027035321id_/https://dartincom.ca/wp-content/uploads/2018/10/Sun-Toronto-Election-Tables-1-Oct-2018-1.pdf) is truncated at 1,048,576 of 1,821,242 bytes and cannot be treated as recovered.

This list identifies the source channels and representative exact objects. A retrieval manifest should still record one source-document URL per sample and a second archived-original URL where available.

## Current mayoral inventory

The 22 current rows reduce to 19 sample proxies:

| Firm | Stored fieldwork end / publication | n | Repository poll ID(s) sharing the sample | Best first-party source | Classification |
|---|---|---:|---|---|---|
| Pallas Data | 2025-06-07 / 06-07 | 611 | `pallas-2025-06-07` | [release and PDF](https://pallas-data.ca/2025/06/12/pallas-toronto-poll-chow-leads-with-a-year-to-go/) | Full tables/questionnaire available |
| Liaison Strategies | 2025-07-06 / 07-06 | 1,000 | `liaison-2025-07-06` | [release and PDF](https://press.liaisonstrategies.ca/toronto-poll-chow-39-tory-35/) | Full tables/questionnaire available |
| Ipsos | 2025-08-29 / 08-29 | 1,001 | `ipsos-2025-08-29` | [release and report](https://www.ipsos.com/en-ca/toronto-city-poll-what-residents-think-about) | Full tables/questionnaire available |
| Forum Research | 2025-09-04 / 09-04 | 1,000 | three `forum-2025-09-04*` scenarios | [release and PDF](https://www.forumresearch.com/news/2025/09/one-year-out-chow-leads-in-toronto-mayoral-race) | Full tables/questionnaire available; one sample, not three |
| Canada Pulse Insights / CityNews | 2025-10-06 / 10-06 | 406 | `canadapulse-2025-10-06` | [release and XLSX](https://canadapulseinsights.com/post/toronto-civic-politics-2025) | Full detailed workbook available |
| Liaison Strategies | 2025-10-23 / 10-23 | 1,000 | `liaison-2025-10-23` | [release and PDF](https://press.liaisonstrategies.ca/toronto-chow-leads-tory-52-to-36/) | Full tables/questionnaire available |
| Liaison Strategies | 2025-12-21 / 12-21 | 1,000 | `liaison-2025-12-21` | [release and PDF](https://press.liaisonstrategies.ca/toronto-chow-leads-tory-39-3-to-35-1/) | Full tables/questionnaire available |
| Abacus Data | 2026-01-27 / 01-27 | 1,001 | `abacus-2026-01-27-bradford-v-chow` | [First-party Coletto analysis](https://davidcoletto.substack.com/p/with-tory-out-torontos-mayoral-race) | Access-gated release/topline; source identity resolved, no table book |
| Liaison Strategies | 2026-02-02 / 02-02 | 1,000 | `liaison-2026-02-02` | [release and PDF](https://press.liaisonstrategies.ca/toronto-chow-40-tory-33-bradford-18/) | Full tables/questionnaire available |
| Mainstreet Research | 2026-02-22 / 02-22 | 802 | `mainstreet-2026-02-22` | [release, public and detailed PDFs](https://www.mainstreetresearch.ca/post/latest-mainstreet-poll-of-toronto-shows-uncertain-choice-for-mayor-in-2026) | Full tables available; detailed attachment labelled subscriber-only |
| Liaison Strategies | 2026-03-08 / 03-08 | 1,000 | `liaison-2026-03-08` | [release and PDF](https://press.liaisonstrategies.ca/toronto-chow-44-bradford-26-ford-16/) | Full tables/questionnaire available |
| Pallas Data | 2026-03-08 / 03-08 | 735 | two `pallas-2026-03-08*` scenarios | [release](https://pallas-data.ca/2026/03/10/pallas-toronto-poll-chow-leads-bradford-35-to-29-but-most-think-city-is-going-in-the-wrong-direction/) and [full PDF](https://pallas-data.ca/wp-content/uploads/2026/03/PallasData-Toronto-10March2026.pdf) | Full tables/questionnaire available; one sample, not two |
| Liaison Strategies | 2026-04-13 / 04-13 | 1,000 | `liaison-2026-04-13` | [release and PDF](https://press.liaisonstrategies.ca/toronto-chow-46-bradford-35-voters-split-on-island-airport/) | Full tables/questionnaire available |
| Liaison Strategies | 2026-05-11 / 05-11 | 1,000 | `liaison-2026-05-11` | [release and PDF](https://press.liaisonstrategies.ca/toronto-chow-50-bradford-37-traffic-frustration-dominates-city-mood/) | Full tables/questionnaire available |
| Mainstreet Research | 2026-06-18 / 06-18 | 1,157 | `mainstreet-2026-06-18` | [release, public and detailed PDFs](https://www.mainstreetresearch.ca/post/bradford-and-chow-matchup-could-be-close) | Full tables available; detailed attachment labelled subscriber-only |
| Liaison Strategies | 2026-06-30 / 06-30 | 1,000 | `liaison-2026-06-30` | [release and PDF](https://press.liaisonstrategies.ca/toronto-chow-49-bradford-40-world-cup-gets-positive-reviews/) | Full tables/questionnaire available |
| Liaison Strategies | 2026-07-26 / 07-26 | 1,000 | `liaison-2026-07-26` | [release and PDF](https://press.liaisonstrategies.ca/toronto-chow-49-bradford-41-city-split-on-direction/) | Full tables/questionnaire available |
| Forum Research | 2026-07-29 / 07-29 | 1,011 | `forum-2026-07-29` | [release and PDF](https://www.forumresearch.com/news/2026/07/chow-leads-bradford-maintains-advantage-with-alexander-added-to-ballot) | Full tables/questionnaire available |
| Liaison Strategies | 2026-08-05 / 08-07 | 1,000 | `liaison-2026-08-05` | [release and PDF](https://press.liaisonstrategies.ca/toronto-chow-47-bradford-40-alexander-10/) | Full tables/questionnaire available |

The two date columns above reproduce current repository values rather than silently substituting dates printed in the source documents. Date reconciliation belongs in ingestion work.

| Firm | Sample proxies | Full public document | Current status and source route |
|---|---:|---:|---|
| Liaison Strategies | 10 | 10 | **Full tables available.** Every sample has a first-party PDF linked from the Ghost post or sitemap. |
| Forum Research | 2 | 2 | **Full tables available.** Both are in Forum's new public JSON/API archive with downloadable PDF attachments. |
| Mainstreet Research | 2 | 2 | **Full tables available.** Each current post exposes a public report and a full-crosstab attachment. The UI labels the latter subscriber-only, but both static URLs returned HTTP 200 during this audit; access terms still need clarification. |
| Pallas Data | 2 | 2 | **Full tables available.** June 2025 has a public PDF; March 2026 has a 27-page first-party report exposed through the post's WordPress REST metadata. |
| Ipsos | 1 | 1 | Full report and banner PDFs are linked from the first-party release page. |
| Canada Pulse Insights / CityNews | 1 | 1 | **Full detailed workbook available.** The first-party release links a public XLSX with question text, bases and crosstabs. |
| Abacus Data | 1 | 0 | First-party analysis by Abacus CEO David Coletto identifies the Jan. 22–27 Toronto Omnibus and publishes ballot results, but no downloadable questionnaire or table book. |
| **Total** | **19** | **18** | One remaining sample needs a direct inquiry or must remain access-gated/release-only. |

### Exact current full-document routes

Liaison's ten sample pages are [July 2025](https://press.liaisonstrategies.ca/toronto-poll-chow-39-tory-35/), [October 2025](https://press.liaisonstrategies.ca/toronto-chow-leads-tory-52-to-36/), [December 2025](https://press.liaisonstrategies.ca/toronto-chow-leads-tory-39-3-to-35-1/), [February 2026](https://press.liaisonstrategies.ca/toronto-chow-40-tory-33-bradford-18/), [March 2026](https://press.liaisonstrategies.ca/toronto-chow-44-bradford-26-ford-16/), [April 2026](https://press.liaisonstrategies.ca/toronto-chow-46-bradford-35-voters-split-on-island-airport/), [May 2026](https://press.liaisonstrategies.ca/toronto-chow-50-bradford-37-traffic-frustration-dominates-city-mood/), [June 2026](https://press.liaisonstrategies.ca/toronto-chow-49-bradford-40-world-cup-gets-positive-reviews/), [July 2026](https://press.liaisonstrategies.ca/toronto-chow-49-bradford-41-city-split-on-direction/), and [August 2026](https://press.liaisonstrategies.ca/toronto-chow-47-bradford-40-alexander-10/). This also repairs the repository's July 2025 source confusion: the current public election table points that sample at the October page, while the sitemap exposes the correct July report.

Other current full-document sources are:

- Forum [September 2025 release](https://www.forumresearch.com/news/2025/09/one-year-out-chow-leads-in-toronto-mayoral-race) and [PDF](https://www.forumresearch.com/news/attachments/b00d29f6-3522-489f-adea-0569e29bc89e.pdf); Forum [July 2026 release](https://www.forumresearch.com/news/2026/07/chow-leads-bradford-maintains-advantage-with-alexander-added-to-ballot) and [PDF](https://www.forumresearch.com/news/attachments/fb26f543-8af1-44fa-b85b-3e7592b84b8d.pdf).
- Mainstreet [February 2026 release](https://www.mainstreetresearch.ca/post/latest-mainstreet-poll-of-toronto-shows-uncertain-choice-for-mayor-in-2026), [public report](https://cdn.prod.website-files.com/66c8dfb086a015b3b519e988/699d0f1e16c4efb458529cc9_Toronto_Feb_2026_Public.pdf), and [full report](https://cdn.prod.website-files.com/66c8dfb086a015b3b519e988/699d0f1b19b29143d353a2fb_Toronto_Feb_2026.pdf); Mainstreet [June 2026 release](https://www.mainstreetresearch.ca/post/bradford-and-chow-matchup-could-be-close), [public report](https://cdn.prod.website-files.com/66c8dfb086a015b3b519e988/6a39f109ba68d015462d1afc_Toronto_Mayoral_June_2026_Public.pdf), and [full report](https://cdn.prod.website-files.com/66c8dfb086a015b3b519e988/6a39f10cd770a2a7e1e6c18f_Toronto_Mayoral_June_2026.pdf).
- Pallas [June 2025 release](https://pallas-data.ca/2025/06/12/pallas-toronto-poll-chow-leads-with-a-year-to-go/) and [full PDF](https://pallas-data.ca/wp-content/uploads/2025/06/PallasData-Toronto-11June2025-compressed-1.pdf); [March 2026 release](https://pallas-data.ca/2026/03/10/pallas-toronto-poll-chow-leads-bradford-35-to-29-but-most-think-city-is-going-in-the-wrong-direction/), [full PDF](https://pallas-data.ca/wp-content/uploads/2026/03/PallasData-Toronto-10March2026.pdf), and [post API](https://pallas-data.ca/wp-json/wp/v2/posts/2177). The March report includes exact questionnaire, methodology, both ballot scenarios, weighted/unweighted bases and demographic/geographic crosstabs.
- Ipsos [August 2025 release](https://www.ipsos.com/en-ca/toronto-city-poll-what-residents-think-about) and [full report](https://www.ipsos.com/sites/default/files/ct/news/documents/2025-09/Toronto%20Star%20Ipsos%20Poll_Full_Report_Final%20Sept%2019%202025.pdf).
- Canada Pulse [September 30–October 6, 2025 release](https://canadapulseinsights.com/post/toronto-civic-politics-2025) and [detailed XLSX](https://cdn.prod.website-files.com/68e8fca1c431166c54a9df49/68f6c7bda2115e7a159ff327_CityBeat%20Toronto%20Civic%202025%20F.xlsx). The workbook contains question text, weighted and unweighted bases, and demographic/geographic crosstabs, so it is a full-detail source even though it is not a PDF.
- Abacus CEO David Coletto's [first-party January 2026 analysis](https://davidcoletto.substack.com/p/with-tory-out-torontos-mayoral-race) identifies a Jan. 22–27 Toronto Omnibus of 1,001 people and reports both the raw ballot and the familiar-with-both-candidates subset stored by the repository. It is an access-gated Substack release, not a downloadable table book.

## Council inventory

### Six historical 2022 samples

All six are Forum IVR samples fielded after candidate certification. Exact full-release URLs are known:

- [Ward 4, Parkdale–High Park](https://poll.forumresearch.com/data/0f87336b-4a32-498e-8411-70b1dd986581Ward%204%20News%20Release.pdf)
- [Ward 5, York South–Weston](https://poll.forumresearch.com/data/74bddea4-50a4-4c53-a017-52dabdd9cb43Ward%205%20News%20Release.pdf)
- [Ward 10, Spadina–Fort York](https://poll.forumresearch.com/data/b390026c-ece7-475d-85f0-9cc0e050e9e0Ward%2010%20News%20Release.pdf)
- [Ward 13, Toronto Centre](https://poll.forumresearch.com/data/a199cd17-a268-43ac-a464-8c75787e2657Ward%2013%20News%20Release.pdf)
- [Ward 20, Scarborough Southwest](https://poll.forumresearch.com/data/00bd353b-b4c5-4efc-ba8a-7e75d5abb630Ward%2020%20News%20Release.pdf)
- [Ward 22, Scarborough–Agincourt](https://poll.forumresearch.com/data/2fc49a81-6baf-49bc-ad01-f22449099fb4Ward%2022%20News%20Release.pdf)

The old host was in maintenance during this pass. These documents are search-indexed and some have archived originals, but a reproducible retrieval pass must obtain and checksum all six. The restricted [U of T Forum collection](https://mdl.library.utoronto.ca/collections/numeric-data/microdata/forum-research-political-polls) may also contain them.

### Six current Forum ward samples

Forum's new [public news API](https://www.forumresearch.com/api/news/paginated?page=1&pageSize=100) returns sample metadata and attachment filenames. The attachment endpoint is deterministic and all six PDFs returned HTTP 200 during this audit.

| Ward | Fieldwork | Sample | Source date / API go-live | Full first-party source | Distinct-sample assessment |
|---|---|---:|---|---|---|
| 20 Scarborough Southwest | 2026-06-22 to 06-23 | 311 | 2026-06-24 / 06-29 | [release](https://www.forumresearch.com/news/2026/06/parthi-kandavel-leads-in-a-divided-scarborough-southwest-municipal-election-poll-and-olivia-chow-leads-for-the-mayoral-preference), [PDF](https://www.forumresearch.com/news/attachments/080be964-71ac-48a6-8358-fb7e8eb60aa3.pdf) | Separate ward sample; its Council and ward-level mayoral questions are dependent readings from this one sample. |
| 5 York South–Weston | 2026-06-22 to 06-23 | 301 | 2026-06-24 / 06-29 | [release](https://www.forumresearch.com/news/2026/06/frances-nunziata-leads-in-a-divided-york-south-weston-municipal-election-poll-and-brad-bradford-leads-for-the-mayoral-preference), [PDF](https://www.forumresearch.com/news/attachments/e1d73221-747d-4f97-bfa1-4aad42c7c537.pdf) | Separate ward sample. |
| 13 Toronto Centre | 2026-06-22 to 06-23 | 355 | 2026-06-24 / 06-29 | [release](https://www.forumresearch.com/news/2026/06/chris-moise-leads-in-toronto-centre-municipal-election-poll-and-olivia-chow-leads-for-the-mayoral-preference), [PDF](https://www.forumresearch.com/news/attachments/aeaf5831-d6be-47b8-9653-30061bcb2368.pdf) | Separate ward sample; current repository sample. Multiple field/scenario questions remain one sample. |
| 19 Beaches–East York | 2026-06-22 to 06-23 | 367 | 2026-06-24 / 06-29 | [release](https://www.forumresearch.com/news/2026/06/nate-erskine-smith-well-ahead-in-beacheseast-york-municipal-election-poll-and-olivia-chow-leads-for-the-mayoral-preference), [PDF](https://www.forumresearch.com/news/attachments/490d62fe-a2c1-4987-992d-a1e162ce826f.pdf) | Separate ward sample. |
| 19 Beaches–East York | 2026-08-11 to 08-12 | 386 | 2026-08-13 / 08-13 | [release](https://www.forumresearch.com/news/2026/08/nate-erskine-smith-holds-commanding-lead-in-beacheseast-york-municipal-election-poll), [PDF](https://www.forumresearch.com/news/attachments/bfc438f8-9618-4981-8413-d784810cd4b7.pdf) | A second separately recruited Ward 19 sample; genuine within-ward replication, still from the same firm. |
| 11 University–Rosedale | 2026-08-12 | 449 | 2026-08-13 / 08-13 | [release](https://www.forumresearch.com/news/2026/08/dianne-saxe-leads-university-rosedale-municipal-election-poll), [PDF](https://www.forumresearch.com/news/attachments/5a055d21-dc54-4bfa-838d-efa840f9704a.pdf) | One sample containing current-field, hypothetical Layton-field, and ward-level mayoral readings. |

The June Ward 20 and Ward 19 methodology paragraphs contain apparent copy-and-paste geography errors, calling their respondents York South–Weston residents. The titles, question tables and samples must be checked rather than silently correcting the source. This is precisely the kind of provenance defect a source-document layer should preserve.

## Minimum post-Final validation subset

Using the repository's last-date proxy and the historical nomination/registration deadlines yields:

| Election | Approximate post-Final historical mayoral samples | Firms represented |
|---|---:|---|
| 2014 | 17 | Forum 7, Mainstreet 6, Ipsos 3, Nanos 1 |
| 2018 | 10 | Forum 5, Mainstreet 3, Probit 1, DART 1 |
| 2022 | 1 | Forum 1 |
| 2023 by-election | 28 | Mainstreet 10, Liaison 8, Forum 7, Viewpoints 2, Ipsos 1 |
| **Total** | **56** | — |

The true qualifying count is probably **52–56**, not exactly 56. A poll whose recorded last date equals the filing deadline may have recruited respondents before the field became final, and the current historical file often records only one date. Full documents are needed to establish fieldwork start/end and public-release time.

The six 2022 Council polls are all post-certification. Therefore a deliberately narrow first acquisition pass is roughly **58–62 samples**: 52–56 mayoral plus six Council. This subset contains far fewer early hypothetical 2013–14 ballot scenarios and should be attempted before a 129-sample extraction campaign.

## What can be automated

### Low-friction, batchable sources

- Forum's new API returns JSON metadata plus deterministic attachment filenames for its current releases.
- Liaison's Ghost sitemap enumerates first-party posts; 2025–26 Toronto posts link direct PDFs.
- Ipsos pages expose direct attachment links.
- Viewpoints and Pallas use predictable WordPress media URLs.
- Nanos maintains a reports catalogue.
- Direct PDFs can be hashed, counted and text-layer-tested automatically after download.

### Manual or semi-manual sources

- Old Forum URLs need a live-host retry, exact Wayback lookup, or authenticated U of T/Borealis download.
- Historical Mainstreet URLs need per-date matching after the website migration.
- Scribd documents can often be read in-browser and search-indexed, but automated durable download and licensing are less clear.
- Image-only table books require OCR/table extraction plus visual verification.
- Same-sample scenarios must be joined manually unless the source explicitly names a survey identifier.
- News/client releases need a pollster or commissioner inquiry to determine whether unpublished tables exist.

Retrieval and extraction should remain separate. A successful HTTP 200 is not a structured Poll Reading; an extracted table is not trustworthy until the question, denominator, weighted/unweighted base, sample lineage and source page have been checked.

## Questions only an access or pollster inquiry can settle

The remaining uncertainty is concentrated rather than universal:

1. **Forum / University of Toronto:** Use the project owner's U of T credentials to test the download route first. Does the collection contain every Toronto mayoral and ward sample in the target dates, including questionnaires, labels, weights and the 2025–26 commissioned samples? What redistribution, publication and model-audit rights apply outside the university?
2. **Mainstreet:** Does a publicly documented subscription catalogue include the broken 2014, 2018 and 2023 Toronto reports, and does it authorize durable internal copies and model auditing rather than only online viewing? The current site labels detailed response crosstabs as available only to logged-in subscribers, but current static attachments being publicly reachable does not answer the licensing question. No evidence found in this pass shows that a subscription unlocks the historical archive; absent such evidence, the missing reports are unavailable rather than a direct-request task.
3. **Liaison:** Can the identified public Scribd records or a documented paid viewer route provide the 2023 reports whose migrated embeds point to the wrong document? If not, use the first-party releases as source-grade toplines and mark the fuller artifacts unavailable.
4. **Abacus / commissioning party:** Can the Jan. 22–27, 2026 questionnaire and table book behind Coletto's first-party analysis be archived and cited?
5. **DART / Maru:** The complete 2018 32-page table book is not publicly recovered; the factum is available and Wayback's detailed-table capture is truncated. **Probit / EKOS:** only the two first-party charts are currently available. Richer documents remain unavailable unless a public or verified purchasable archive is identified.

The newly recovered Viewpoints and Pallas reports remove two known gaps. Without pretending that the remaining historical leads have already been downloaded and inspected, a reasonable working expectation is now roughly **9–17 historical/current samples** remaining topline-only, access-restricted, dead, corrupt, or unresolved after a normal public-web retrieval pass. Exactly one is a current mayoral sample: Abacus January 2026. The exact total requires the manifest run and U of T archive inspection; it cannot be determined by URL probing alone.

## Recommended next acquisition experiment

A bounded trial can answer the user's difficulty question without committing to a full archive build:

1. Build a manifest for the 58–62 minimum historical post-Final samples and the six current Council samples.
2. Attempt scripted retrieval from first-party URLs, then archived-original URLs.
3. Record `retrieved`, `full-table verified`, `topline only`, `restricted`, `dead`, or `unresolved` without substituting a secondary summary for a missing original.
4. Test authenticated Forum corpus download with the project owner's U of T access and evaluate only publicly documented paid archives for the remaining gaps.
5. Extract and visually verify a stratified ten-document pilot: two Forum, two Mainstreet, two Liaison, one Ipsos, one Nanos, one Viewpoints/Pallas, and one image-only table book.

That experiment should take about **two focused days of retrieval work plus two to three days of extraction/QA**. It will produce an observed recovery rate and minutes-per-document distribution, which is a stronger basis for later schema and purchase decisions than either assuming every PDF is obtainable or designing around the two examples already supplied.

## Reproducibility notes

Repository inputs inspected:

- `data/raw/polls/historical_mayoral_polls.csv`
- `data/raw/polls/polls.csv`
- `data/raw/polls/ward_poll_readings.csv`
- `scripts/fetch_historical_mayoral_polls.py`
- `scripts/fetch_polls.py`
- `docs/research/unmeasured-candidate-tail.md`
- `docs/research/full-detail-poll-pdf-audit.md`

All public current Forum attachment URLs listed above returned `200 application/pdf` on 2026-08-17. Liaison's sitemap and current Toronto PDFs, the two current Mainstreet public/full attachment pairs, the Canada Pulse detailed workbook, all three Viewpoints reports, all five historical Ipsos table sets, and both current Pallas PDFs were also inspected at their first-party or archived-original locations. DART's factum is complete, but its companion detailed-table capture is explicitly classified as corrupt rather than recovered. Old-host or archive URLs are described as leads where complete recovery was not verified.
