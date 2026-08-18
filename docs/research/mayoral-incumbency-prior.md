# Historical population for a Toronto mayoral incumbency prior

**Research date:** 2026-08-17

**Question:** What historical election population could support a distinct Mayoral Incumbency Prior for Toronto's 2026 Mayoral Forecast?

**Scope:** Evidence and data-design audit only. This note does not choose a prior, a pooling rule, a feature, or a Publication Gate.

## Executive findings

1. **Toronto alone cannot estimate an incumbent-defeat rate with useful empirical resolution.** Since amalgamation, the incumbent mayor appeared on the Final Ballot in four regular elections: Mel Lastman in 2000, David Miller in 2006, and John Tory in 2018 and 2022. All four won. The City's current candidate-level archive begins in 2003, but an archived copy of the City's own 2000 final-results page preserves all 26 mayoral candidates after all 1,992 polls reported, including Lastman's 483,277 votes ([archived City result](https://web.archive.org/web/20010214042440id_/http://www.city.toronto.on.ca/vote2000/live_final/000.htm)). The City's office chronology and election archive establish the office and archive boundaries ([City mayor chronology](https://www.toronto.ca/explore-enjoy/history-art-culture/mayors-councillors-reeves-chairmen/mayor-reeve-chairman/), [Toronto general-election archive](https://www.toronto.ca/city-government/elections/election-results-reports/election-results/general-election-results/)).

2. **Pre-amalgamation Toronto is not simply more observations of the same office.** The current City came into being on January 1, 1998; the former City of Toronto, Metropolitan Toronto and five other municipalities ceased to be the same governing units. Their mayors and the Metro chair governed different electorates and allocations of responsibility ([City Archives guide to former municipalities](https://www.toronto.ca/city-government/accountability-operations-customer-service/access-city-information-or-records/city-of-toronto-archives/whats-in-the-archives/research-by-topic/resources-on-former-municipalities/)). Those elections may be research material, but treating them as direct Toronto mayoral trials would silently cross an office and geography break.

3. **A narrow, same-province expansion is reconstructed but remains small.** The frozen audit of regular elections from 2006 through 2022 in Toronto, Ottawa, Hamilton, Mississauga and Brampton contains 19 incumbent attempts: 13 wins and 6 losses, contributed by only 12 people in five cities. Eighteen attempts have official result artifacts. Hamilton 2006 is admitted as `corroborated_secondary`: the incumbent defeat is independently verified, the exact City endpoint and two official ward reports survive, and a contemporaneous City-derived transcription supports the exact top-two result, but the complete certified City payload is missing. A continuous-share sensitivity must omit that trial rather than treating the evidence grade as invisible.

4. **No historical trial matches the current Toronto powers-and-accession combination.** Ontario's strong-mayor provisions took effect for Toronto on November 23, 2022. No Toronto or Ontario incumbent completed a full term under that regime and then faced a regular election before 2026. Olivia Chow also entered office through the 2023 by-election rather than the preceding regular election ([Ontario proclamation](https://www.ontario.ca/document/ontario-gazette-volume-155-issue-50-december-10-2022/proclamation), [Ontario strong-mayor backgrounder](https://news.ontario.ca/en/backgrounder/1003166/strong_mayor_powers_expanded_to_mayors_in_26_municipalities), [Toronto 2023 supplementary election report](https://www.toronto.ca/wp-content/uploads/2023/12/8bb4-Final-for-web-2023-Mayor-ByElection-Report.pdf)).

5. **Other Canadian cities offer more records, not automatically more comparability.** Winnipeg, Edmonton, Vancouver, Montreal and Calgary have substantial official result archives. They also introduce different provincial statutes, party-labelled municipal ballots in some cities, historical term-length changes, different mayoral powers, and new regime breaks such as Alberta's 2025 local-party pilot. Pooling them would be a substantive extrapolation choice, not a consequence forced by the data.

6. **The convenient Ontario-wide dataset is outcome-truncated.** Ontario publishes municipal data and “Successful Candidate Data” for 2014, 2018 and 2022. It contains winners, their votes and some incumbency fields, but not every losing candidate. It therefore cannot identify defeated incumbent attempts by itself ([Ontario municipal-election dataset](https://data.ontario.ca/en/dataset/municipal-election-results), [2022 successful-candidate resource and dictionary](https://data.ontario.ca/en/dataset/municipal-election-results/resource/7f408f5e-71c7-43fa-82bf-5eb8be77b9a7)).

7. **The 2023 John Tory–Ana Bailão episode is a timestampable association, not an identified endorsement effect.** In Forum Research's same-firm weekly series, Bailão moved from 13% on June 16 to 20% on June 23 among decided/leaning respondents after Tory's June 21 endorsement. Liaison's all-voter readings moved from 11% before the event to 15% and then 20% in two post-event polls. These were independent cross-sections during the final campaign week, with other endorsements, strategic consolidation and turnout selection occurring at the same time. They cannot assign any of the movement, or any part of the final result, causally to Tory.

## 1. Define the event before collecting it

The historical event should be specified independently of any observed outcome. A reproducible candidate definition is:

> A person who legally held the elected office of mayor immediately before a regular general election and whose name appeared as a candidate for that same office on the certified Final Ballot.

This definition estimates an outcome **conditional on seeking re-election and reaching the Final Ballot**. It does not estimate unconditional office retention. That distinction matters because retirement, withdrawal, death, appointment and removal occur before the conditional event.

The following cases require separate codes rather than retrospective judgment:

- **Open election:** the officeholder did not appear on the Final Ballot.
- **Withdrawal:** an initially nominated incumbent withdrew before certification. Rob Ford in Toronto in 2014 is not a completed incumbent mayoral trial.
- **Former mayor:** a previous officeholder seeking a return is a challenger, not the incumbent. Fred Eisenberger in Hamilton in 2014 is an example.
- **Acting or appointed mayor:** code accession route and legal status; do not infer equivalence to an elected incumbent.
- **First election for a new or amalgamated office:** no incumbent trial even if a candidate led a predecessor municipality. Mel Lastman in 1997 was mayor of North York but not incumbent mayor of the new amalgamated City of Toronto.
- **By-election:** retain as a different election type. Its calendar, electorate and turnout process can differ from a regular general election.
- **Acclamation:** retain explicitly but do not manufacture a vote share or winning margin.

At minimum, the outcome record needs the full candidate field, votes, valid-vote denominator, winner, winning margin, election type, certified ballot, and official source. The officeholder record needs the source-backed incumbent flag, accession mode, term start, whether the person is a former rather than current mayor, and any office-continuity break.

## 2. Toronto's post-amalgamation population

Toronto's current result page covers general elections from 2003 through 2022 and provides official declarations plus poll-by-poll data for each candidate. The City also retains older municipal government records through the Archives, but those records are not exposed as one comparable online candidate table ([general-election archive](https://www.toronto.ca/city-government/elections/election-results-reports/election-results/general-election-results/), [City Archives government-record holdings](https://www.toronto.ca/city-government/accountability-operations-customer-service/access-city-information-or-records/city-of-toronto-archives/whats-in-the-archives/government-records/)).

| Election | Officeholder before election | Final Ballot status | Historical classification | Official-result status |
|---|---|---|---|---|
| 1997 | None for the newly amalgamated office | Mel Lastman won | First election; not an incumbent trial | The inaugural Council minutes certify Lastman as the new City's first mayor ([minutes](https://www.toronto.ca/legdocs/minutes/council/cc980102.htm)) |
| 2000 | Mel Lastman | Ran and won | Incumbent win | An archived City final-results page reports all 1,992 polls and all 26 candidate totals; Lastman received 483,277 votes ([archived City result](https://web.archive.org/web/20010214042440id_/http://www.city.toronto.on.ca/vote2000/live_final/000.htm)). The local audit copy is 4,694 bytes with SHA-256 `513988ddce0949b081f69fd2abf9d35060e156b3136112da111c00a0dda4070b`. |
| 2003 | Mel Lastman | Did not run | Open election | Online official archive available |
| 2006 | David Miller | Ran and won | Incumbent win | [Clerk's official declaration](https://www.toronto.ca/wp-content/uploads/2017/08/8f72-election-2006-clerksofficialdeclaration.pdf) |
| 2010 | David Miller | Did not run | Open election | [Clerk's official declaration](https://www.toronto.ca/wp-content/uploads/2017/08/9783-election-2010-clerksofficialdeclaration.pdf) |
| 2014 | Rob Ford | Withdrew from the mayoral contest before the Final Ballot | Open election for this estimand | [Clerk's official declaration](https://www.toronto.ca/wp-content/uploads/2017/08/9059-election-2014-clerksofficialdeclarationofresults.pdf) lists Doug Ford, not Rob Ford, in the mayoral result |
| 2018 | John Tory | Ran and won | Incumbent win | [Clerk's official declaration](https://www.toronto.ca/wp-content/uploads/2018/10/97da-2018clerksofficialdeclarationofresults.pdf) |
| 2022 | John Tory | Ran and won | Incumbent win | [Clerk's official declaration](https://www.toronto.ca/wp-content/uploads/2022/10/9085-FinalDeclaration-of-Results-for-the-2022-Toronto-Municipal-Election.pdf) |
| 2023 | Office vacant after Tory resigned | By-election Final Ballot | Open by-election; not an incumbent trial | [Clerk's official declaration](https://www.toronto.ca/wp-content/uploads/2023/06/900e-Declaration-of-Results-for-the-2023-Toronto-By-Election-for-Mayor.pdf) |

The resulting Toronto-only count is **4 attempts, 4 wins, 0 losses**. All four now have source-backed candidate-level results, although 2000 is an archived City final-results page rather than the Clerk's declaration used for later cycles. An all-success sample of four does not reveal the frequency or shape of rare incumbent defeats; any non-zero tail would necessarily come from assumptions, partial pooling, or other populations.

The repeated-person structure further reduces information: John Tory supplies two of the four observations. Election records are not independent coin flips, because the same person, city, institutions and electorate persist across cycles.

## 3. Ontario populations that could be audited

### 3.1 Shared law does not mean identical offices

Ontario municipalities administer elections under the *Municipal Elections Act, 1996*. Toronto's head of council is elected by general vote under the *City of Toronto Act, 2006* ([Municipal Elections Act](https://www.ontario.ca/laws/statute/96m32), [City of Toronto Act](https://www.ontario.ca/laws/statute/06c11)). Toronto describes its mayor and councillors as independent rather than elected representatives of political parties ([City explanation of local government](https://www.toronto.ca/city-government/council/my-local-government-its-for-me/about-your-local-government/)). This gives Ontario elections a useful common legal baseline.

There are still material differences:

- Toronto, Ottawa and Hamilton are large single-tier municipalities; Mississauga and Brampton have historically operated as lower-tier municipalities within Peel. Service responsibilities and the political meaning of the mayoralty differ ([Ontario municipal organization guide](https://www.ontario.ca/document/ontario-municipal-councillors-guide/5-municipal-organization), [Ontario list of municipalities](https://www.ontario.ca/page/list-ontario-municipalities)).
- Ontario shifted from three-year to four-year regular municipal terms for the 2006 election cycle. A longer window crosses that calendar break ([historical Municipal Elections Act version](https://www.ontario.ca/laws/statute/96m32/v2), [2026 Ontario voters' guide](https://www.ontario.ca/document/2026-voters-guide-ontario-municipal-council-and-school-board-elections)).
- Strong-mayor powers are a recent and staggered intervention, first applying to Toronto and Ottawa in late 2022 and later to additional municipalities ([Strong Mayors, Building Homes Act](https://www.ontario.ca/laws/statute/s22018), [Ontario strong-mayor guide](https://www.ontario.ca/document/ontario-municipal-councillors-guide/10-strong-mayor-powers-and-duties)).

Statistics Canada's fixed 2021 Census ranking offers an outcome-independent way to define a present-day large-city screen: Toronto (2,794,356), Ottawa (1,017,449), Mississauga (717,961), Brampton (656,480) and Hamilton (569,353) are Ontario's municipalities in the national top 25 ([Statistics Canada, “Canada's large urban centres continue to grow and spread”](https://www12.statcan.gc.ca/census-recensement/2021/as-sa/98-200-x/2021001/98-200-x2021001-eng.pdf)). Population similarity is only a screening variable; it does not erase office differences. This screen also answers “cities that are large now,” not “cities that were large at each election”; the latter would require a pre-declared contemporaneous-census rule.

### 3.2 Frozen five-city event population, 2006–2022

The following audit uses an outcome-blind window: regular four-year Ontario elections from 2006 through 2022, and the five Ontario municipalities in Statistics Canada's national top 25. It is presented to measure scarcity, not to select the training population.

| City | Incumbent attempts | Wins–losses | Distinct incumbent people | Current official accessibility |
|---|---:|---:|---:|---|
| Toronto | 3 | 3–0 | 2 | Full candidate-level declarations online for the window |
| Ottawa | 4 | 2–2 | 3 | All four trials have durable official result artifacts. Archived City pages cover 2006 and 2010; for 2014 and 2018 the retained City open-data workbooks independently match the archived official XML result feeds. |
| Hamilton | 3 | 1–2 | 2 | The 2010 and 2018 trials have durable City result artifacts. Hamilton 2006 is retained as a documented `corroborated_secondary` exception: the City endpoint is identified, two official ward reports survive, and the exact result is strongly corroborated, but the complete City payload is missing. ([Hamilton recovery and proportionality audit](hamilton-2006-official-mayoral-result.md)) |
| Mississauga | 4 | 4–0 | 2 | Certified full results online from 1997 through 2024 ([Mississauga official results archive](https://www.mississauga.ca/publication/official-election-results/)) |
| Brampton | 5 | 3–2 | 3 | Official result files online from 2006 through 2022 ([Brampton election archive](https://www.brampton.ca/EN/City-Hall/Election/Pages/Election-Archives.aspx)) |
| **Total** | **19** | **13–6** | **12** | Harmonized tables exist; 18 trials have official artifacts and one is admitted with a qualified secondary evidence grade |

The event list behind that count is:

- **Toronto:** Miller 2006; Tory 2018 and 2022.
- **Ottawa:** Bob Chiarelli 2006; Larry O'Brien 2010; Jim Watson 2014 and 2018.
- **Hamilton:** Larry Di Ianni 2006; Fred Eisenberger 2010 and 2018. Eisenberger's 2014 return was not an incumbent attempt.
- **Mississauga:** Hazel McCallion 2006 and 2010; Bonnie Crombie 2018 and 2022. The City's account of McCallion's tenure says she won 12 consecutive terms and did not run in 2014 ([City of Mississauga, McCallion life and legacy](https://www.mississauga.ca/hazel-mccallion-in-memory/life-and-legacy/)).
- **Brampton:** Susan Fennell 2006, 2010 and 2014; Linda Jeffrey 2018; Patrick Brown 2022. The official 2014 and 2018 files record the two incumbent defeats ([2014 results](https://www.brampton.ca/EN/City-Hall/Election/Documents/2014%20Results.pdf), [2018 results](https://www.brampton.ca/EN/City-Hall/election/Documents/2018%20Results/2018%20City%20of%20Brampton%20Municipal%20Election%20Official%20Results.pdf)).

The tracked source and trial tables are [`mayoral_incumbency_sources.csv`](../../data/raw/elections/mayoral_incumbency_sources.csv) and [`mayoral_incumbency_trials.csv`](../../data/raw/elections/mayoral_incumbency_trials.csv). [`mayoral_incumbency.py`](../../backend/model/mayoral_incumbency.py) validates the fixed city/cycle counts, derives outcomes and vote-share quantities from the candidate totals, constructs leave-one-city-out folds, and verifies each retained artifact's size, signature and SHA-256. Toronto 2000 is coded separately as a three-year-term sensitivity; it is not a twentieth v1 observation.

**Evidence-grade warning:** Hamilton 2006 is fit-eligible but remains materially different from the other 18 trials. Dropping it from the primary population would remove a known incumbent defeat because its official webpage did not survive, creating convenience-sample bias. Continuous-share and margin work must nevertheless retain a pre-declared Hamilton-omission sensitivity because the complete certified City table was not recovered.

### 3.3 Why the provincial file cannot finish the job

Ontario's 2014, 2018 and 2022 candidate resources are explicitly labelled **Successful Candidate Data**. The 2022 dictionary includes `COUNCIL_INCUMBENT` and `OFFICE_INCUMBENT`, but only for the person who obtained office. The 2014 and 2018 files similarly identify the elected person and whether that person served on the prior council ([2014 resource](https://data.ontario.ca/dataset/municipal-election-results/resource/562a2b81-b4b0-41ee-97dc-33f10c400f61), [2018 resource](https://data.ontario.ca/en/dataset/municipal-election-results/resource/80304bc4-1ab9-443e-876a-9f79dcbd2c98), [2022 resource](https://data.ontario.ca/en/dataset/municipal-election-results/resource/7f408f5e-71c7-43fa-82bf-5eb8be77b9a7)).

Consequences:

- an incumbent winner can be found;
- an incumbent loser is absent;
- “served on council” is not the same as “held this office”; and
- full vote shares and margins cannot be reconstructed without the losing candidates.

Using that file alone would mechanically select successes and induce survivorship bias.

## 4. Canadian expansion candidates

The following are data-availability findings, not a claim that the elections are exchangeable with Toronto.

| City | Official candidate-level history | Comparability issue to resolve |
|---|---|---|
| Winnipeg | General-election archive from 1966 through 2022 and an official open-data result table ([archive](https://legacy.winnipeg.ca/clerks/election_services/election-archive/default.stm), [open data](https://data.winnipeg.ca/Council-Services/Winnipeg-Election-Results/7753-3fjc)) | Manitoba law; historical term lengths and office powers. Winnipeg records four-year mayoral terms only from 1998 ([City mayor history](https://www.winnipeg.ca/people-culture/winnipegs-history/mayors-past-present)). |
| Edmonton | Election history and results from 1892 onward ([City election history](https://www.edmonton.ca/city_government/municipal_elections/election-history-and-results)) | Alberta law and term changes; the City warns that derived historical data may contain discrepancies. Alberta also introduced a local-party/slate pilot for Edmonton and Calgary in 2025. |
| Vancouver | Previous-election results and open data to 1996, with older records available through Archives ([City previous elections](https://vancouver.ca/your-government/previous-elections.aspx)) | British Columbia municipal parties and ballot affiliations are visible in official results, unlike Toronto's non-party ballot ([Vancouver 2022 official results](https://vancouver.ca/news-calendar/official-2022-vancouver-election-results.aspx)). |
| Montreal | Official documentation includes a historical 1833–2005 result volume and detailed modern election reports ([Élections Montréal documentation](https://elections.montreal.ca/en/documentation/page/10/), [general-election results](https://elections.montreal.ca/en/results-of-the-general-election/)) | Quebec law, French-language records, borough governance and authorized municipal political parties. Quebec explicitly permits authorized parties in municipalities of 5,000 or more ([Élections Québec candidate guide](https://www.electionsquebec.qc.ca/simpliquer/devenir-candidate-ou-candidat/)). |
| Calgary | Official current and historical result files, including detailed 2010, 2017 and 2021 records ([2010 results](https://elections-prd.calgary.ca/content/dam/www/election/documents/2010-election/2010-general-election-results.pdf), [2017 open data](https://data.calgary.ca/Government/Official-Results-General-Election-2017/wfy7-ea5g), [2021 results](https://elections-prd.calgary.ca/results/2021-results.html)) | Alberta moved from three- to four-year terms in 2013, and the 2025 local-party pilot permits party/slate names on Calgary and Edmonton ballots ([Calgary election-history exhibit](https://www.calgary.ca/info-requests/archives/election-exhibit.html), [Alberta local-party pilot fact sheet](https://open.alberta.ca/dataset/4c0175d9-fa08-4502-b609-5085a6377e98/resource/1ddf1810-8db3-408c-aa51-594658cf1be0/download/ma-changes-to-laea-2024-local-political-parties-slates-2024.pdf)). |

These archives make a national dataset technically possible. They do not establish a common estimand. A national population would need year-level legal coding, not one city-level “comparable” flag.

## 5. Regime variables and structural breaks

Any candidate population should preserve enough information to test or stratify at least these differences:

1. **Office continuity:** amalgamation, dissolution, boundary or service-responsibility change.
2. **Election type:** regular general election versus by-election.
3. **Accession mode:** elected in the prior regular election, elected in a by-election, appointed/acting, or otherwise succeeded.
4. **Term length and time served:** Toronto's 2000 trial was in the former three-year schedule; 2006 onward uses four years.
5. **Legal powers:** especially strong-mayor authority and its effective date.
6. **Municipal tier:** single-tier versus lower-tier within a region.
7. **Ballot structure:** party-labelled, slate-labelled or nominally non-partisan; candidate ordering; runoff versus plurality if a jurisdiction or year differs.
8. **Candidate status:** current mayor, former mayor, component-municipality mayor, councillor, or acting mayor.
9. **Election administration:** voting methods, eligibility and campaign-finance regime.
10. **Contestation:** number of candidates, acclamation, withdrawal and whether a material challenger was on the certified ballot.

For 2026 Toronto specifically, two facts have no direct completed historical match in the narrow Ontario audit: an incumbent first elected in a citywide by-election, and an incumbent who governed most of a term with strong-mayor powers.

## 6. Selection protocol that avoids choosing the answer

The defensible sequence is procedural:

1. **Freeze the estimand.** State whether the target is incumbent win/loss, incumbent vote share, winning margin, or an election-day outcome distribution conditional on Final Ballot presence.
2. **Freeze the jurisdiction screen before looking at results.** Examples of objective inputs are province, municipal tier, direct citywide plurality, population at a fixed census, and office continuity.
3. **Freeze the date window before looking at outcomes.** Every legal regime break should be declared. “All data we can easily download” is not a date rule.
4. **Collect complete candidate fields from official declarations.** A winners-only file cannot support the event definition.
5. **Write an incumbent-status audit trail.** Store the source and rationale for every positive, negative and excluded event.
6. **Retain clustering keys.** At minimum: candidate person, city, province and election cycle.
7. **Separate acquisition from evaluation.** Do not add or remove cities after seeing whether pooling produces a preferred incumbent advantage.
8. **Version and hash raw sources.** Municipal pages and files move; archive the retrieved declaration and record retrieval date.

An ingestion-ready table should include:

```text
election_id
jurisdiction_id
election_date
election_type
office_continuity_regime
term_length_years
legal_powers_regime
municipal_tier
ballot_party_regime
candidate_id
candidate_name_as_certified
votes
valid_votes_for_office
elected
incumbent_same_office
incumbent_status_source
accession_mode
term_start
former_mayor
withdrawn_before_final_ballot
official_result_url
source_retrieved_at
source_hash
```

## 7. Leakage, selection and dependence risks

- **Outcome-aware jurisdiction selection:** adding cities because they contain famous defeats or removing cities because their mayors “always win.”
- **Population-screen look-ahead:** using the 2021 ranking for elections back to 2006 privileges municipalities that survived or grew into today's peer set. That is coherent for a present-day comparator estimand, but not for an estimand defined by city size at the historical election date.
- **Convenience-sample leakage:** current web archives are complete for some cities and incomplete for others. Online-only selection can omit older defeats.
- **Winner-only truncation:** Ontario's centralized files omit losing incumbents.
- **Conditional-on-running selection:** weak incumbents may retire or withdraw. A prior conditional on Final Ballot presence answers a narrower question than office retention.
- **Repeated-person and repeated-city dependence:** McCallion, Fennell, Watson, Tory and others contribute multiple trials. Treating 19 rows as 19 independent draws overstates information.
- **Retrospective status errors:** a council incumbent is not necessarily an office incumbent; a former mayor is not the current incumbent; a pre-amalgamation mayor is not incumbent of the successor office.
- **Regime leakage:** strong-mayor powers, amalgamation, term-length changes and party labels can make earlier outcomes a different data-generating process.
- **Post-election feature leakage:** final turnout, certified campaign spending, post-cutoff polls and facts learned in post-mortems were unavailable at the historical forecast cutoff.
- **Historical-poll availability bias:** old, low-salience and uncompetitive municipal races are less likely to have recoverable polls. Conditioning feature evaluation on polling availability is not random.
- **Current-cycle tuning:** the 2026 polls, candidate identities or desired public story must not determine the historical cohort or smoothing strength.
- **Publication feedback:** Publication Gates should not be tuned after seeing whether an incumbency prior makes the 2026 race publishable.

## 8. Endorsement-event audit: John Tory and Ana Bailão, 2023

This section tests a specific historical claim because an Endorsement Event may later be considered as a candidate Predictive Feature. It is not evidence about the Mayoral Incumbency Prior itself.

### 8.1 Reconstructible chronology

| Date | Event or observation | Exact evidence |
|---|---|---|
| June 8–13 | Advance voting | Toronto reports 129,745 advance ballots. Mail voting closed June 15 and ultimately supplied another 28,143 ballots ([City supplementary report](https://www.toronto.ca/wp-content/uploads/2023/12/8bb4-Final-for-web-2023-Mayor-ByElection-Report.pdf)). |
| June 16 | Forum pre-event fieldwork | One-day IVR poll, n=1,006, reported June 18 and indexed June 19. Decided/leaning: Chow 32%, Saunders 15%, Bailão 13%, Furey 13%, Matlow 9%, Hunter 6%, Bradford 4%, other 10% ([Forum final release's full trend table](https://poll.forumresearch.com/data/cb12c41a-8453-40e6-90f1-7558d098f7e1Chow%20lead%20narrowing%20in%20final%20days%20of%20campaign_June%2024%202023.pdf), [Forum Toronto release index](https://poll.forumresearch.com/m/category/3/toronto/)). |
| June 17–18 | Liaison pre-event fieldwork | IVR poll, n=1,152, published June 20, margin of error ±2.89 points. All voters: Chow 26%, Saunders 14%, Matlow 11%, Bailão 11%, 12% undecided. Decided: Chow 30%, Saunders 16%, Matlow 13%, Bailão 12% ([Liaison release](https://press.liaisonstrategies.ca/chow-steady-as-she-goes-while-rest-of-field-has-minor-ups-downs/)). |
| June 20 | A competing elite endorsement | Premier Doug Ford said publicly that he would vote for Mark Saunders and that Saunders would be the best mayor ([record of Ford's press-conference statement](https://toronto.citynews.ca/2023/06/20/doug-ford-endorses-mark-saunders-ahead-of-toronto-byelection/)). |
| **June 21** | **John Tory endorsed Ana Bailão** | Bailão's campaign posted Tory's six-minute endorsement video on June 21. The first-party post is preserved on [X](https://twitter.com/anabailaoTO/status/1671602615480664064) and [Bailão's LinkedIn account with transcript](https://www.linkedin.com/posts/anabailaoto_thank-you-john-tory-activity-7077372957097934848-LpJn). This is the exact public event date. |
| June 21 | Another same-candidate endorsement | The Toronto Star editorial board endorsed Bailão on the same date ([Star editorial](https://www.thestar.com/opinion/editorials/2023/06/21/ana-bailo-is-the-best-choice-to-lead-toronto.html), [Bailão campaign's first-party share](https://www.linkedin.com/posts/anabailaoto_editorial-ana-bail%C3%A3o-is-the-best-choice-activity-7077241413733675008-caCn)). |
| June 22–23 | Liaison post-event fieldwork | IVR poll, n=1,086, published June 24, margin of error ±2.97 points. All voters: Chow 28%, Bailão 15%, Saunders 14%, Furey 10%, Matlow 9%, 9% undecided. The release headline reports Bailão at 17% among decided voters; its decided-voter list appears to contain a transcription error, printing 12% beside “+5” ([Liaison release](https://press.liaisonstrategies.ca/chow-leads-in-final-days-of-campaign/)). |
| June 23 | Forum post-event fieldwork | One-day IVR poll, n=1,037, margin of error ±3 points; release dated June 24 and indexed June 25. Decided/leaning: Chow 29%, Bailão 20%, Saunders 15%, Furey 11%, Matlow 8%, Hunter 5%, Bradford 3%, other 9% ([Forum release](https://poll.forumresearch.com/data/cb12c41a-8453-40e6-90f1-7558d098f7e1Chow%20lead%20narrowing%20in%20final%20days%20of%20campaign_June%2024%202023.pdf)). |
| June 24–25 | Liaison second post-event fieldwork | IVR poll, n=1,008, published June 25, margin of error ±3.08 points. All voters: Chow 30%, Bailão 20%, Saunders 14%, Furey 9%, Matlow 7%, 8% undecided. Decided: Chow 32%, Bailão 22%, Saunders 15% ([Liaison release](https://press.liaisonstrategies.ca/bailao-surging-but-chow-remains-in-lead/)). |
| June 26 | Election day | Toronto held the by-election. |
| June 28 | Official result certified | Olivia Chow 269,372; Ana Bailão 235,175; Mark Saunders 62,167. Chow's certified margin over Bailão was 34,197 votes ([Clerk's declaration](https://www.toronto.ca/wp-content/uploads/2023/06/900e-Declaration-of-Results-for-the-2023-Toronto-By-Election-for-Mayor.pdf), [City certification release](https://www.toronto.ca/news/toronto-city-clerk-certifies-by-election-for-mayor-results-and-declares-olivia-chow-as-mayor-elect/)). |

At least **157,888 of 725,333 ballots (21.8%)** were cast through mail or advance voting before Tory's public endorsement. The official report separately records 28,143 mail ballots, 129,745 advance ballots and 566,750 election-day ballots. Those three displayed mode totals sum to 724,638, which is 695 fewer than the reported overall total; that small discrepancy should be reconciled before using mode-level counts analytically. It does not alter the chronology: a material share voted before June 21.

### 8.2 What the record establishes

- The endorsement is a valid, timestamped **Endorsement Event**.
- In Forum's repeated, same-question series, Bailão's decided/leaning reading rose **7 percentage points**, from 13% on June 16 to 20% on June 23. Chow fell 3 points; Saunders was unchanged.
- Liaison's all-voter reading rose from **11%** on June 17–18 to **15%** on June 22–23 and **20%** on June 24–25. Its decided-voter readings were 12% before the event, a headline-reported 17% in the first post-event poll, and 22% in the second. The first post-event release's internal 12%/“+5” inconsistency must be preserved as a source-quality flag rather than silently corrected in ingested data.
- Bailão ultimately finished second, 34,197 votes behind Chow and far above her early-June poll readings.

These are descriptive temporal facts.

### 8.3 What cannot be inferred causally

The seven-point Forum change is **not** an estimate of Tory's causal effect because:

1. The surveys used different respondents; there is no voter-level before/after panel or measured exposure to the endorsement.
2. There is no untreated Toronto comparison experiencing the same final-week campaign without Tory's endorsement.
3. The Star endorsed Bailão the same day, and other endorsers, advertising, robocalls, news, debates and campaign contact were active.
4. Late strategic consolidation is an alternative mechanism: voters may have moved toward whichever non-Chow candidate appeared most viable, whether or not Tory persuaded them.
5. Poll sampling error, weighting, coverage, turnout error and undecided allocation remain. Forum itself describes each poll as a point-in-time snapshot rather than necessarily predictive.
6. More than one-fifth of ballots were already cast. The final result combines people who could and could not have been exposed before voting.
7. The result-minus-poll gap also contains post-poll movement and poll error. It is not an endorsement estimator.

The episode therefore cannot identify how many voters Tory moved, whether he mainly persuaded or coordinated them, whether the endorsement helped rather than merely coincided with momentum, or what a different endorser would do in 2026.

If endorsements are evaluated as a Predictive Feature, the dataset must collect **all** qualifying endorsements as of each historical forecast cutoff, including apparently ineffective and adverse events. Selecting this case because it was followed by a surge would be outcome leakage.

### 8.4 Other reconstructible or near-reconstructible cases

Three cases help show both the opportunity and the limits:

1. **David Miller → Joe Pantalone, Toronto 2010.** The outgoing mayor publicly endorsed his deputy on October 6 ([contemporaneous event report](https://toronto.citynews.ca/2010/10/06/miller-backs-pantalone/)). Ipsos fieldwork on September 24–26, published September 27, put Pantalone at 10% among all respondents and 14% among respondents absolutely certain to vote ([Ipsos pre-event release](https://www.ipsos.com/en-ca/month-go-its-shaping-be-horserace-toronto-mayor)). The same firm's October 8–10 poll, published October 13, put him at 11% and 15% respectively ([Ipsos post-event release](https://www.ipsos.com/en-ca/heading-down-back-stretch-its-horserace-toronto-mayor-edge-smitherman)). He received 95,482 votes, 11.7% of the candidate vote, in the October 25 election ([Toronto Clerk's declaration](https://www.toronto.ca/wp-content/uploads/2017/08/9783-election-2010-clerksofficialdeclaration.pdf)). This is a genuinely reconstructible same-firm sequence with only a one-point descriptive change. It is still not causal: Sarah Thomson withdrew and endorsed George Smitherman on September 28; Pantalone ally Joe Mihevc endorsed Smitherman on October 5 ([contemporaneous report](https://torontolife.com/city/anyone-but-ford-movement-gathers-steam-joe-mihevc-jumps-off-pantalones-ship-and-onto-the-deck-of-the-s-s-smitherman/)); and strategic-voting pressure intensified throughout the period.

2. **Doug Ford → Mark Saunders, Toronto 2023.** The public statement occurred June 20, inside the same Forum before/after window. Saunders was 15% in both the June 16 and June 23 Forum readings and then received 62,167 votes. This is a useful same-election comparison, but it is not a causal control: the endorsers, candidates, audiences and campaign activity differed.

3. **Hazel McCallion → Bonnie Crombie, Mississauga 2014.** This frequently cited case is only near-reconstructible because the treatment timestamp is not clean. One contemporaneous report, published October 14, says McCallion urged a crowd to vote for Crombie at an event on Friday, October 10; another, published October 13, says she announced on Sunday, October 12 that she would vote for Crombie ([Global event report](https://globalnews.ca/news/1612830/watch-hurricane-hazel-endorses-bonnie-crombie-for-mississauga-mayor/), [CHCH event report](https://www.chch.com/chch-news/mississauga-mayor-endorses-bonnie-crombie/)). Forum's last located primary pre-event release was fielded September 27 (n=557, ±4.2 points) and had the actual three-candidate field at Crombie 36%, Steve Mahoney 40%, Stephen King 9%, undecided 15% ([Forum pre-event release](https://poll.forumresearch.com/data/Mississauga%20Issues%20News%20Release%20%282014%2009%2027%29%20Forum%20Research.pdf)). Contemporaneous reports describe a Forum poll fielded October 15 (n=769, ±3.5 points) at Crombie 56%, Mahoney 31%, King 4%, undecided 9%, and published October 16–17; the original Forum release was not located in the current primary archive ([Global poll report](https://globalnews.ca/news/1620097/crombie-pulls-ahead-in-mississauga-mayor-race-after-mccallion-endorsement-poll/), [CityNews poll report](https://toronto.citynews.ca/2014/10/16/exclusive-crombie-leads-in-mississauga-after-hazels-endorsement-poll-shows/)). Mississauga's official result was Crombie 102,346 (63.49%) and Mahoney 46,224 (28.68%) ([official result](https://www.mississauga.ca/wp-content/uploads/sites/12/2021/11/15101856/2014-Municipal-Election-Official-Results.pdf)). Before use, the raw event artifact and Forum release must be recovered, and earlier McCallion appearances with Crombie must be enumerated. The observed twenty-point poll change is not itself an endorsement effect.

Candidate withdrawal plus endorsement should be a separate event class. It changes both the cue and the available choice set, so it is not comparable to an endorsement that leaves the candidate field unchanged.

## 9. Outstanding acquisition work

Before any historical population is used:

1. Continue passive recovery of the jurisdiction-wide Hamilton 2006 City payload when a free or purchasable archive lead appears. This is no longer a readiness blocker, but recovery would retire the qualified-secondary exception.
2. Reconcile office accession and legal-power effective dates at the event level before fitting an incumbency specification.
3. Keep Toronto 2000 as the pre-declared three-year-regime sensitivity and evaluate the five-city prior with leave-one-city-out folds.
4. If testing a national population, construct a year-level legal-regime table before joining results.
5. For endorsement research, retrieve Forum's original October 2014 Mississauga post-event release and the raw recordings or first-party records needed to resolve McCallion's event timing; capture a primary artifact for Miller's 2010 endorsement; and enumerate all endorsements under a fixed definition rather than collecting famous successes.

## Bottom line

The available evidence defines a ladder of increasingly broad historical populations:

- **Toronto post-amalgamation:** four incumbent trials, all wins; closest office match, insufficient failures.
- **Large Ontario cities in the common four-year era:** a fixed 19-trial population with 13 wins and 6 losses; same provincial election law, but only five cities, 12 people and substantial office differences. Eighteen trials have official artifacts; Hamilton 2006 is a transparent qualified-secondary exception with a mandatory omission sensitivity for continuous quantities.
- **Other Canadian large cities:** much richer official archives; materially weaker institutional comparability and additional regime coding.

The records can quantify the scarcity and document candidate populations. They cannot, by themselves, decide which extrapolation is appropriate or how much weight a broader population should receive.
