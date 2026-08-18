# Toronto Election Forecasting

The language of the Toronto municipal-election forecasting system. It distinguishes statistical inference from the separately authored editorial product.

## Language

**Mayoral Forecast**:
The predictive distribution of election-day outcomes in the Toronto mayoral election at an explicit Analysis Cutoff. It is neither an estimate of current support nor a published prediction of the path support will take. It does not consume predictive inputs or outputs from the Council Forecast.
_Avoid_: Election model, mayoral model

**Council Forecast**:
The predictive distribution of election-day outcomes in Toronto's ward-level council elections. It maintains one full-field distribution while allowing empirically validated interactions or pooling structures to differ between incumbent and open-seat races. Its first rebuilt version publishes race-level quantities and defers any council-wide aggregate. It does not consume mayoral polling, candidate alignments, coattail estimates, or outputs from the Mayoral Forecast.
_Avoid_: Election model, council model

**Final Ballot**:
The official set of candidates eligible to receive votes after registration, withdrawal, and certification are complete. The forecasts are intended for publication only once this set is known.
_Avoid_: Current field, target field, expected field

**Internal Outcome Distribution**:
The forecast's complete probability distribution over election-day valid-vote shares before any Publication Gates determine which summaries may be shown publicly.
_Avoid_: Published forecast, public odds

**Analysis Cutoff**:
The explicit timestamp through which evidence is eligible to inform an Internal Outcome Distribution. It is an input to a reproducible forecast artifact, not the wall-clock time at which software happens to run.
_Avoid_: Today, build time, latest

**Election Outcome Draw**:
One possible election-day result containing a valid-vote share for every named Final Ballot candidate and for each latent candidate in the Unmeasured Candidate Tail. Every predictive quantity is derived from the same set of draws.
_Avoid_: Model run, scenario

**Unmeasured Candidate Tail**:
The Final Ballot candidates who are not measured by name in a relevant Poll Reading or evidence set. It is an evidence-relative status rather than a permanent candidate class: a candidate may be measured in one reading and unmeasured in another. Every candidate remains distinct in every Election Outcome Draw; their collective support and effect on measured candidates remain part of the Internal Outcome Distribution without individual published tail odds.
_Avoid_: Zero, Other candidate

**Poll Residual**:
A poll's reported response category for support not assigned to a named candidate, such as “other,” refusal, or an unspecified preference. It is not the Unmeasured Candidate Tail. Until a residual-to-election relationship validates, it affects only response and denominator handling rather than being converted into candidate support.
_Avoid_: Other candidate, minor-candidate vote

**Current Incumbent**:
A deterministic label for a candidate whose Officeholding Spell covers the Analysis Cutoff and who is seeking the same contested office. It is derived for presentation and for defining Incumbent Defeat Probability, not curated as a separate Council model input. The label applies whether the spell began through a general election, by-election, or appointment.
_Avoid_: Former incumbent, incumbent of a sort

**Officeholding Spell**:
A sourced interval during which a person held a particular elected office, recording its geography, start and end, and Accession Route. A spell is not itself an election win.
_Avoid_: Tenure score, term count

**Officeholding Recency**:
The elapsed time between the end of an Officeholding Spell and the Analysis Cutoff, with an active spell represented as zero elapsed time. It is derived under the same rule for every candidate.
_Avoid_: Current-incumbent flag, former-incumbent tier

**Accession Route**:
The objective way an Officeholding Spell began: general election, by-election, appointment, or another explicitly sourced legal route.
_Avoid_: Incumbency quality, mandate strength

**Electoral Appearance**:
A candidate's sourced appearance in a certified election field, retaining the election type, represented geography, votes, valid-vote share, margin, outcome, and any reason a numeric result is unavailable.
_Avoid_: Career score, candidate strength

**Representation Continuity**:
The sourced relationship between a candidate's earlier represented geography and the currently contested geography, classified using a frozen boundary crosswalk rather than ward-number equality.
_Avoid_: Same ward, local roots

**Boundary-Shock Contest**:
An election whose geography has no single comparable predecessor, including a contest created by a major ward-boundary change that places multiple sitting officeholders in one new ward. Toronto's 2018 Council election is retained under this label rather than treated as an ordinary incumbent-retention cycle.
_Avoid_: Incumbent defeat cycle, normal redistricting

