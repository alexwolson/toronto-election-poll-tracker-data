# Council reopening probe: open-seat win probability and ward-poll accuracy

**Research date:** 2026-09-23
**Status:** exploratory, closed. No decision was taken and no ADR changes; ADR 0043 (Council v1 is a descriptive race card) stands. The maintainer's instruction was "try 1 & 2 but no commitment we will use either." **Disposition (2026-09-24):** the maintainer judged nothing here worth surfacing at this stage. This note is the only artifact retained; the probe scripts, the ingested 2022 ward samples, the workflow prompt branch and the test-pin edits were all reverted.
**Scope:** the one stratum the ADR 0043 signal search never tested (open contests), and the first historical calibration set for ward-level council polling (the six Forum ward releases of September 2022).
**Reproducing:** the probes were scratch code and are not retained. Probe 1 needs only the sibling `defeatability-index` candidate-history frame (`data/out/candidate_history/candidate_history_frame.csv`) and the pre-registration below; a numpy conditional logit fit by Newton's method with L2 = 1.0 reproduces the tables. Probe 2 needs the six PDFs re-acquired from the Internet Archive captures listed under Acquisition (digests given) and run through the repo's double-read workflow with a council-table prompt.

## Why reopen

The ADR 0043 search ([council-defeat-beyond-cdi.md](council-defeat-beyond-cdi.md)) established that an incumbent-defeat probability cannot validate: 5–7 defeats across four normal cycles. It stopped there. A stratified re-read of the sibling project's leave-one-year-out candidate model (this session, throwaway probes) showed the incumbent branch flat but the open-contest branch alive: AUC for "elected" 0.63 → 0.86 with history features, on 24 open contests. That model was never packaged, and its incumbent handling was handicapped (86–94 % of 2010/2014 incumbents lack the narrow most-recent-margin feature; a three-term councillor returning in 2022 was coded as having no prior office). So the question here is narrower than ADR 0009's full forecast: **can an open-seat Candidate Win Probability beat simple baselines out of sample, and how far can a ward poll be trusted?**

## Probe 1 — open-seat win probability

### Pre-registration (fixed before running)

| Item | Choice |
|---|---|
| Unit | open general-election contests (no sitting incumbent on the ballot) with ≥ 2 candidates |
| Primary folds | 2010, 2014, 2022 — stable boundaries, ≥ 7-year observable history window |
| Sensitivity | + 2006 as a fold (3-year window); 2018 as a stress fold only |
| Features | contract-2.1 history fields (the ones the ADR 0047 hints already use), so the 2026 field is computed identically |
| B0 | uniform 1/n |
| B1 | "prior-winner rule": mass π shared equally by candidates with any prior electoral win, 1−π by the rest; π = training-fold rate at which such a candidate won when present (Laplace-smoothed); uniform when none present |
| M1 | within-contest conditional logit, three binary features (any prior win, returning councillor, any prior race), L2 = 1.0 |
| M2 | M1 + victory count, most-recent margin (+ missing flag), trustee win, MP/MPP win; L2 = 1.0 |
| Score | mean −log P(winner); tie-aware top-1; Brier; contest-clustered bootstrap 95 % CI on the log-score delta |
| Bar (ADR 0030) | a model counts only if it beats **both** baselines on the primary folds with a CI excluding zero **and** the direction holds in every held-out cycle |

No tuning on held-out folds. Identity is the canonical `person_id`; 52 of 426 candidacies have unresolved history and are treated as no history.

### Results — primary leave-one-cycle-out (24 open contests, 245 candidacies)

| model | −log P(winner) | tie-aware top-1 | Brier |
|---|---:|---:|---:|
| B0 uniform | 2.226 | 0.121 | 0.0861 |
| B1 prior-winner rule | 1.462 | 0.469 | 0.0567 |
| M1 minimal logit | 1.416 | 0.564 | 0.0589 |
| M2 extended logit | 1.310 | 0.606 | 0.0549 |

| comparison | mean log-score gain | 95 % CI | direction by cycle (2010 / 2014 / 2022) |
|---|---:|---|---|
| M1 vs B0 | +0.810 | [+0.372, +1.209] | ✓ / ✓ / ✓ |
| M1 vs B1 | +0.045 | [−0.235, +0.375] | ✗ / ✓ / ✓ |
| M2 vs B0 | +0.917 | [+0.452, +1.370] | ✓ / ✓ / ✓ |
| M2 vs B1 | +0.152 | [−0.169, +0.478] | ✗ / ✓ / ✓ |

Sensitivity (+2006, 32 contests): M2 vs B1 +0.264 [+0.013, +0.549], direction ✓ in all four cycles; M1 vs B1 +0.131 [−0.124, +0.411]. 2018 stress fold (3 contests): B1 is worse than uniform (2.65 vs 2.46) while M1/M2 hold (1.95 / 1.66); too small to weigh.

