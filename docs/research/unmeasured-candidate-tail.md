# Registered candidates without individual poll estimates: historical Toronto evidence

**Research date:** 2026-08-17  
**Scope:** Toronto mayoral elections, Toronto council elections, and publicly accessible poll documentation  
**Purpose:** Evidence for understanding an Unmeasured Candidate Tail. This note does not set model or publication policy.

## Findings in brief

- A long ballot does not imply that every candidate outside the leaders is individually consequential, but the aggregate remainder is often consequential. Across the seven Toronto mayoral elections from 2003 through the 2023 by-election, the final share outside the top three ranged from **2.85% to 21.79%** (median **9.50%**). In council races, the combined final share of candidates finishing third or lower had a median of **17.84%** across 223 comparable ward-races from 2003 through 2022, and **24.11%** in the 2018–2022 25-ward era.
- The closest defensible measure of a poll omission is not that broad result tail. It is the final vote share of registered candidates who received no individual row in a published poll. In three late-campaign mayoral examples, that realized unnamed share was **2.85% (2014), 12.92% (2018), and 7.72% (2023)**. No unnamed candidate finished first or second. In 2023, however, unnamed Chloe Brown finished seventh with 2.60%, ahead of individually reported Brad Bradford in eighth with 1.28%.
- Six post-registration Forum Research ward polls from 2022 provide a small direct council sample. The realized share of candidates without an individual published row ranged from **0% to 30.24%** (median **16.60%**); it exceeded 20% in three of six wards. No such candidate won, but one did finish second: **Bill Wu received 18.73% in Ward 22**, while the poll release described individually reported Serge Khatchadourian as being in second place; Khatchadourian ultimately finished fifth.
- A poll's `Other` category is not an estimate of the final unmeasured-candidate share. In Wards 5 and 20, Forum gave every eventual ballot candidate an individual row, yet `Other` was **12% and 14%**, respectively. Conversely, the realized unnamed tail exceeded the reported `Other` share in Wards 10, 13, and 22.
- The verified poll-result matches contain **no omitted winner**, but they are not a representative sample from which a near-zero winner probability can be estimated. The council evidence consists of six small IVR polls from one firm and one election, and publication/archival selection is unknown.

## Definitions and method

This note uses three different quantities and does not treat them as interchangeable:

1. **Result tail after the top three (mayor):** the combined final valid-vote share of candidates finishing fourth or lower. This describes ballot fragmentation; it does not identify who a poll omitted.
2. **Result tail after the top two (council):** the combined final valid-vote share of candidates finishing third or lower. This is a broad outcome-based measure of the vote outside the leading pair; it is not a poll-omission measure.
3. **Realized unnamed tail (matched polls):** the combined final valid-vote share of candidates who had no individual candidate row in the poll's published vote-intention table. `Other`, `another candidate`, undecided, and refusal categories are not counted as individual candidate rows.

“Unnamed” therefore means **not individually reported in the public topline**, not necessarily “never read to a respondent.” Most releases do not publish the IVR recording or complete questionnaire logic needed to prove the latter.

All final shares use votes credited to candidates as the denominator, excluding rejected, declined, and blank ballots. Candidate names were manually matched between poll tables and City results. The council-wide calculations group the repository's official-result extract by election year and ward, sort candidates by vote share, and calculate:

```text
combined_third_or_lower = 1 - winner_share - runner_up_share
largest_outside_top_two = third_place_share
winner_margin = winner_share - runner_up_share
```