**Candidate Officeholding History**:
A candidate's collection of Officeholding Spells and Electoral Appearances, including prior wins, vote shares, margins, represented geographies, duration, and Officeholding Recency. Every sourced elected office is retained, but Toronto Council history is the core Council feature family; trustee, mayoral, MPP, and MP service are separately named proposed Predictive Features. Every Council candidate has a history, including an empty one. Candidates with no validated distinguishing facts receive the same deliberately broad structural starting distribution while retaining distinct Election Outcome Draw values. The component observations remain separate so competing models can learn whether active service and recency have smooth, nonlinear, or discontinuous predictive relationships rather than consume a hand-built composite or privileged incumbent flag.
_Avoid_: Incumbency score, experience tier

**Endorsement Event**:
A publicly documented and timestamped declaration of support for a candidate by an identifiable person or organization. Its existence is an observation; any electoral effect must be established separately.
_Avoid_: Endorsement boost, supporter

**Event Response**:
The uncertain candidate-specific change in support following an Endorsement Event. Subsequent Poll Readings update the estimated response, which may shrink toward no effect when the expected movement does not occur.
_Avoid_: Endorsement bonus, fixed bump

**Local Family Officeholding Relationship**:
A documented parent, stepparent, adoptive parent, child, sibling, or spouse who held elected office as a Toronto mayor, councillor, or school trustee, or as an MPP or MP for a geography overlapping Toronto. The exact office and relationship remain separate. Multiple relationships form a graph of candidate facts, not additive measures of dynasty strength.
_Avoid_: Political dynasty, legacy candidate

**Predictive Feature**:
A fact available at the historical forecast cutoff whose inclusion has improved predictions on unseen election cycles under the pre-declared evaluation protocol.
_Avoid_: Signal, editorial factor

**Held-Out Election Cycle**:
A complete historical target election reconstructed only from facts available at its Analysis Cutoff and withheld as one independent validation unit. Wards, candidates, Poll Readings, and repeated cutoffs inside the cycle do not become independent replications.
_Avoid_: Test row, validation case

**Qualification Baseline**:
A simpler forecast specification trained entirely inside each historical fold and used to decide whether added complexity earns inclusion. Applicable baselines include structural history-only, incumbent or officeholding-history, and polling-only forecasts.
_Avoid_: Current model, naive benchmark

**Mayoral Endpoint Bridge**:
The initial polling-only Qualification Baseline for the Mayoral Forecast. It translates eligible Poll Readings at their historical lead times into a joint election-day vote-share distribution using empirically reconstructed Toronto poll-to-result uncertainty, without requiring a latent day-by-day campaign path. It must itself clear frozen reliability checks against a pre-declared simple polling comparator before any Mayoral predictive quantity may publish. A dynamic specification may replace it only by qualifying on whole Held-Out Election Cycles.
_Avoid_: Polling average, current support model, trajectory model

**Poll Reading**:
The reported result of one poll, retaining its tested ballot, population, denominator, fieldwork period, and undecided or residual responses. One eligible Poll Reading updates the Internal Outcome Distribution, but does not by itself make any forecast quantity available or satisfy the Candidate Win Probability gates.
_Avoid_: Polling average, forecast

**Distinct Poll Sample**:
A separately recruited qualifying survey sample with no disclosed overlap with another counted sample. This operational definition does not claim respondent-level independence that a public release cannot verify. Multiple ballot scenarios, questions, or denominators from the same respondents remain one sample and may enter together only when their dependence is represented. A Council challenger's Candidate Win Probability requires at least two Distinct Poll Samples from at least two pollsters, with that candidate individually measured in both, before its remaining Publication Gates are evaluated.
_Avoid_: Independent sample, poll count, repeated release

**Poll Candidate Observation Status**:
The evidence state for a candidate in one Poll Reading: individually published, offered but not individually published, known not offered, or tested-ballot status unknown. These states are not interchangeable and none implies zero support.
_Avoid_: Missing candidate, other

**Irreducible Election Error**:
The non-zero election-day uncertainty remaining after the latest evidence, including turnout composition, poll-to-result error, unresolved candidate-tail support, and other unobserved variation. It prevents the Internal Outcome Distribution from collapsing onto even a late Poll Reading.
_Avoid_: Sampling error, model noise

**Polling Estimate**:
A current descriptive average of comparable direct Poll Readings from at least two pollsters. Its contest-specific comparability rules are stricter than the rules for displaying an individual Poll Reading; it is not an election forecast or a substitute for the underlying readings in either forecast.
_Avoid_: Polling forecast, win probability