Held-out calibration of M1 on the primary folds is reasonable: predicted 0.03 → observed 0.02 (n=155); 0.10 → 0.10 (n=60); 0.34 → 0.45 (n=11); 0.60 → 0.78 (n=9); 0.80 → 0.75 (n=4). Pooled B1 π = 0.85.

Per contest, the M1 held-out winner probability and rank: the winner is ranked first in 19 of 24 and never below fourth. The misses are all contests with no prior-winner candidate (Doug Ford 2010, Fragedakis 2010, Colle 2010, Wong-Tam 2010, Carmichael Greb 2014) plus Crisanti 2022, where two prior winners split the mass.

### Verdict against the bar

- **Both models beat uniform decisively.** There is real, validated structure in open seats: a candidate with a prior electoral win takes most of the probability mass.
- **Neither model beats the pre-registered rule.** M1 vs B1 and M2 vs B1 have CIs spanning zero on the primary folds and the direction flips in 2010. M2 clears the CI only in the sensitivity scope. Under ADR 0030 the richer models are not authorised; **the validated content is the B1 rule itself**: when one or more prior winners run in an open seat, they collectively win about 85 % of the time (10 of 11 primary contests; both 2006 open seats with a returning councillor also went to them), and the seat is otherwise a near-uniform lottery among the field.
- What the rule cannot do: split mass between several prior winners (only two historical contests had ≥ 2; both went to the returning councillor), or say anything in a field with none.

### 2026 illustration (not a published quantity)

Four seats are open. Under the rule and the two logits (pooled primary fit):

| ward | prior-winner candidates | B1 | M1 | M2 |
|---|---|---:|---:|---:|
| 4 | Debbie King (1 trustee win) | 0.85 | 0.60 | 0.80 |
| 11 | Mike Layton (3 council wins) | 0.85 | 0.72 | 0.98 |
| 14 | Fragedakis (2 council wins), Saxe (1 council win, sitting in Ward 11), Ehrhardt (1 trustee win) | 0.28 each | 0.26 / 0.26 / 0.20 | 0.38 / 0.15 / 0.33 |
| 19 | Nate Erskine-Smith (4 MP wins) | 0.85 | 0.57 | 0.99 |

Ward 14 has no historical analog (three prior winners); the honest statement there is "one of these three, about 85 % combined". Every other candidate in these four fields sits at 0.01–0.10.

### Adversarial critique

- 24 contests over three cycles. The rule's 10-of-11 is a small-sample rate; the 95 % interval on π is roughly 0.6–1.0.
- Selection: prior winners choose to run in open seats they expect to win. That inflates the rule as an explanation, not as a forecast, but it does mean the rate is conditional on today's candidate-entry behaviour.
- Left-censoring: 2010 training rows had a 7-year history window; 2026 candidates carry 2003–2025. Prior-win flags are therefore more complete for 2026 than for training, a favourable asymmetry that is also a distribution shift.
- The sibling frame and its fold code were read, not re-run; features are pre-contest by construction (`all_prior_*`).
- Coefficients were fit with a fixed L2 = 1.0; no penalty search was run, by design.

## Probe 2 — ward-poll accuracy from the September 2022 Forum releases

### Acquisition

The live host (`poll.forumresearch.com`) returned HTTP 503 for every 2022 release on 2026-09-23. All six were recovered from the Internet Archive through the `id_` raw endpoint; the archive's CDX SHA-1 digest matches each retrieved file. Prepared with `scripts/ingest_prep.py`, extracted by the double-read workflow (`scripts/poll_extract.workflow.js` with a temporary council-table prompt branch, since reverted), and appended with `scripts/ingest_poll_source.py current-cycle` under `election_cycle_id = toronto-2022` for the duration of the probe. All twelve reads agreed on every value; every council table was also spot-checked against its rendered page by the orchestrating session. The PDFs were not retained after the exploration closed; the captures and digests below identify them exactly.

| ward | fieldwork | released | n | council base (decided/leaning) | archive capture | SHA-256 |
|---|---|---|---:|---:|---|---|
| 4 Parkdale–High Park | 2022-09-13 | 09-14 | 228 | 162 | 2025-02-27 | `74bb49a7ce9a…` |
| 5 York South–Weston | 2022-09-13 | 09-14 | 211 | 153 | 2025-02-27 | `73e01b0fd533…` |
| 10 Spadina–Fort York | 2022-09-14 | 09-15 | 208 | 105 | 2025-02-27 | `ec7d6072e46e…` |
| 13 Toronto Centre | 2022-09-14 | 09-15 | 217 | 90 | 2025-02-27 | `7052a1572b69…` |
| 20 Scarborough Southwest | 2022-09-15 | 09-16 | 216 | 165 | 2022-10-06 | `fd392e38eb95…` |
| 22 Scarborough–Agincourt | 2022-09-15 | 09-16 | 207 | 118 | 2022-10-06 | `43e08675fae0…` |

