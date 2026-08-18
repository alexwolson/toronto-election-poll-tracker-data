# Council incumbency prior: defensible historical population

Research date: 2026-08-17

This note audits the historical population that could support a **Council Incumbency Prior**. It does not select a statistical model. Its purpose is to define what the observations are, identify where the current derived artifact departs from that definition, and separate reconstructible pre-election facts from hindsight.

## Bottom line

The defensible population available from the City's currently published post-amalgamation election records is **126 same-ward incumbent general-election attempts, with 118 wins and 8 losses (93.65% retention), across 63 people and four target elections**. That is an unconditional descriptive base rate, not a calibrated forecast and not evidence that every attempt is an independent observation.

The current processed artifact contains **121 attempts, 113 wins and the same 8 losses (93.39%)**. It omits five valid wins:

- the 2006 re-election wins of Giorgio Mammoliti and David Shiner, because their 2003 victories were acclamations;
- the 2006 re-election wins of Cliff Jenkins and Norm Kelly, because the official files change `Clifford` to `Cliff` and `Norman` to `Norm`; and
- Nick Mantas's 2022 re-election win after he entered Council through the 2021 Ward 22 by-election.

The first four omissions can be seen by comparing the official-result extract with [`build_historical_incumbent_cases`](../../backend/model/council.py); the fifth requires the City's [2021 Ward 22 by-election declaration](https://www.toronto.ca/wp-content/uploads/2021/01/8e1c-Results_Official_Declaration_2021_By-Election_Ward-22.pdf) and its [Council service roster](https://www.toronto.ca/explore-enjoy/history-art-culture/mayors-councillors-reeves-chairmen/city-of-toronto-councillors/), not just the preceding general-election winner.

The corrections do **not** add a ninth defeat. The eight observed incumbent defeats remain the binding empirical scarcity. The 126 attempts are also repeated observations of only 63 councillors: 37 people appear more than once. Any uncertainty calculation that treats all 126 rows as independent would overstate the information in the sample.

The 2018 election should not be pooled into this ordinary same-ward population. Toronto changed from 44 wards to 25, creating incumbent-versus-incumbent contests and new geographies. It is useful as a separately labelled boundary-shock sample.

## Primary data and coverage