**Mayoral Polling Estimate**:
A Polling Estimate of direct decided-and-leaning readings sharing one published named field, using each pollster's newest eligible sample within 21 days and weighting pollsters equally. Incompatible or insufficient evidence remains visible separately.
_Avoid_: Mayoral forecast, support projection

**Ward Polling Estimate**:
A ward-level Polling Estimate requiring the same published named field from at least two pollsters within 21 days. It uses each pollster's newest eligible reading for that field and weights pollsters equally. It may combine ordinary ward-wide adult, eligible-voter, registered-voter, or likely-voter screens and pollster-published expressed-preference toplines with different denominator labels when each excludes undecided and non-voters; it performs no project-authored renormalization or turnout correction. Named candidates may be averaged when a reading omits its Poll Residual, but the residual itself is published only when every selected reading reports one. If several fields qualify, the unique most-inclusive Final Ballot field is used; incomparable maximal fields or a fresh unreplicated expansion make the estimate unavailable. Evidence from only one pollster remains visible as dated Ward Poll Readings and is not presented as an average.
_Avoid_: Single-poll average, ward forecast

**Ward Poll Reading**:
A direct Council vote-intention result preserved as Observed Evidence when it cannot form a Ward Polling Estimate. Current-cycle readings retain their source field, denominator, date, and limitations and remain visible when stale; repeated readings from one pollster are shown chronologically rather than averaged. A source-authored hypothetical field becomes current-race evidence only if every named candidate appears on the Final Ballot.
_Avoid_: Ward estimate, ward forecast, stale poll deletion

**Open Seat**:
A Council race in which no Current Incumbent is seeking re-election. It is a factual race property, not a claim that the race is close or a substitute for a forecast quantity.
_Avoid_: Open race, competitive race

**Incumbent Defeat Probability**:
The probability that the officeholder seeking re-election does not win their contest. Publishing it necessarily reveals the incumbent's complementary win probability even when challenger Candidate Win Probabilities are unavailable. It is Not Applicable in an open-seat race.
_Avoid_: Vulnerability score, competitiveness score

**Council Evidence Tier**:
The public description of direct ward-poll evidence for a Council race: `C0 — No Qualifying Poll`, `C1 — Unreplicated Polling` from one pollster, or `C2 — Replicated Polling` with at least two Distinct Poll Samples from at least two pollsters. It is independent of Ward Polling Estimate availability: incompatible or stale C2 readings may still leave the estimate unavailable. The tier is displayed separately from forecast availability and is not a confidence rating.
_Avoid_: Confidence level, model quality

**Mayoral Evidence Tier**:
The public description of current-cycle mayoral polling evidence: `M0 — Structural Only`, `M1 — Pre-Final Polling`, `M2 — Post-Final Polling`, or `M3 — Replicated Post-Final Polling`. At the source's recorded date-time precision, a Distinct Poll Sample counts as post-Final when any part of its fieldwork interval overlaps or follows the conservative date-time when the certified Final Ballot was publicly knowable; a sample completed entirely before that boundary remains pre-Final. The Clerk's unobserved internal action time is not a model input. M2 requires at least one post-Final sample. For a challenger's Candidate Win Probability, M3 requires at least three Distinct Poll Samples across at least two pollsters, at least two post-Final, with the challenger individually measured in all three. The tier is displayed separately from forecast availability and is not a confidence rating.
_Avoid_: Confidence level, model quality

**Licensed Poll Detail**:
Non-public polling material permitted to enter a forecast only when the project has durable archival and internal audit rights, complete provenance, sufficient methodological disclosure, and a mandatory public-data-only sensitivity. Licensing does not turn crosstabs from one respondent sample into additional Distinct Poll Samples.
_Avoid_: Extra polls, raw public data

**Close-Result Probability**:
The probability that the election-day winning margin is no greater than five percentage points of valid votes. The threshold is shared by the Mayoral Forecast and Council Forecast.
_Avoid_: Competitiveness score, toss-up rating

**Candidate Win Probability**:
The probability that a named candidate wins the election, published only when its own applicable Publication Gates pass.
_Avoid_: Competitiveness score, candidate rating

**Probability Band**:
A fixed, pre-declared interval containing an exact internal forecast probability. The public grid is 0–<5%, 5–<15%, successive centred ten-point bands through 85–<95%, and 95–100%. It is the most precise form of that probability released publicly, not a claim that each band's realized frequency has been independently demonstrated from Toronto's small historical sample.
_Avoid_: Rounded probability, confidence interval

**Frequency Statement**:
A plain-language rendering of a Probability Band as an approximate number of outcomes in ten elections consistent with the model and evidence. It is not an empirical ten-election count from the validation archive.
_Avoid_: Model wins, simulation count

