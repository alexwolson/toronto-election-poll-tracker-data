# Historical mayoral Forum wave: 2022–2023 source audit

**Research date:** 2026-08-17
**Scope:** Forum's October 2022 Toronto mayoral sample and the ten source-matched 2023 samples
**Output boundary:** source-faithful draft only; no canonical historical CSV, crosswalk, live input, or model code changed

## Outcome

All eleven respondent samples are recoverable from public archived replays of
first-party Forum Research PDFs. Two 2023 samples each produced a second
first-party release with a hypothetical John Tory ballot. The recovered corpus
therefore contains **13 source documents, 13 sample-document links, 11 Distinct
Poll Samples, 21 dependent ballot readings, and 206 response rows**. Of the
response rows, 186 contain source-published values and 20 preserve named
candidates known to have been offered but not individually published in four
late decided/leaning tables.

The generic five-table source draft is in
`/private/tmp/forum_2022_2023_wave/`. The PDF artifacts are retained under the
gitignored path
`data/source_documents/historical_mayoral/forum_2022_2023/`.

This was a public-source recovery. It did not require a purchase, institutional
login, paywall bypass, or direct request to Forum.

## Artifact record

Every archived replay returned complete PDF bytes with a `%PDF-` signature and
a usable text layer. All **87 physical pages** were rendered and visually
inspected. No page was clipped, corrupt, blank, or unreadable. Public
availability is not an affirmative reuse licence, so the draft records
redistribution status as unknown and keeps the raw PDFs gitignored.