The City says its general-results page covers declarations and poll-by-poll results from 2003 through 2022; the repository extract records the direct City Open Data archive URL on every row. [City of Toronto general election results](https://www.toronto.ca/city-government/elections/election-results-reports/election-results/general-election-results/)

## Mayoral elections

### Complete-result tails

The following table is descriptive. “Outside top three” is not the set of candidates omitted by a particular poll.

| Election | Candidates receiving a result | Final top three | Share outside top three | Largest candidate outside top three | Official source |
|---|---:|---|---:|---|---|
| 2003 | 44 | David Miller; John Tory; Barbara Hall | 9.50% | John Nunziata, 5.20% | [City declaration](https://www.toronto.ca/wp-content/uploads/2017/08/9868-election-2003-clerkofficialdeclaration.pdf) |
| 2006 | 38 | David Miller; Jane Pitfield; Stephen LeDrew | 9.33% | Michael Alexander, 0.90% | [City declaration](https://www.toronto.ca/wp-content/uploads/2017/08/8f72-election-2006-clerksofficialdeclaration.pdf) |
| 2010 | 40 | Rob Ford; George Smitherman; Joe Pantalone | 5.55% | Rocco Rossi, 0.62% | [City declaration](https://www.toronto.ca/wp-content/uploads/2017/08/9783-election-2010-clerksofficialdeclaration.pdf) |
| 2014 | 65 | John Tory; Doug Ford; Olivia Chow | 2.85% | Ari Goldkind, 0.40% | [City declaration](https://www.toronto.ca/wp-content/uploads/2017/08/9059-election-2014-clerksofficialdeclarationofresults.pdf) |
| 2018 | 35 | John Tory; Jennifer Keesmaat; Faith Goldy | 9.53% | Saron Gebresellassi, 2.01% | [City declaration](https://www.toronto.ca/wp-content/uploads/2018/10/97da-2018clerksofficialdeclarationofresults.pdf) |
| 2022 | 31 | John Tory; Gil Penalosa; Chloe-Marie Brown | 13.84% | Blake Acton, 1.61% | [City declaration](https://www.toronto.ca/wp-content/uploads/2022/10/9085-FinalDeclaration-of-Results-for-the-2022-Toronto-Municipal-Election.pdf) |
| 2023 by-election | 102 | Olivia Chow; Ana Bailão; Mark Saunders | 21.79% | Anthony Furey, 4.95% | [City declaration](https://www.toronto.ca/wp-content/uploads/2023/06/8eef-Declaration-of-Results-for-the-2023-Toronto-By-Election-for-Mayor-Final.pdf) |

The 2023 result is a warning against treating “minor candidates” and “everyone outside the top three” as synonyms: Furey, Matlow, Hunter, Brown, and Bradford together formed a meaningful part of the result even though none finished in the top three. The City certified 102 candidates after a May 12 nomination deadline. [City of Toronto 2023 by-election fact sheet](https://www.toronto.ca/news/torontos-2023-by-election-for-mayor/)

### Poll-result matches

These examples use late-campaign public releases with an explicit candidate table and a final ballot already substantially or fully settled.

| Election and poll | Individually published candidates | Published aggregate category | Realized unnamed tail | Largest unnamed finisher | Ordering relevance |
|---|---|---:|---:|---|---|
| 2014 Ipsos, Oct. 21–23, n=1,201 | Tory; Doug Ford; Chow | Other 2% | 2.85% | Ari Goldkind, 0.40% (4th) | No unnamed candidate entered the top three. |
| 2018 Forum, Sept. release, n=811 (729 decided/leaning) | Tory; Keesmaat | Another candidate 15% | 12.92% | Faith Goldy, 3.40% (3rd) | Winner and runner-up were individually reported. |
| 2023 Ipsos, June 9–13, n=1,001 | Chow; Saunders; Bailão; Matlow; Furey; Hunter; Bradford | Other candidates 10% | 7.72% | Chloe Brown, 2.60% (7th) | Brown finished ahead of named Bradford, 1.28% (8th); the top six were named. |

Sources: Ipsos's 2014 release reports 42% Tory, 31% Ford, 25% Chow, and 2% other among decided voters, with field dates and mixed-mode sample details. [Ipsos 2014 release](https://www.ipsos.com/en-ca/john-tory-42-headed-toronto-mayors-chain-office-over-ford-31-chow-25) Forum's 2018 table reports only Tory, Keesmaat, and `Another candidate` as vote-intention rows. [Forum Research 2018 release](https://poll.forumresearch.com/data/11295651-2b49-4142-b192-e9d95b16d42bTO_Affordability%20News%20Release%20from%20Forum%20Research_Sep%207%2C%202018.pdf) Ipsos's 2023 factum reports the seven named candidates, 10% supporting other candidates, 14% unsure, and the June 9–13 mixed online/telephone methodology; its detailed tables publish the exact vote-intention question and response rows. [Ipsos 2023 factum](https://www.ipsos.com/sites/default/files/ct/news/documents/2023-06/22-003004-01%20GN%20Media%20Release%20%283%29.pdf) [Ipsos 2023 detailed tables](https://www.ipsos.com/sites/default/files/ct/news/documents/2023-06/Toronto%20Mayoral%20Race%20Tables%202.pdf)

Across these three matched mayoral cases, no candidate without an individual published estimate finished first or second. The strongest ordering discrepancy was Brown passing Bradford in 2023, but both remained below 3% of valid votes.

## Council elections

### Complete-result tails

The official-result extract contains 226 ward-races: 44 wards in each of 2003, 2006, 2010, and 2014, and 25 wards in each of 2018 and 2022. The comparable summaries below exclude two 2003 acclamations, where a top-two tail is undefined, and 2022 Ward 23. The City states that votes cast for the late Cynthia Lai in Ward 23 were not counted and are unavailable, so that result does not represent the complete candidate field. [City of Toronto 2022 certification notice](https://www.toronto.ca/news/toronto-city-clerk-certifies-2022-toronto-municipal-election-results/)

| Scope | Comparable ward-races | Median candidates | Combined third-or-lower share, median (IQR; 90th percentile; max) | Median largest candidate outside top two | Combined tail larger than winner margin | Third-place share larger than winner margin |
|---|---:|---:|---:|---:|---:|---:|
| 2003–2022 | 223 | 6 | 17.84% (11.00–28.31%; 38.09%; 66.43%) | 8.25% | 92/223 (41.3%) | 62/223 (27.8%) |
| 2018–2022, 25-ward era | 49 | 8 | 24.11% (15.53–33.25%; 38.37%; 52.99%) | 9.03% | 29/49 (59.2%) | 20/49 (40.8%) |
| 2022 only | 24 | 6 | 18.08% (14.33–32.53%; 35.11%; 42.11%) | 8.43% | 11/24 (45.8%) | 6/24 (25.0%) |

Those last two columns establish arithmetic salience only. They do **not** show that lower-ranked candidates caused a different winner: first-past-the-post results contain no second preferences and do not identify how votes would move under a smaller candidate field.

### Six directly matched 2022 ward polls

Toronto certified the final 2022 field on August 20, after the August 19 filing/withdrawal deadline: 164 candidates ran for council. [City of Toronto candidate certification](https://www.toronto.ca/news/toronto-city-clerk-certifies-372-candidates-for-october-24-municipal-election/) Forum then published polls conducted September 13–15 in Wards 4, 5, 10, 13, 20, and 22. Each used an IVR sample of 207–228 eligible ward voters; the published councillor tables were based on 90–165 decided/leaning respondents.

The table matches each poll's individually reported rows to the [City's official 2022 result](https://www.toronto.ca/wp-content/uploads/2022/10/9085-FinalDeclaration-of-Results-for-the-2022-Toronto-Municipal-Election.pdf). One mid-September poll per ward is used; a later second Ward 5 poll is not double-counted.

| Ward and primary poll | Individual candidate rows | Poll `Other` | Realized unnamed tail | Largest unnamed final result | Final winner margin | Ordering relevance |
|---|---|---:|---:|---|---:|---|
| [4, Parkdale–High Park](https://poll.forumresearch.com/data/0f87336b-4a32-498e-8411-70b1dd986581Ward%204%20News%20Release.pdf) | Perks; Agrell; Lhamo; Gorham | 11% | 5.26% | Christopher Jurik and Steve Yuen, 2.63% each (tied 4th) | 3.91% | Winner and runner-up named; both unnamed candidates finished ahead of named Gorham. |
| [5, York South–Weston](https://poll.forumresearch.com/data/74bddea4-50a4-4c53-a017-52dabdd9cb43Ward%205%20News%20Release.pdf) | Nunziata; Padovani; Takang | 12% | 0% | None | 0.44% | Every final candidate had an individual row. |
| [10, Spadina–Fort York](https://poll.forumresearch.com/data/b390026c-ece7-475d-85f0-9cc0e050e9e0Ward%2010%20News%20Release.pdf) | Malik; Engelberg; Achampong; Nation | 22% | 28.88% | Peter George, 7.99% (4th) | 15.21% | Final top three named; George and Igor Samardzic finished ahead of named Nation. |
| [13, Toronto Centre](https://poll.forumresearch.com/data/a199cd17-a268-43ac-a464-8c75787e2657Ward%2013%20News%20Release.pdf) | Moise; Ward; Lester | 23% | 30.24% | Caroline Murphy, 12.17% (3rd) | 30.22% | Unnamed Murphy finished third, ahead of named Lester. |
| [20, Scarborough Southwest](https://poll.forumresearch.com/data/00bd353b-b4c5-4efc-ba8a-7e75d5abb630Ward%2020%20News%20Release.pdf) | All eight final candidates | 14% | 0% | None | 5.46% | Every final candidate had an individual row. |
| [22, Scarborough–Agincourt](https://poll.forumresearch.com/data/2fc49a81-6baf-49bc-ad01-f22449099fb4Ward%2022%20News%20Release.pdf) | Nick Mantas; Antonios Mantas; Serge Khatchadourian; Anthony Internicola | 21% | 27.94% | Bill Wu, 18.73% (2nd) | 30.15% | The release called Khatchadourian second; unnamed Wu became the actual runner-up. Unnamed Roland Lin also finished ahead of Khatchadourian. |

Across the six wards:

- the realized unnamed tail had a mean of **15.39%**, median of **16.60%**, and range of **0–30.24%**;
- three of six had an unnamed tail above 20%; two of six had no unnamed ballot candidate at all;
- four of six had at least one unnamed candidate finish ahead of an individually reported candidate;
- two of six had an unnamed top-three finisher; one of six had an unnamed runner-up; and
- none had an unnamed winner.

In three of six wards (4, 10, and 13), the aggregate realized unnamed tail was larger than the final winner–runner-up margin. This remains an arithmetic comparison, not evidence that votes would have transferred as a bloc or changed the winner.

## What can and cannot be inferred

### Supported by the observed record

- Individually unreported candidates can be relevant to **which candidate is the leading challenger**, even where the winner remains correctly identified. Ward 22 is the direct example.
- An aggregate tail can be substantial while no single tail candidate is close to winning. Ward 10's unnamed candidates totalled 28.88%, but the largest had 7.99% and finished fourth.
- A relatively small individual share can still alter lower-rank ordering. This occurred with Chloe Brown versus Brad Bradford in the 2023 mayoral result and in four of the six ward matches.
- `Other` is empirically not interchangeable with a sum of unreported registered candidates. The zero-tail Ward 5 and Ward 20 examples prove that it captures something else or is affected by measurement error even when the published table names the complete final field.

### Not established by these data

- **No universal “omitted candidates never win” rate.** Zero omitted winners among three mayoral and six ward matches is a factual sample result, not a population estimate. The examples were not randomly selected, and the public ward-poll archive is sparse.
- **No spoiler or vote-transfer effect.** Final results do not reveal second choices or the counterfactual result if a candidate had not run, had been named in a poll, or had received more coverage.
- **No conversion from poll `Other` to election-day tail.** Poll bases differ (all eligible voters, likely voters, decided voters, or decided/leaning voters), field dates differ, and `Other` can include responses unrelated to a registered candidate.
- **No proof of questionnaire omission from a topline omission.** A candidate without a published row may have been available through an `Other` prompt or may have been suppressed in reporting. The public releases generally do not include complete IVR scripts.
- **No justified pooling of mayoral and council tails.** Citywide media exposure and name recognition differ from ward campaigning, and ward candidate fields vary sharply. The 44-ward elections through 2014 also differ structurally from the 25-ward elections beginning in 2018.

## Data and archival limitations

1. **Pollster selection is endogenous.** Firms usually give individual rows to candidates already believed to be relevant. Small realized unnamed shares may reflect successful preselection, not a natural distribution that applies to a new race.
2. **Publication selection is unknown.** The six council matches are public releases from one firm, one election, and selected wards. There may have been unpublished polls or public releases no longer discoverable.
3. **Small ward samples make rankings noisy.** The decided/leaning bases were as low as 90. The observed Ward 22 discrepancy combines candidate-field reporting, sampling error, campaign change, and turnout; it cannot be attributed solely to omission.
4. **Timing matters.** A clean omission study should only treat a candidate as eligible for the final tail after the filing/withdrawal deadline and should retain poll field dates. Candidates who stop campaigning but remain on the ballot further complicate hindsight classifications.
5. **Results observe outcomes, not pre-election plausibility.** Calling a candidate “minor” based on a low final share uses hindsight. Conversely, a high final share does not establish that the candidate was recognizably viable on the poll date.
6. **Source durability is poor.** Several Forum PDF links were intermittently returning 404/502 responses on the research date despite remaining search-indexed. Reproducible future work requires storing the original release, questionnaire/topline, retrieval date, and checksum rather than relying only on a URL.

## Reproducibility notes

Repository inputs used:

- `data/raw/elections/historical_council_results.csv` — 1,516 candidate rows across 226 ward-races, with a direct City source URL on each row;
- `scripts/fetch_historical_council_results.py` — parser and validation for the 2003, 2006, 2010, 2014, 2018, and 2022 official archives; and
- `data/raw/elections/mayoral_results.csv` — official ward-level candidate votes for 2018, 2022, and 2023.

Older mayoral totals were summed from the same City result archives linked through the City's general-results page. Every matched-poll percentage in this note was recalculated from final candidate votes rather than copied from a secondary election summary.