**Mayoral Incumbency Prior**:
The empirically estimated candidate starting distribution for an incumbent mayor's election-day share or margin. It is a proposed structural component, not a guaranteed input: it receives operational weight only if an incumbency-informed endpoint forecast qualifies against its polling-only Qualification Baseline. Otherwise the polling-only forecast remains authoritative and the incumbency-informed specification is retained as a Mandatory Sensitivity Variant. When used, the prior regularizes sparse evidence but can be overwhelmed by repeated high-quality Poll Readings; it is not a post-poll incumbent or win-probability bonus. The v1 polling likelihood and any campaign-evolution component otherwise treat candidates symmetrically conditional on their evidence, and every probability is derived from the shared Election Outcome Draws. The prior retains a Toronto-specific estimate while partially pooling the Mayoral Comparison Population, independently of the Council Officeholding-History Prior.
_Avoid_: Toronto incumbency prior, council retention rate

**Mayoral Comparison Population**:
Legal incumbent defences in regular 2006–2022 elections in Toronto, Ottawa, Hamilton, Mississauga, and Brampton, selected by Statistics Canada's fixed 2021 national top-25 population screen. The legal incumbent must appear on the Final Ballot; open elections, withdrawals, first elections for a new office, and by-election contests are excluded. Toronto's 2000 incumbent defence belongs only to the Toronto-specific stratum. This population may estimate the Mayoral Incumbency Prior but does not estimate Toronto poll-to-result, lead-time, or choice-set behaviour; those relationships are learned only from usable Toronto mayoral elections.
_Avoid_: Ontario win rate, comparable mayors

**Council Officeholding-History Prior**:
The empirically estimated starting distribution for a Council candidate derived from the common Candidate Officeholding History representation. It contains no separately curated current-incumbency input or hand-set incumbent bonus and is derived independently of the Mayoral Incumbency Prior.
_Avoid_: Council Incumbency Prior, incumbent bonus, mayoral incumbency effect

**Editorial Layer**:
Journalistic assessment and interpretation authored independently of both forecasts and managed by Matt Elliott for the Toronto Star. Editorial judgments do not enter forecast inputs or determine whether a forecast is available.
_Avoid_: Model output, forecast input

**Forecast Available**:
The publication state in which a particular forecast quantity for a particular race has passed every applicable Publication Gate and may be presented.
_Avoid_: Modelled, publishable enough

**Forecast Unavailable**:
The publication state in which a particular forecast quantity for a particular race has not passed every applicable Publication Gate, so that estimate may not be presented. It is not a zero probability.
_Avoid_: Zero, suppressed forecast

**Observed Evidence Only**:
The publication state in which measured evidence may be presented descriptively but may not be converted into a forecast estimate.
_Avoid_: Partial forecast, provisional odds

**Not Applicable**:
The state in which a forecast quantity has no defined event for the race, such as Incumbent Defeat Probability in an open-seat contest. It is neither Forecast Unavailable nor a zero probability.
_Avoid_: Unavailable, zero

**Publication Gate**:
A pre-declared, versioned numeric criterion that automatically determines whether a forecast quantity may be presented. Gates are frozen before the current publishable forecast is evaluated.
_Avoid_: Editorial call, judgment call

**Mandatory Sensitivity Variant**:
A pre-declared alternative the preferred forecast must survive, including applicable prior population or strength, low/base/high candidate-tail assumptions, leave-one-sample-out, leave-one-pollster-out, the Mayoral Forecast's regular-election-only polling fit, every pre-declared model family that clears its Qualification Baseline, and that family's simpler authoritative baseline. A variant that cannot run fails the affected Publication Gate; no arbitrary near-best score tolerance selects which qualified families count.
_Avoid_: Optional check, robustness note

**Band Stability Gate**:
A Publication Gate requiring every Mandatory Sensitivity Variant to place a forecast quantity in the same Probability Band and its two-sided 99% numerical-error interval wholly inside that band. A quantity that crosses or touches a band boundary after additional computation is Forecast Unavailable.
_Avoid_: Preferred-model band, close enough

**Operational Integrity Gate**:
A toolkit-neutral Publication Gate requiring valid inputs, complete Final Ballot mapping, normalized Election Outcome Draws, successful mandatory fits, and every applicable method-specific diagnostic. Failure invalidates the affected forecast quantity while leaving eligible observed evidence available.
_Avoid_: Best-effort forecast, warning only