| Document | Archived first-party original | Bytes | Pages | SHA-256 |
|---|---|---:|---:|---|
| 2022 Oct. 11 release | [Forum PDF replay](https://web.archive.org/web/20221013194533id_/https://poll.forumresearch.com/data/d8c2ba39-b222-4066-a9c4-5b2421fb82abGeneral%20Mayoral%20News%20Release%20Final.pdf) | 398,487 | 4 | `8a9c750df3ffd4993a550558353c03e29b8007200c584c242339747a64139f55` |
| 2023 Feb. 14 release | [Forum PDF replay](https://web.archive.org/web/20230307095415id_/http://poll.forumresearch.com/data/d946c7ad-28c3-463c-af29-247201cdf98fTorontonians%20Split%20on%20John%20Tory%20Resignation%20Feb%2014%202023.pdf) | 404,475 | 4 | `b2ed95e9a908a9f0674a12fccd75ac3abfd4b9066b8024d91b61d596cf8b1cc5` |
| 2023 Mar. 24 release | [Forum PDF replay](https://web.archive.org/web/20230327175538id_/http://poll.forumresearch.com/data/e8944ec2-a76a-48bb-b35d-94f13a395a1cChow%20and%20Saunders%20Lead%20Potential%20Mayor%20Race%20March%2024%202023.pdf) | 501,836 | 9 | `3d6df6ca259734faf48db5630aa4e8107203cf3ebfd7190d30c52085b5803727` |
| 2023 Apr. 27 current-field release | [Forum PDF replay](https://web.archive.org/web/20230517052033id_/https://poll.forumresearch.com/data/1172cde0-151b-4e99-a2a6-7cba7c47a0a0Chow%20pulls%20ahead%20in%20mayor%20race%20April%2027%202023.pdf) | 482,319 | 8 | `2b423eff5500c49e4ebaba2c6e5934589044ff2add720a722713d70e5a2725bc` |
| 2023 Apr. 27 Tory companion | [Forum PDF replay](https://web.archive.org/web/20230606103937id_/https://poll.forumresearch.com/data/b00a589b-f969-44a4-8d3a-a803d9eb62f3Tory%20still%20top%20choice%20for%20mayor%20April%2027%202023.pdf) | 396,403 | 4 | `71a096e4acada5bd0adf291145000f4be3bf5778d6fe68ab7e0386f69381d856` |
| 2023 May 8 current-field release | [Forum PDF replay](https://web.archive.org/web/20230511051029id_/https://poll.forumresearch.com/data/9eb54fbe-7a67-41c5-a55e-de9439827d48Chow%20grows%20lead%20in%20mayor%20race%20May%208.pdf) | 259,271 | 6 | `800c8caf66d73a0b48099190bf25ba8852023debab1fdd160f69a1c88b0da84d` |
| 2023 May 8 Tory companion | [Forum PDF replay](https://web.archive.org/web/20230518162133id_/https://poll.forumresearch.com/data/ece1373a-31ce-4753-b1cb-7bbcfb1f261bTory%20remains%20top%20choice%20for%20mayor%20May%208.pdf) | 387,678 | 3 | `13f62514834df00f692042c1cd2f0882c83d78be08a06cb112eecd30784f2387` |
| 2023 May 15 release | [Forum PDF replay](https://web.archive.org/web/20230517014815id_/https://poll.forumresearch.com/data/bd46aa03-810b-450a-a958-5e01830e3c72Chow%20remains%20first%20choice%20in%20mayor%20race%20May%2015%202023.pdf) | 494,267 | 6 | `d86945ac07f38d47b77c024527d79d34f557abb6efda2a312d0f2e1795b10a8f` |
| 2023 May 21 release | [Forum PDF replay](https://web.archive.org/web/20250226214239id_/https://poll.forumresearch.com/data/e8299849-ea40-44a7-bcf0-65ae5d08b26cChow%20holds%20strong%20as%20front%20runner%20in%20mayor%20race%20May%2021%202023.pdf) | 500,370 | 6 | `70a5e209dffab005a6c182c671f6d4872b27aaae2e69bf5542080f75c8a4fd5f` |
| 2023 May 28 release | [Forum PDF replay](https://web.archive.org/web/20230530033358id_/https://poll.forumresearch.com/data/98079d92-72c1-454b-86a4-8997b6eb0056Chow%E2%80%99s%20lead%20unchanged%20in%20latest%20mayoral%20poll.pdf) | 538,886 | 7 | `b6b41716a5472bc7e75b8439860126799790b7d9bd42279f97a83ea80256d35d` |
| 2023 June 4 release | [Forum PDF replay](https://web.archive.org/web/20230726065608id_/https://poll.forumresearch.com/data/972939ff-a147-412d-8d5c-b3430dc4210eChow%20strengthens%20lead%20in%20mayor%20race%20June%204%202023.pdf) | 560,417 | 10 | `2a6a42a7da826997984ad1709570304823c3393fdc0d63679547c2153ee13046` |
| 2023 June 11 release | [Forum PDF replay](https://web.archive.org/web/20230612151823id_/http://poll.forumresearch.com/data/1b545e66-8ba5-4da8-885d-14d47b08c744Fresh%20gains%20for%20Bailao,%20Saunders%20and%20Furey%20June%2011%202023.pdf) | 561,841 | 10 | `c83a8abcd8f109079dfd7f0569f540714f805297e50d1fcf10fff129e4fdcbb2` |
| 2023 June 24 release | [Forum PDF replay](https://web.archive.org/web/20230726065606id_/https://poll.forumresearch.com/data/cb12c41a-8453-40e6-90f1-7558d098f7e1Chow%20lead%20narrowing%20in%20final%20days%20of%20campaign_June%2024%202023.pdf) | 568,119 | 10 | `6f7914b3c9123becf99478e38073d1a355992ea0b2c1c50d694997b64d6abfbb` |

## Respondent-sample lineage and retained readings

The sample, not a table or scenario, is the unit of independent evidence. The
April and May Tory companions are especially important: each companion uses
the same field dates, methodology, sample size, and respondents as its
current-field release. They are dependent scenario readings, not extra polls.

| Fieldwork | Parent sample | Ballot readings retained | Reported reading bases | Source boundary |
|---|---:|---|---|---|
| 2022-10-07 to 2022-10-08 | 1,017 eligible Toronto voters | Decided/leaning | reported `Sample 840` | Forum prints the complete offered response set: four named candidates plus the explicit `Other` catch-all. |
| 2023-02-13 | 1,042 | Decided/leaning | reported `Sample 707` | Release prose says Toronto residents; methodology says Ontario residents. Both statements are preserved. |
| 2023-03-22 to 2023-03-23 | 1,009 Toronto residents age 18+ | All respondents; decided/leaning | reported 1,009; 772 | The decided table omits a residual response even though the all-respondent table prints `Other`; coverage is partial. |
| 2023-04-25 to 2023-04-26 | 1,022 | All respondents; current-field decided/leaning; hypothetical-Tory decided/leaning | reported 1,022; 856; 919 | Two PDFs, three dependent ballot readings, one recruited sample. The companion's separate yes/no willingness-to-vote-for-Tory question is not a ballot reading. |
| 2023-05-06 to 2023-05-07 | 2,000 | Current-field decided/leaning; hypothetical-Tory decided/leaning | reported 1,708; 1,827 | Two PDFs and two dependent readings from one sample. |
| 2023-05-13 | 1,029 | All respondents; decided/leaning | reported 1,029; 924 | The legacy date is May 14; the source field date is May 13 and release date is May 15. |
| 2023-05-19 | 1,000 | All respondents; decided/leaning | reported 1,000; 889 | The legacy date is May 20; the source field date is May 19 and release date is May 21. |
| 2023-05-26 | 1,007 | All respondents; decided/leaning | reported 1,007; 874 | Five named candidates printed in the all-respondent table are omitted from the decided table; they remain offered-but-unpublished observations with unknown values. |
| 2023-06-02 | 1,032 | All respondents; decided/leaning | u/w–w/t 1,032–1,032; 936–923 | Source explicitly distinguishes unweighted and weighted bases. |
| 2023-06-09 | 1,047 | All respondents; decided/leaning | u/w–w/t 1,047–1,047; 976–965 | Source explicitly distinguishes unweighted and weighted bases. |
| 2023-06-23 | release prose 1,037 | All respondents; decided/leaning | u/w–w/t 1,035–1,035; 977–967 | The release's parent `n=1,037` conflicts with the ballot tables' all-reading `n=1,035`; both are retained in their source roles. |

The 21 retained readings are only mayoral ballot readings. Issue questions,
resignation questions, and the companions' yes/no Tory questions are outside
scope. Forum's `Decided/Leaning` bases are recorded as custom denominators,
not silently reduced to decided respondents. Published integer percentages
remain exactly as printed even when a
column totals 98%, 99%, 101%, or 102% because of rounding. No residual is
invented and no column is renormalized.

Canonical candidate IDs and names are used for joins, while
`response_label` retains Forum's printed spelling. Examples include source
labels `Gil Penalosa`, `Ana Bailao`, `Chloe-Marie Brown`, and Forum's repeated
misspelling `Anthony Perruza`; their canonical names remain Gil Peñalosa, Ana
Bailão, Chloe Brown, and Anthony Perruzza.

## Legacy reconciliation

These are the proposed identity mappings. A mapping identifies the underlying
sample and source reading; it does not bless the legacy vector when the old
parser altered, omitted, or misassigned source values. The 2023 legacy sample
sizes also carry an apparent factor-of-ten parsing error (`10420` for 1,042,
`10090` for 1,009, and so on), which canonical sample sizes supersede.

| Legacy poll ID | Proposed sample / reading | Reconciliation |
|---|---|---|
| `toronto_2022-2022-10-08-193526f0` | `forum_city_2022_10_07_08_n1017` / `forum_2022_oct08_decided_leaning` | Source-equivalent five-row vector. |
| `toronto_2023-2023-02-14-5a8ad8e6` | `forum_city_2023_02_13_n1042` / `forum_2023_feb13_decided_leaning` | Legacy retains only Bailão and Bradford at 11% each and uses a 78% complement residual. Source separately publishes Layton 26%, Peñalosa 17%, Brown 13%, and `Some other candidate` 23%; the legacy distribution is not source-equivalent. |
| `toronto_2023-2023-03-23-9ed06eb6` | `forum_city_2023_03_22_23_n1009` / `forum_2023_mar23_decided_leaning` | Source prints Saunders 22% and Peñalosa 8%. Legacy assigns 8% to Saunders, omits Peñalosa, and stores 22% as residual: a clear parser misattribution. |
| `toronto_2023-2023-04-26-60f8ec78` | `forum_city_2023_04_25_26_n1022` / `forum_2023_apr26_decided_leaning` | Sample/reading identity matches, but the legacy vector differs materially from the PDF; canonical source values supersede it. |
| `toronto_2023-2023-05-07-6f5a8760` | `forum_city_2023_05_06_07_n2000` / `forum_2023_may07_decided_leaning` | Source-equivalent current-field vector. The Tory scenario remains a dependent additional reading, not another sample. |
| `toronto_2023-2023-05-14-f216820b` | `forum_city_2023_05_13_n1029` / `forum_2023_may13_decided_leaning` | Legacy divides the PDF's integer column, which sums to 101%, by 101. Canonical values preserve the printed percentages. |
| `toronto_2023-2023-05-20-b403ec48` | `forum_city_2023_05_19_n1000` / `forum_2023_may19_decided_leaning` | Source-equivalent vector; legacy date is one day after fieldwork. |
| `toronto_2023-2023-05-27-ad718bff` | `forum_city_2023_05_26_n1007` / `forum_2023_may26_decided_leaning` | Source-equivalent published vector; canonical extraction additionally preserves five offered-but-unpublished candidates. |
| `toronto_2023-2023-06-02-5e744916` | `forum_city_2023_06_02_n1032` / `forum_2023_jun02_decided_leaning` | Legacy divides the PDF's integer column, which sums to 101%, by 101. Canonical values and explicit u/w–w/t bases supersede it. |
| `toronto_2023-2023-06-09-c2c4b67a` | `forum_city_2023_06_09_n1047` / `forum_2023_jun09_decided_leaning` | Legacy keeps the named values but replaces Forum's published 10% `Some other candidate` with a 9% complement residual. |
| `toronto_2023-2023-06-23-5253ec7d` | `forum_city_2023_06_23_n1037` / `forum_2023_jun23_decided_leaning` | Source-equivalent published vector; source base conflict remains explicit. |

`toronto_2023-2023-06-16-e57b0970` remains deliberately unmatched. The June
24 first-party release prints a June 16 trend column that corroborates its
topline vector, but no sample-specific June 16 release was recovered. The trend
column does not establish that wave's exact question wording, sample lineage,
methodology, bases, or publication timing. It is useful corroboration, not
enough evidence to promote a fully audited canonical sample.

## Verification

`load_poll_source_bundle(..., require_audited_sources=True)` accepted the draft,
and `verify_poll_source_artifacts(...)` reproduced every artifact's byte size,
SHA-256, and PDF signature. Final draft counts are:

- 13 source documents and 13 sample-document links;
- 11 respondent samples;
- 21 ballot readings;
- 206 response rows: 186 published values and 20 offered-but-unpublished
  observations; and
- 87 rendered and visually inspected PDF pages.

A temporary in-memory-style integration copy appended this bundle to the
current canonical historical source tables and applied only the proposed
legacy mappings above. `load_historical_mayoral_corpus` accepted the result at
31 documents, 24 samples, 49 readings, and 375 responses. The existing corpus's
other unresolved legacy proxies remain blockers; this Forum wave introduces no
new structural validation failure.