The City says its online general-election results span **2003 through 2022** and provide poll-by-poll results for every candidate and ward ([General Election Results](https://www.toronto.ca/city-government/elections/election-results-reports/election-results/general-election-results/)). The repository's [`fetch_historical_council_results.py`](../../scripts/fetch_historical_council_results.py) downloads those six official archives into [`historical_council_results.csv`](../../data/raw/elections/historical_council_results.csv).

The extract has the following shape:

| Election | Wards | Councillor candidate rows in result files | Councillor acclamations |
|---:|---:|---:|---:|
| 2003 | 44 | 199 | 2 |
| 2006 | 44 | 275 | 0 |
| 2010 | 44 | 279 | 0 |
| 2014 | 44 | 358 | 0 |
| 2018 | 25 | 242 | 0 |
| 2022 | 25 | 163 | 0 |

The two councillor acclamations are Giorgio Mammoliti in Ward 7 and David Shiner in Ward 24 in 2003. The official files encode each with zero votes; the repository parser correctly marks the sole candidate as acclaimed and assigns a result share of one for validation. That synthetic share must not be interpreted as a measured 100% vote share.

Result files are not always a faithful copy of the **Final Ballot**. The Clerk certified **164** council candidates in 2022 ([certification release](https://www.toronto.ca/news/toronto-city-clerk-certifies-372-candidates-for-october-24-municipal-election/)), while the result archive has 163 council rows. The missing row is not a parsing error: incumbent Cynthia Lai died before election day, and the Clerk states that votes cast for her were not counted and would not be available in the results ([2022 certification of results](https://www.toronto.ca/news/toronto-city-clerk-certifies-2022-toronto-municipal-election-results/)). Historical candidate fields therefore need archived certified-candidate lists, with result files used for outcomes.

## Risk-set definition

The unit is a **candidate-election attempt**, not a ward and not a unique politician. An observation enters the ordinary Council incumbency population when all of the following are true at the historical forecast cutoff:

1. The person is the sitting councillor for a ward when nominations are finally certified.
2. The person is on the certified ballot for the same geographically comparable ward.
3. The election produces a valid, counted councillor result.
4. The outcome is whether that person won the ward.

This definition has several consequences:

- **Include prior acclamations in the base-rate population.** Mammoliti and Shiner were sitting same-ward councillors seeking re-election in 2006. Their prior vote share and margin are missing, but the outcome is not. Excluding them from the base rate selects observations according to whether a proposed predictor happens to exist.
- **Include interim entrants.** A councillor elected in a by-election or appointed during the term is an incumbent if they seek the same ward. Mantas therefore enters the 2022 risk set. The City's [by-election index](https://www.toronto.ca/city-government/elections/election-results-reports/election-results/by-election-results/) and Council decisions are required alongside general-election results.
- **Do not infer incumbency from the preceding general-election winner alone.** The official [Council service roster](https://www.toronto.ca/explore-enjoy/history-art-culture/mayors-councillors-reeves-chairmen/city-of-toronto-councillors/) includes by-election winners and appointees who do not appear as the prior general-election winner.
- **Keep ward movers separate.** Paul Ainslie was appointed to Ward 41 in January 2006 and won Ward 43 that fall; Robin Buxton Potts was appointed to Ward 13 in 2022 and ran in Ward 11. They were sitting councillors, but they were not same-ward incumbents. `sitting_councillor_new_ward` is more accurate than forcing either into `incumbent` or `open`.
- **Censor non-electoral endings.** Lai's 2022 row is neither a defeat nor an ordinary open-seat contest. It is an incumbent attempt with no countable election outcome.
- **Separate boundary shocks.** A matching ward number is insufficient when the geography changes materially.

There were no target-election councillor acclamations in 2006, 2010, 2014 or 2022. If a future target election contains one, it belongs in the retention outcome population but contributes no competitive vote-share outcome.

## Reconciled population

The hand audit below uses the official general-election results, interim election declarations, Council service records, and explicit candidate aliases. “Other valid-result wards” means no same-ward incumbent attempt under the definition above; it is deliberately not called “open,” because the group can contain a councillor moving from another ward.

| Target election | Current artifact: cases / wins / losses | Audited cases / wins / losses | Other valid-result wards | Censored wards |
|---:|---:|---:|---:|---:|
| 2006 | 33 / 32 / 1 | **37 / 36 / 1** | 7 | 0 |
| 2010 | 35 / 30 / 5 | **35 / 30 / 5** | 9 | 0 |
| 2014 | 37 / 36 / 1 | **37 / 36 / 1** | 7 | 0 |
| 2022 | 16 / 15 / 1 | **17 / 16 / 1** | 7 | 1 |
| **Total** | **121 / 113 / 8** | **126 / 118 / 8** | **30** | **1** |

The 157 target wards reconcile as 126 valid same-ward incumbent attempts, 30 other valid-result wards, and Lai's one censored ward.

### The five omitted wins

| Target | Ward | Incumbent | Why the current derivation misses the case | Audited outcome |
|---:|---:|---|---|---|
| 2006 | 7 | Giorgio Mammoliti | 2003 prior win was acclaimed; code skips all prior acclamations | Won |
| 2006 | 24 | David Shiner | 2003 prior win was acclaimed; code skips all prior acclamations | Won |
| 2006 | 25 | Cliff Jenkins | `Jenkins, Clifford` becomes `JENKINS CLIFF`; token equality treats these as different people | Won |
| 2006 | 40 | Norm Kelly | `Kelly, Norman` becomes `KELLY NORM`; token equality treats these as different people | Won |
| 2022 | 22 | Nick Mantas | The prior general-election winner was Jim Karygiannis; Mantas won the intervening 2021 by-election | Won |

The name and outcome records are in the repository's official-data extract, [`historical_council_results.csv`](../../data/raw/elections/historical_council_results.csv). Mantas won the 2021 by-election with 3,261 votes to Manna Wong's 3,038, according to the [Clerk's declaration](https://www.toronto.ca/wp-content/uploads/2021/01/8e1c-Results_Official_Declaration_2021_By-Election_Ward-22.pdf), then won Ward 22 in the official 2022 results.

An explicit person/entity table is necessary. Sorting name tokens handles order changes, but it cannot resolve nicknames, shortened legal names, changed surnames, transliterations, or two different people with the same name.

### The eight observed defeats

| Election | Ward | Incumbent defeated |
|---:|---:|---|
| 2006 | 8 | Peter Li Preti |
| 2010 | 1 | Suzan Hall |
| 2010 | 13 | Bill Saundercook |
| 2010 | 25 | Cliff Jenkins |
| 2010 | 32 | Sandra Bussin |
| 2010 | 35 | Adrian Heaps |
| 2014 | 26 | John Parker |
| 2022 | 3 | Mark Grimes |

These rows can be reproduced from the official-data extract by joining each sitting same-ward incumbent to the target result. The current [`historical_council_incumbent_cases.csv`](../../data/processed/historical_council_incumbent_cases.csv) contains all eight, even though it omits five wins.

## Boundary comparability and excluded transitions

### 2014 to 2018 is a different election regime

The City's boundary review explains that Toronto had used its prior ward structure since the 2000 review and that provincial Bill 5 established the 25-ward model ([Ward Boundaries for Toronto](https://www.toronto.ca/city-government/accountability-operations-customer-service/city-administration/city-managers-office/ward-boundaries-for-toronto/)). Council's 2018 implementation record separately identifies the pre-December 2018 wards by Ontario Regulation 191/00 and the new wards taking effect afterward ([EX35.2](https://secure.toronto.ca/council/agenda-item.do?item=2018.EX35.2)). The Province prescribed the 25 named wards in [O. Reg. 408/18](https://www.ontario.ca/laws/regulation/r18408).

A hand join of the official Council service roster, the 2016 and 2017 council by-election declarations, and the official 2018 result produces this boundary-shock description:

- 34 sitting councillors appeared on 2018 council ballots across 23 of the 25 new wards;
- 21 of those 34 candidates won and 13 lost;
- 12 wards had one sitting councillor on the ballot, 11 had two, and 2 had none; and
- a sitting councillor won 21 of the 23 wards containing at least one incumbent. In Wards 8 and 25, every sitting councillor lost.

Thus “21 of 34 incumbent candidates won” and “21 of 23 wards with an incumbent returned one” are both correct but answer different questions. Pooling either with same-ward retention would change the estimand. The official inputs are the [2018 Clerk declaration](https://www.toronto.ca/wp-content/uploads/2018/10/97da-2018clerksofficialdeclarationofresults.pdf), the [Council service roster](https://www.toronto.ca/explore-enjoy/history-art-culture/mayors-councillors-reeves-chairmen/city-of-toronto-councillors/), and the City's [2016 Ward 2](https://www.toronto.ca/wp-content/uploads/2017/08/8e3a-2017-byelection-ward2-declarationofresults.pdf) and [2017 Ward 42](https://www.toronto.ca/wp-content/uploads/2017/08/96c5-ward42_byelection_declarationofresults.pdf) by-election declarations.

The 2018 observations can be retained as a labelled redistricting stress test, but not silently treated as ordinary incumbent retention.

The current derivation makes the opposite choice explicitly. [`HISTORICAL_PAIRS`](../../backend/model/council.py) contains 2003→2006, 2006→2010, 2010→2014 and 2018→2022, but not 2014→2018. It also enforces one incumbent case per election and ward. That is appropriate for a same-ward retention table, but it cannot represent the 11 new wards in which two sitting councillors competed; attempting to add both would violate its election-and-ward uniqueness check.

A candidate-officeholding history could retain 2018, but only as a different regime with candidate-level rows. The official [2018 Municipal Election Report](https://www.toronto.ca/wp-content/uploads/2019/07/96b2-2018-Election-Report.pdf) says Bill 5 aligned 25 wards with federal and provincial districts, that the governing ward model changed from 47 to 25, back to 47, and finally to 25 during the nomination period, and that the final 25-ward field was certified only on September 21. The City also publishes both the former 44-ward and new 25-ward polygon files in its [City Wards open-data package](https://open.toronto.ca/dataset/city-wards/), including the direct [44-ward](https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/5e7a8234-f805-43ac-820f-03d7c360b588/resource/d96d198c-fb5b-4229-a586-7673c45e80e7/download/44-ward-model-may-2010-wgs84-latitude-longitude.zip) and [25-ward](https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/5e7a8234-f805-43ac-820f-03d7c360b588/resource/35f67d86-cfc8-4483-8d77-50d035b010d9/download/25-ward-model-december-2018-wgs84-latitude-longitude.zip) geometries. An objective spatial crosswalk is therefore feasible.

A projected-area intersection of those two official files illustrates why ward number or candidate identity is insufficient. Ignoring boundary slivers below 0.01%, new Ward 11's polygon area comes from old Wards 27 (45.60%), 20 (31.65%), 19 (17.96%), 29 (4.51%) and 22 (0.27%). Only 34.82% of old Ward 19's area lies in new Ward 11. Thus Layton's 2010 and 2014 Ward 19 wins are genuinely overlapping-geography history, but they are not previous wins in the current Ward 11 electorate. These are geometric-area shares computed after projecting both City files to EPSG:2952; they are not population or elector weights.

That crosswalk would not, by itself, make a 2014 vote share a 2018-ward vote share. Area overlap is not voter overlap, and support can differ sharply within an old ward. Before 2018 is used alongside ordinary elections, the data contract would have to freeze:

- the source and target boundary eras and a population- or elector-weighted overlap rule computed without using the 2018 outcome;
- whether `prior_share` remains the share in the source contest or is re-aggregated from archived poll-level votes into the target geography;
- a separate `sitting_at_cutoff` and `continuous_service` fact, because two sitting councillors can share the same target ward;
- a boundary-shock flag and a validation report that shows 2018 separately; and
- a ward choice-set identifier, because the two experienced candidates' outcomes are mutually exclusive rather than independent Bernoulli observations.

Those conditions permit 2018 to inform a history-based analysis without relabelling its 13 losing sitting councillors as 13 ordinary incumbent defeats. They do not determine whether the cycle should be used for estimation, held out as a stress test, or kept descriptive.

### Earlier elections

The City's current online election-results product begins in 2003, so 2003 is the defensible start for the presently sourced dataset ([Election Results](https://www.toronto.ca/city-government/elections/election-results-reports/election-results/)). The Province established the 44-ward structure for the 2000 election in [O. Reg. 191/00](https://www.ontario.ca/laws/regulation/r00191), then changed Wards 27 and 28 for 2003 in [O. Reg. 438/02](https://www.ontario.ca/laws/regulation/r02438).

The 2000-to-2003 transition might eventually contribute up to 42 geographically stable wards, but only after official 2000 results, the certified 2003 field, term vacancies, and the two changed wards are acquired and audited. It should not be populated from secondary election summaries merely to enlarge the sample. The 1997-to-2000 election is another boundary transition: Council went from 56 members to 44, according to the City's [2000-2003 term archive](https://www.toronto.ca/legdocs/term2000-2003/cc-mtgs.htm).

## What can be reconstructed without hindsight

The historical cutoff should mirror the intended current publication cutoff: the Final Ballot after nominations close and the Clerk certifies nominations. For 2026, nominations close at 2 p.m. on August 21 and certification is due August 24 ([Key Election Dates](https://www.toronto.ca/city-government/elections/key-dates/)).

| Candidate or race fact | Reconstructible at the cutoff? | Required source and caveat |
|---|---|---|
| Final Ballot and candidate count | **Yes**, if archived | Use the certified-candidate list, not result-row count. The 2022 Lai discrepancy proves the distinction. |
| Sitting councillor, ward and same-ward status | **Yes** | Join service spells from the Council roster, by-elections and appointment decisions to the certified field. Do not substitute “previous general-election winner.” |
| Prior vote share and margin | **Yes, conditionally** | Use the most recent official election in a comparable ward. Preserve `missing_due_to_acclamation`; do not turn it into a measured 100% share. Tag whether the prior contest was a general election or by-election. |
| Returning prior runner-up | **Yes, conditionally** | Join the prior official result to the Final Ballot through a reviewed person-identity table. Raw name equality is inadequate. |
| Candidate's Toronto Council win count, last win and last share | **Yes for post-2003 careers; otherwise left-censored** | Define whether the count includes general elections, by-elections, exact-current-ward wins, overlapping wards, or all Toronto council wards. The City's online result series starts in 2003, so a raw count understates longer careers. An appointment is service but not a win. Prior share is missing after an acclamation and requires a boundary-era tag. |
| Former same-ward officeholder | **Yes** | Join complete service spells and boundary eras to the Final Ballot. Keep this distinct from sitting incumbency, a returning runner-up, a sitting councillor moving wards, and a family relationship. Record service end, time since service, and whether the earlier ward is exact or merely overlapping. |
| Tenure or first-term status | **Yes, after more data work** | Reconstruct service start/end and entry route. The current code labels every 2003 winner as first-term in 2006 because no earlier result exists in its input; that is missing history, not evidence of first-term status. |
| Entry route | **Yes** | General election, by-election and appointment are objective, dated events in Clerk declarations and Council decisions. |
| Moved ward / boundary shock | **Yes** | Requires a ward-boundary era table and a candidate service/appearance join. Keep it distinct from same-ward incumbency. |
| Previous-cycle campaign finance | **Potentially** | Prior filed statements existed before the next election and could be archived. Current-cycle totals are not available at forecast time: 2026 initial statements are not due until March 30, 2027 ([Key Election Dates](https://www.toronto.ca/city-government/elections/key-dates/)). |
| Demographic context | **Potentially** | Use only census products released before each historical cutoff and map the contemporary vintage to the historical ward. Later census releases or today's rebased boundaries leak information. |
| Timestamped ward polling | **Only where archived** | The poll, questionnaire, field dates and released values must all have existed by the cutoff. An unpolled candidate is unmeasured, not zero. The current official-result dataset supplies no such history. |
| Same-election ward turnout, mayoral ward result or final spending | **No** | These are election-day or post-election outcomes. Treating them as known predictors is direct hindsight leakage. |
| Editorial race assessment | **No, not as a model input** | A retrospective label is neither objective nor reproducible at the cutoff. It belongs in the separately managed Editorial Layer. |

Every reconstructed field should carry `source_url`, `source_published_at` or an archived retrieval date, `known_at_cutoff`, and an explicit missingness reason. That allows a backtest to distinguish “false,” “not applicable,” “not found,” and “not yet known.”

## Candidate officeholding history and the Ward 11 live case

A binary incumbent flag collapses several objectively different histories. A candidate-history record can expose those facts without pretending they have one common effect:

- `sitting_at_cutoff` and `continuous_service_through_cutoff`;
- Toronto Council election wins, separately counting general and by-election wins;
- exact-current-ward wins and wins in geographically overlapping predecessor wards;
- last service end, last win date, years since each, and the entry/exit route;
- the vote share and margin in each prior contest, with acclamation missingness preserved; and
- source-to-target ward overlap under a frozen boundary crosswalk.

The count's noun matters. “Three Toronto Council wins,” “one win on the exact current Ward 11 boundaries,” and “two wins in a predecessor ward that partly overlaps Ward 11” are different facts. So are winning a by-election and entering by appointment. A single `wins` integer would conceal those choices and would be left-censored for politicians first elected before the City's online result series begins in 2003.

### As-of-time reconstruction on 2026-08-17

The reported Mike Layton return is a useful prospective data-contract test, not historical validation. The observations available on the research date were:

| Observation | Primary-source status at the observation time | Defensible coding |
|---|---|---|
| A report supplied for this audit says Layton announced on August 17 that he would run in Ward 11. | No candidate-controlled announcement or nomination record was located in this primary-source pass. | `publicly_reported_intent = true`; do not yet create a certified candidate appearance. |
| The City's live [2026 councillor-candidate JSON](https://www.toronto.ca/data/elections/candidate_list/councilorCandidates_2026.json), retrieved on August 17, listed ten active Ward 11 candidates, including Dianne Saxe, and did not list Mike Layton. The response carried `seq=1786969380743`. | Official but provisional registration feed. Absence can reflect filing or publication timing and is not a Final Ballot decision. | `registration_observed = false` for that snapshot, with the URL, retrieval date and sequence retained. |
| Nominations close August 21 and the Clerk's certification deadline is August 24. | Official [Key Election Dates](https://www.toronto.ca/city-government/elections/key-dates/). | `final_ballot_status = pending`; no forecast-cutoff record exists yet. |
| Layton held Ward 11 in the 2018–2022 term; Saxe holds Ward 11 in the 2022–2026 term. | Official [Council service roster](https://www.toronto.ca/explore-enjoy/history-art-culture/mayors-councillors-reeves-chairmen/city-of-toronto-councillors/) and current [Ward 11 member page](https://www.toronto.ca/city-government/council/members-of-council/councillor-ward-11/). | Saxe is `sitting_at_cutoff`; if Layton is certified, he is a `former_same_exact_ward_officeholder`, not an incumbent. |
| Layton won Ward 11 in 2018 with 22,370 votes and 69.565%. Saxe won the open 2022 contest with 8,614 votes to Norm Di Pasquale's 8,491: 123 votes and 0.505 percentage points. | Repository extract [`historical_council_results.csv`](../../data/raw/elections/historical_council_results.csv), sourced from the City's official [2018](https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/96d35404-44d9-49d8-95bb-fb1e5489240d/resource/2fcd5f20-90f5-4dd0-88eb-22e978b9bf89/download/2018-results.zip) and [2022](https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/96d35404-44d9-49d8-95bb-fb1e5489240d/resource/3ad371de-7c51-45d3-9ea4-0b4efac5fc2b/download/2022-results.zip) archives. | Preserve the raw prior contests. They are descriptive historical evidence, not automatically current support. |

On a Toronto-Council-only definition, the available official results give Saxe one council win, in 2022, and Layton three, in 2010, 2014 and 2018. Their last-win recencies at the 2026 election are four and eight years. On an **exact current-boundary** definition, each has one Ward 11 win. Thus both can share the same candidate-history schema while retaining materially different values and service states.

`Former same-ward officeholder` is also conceptually independent of a Local Family Officeholding Relationship. Layton's own prior Ward 11 service is candidate-specific electoral evidence; his documented relationship to Jack Layton is a separate family fact with different sourcing and selection problems. Neither should be used as a proxy for the other.

If Layton is ultimately certified, the final-cutoff feature row should be frozen before the election and retained whatever the result. The 2026 outcome can later be a genuinely prospective test. It must not be fed back into the historical feature definition, counted as validation now, or used to tune gates during this cycle.

## Local Family Officeholding Relationship

The project's defined term is a **Local Family Officeholding Relationship**: a documented parent, child, sibling or spouse who held elected office in Toronto or an overlapping electoral geography ([`CONTEXT.md`](../../CONTEXT.md)). The official election files can identify candidates and outcomes, but they contain no relationship field. Positive instances can be researched; a complete binary variable cannot be inferred directly from the election data.

### What a defensible record would contain

A candidate-level relationship table should record, at minimum:

- `candidate_person_id` and `relative_person_id`;
- relation type, restricted in advance to parent, child, sibling or spouse;
- the relative's office, geography, service dates, and whether that service began before the forecast cutoff;
- a primary source for the relationship and a primary source for the officeholding;
- when each source was published or first archived; and
- a status of `confirmed`, `unknown`, or `reviewed_no_qualifying_relationship`.

`Not found` is not automatically a negative. An exhaustive negative would require the same search protocol for every candidate, independent review, and a recorded stopping rule. Surname matching is particularly indefensible: it misses spouses and name changes, falsely joins unrelated people, and does not establish that a same-named relative held office.

The office definition also needs to be frozen before coding. “Elected office in Toronto or an overlapping electoral geography” must say whether it includes school-board trustees, former municipalities, offices elsewhere in the GTA, city-wide offices, and federal or provincial districts that only partly overlap a ward. Expanding or narrowing these choices after seeing outcomes is researcher discretion, not a stable feature.

### Primary-source lower bound in the audited incumbent population

A non-exhaustive primary-source pass confirms at least **nine people and 14 of the 126 incumbent attempts** under the current parent/child/sibling/spouse definition. All 14 attempts were wins. This is a lower bound on positive cases, not a measured prevalence and not evidence of a predictive effect.

| Incumbent | Counted target election(s) | Relationship and prior officeholding evidence | Outcomes |
|---|---|---|---:|
| Rob Ford | 2006 | Ontario's Premier described him as the son of former MPP Doug Ford Sr. ([Ontario statement](https://news.ontario.ca/en/statement/36241/premiers-statement-on-the-death-of-rob-ford)) | 1 win |
| Maria Augimeri | 2006, 2010, 2014 | Sitting MPP Odoardo Di Santo called Augimeri his wife in 1982 ([Ontario Hansard](https://www.ola.org/en/legislative-business/house-documents/parliament-32/session-2/1982-11-09/hansard-1)); his official [member record](https://www.ola.org/en/members/all/odoardo-di-santo) records the office. | 3 wins |
| Adam Vaughan | 2010 | Ontario Hansard identifies Adam as the son of Colin Vaughan and describes Colin as a former Toronto councillor ([Ontario Hansard](https://www.ola.org/en/legislative-business/house-documents/parliament-41/session-2/2016-10-04/hansard)). | 1 win |
| Frances Nunziata | 2006, 2010, 2014, 2022 | Ontario Hansard identifies former York South-Weston MPP John Nunziata as her brother ([Ontario Hansard](https://www.ola.org/sites/default/files/node-files/hansard/document/pdf/2013/2013-04/house-document-hansard-transcript-2-EN-17-APR-2013_L026.pdf)); the House of Commons also records his [federal service](https://www.ourcommons.ca/Members/en/john-nunziata%281121%29). | 4 wins |
| Josh Colle | 2014 | Mike Colle referred to his son Josh while serving in the Legislature ([Ontario Hansard](https://www.ola.org/en/legislative-business/house-documents/parliament-37/session-1/1999-12-02/hansard)); the official Toronto service roster records Josh's council service. | 1 win |
| Mike Layton | 2014 | York University records that Jack Layton's son Mike followed him to Toronto Council ([York University](https://www.yorku.ca/research/2011/08/23/jack-layton-made-his-political-entree-at-york-2/)); the City roster records both service histories. | 1 win |
| Michelle Berardinetti | 2014 | MPP Lorenzo Berardinetti introduced his wife Michelle as Ward 35's councillor-elect in 2010 ([Ontario Hansard](https://www.ola.org/en/legislative-business/house-documents/parliament-39/session-2/2010-10-28/hansard)). | 1 win |
| Stephen Holyday | 2022 | Ontario Hansard identifies Councillor Stephen Holyday as former councillor and MPP Doug Holyday's son ([Ontario Hansard](https://www.ola.org/en/legislative-business/house-documents/parliament-42/session-1/2018-08-02/hansard)). | 1 win |
| Mike Colle | 2022 | The same father-son relationship applies in reverse; Josh Colle had already served on Toronto Council, as recorded in the City service roster. | 1 win |
| **Total** |  |  | **14 wins, 0 losses** |

The source-timing distinction matters. Ten of those 14 attempts have a relationship source found in this pass that predates the target election. The four exceptions are Rob Ford in 2006, Adam Vaughan in 2010, and Frances Nunziata in 2006 and 2010: the cited primary sources confirm immutable relationships later, but do not prove that the same evidence was captured by the historical cutoff. Those four should remain `unknown_at_cutoff` until contemporaneous documentation is archived if the hypothesized signal is public political-family recognition rather than kinship itself.

There are also plausible additional cases that should not be promoted to `confirmed` from an inference. For example, 1987 Ontario Hansard records that former North York councillor Esther Shiner had a son named David ([Ontario Hansard](https://www.ola.org/en/legislative-business/house-documents/parliament-34/session-1/1987-12-21/hansard)), and the City records councillor David Shiner, but this pass did not find a primary source explicitly linking that son to the candidate. Adding his three wins would raise the lower bound to 17 attempts without changing the zero-loss result, which demonstrates how source and identity rules change the count.

### Selection, leakage and interpretation risks

- **Outcome-dependent documentation:** winners and long-serving politicians receive richer official biographies and tributes. Coding well-documented people as `true` and everyone else as `false` builds political prominence and survival into the feature.
- **Future-office leakage:** the relative must have held the qualifying office before the candidate's historical cutoff. A relative elected later cannot retroactively make an earlier attempt a family-officeholding case.
- **Public salience is not the relationship fact:** a later obituary can confirm an immutable relationship, but cannot prove voters knew or cared about it at an earlier election. If “name recognition” is the proposed mechanism, timestamped contemporaneous evidence is necessary.
- **Definition sensitivity:** parent/child/sibling/spouse, office level, geographic overlap, living versus deceased relatives, and former versus sitting officeholders all change the coded population.
- **Confounding and double counting:** a family relationship can coincide with the candidate's own prior office, incumbency, succession into an open seat, shared surname, fundraising, or media attention. A relationship coefficient would not be a causal dynasty effect.
- **Sparse outcome support:** even the 14-case lower bound has no losses. It cannot by itself show whether the fact separates incumbent defeats, and it is dominated by repeated wins from a few people.

Accordingly, Local Family Officeholding Relationship is **objectively confirmable for positive cases but not yet fit-ready as a complete historical predictor**. It should enter candidate data as sourced evidence with unknowns, then face the same pre-declared out-of-cycle validation as any other proposed predictive feature. It must not be backfilled from winner biographies and presented as a clean binary covariate.

## Data work required before recalibration

The historical population should be materialized from auditable intermediate tables rather than inferred directly from adjacent general-election rows:

1. `people`: stable person IDs, canonical names, and sourced aliases.
2. `council_service_spells`: ward, start/end dates, and entry route (`general_election`, `by_election`, `appointment`).
3. `certified_candidate_appearances`: election, office, ward, certification status, and source snapshot.
4. `ward_boundary_eras`: geographic comparability and explicit transition labels.
5. `election_results`: counted outcome, including `acclaimed`, `void`, `candidate_died`, and other missingness reasons.
6. `incumbent_attempts`: the deterministic join that yields `same_ward`, `moved_ward`, `boundary_shock`, `valid_outcome`, and the win/loss response.
7. `candidate_officeholding_histories`: dated wins, service spells, entry/exit routes, sitting status, recency and prior-result facts, without reducing them to one incumbent flag.
8. `ward_boundary_overlaps`: source and target era, exact/overlapping status, frozen overlap measure, geometry sources and computation version.
9. `family_officeholding_relationships`: evidence-backed positive/unknown/reviewed records with historical source timing.

The resulting 126-case audit should be treated as provisional until those entity and service tables reproduce it. That implementation should also emit a ward-level reconciliation report for every target election so no row can disappear silently because a predictor, alias, or result is missing.

## Implications for the prior and baseline, without choosing a model

- The observed same-ward Toronto retention base rate is 118/126, not 113/121.
- The evidence contains only eight defeats and four target-election cycles; correcting missing wins does not solve that scarcity.
- Attempts are clustered within 63 councillors and within election cycles, so 126 is not the effective number of independent observations.
- Open/no-same-ward contests, same-ward incumbents, moved-ward councillors, boundary-shock contests, and censored contests are distinct historical states.
- A former same-ward officeholder can share a candidate-history schema with a sitting incumbent, but `sitting_at_cutoff`, service continuity, win scope, recency and boundary continuity remain separate facts.
- The 2018 cycle supplies 34 sitting-councillor candidate observations and 11 incumbent-versus-incumbent wards, but it is a boundary and nomination-regime shock; it cannot silently supply 13 ordinary incumbent losses.
- Acclamations belong in an unconditional retention count even when vote-share predictors are unavailable.
- A baseline comparison must be derived inside each historical training fold. Using the full-sample 93.65% rate to judge held-out elections would leak their outcomes.
- Any proposed variable, including family officeholding, must first be shown reconstructible at the historical cutoff. A plausible story or a retrospective list of famous cases is not enough.

These findings constrain what can be learned from the data; they do not determine which modelling family, if any, should be published.
