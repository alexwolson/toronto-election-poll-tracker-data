# Hamilton 2006 official mayoral-result source recovery

**Research date:** 2026-08-17

**Question:** Can the 2006 City of Hamilton jurisdiction-wide mayoral result be recovered from a freely accessible first-party artifact, without a direct request or secondary-source ingestion?

**Decision:** **Blocked for promotion.** The exact official City endpoint is known, but its jurisdiction-wide result payload is not preserved in any public archive checked. Only two of the fifteen official ward reports survive. Those two reports prove the candidate field and the reconstruction method, but they cannot establish the complete citywide totals.

## Executive findings

1. The City itself linked **“2006 Municipal Election Results”** to `http://old.hamilton.ca/clerk/election/2006-election-results/default.asp`. An archived City election landing page contains that direct link twice ([archived City landing page](https://web.archive.org/web/20070926233849id_/http://www.myhamilton.ca/myhamilton/CityandGovernment/CityDepartments/CorporateServices/Clerks/MunicipalElection/)). A separate archived City static mirror also redirects to the identical endpoint ([archived City mirror](https://web.archive.org/web/20160317060119id_/http://www2.hamilton.ca/CityDepartments/CorporateServices/Clerks/MunicipalElection/2006/index.html)).

2. Hamilton's surviving 2010 page at the corresponding endpoint shows what `default.asp` contained: the City wrapper followed directly by a GEMS **“Election Summary Report / Summary For Jurisdiction Wide, All Counters, All Races / Official Results”**, including the complete mayoral table ([archived 2010 City result](https://web.archive.org/web/20160122115108id_/http://old.hamilton.ca/clerk/election/2010-election-results/default.asp)). The desired 2006 artifact is therefore the missing `default.asp` payload itself, not an unidentified attachment behind it.

3. Wayback's index contains no capture of the 2006 `default.asp` under any tested Hamilton host alias. Across the archived `hamilton.ca` election namespace, the only 2006 result payloads are the official Ward 2 and Ward 7 GEMS reports. Both say **“Official Results”**, report every poll in the ward, and contain the same seven-candidate mayoral field ([Ward 2](https://web.archive.org/web/20221008173724id_/https://old.hamilton.ca/clerk/election/2006-election-results/WardByWard/results-2.htm), [Ward 7](https://web.archive.org/web/20220401131121id_/https://old.hamilton.ca/clerk/election/2006-election-results/WardByWard/results-7.htm)).

4. The complete result could be reconstructed exactly by summing the **MAYOR / Total Votes** rows in all fifteen official ward reports, at the deterministic paths `WardByWard/results-1.htm` through `results-15.htm`. That route is presently incomplete: thirteen ward payloads are absent from the public archives checked. Cards cast must not be substituted for mayoral valid votes.

5. Hamilton's current official results archive starts at 2014, and its public ArcGIS/open-data catalog exposes election-result data for newer cycles but no candidate-level 2006 result ([current City archive](https://www.hamilton.ca/city-council/municipal-election/election-results-archives), [official ArcGIS election catalog query](https://www.arcgis.com/sharing/rest/search?f=json&num=100&q=orgid%3ArYz782eMbySr2srL%20election), [official GIS service directory](https://spatialsolutions.hamilton.ca/webgis/rest/services/OpenData?f=pjson)). The City's public eSCRIBE meeting-document search also returned no result for the exact endpoint title, candidate names, or distinctive result terms.

6. No direct request was made. No secondary result table was promoted as a first-party or certified City artifact. The separate proportionality audit below later admits one archived secondary table under an explicitly qualified evidence grade.

## Frozen first-party artifacts

The raw copies are retained under the ignored `data/source_documents/mayoral_comparison_population/hamilton/` directory.

| Local artifact | Original official URL | Archive replay | Bytes | SHA-256 | What it establishes |
|---|---|---|---:|---|---|
| `hamilton_2006_official_election_landing_2007-09-26.html` | `http://www.myhamilton.ca/myhamilton/CityandGovernment/CityDepartments/CorporateServices/Clerks/MunicipalElection/` | [2007-09-26](https://web.archive.org/web/20070926233849id_/http://www.myhamilton.ca/myhamilton/CityandGovernment/CityDepartments/CorporateServices/Clerks/MunicipalElection/) | 46,591 | `322f6175e6f990bb3581b604dabe431cdf6820945f8d7e67f931706d72122816` | The City's election page links the 2006 results to the exact retired endpoint. |
| `hamilton_2006_official_redirect_mirror_2016-03-17.html` | `http://www2.hamilton.ca/CityDepartments/CorporateServices/Clerks/MunicipalElection/2006/index.html` | [2016-03-17](https://web.archive.org/web/20160317060119id_/http://www2.hamilton.ca/CityDepartments/CorporateServices/Clerks/MunicipalElection/2006/index.html) | 989 | `57502bda5b4bf6e0e70f2f0e4d96234beedf699ca31009c0c9ad43d2927c833e` | A second City-owned path redirects to the same exact endpoint. |
| `hamilton_2006_official_ward_02_results_2022-10-08.html` | `https://old.hamilton.ca/clerk/election/2006-election-results/WardByWard/results-2.htm` | [2022-10-08](https://web.archive.org/web/20221008173724id_/https://old.hamilton.ca/clerk/election/2006-election-results/WardByWard/results-2.htm) | 4,948 | `96a9816ae60793d2c2314851420e694dc340014b566d6a90be473e54a137d4fb` | Official Ward 2 GEMS report, 16/16 polls reporting. |
| `hamilton_2006_official_ward_07_results_2022-04-01.html` | `https://old.hamilton.ca/clerk/election/2006-election-results/WardByWard/results-7.htm` | [2022-04-01](https://web.archive.org/web/20220401131121id_/https://old.hamilton.ca/clerk/election/2006-election-results/WardByWard/results-7.htm) | 5,444 | `095117344dba56c71f48e359bc864b18862ed9579b39ea709d6d2e6ea36dd6d8` | Official Ward 7 GEMS report, 21/21 polls reporting. |
| `hamilton_2010_official_results.html` | `http://old.hamilton.ca/clerk/election/2010-election-results/default.asp` | [2016-01-22](https://web.archive.org/web/20160122115108id_/http://old.hamilton.ca/clerk/election/2010-election-results/default.asp) | 41,538 | `8ccd06fecf6d33481a068ee7dcd2c2a1e7eba58124fe67296972a1e1a049daa0` | Structural analogue proving that `default.asp` directly embeds the jurisdiction-wide GEMS report. |

The hashes are for the local replay payloads, not for the retired live server's unarchived originals.

## What the surviving official reports establish

Both reports were generated on November 20, 2006, approximately one second apart. Their mayoral rows reconcile exactly to each report's displayed **Total Votes**.

| Candidate name as shown | Ward 2 | Ward 7 | Surviving two-ward subtotal |
|---|---:|---:|---:|
| Michael J. BALDASARO | 367 | 465 | 832 |
| Larry DiIANNI | 2,386 | 6,144 | 8,530 |
| Fred EISENBERGER | 2,574 | 5,938 | 8,512 |
| Diane ELMS | 518 | 1,060 | 1,578 |
| Steve LEACH | 93 | 151 | 244 |
| Gino SPEZIALE | 86 | 232 | 318 |
| Martin S. ZULINIAK | 60 | 53 | 113 |
| **Valid mayoral votes** | **6,084** | **14,043** | **20,127** |

Ward 2 separately reports 6,182 cards cast and Ward 7 reports 14,209. The difference from valid mayoral votes is expected and demonstrates why cards cast cannot be used as the mayoral denominator.

The two reports establish the seven candidate names and their order in the GEMS output. They do **not** establish any candidate's jurisdiction-wide total, the citywide valid-vote denominator, or the citywide registered-voter/turnout figures.

## Archive and live-source audit

### Exact endpoint and known aliases

Wayback CDX returned no row for the exact `default.asp` under HTTP or HTTPS on:

- `old.hamilton.ca`
- `hamilton.ca`
- `www.hamilton.ca`
- `www2.hamilton.ca`
- `myhamilton.ca`
- `www.myhamilton.ca`

The broader archived Hamilton election URL inventory found only three 2006 result URLs with successful payloads: the City mirror redirect plus Ward 2 and Ward 7. A MyHamilton CMS alias named `2006MunicipalElectionResults.htm` has only a 2016 redirect to a Hamilton Public Library 404 page; it does not preserve results.

Archive-It returned no capture for the exact endpoint. Arquivo.pt and Common Crawl returned no exact or prefix match. Internet Archive item search did not locate a separately uploaded City report. The retired `old.hamilton.ca` host no longer resolves; bounded checks of its last publicly observed server addresses did not recover a live service.

### Current City systems

- The current results archive exposes 2014, the 2016 Ward 7 by-election, 2018 and 2022, but no 2006 result.
- The official ArcGIS organization search returns modern election maps/results, with no 2006 candidate-result item.
- The public GIS `OpenData` service catalog contains 2022 election result tables, but no 2006 election result table.
- The current City site index finds 2006 election-administration by-laws, not a result declaration or summary.
- No retained eSCRIBE meeting attachment was located through exact report-title, candidate-combination, or result-specific searches.

These are evidence of a public-access gap, not proof that the City never retained the permanent record elsewhere.

## Promotion decision and remaining gap

**Do not promote a Hamilton 2006 candidate result from this bundle.** Under the first-party-only rule, the complete candidate totals remain unverified.

The minimum artifact that would clear the block is one of:

1. the archived or live City payload for `.../2006-election-results/default.asp`;
2. a City-issued declaration or jurisdiction-wide GEMS export containing the full mayoral table; or
3. all thirteen missing official ward reports, allowing a reproducible sum across Wards 1–15.

Until one of those appears through a freely accessible or purchasable archival route, the honest **first-party artifact** state is `source_unavailable`. The separate decision below admits corroborated values for modelling without presenting the secondary reconstruction as official.

## Proportionality audit: admission under a broader evidence policy

**Separate decision:** **Admit Hamilton 2006 to the incumbency comparison population with a qualified source status.** This does not change the source-recovery finding above: the certified jurisdiction-wide City payload has not been recovered. It changes the modelling gate because “official artifact not recovered” is not the same claim as “result unverified.”

The grades below are project-specific judgments, not an external rating system:

- **A — verified:** independently supported by strong evidence appropriate to the claim;
- **B+ — strongly corroborated:** exact key values survive in a contemporaneous City-derived transcription and agree across the evidence chain, but the certified artifact is absent; and
- **B — corroborated:** the complete value set is durable and internally consistent, but its exact figures do not have a second independent high-trust transcription.

| Claim | Grade | Evidence and limit |
|---|---|---|
| Incumbent Larry Di Ianni lost to Fred Eisenberger | **A** | A next-day CityNews report says Di Ianni was defeated by Eisenberger ([CityNews, November 14, 2006](https://toronto.citynews.ca/2006/11/14/miller-gets-four-more-years-as-incumbents-dominate-election-day/)). Anderson and Morgan's academic incumbency study includes Hamilton 2006 and says its Hamilton election data came from the City website and direct contact with the City Clerk's Office ([Anderson and Morgan, 2011](https://cpsa-acsp.ca/papers-2011/Anderson.pdf)). Neither source supplies the complete result table. |
| Seven-candidate field | **A** | The surviving official Ward 2 and Ward 7 GEMS reports independently display the same seven-candidate mayoral field. They cannot establish citywide vote totals. |
| Eisenberger 54,110; Di Ianni 53,658; 452-vote margin | **B+** | On election night, Raise the Hammer reported that the City's Election Summary Report had all 206 polls reporting and transcribed Eisenberger's 54,110 total; its contemporaneous discussion records Di Ianni at 53,658 and the 452-vote margin ([Raise the Hammer, November 13, 2006](https://www.raisethehammer.org/blog/389/)). A next-day Wikipedia revision identifies the City endpoint as its source and records the 452-vote margin ([revision 87796727](https://en.wikipedia.org/w/index.php?title=2006_Hamilton,_Ontario,_municipal_election&oldid=87796727)). This is strong preservation of the City's reported return, not a recovered certified City payload. |
| Full candidate table and 125,239 valid mayoral votes | **B** | A durable 2008 article revision contains the seven exact candidate totals and labels 125,239 as valid votes ([revision 228503734](https://en.wikipedia.org/w/index.php?title=2006_Hamilton,_Ontario,_municipal_election&oldid=228503734)). The figures sum exactly: 54,110 + 53,658 + 9,459 + 4,520 + 1,274 + 1,250 + 968 = 125,239, and the displayed percentages reconcile. This table belongs to the same City-return evidence lineage; it is not an independent recount. |

The Canadian Municipal Elections Database does not add an independent check: its historical 2000–2014 coverage was limited to Calgary, Edmonton, Montreal, Toronto, Vancouver and Winnipeg, not Hamilton ([CMED introduction](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/61ED977A61A366C6BDD9D6876E753BC9/S000842392000102Xa.pdf/womens_municipal_electoral_performance_an_introduction_to_the_canadian_municipal_elections_database.pdf)). No accessible report of a recount or corrected final total was found.

### Why the first-party-only block is disproportionate

Excluding this row selects on archival survival rather than electoral uncertainty. The incumbent defeat itself is not in doubt, and removing a known loss from this small comparison population changes the observed record from 13 wins in 19 attempts (68.4%) to 13 in 18 (72.2%).

The exact-value risk is bounded. Hamilton 2006 has an incumbent share of 53,658 / 125,239 = 42.84% and an incumbent margin of -452 / 125,239 = -0.36 percentage points. Each is the sixth-lowest value among the 19 regular trials, rather than a median-setting observation. Omitting the row would move the sample medians from 59.65% to 60.82% for incumbent share and from 34.10 to 37.00 percentage points for margin. That modest sensitivity can be reported without blocking the entire population.

### Exact recommended status contract

Keep the existing source-table columns. Add this value to the `verification_status` vocabulary:

```text
corroborated_secondary
```

Its exact definition should be:

> Exact trial values are fit-eligible under the proportionate evidence policy because a contemporaneous City-derived transcription is supported by independent outcome evidence, but a complete official jurisdiction-wide artifact has not been recovered.

Only `source_gap` should remain readiness-blocking. `corroborated_secondary` should remain distinct from `verified_artifact` and `verified_official_dynamic_source`; it must not imply certification of the missing City payload. A retained secondary webpage may carry its own real hash and local audit path, provided those fields are clearly metadata for that secondary artifact rather than the missing official result.

Recommended source-row note:

```text
Fit-eligible under the proportionate evidence policy. Incumbent defeat and seven-candidate field are verified (grade A); exact top-two totals are strongly corroborated (grade B+); full candidate table and 125,239 valid-vote denominator are corroborated and arithmetic-consistent (grade B). Certified jurisdiction-wide City payload not recovered. See docs/research/hamilton-2006-official-mayoral-result.md.
```

Recommended trial-row source locator and note:

```text
source_locator: City-derived secondary transcription; certified City payload not recovered
notes: Admitted to v1 under the proportionate evidence policy; retain a Hamilton-omission sensitivity for continuous-share summaries.
```

No additional certification column is warranted for this one exception: the qualified status plus the precise note preserves the material distinction without expanding a small hobby-project schema.