Each release also carries a ward-level mayoral table (all respondents, including Don't know); those are ingested as dependent readings of the same sample. Four of the six council tables name only part of the registered field (Ward 13 omits the eventual third-place candidate at 12 %; Ward 22 omits the runner-up at 19 %), so `tested_choice_set_status = partial` and the unnamed are compared as a group against the residual row.

### Results (fieldwork 39–41 days before election day; one firm, one cycle)

| ward | poll leader | poll | winner | actual | poll margin | actual margin | eventual runner-up: poll → actual |
|---|---|---:|---|---:|---:|---:|---|
| 4 | Perks | 52 | Perks | 35.5 | +31 | +3.9 | Lhamo 6 → 31.6 |
| 5 | Nunziata | 52 | Nunziata | 47.6 | +24 | +0.4 | Padovani 28 → 47.2 |
| 10 | Malik | 52 | Malik | 36.6 | +39 | +15.2 | Engelberg 8 → 21.3 |
| 13 | Moise | 41 | Moise | 48.5 | +15 | +30.2 | Ward 26 → 18.3 |
| 20 | Crawford | 39 | Crawford | 35.1 | +18 | +5.5 | Kandavel 9 → 29.6 |
| 22 | N. Mantas | 43 | N. Mantas | 48.9 | +20 | +30.2 | Wu unnamed → 18.7 |

- **Leader called 6 of 6.**
- **Candidate-level error** over 26 named pairs: mean −0.3 pt, **SD 11.1 pt**, RMSE 10.9, MAE 8.9. Pure sampling error at the median base is about 4 pt, so roughly two-thirds of the spread is not sampling noise.
- **Margins were overstated:** poll − actual margin mean **+10.3 pt, SD 18.5**. The eventual runner-up polled low in 4 of the 5 polls that named them (Lhamo −26, Kandavel −21, Padovani −19, Engelberg −13). The pattern is late consolidation behind one challenger, which a six-weeks-out decided/leaning read does not see.

### What this means for the 2026 polled wards

Taken naively (normal margin error with the 2022 mean and SD, n = 6), even large early leads keep a visible tail: a +27 lead (the August Ward 11 hypothetical Layton field) leaves roughly one-in-five odds of the actual margin being negative, a +34 lead (August Ward 19) roughly one-in-ten. The June readings in Wards 5 and 20 (+18 and +6) are not informative about the winner at this error level. Three cautions dominate any use: the 2026 readings were taken 2–4 months out, further than the 2022 set; two of the four operative readings are hypothetical fields that no longer match the ballot (Saxe has moved to Ward 14); and an SD from six polls of one firm in one cycle is itself a wide interval. This set can support a *coarse* "poll agrees with the structural prior" cue; it cannot by itself unlock the C1 tier as ADR 0026 defines it.

## What changed on disk

Nothing beyond this note. The six 2022 samples were ingested, validated and scored during the session (bundle counts reached 47 documents / 38 samples / 85 readings / 401 responses with every poll-source test passing after the inventory pins were updated), then reverted with the rest of the scratch work when the maintainer closed the exploration. The only lasting side effect is knowledge: the archive captures, digests and table layout above make re-ingestion a short task if the question is reopened.

## Options this leaves open (no recommendation adopted)

1. **Leave ADR 0043 as is.** Nothing here contradicts it; the race card could still surface the prior-winner base rate as another descriptive fact ("in open seats since 2010, a candidate with a prior electoral win has won 10 of 11 times").
2. **A coarse open-seat structural quantity** built on the validated rule only: one band per open seat, gated by ADR 0006/0049 band stability, never a per-candidate point. It would apply to four wards in 2026 and say nothing about the 21 incumbent races.
3. **Wait for the endorsement events** (sibling endorsement study: four endorsers with clear incumbency-matched associations; zero 2026 facts yet), which are the only in-cycle signal that could differentiate incumbent races.

## Exploration — other signals that could predict council races (2026-09-23, same session)

Brainstormed beyond the ADR 0043 list, then checked each for availability and ran throwaway probes where the data was already on disk or one request away. Probes are scratch; this section is their record. Ward-level mayoral shares were built by summing the per-ward sheets of the upstream poll-by-poll workbooks (2018 and 2022 general, 2023 by-election); unweighted ward means reproduce the official citywide shares to within a point (Tory 2018 0.640 vs 0.635; Tory 2022 0.630 vs 0.620; Chow 2023 0.365 vs 0.372).

| signal | available for 2026? | historical evidence (this session) | verdict |
|---|---|---|---|
| **Ideological fit: candidate camp × ward lean** | ward lean yes (2018/2022/2023 results, stable: r = 0.98 between 2018 and 2022 non-Tory share, 0.86 vs Chow 2023); camp only once 2026 endorsements land | 22 endorsed non-incumbents 2018/2022 (camps from endorsers: Progress Toronto/ATU/ETT/CUPE vs Sun/Tory). Sign flips by camp for every endorser: progressive-endorsed share rises with ward non-Tory share (r = +0.56, n = 13), conservative-endorsed falls (r = −0.42, n = 9). Pooled: **+7.6 pts of share per 10 pts of favourable lean**, bootstrap 95 % CI [+1.1, +12.7], permutation p = 0.059. | **Promising, untested as a forecast.** Not barred by ADR 0014 (past results, not the mayoral forecast). Sharpens the endorsement signal rather than replacing it. |
| **Prior vote share under another office in the same geography** | yes: 2025 MPP/MP shares in the identically-bounded riding for Guerrera (W4, 31 %), Di Giorgio (W5, 35 %), Zuniga (W17, 30 %), Erskine-Smith (W19, 68 %, won), Chen (W23, 63 %, won); trustee wins for King, Ehrhardt, Patel, Martino | 13 non-incumbent council candidates 2018/2022 with a same-geography MP/MPP run: r = 0.61 between that share and their council share; 0.63 using the last share anywhere, so the same-geography refinement is not separable at this n | **Real, mostly already captured** by the contract-2.1 most-recent-margin hint (+5.2 pp per 10). Worth carrying as a continuous feature if an open-seat quantity is ever built. |
| **Prior-winner rule in by-elections** | n/a (validation only) | 2023 W20, 2024 W15, 2025 W25: all three open by-election seats went to a prior winner (trustee, trustee, councillor); the 2025 runner-up was also a prior trustee winner | Out-of-scope confirmation of the probe-1 rule: 13 of 14 including by-elections. |
| Ballot order (alphabetical surname) | yes | 937 low-information candidacies in 167 contests, 2006–2022: r = −0.07 between ballot position and within-contest share; first-listed +0.4 pt in the tail, and lower among all non-incumbents once field size confounds | **Dead.** |
| Wikipedia article / pageviews | yes, but leaks | Malik, Moise, Cheng and Myers articles were created on 2022-10-25, the day after they won; Lhamo's in 2025; Padovani has none. Pre-election views exist only for prior notables, and are not monotone with outcome (Smitherman 1,509 views → 15 %; Bravo 598 → 71 %) | **Dead:** post-hoc article creation makes it unvalidatable, and what remains duplicates prior-office history. |
| News-mention counts (GDELT) | in principle | Rate-limited to one request per 5 s and stricter in practice; sparse (Cheng 7, Perks 9, Lhamo 6 articles over seven weeks); common names collide (a "Daniel Lee" query returns legal and finance press). The one clean lottery contest (Ward 18, 2022) did rank the winner first. | **Not practical** without a curated local-news index. Would be the only pre-election signal in no-prior-winner open seats. |
| Fundraising | no | Toronto Open Data publishes contribution files for 2018 only; 2022 filings are not released as data; 2026 filings arrive in 2027 | Dead for 2026, as ADR 0043 recorded. |
| Nomination timing | 2026 yes (`date_nomination`) | no historical candidate-list-with-dates dataset found on Open Data | Untestable now; recoverable from archived candidate lists if wanted. |
| Editorial overlay (name recognition, alignment) | yes | 101 rows: 74 "unknown", 4 aligned challengers. Design already rejects fame tiers as inputs (ADR 0009) | Too thin to carry the fit cue; endorsements are the honest source of camp. |

Two cautions on the fit result: endorsers select candidates partly *because* of ward lean, so the slope is a forecasting association, not an effect of alignment; and n = 22 with a permutation p just above 0.05 is one cycle's worth of evidence short of the bar this repo applies elsewhere. The ward-lean table (a per-ward sum of the upstream poll-by-poll mayoral sheets, ASCII-safe row filter required because of accented surnames) is cheap to regenerate; it was scratch and is not retained. The missing half is the 2026 camp labels, which arrive with the October endorsements.

Illustration of how the pieces stack in one race: Ward 5. The 2022 Forum poll read Nunziata 52, Padovani 28 six weeks out; the result was 47.6 to 47.2. In 2026 the June poll reads Nunziata 42, Di Giorgio 24, Padovani 20; Di Giorgio's 2025 provincial run in the identically-bounded riding drew 35 %; the ward's Chow-2023 share is 0.30, the most conservative-leaning of the polled wards. None of that is a forecast, but it is the kind of structured, dated evidence the race card could show.
