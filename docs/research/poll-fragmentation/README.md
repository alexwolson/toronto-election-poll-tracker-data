# Historical polling fragmentation — 2026-09-29

This is a descriptive audit of the source-verified historical mayoral corpus in
`data/raw/polls/historical_mayoral/`, not the discovery-only legacy CSV. No
forecast, release, ingestion input or publication feed is changed.

Run `python3 compute.py` in this directory to reproduce the CSVs. Only the Python
standard library is required. The script checks the index's mathematical bounds
and uniqueness of selected respondent samples.

## Measure and selection

Effective named candidates = 1 / sum(p_i squared), where p_i is each individually
published candidate's share divided by total individually published candidate
support. Undecided, refusal, would-not-vote and Other responses are excluded.
Consequently this measures concentration *among named candidates*, not a fully
observed ballot. Other remains a survey response category, consistent with ADR
0010; it is not allocated to omitted candidates or treated as a single candidate.
These numbers are not bounds on full-field fragmentation. In particular, excluded
Other support is material in 2022 (12% of the published denominator).

`per_reading.csv` contains all 260 readings with positive named support, including
partial and hypothetical readings, with explicit summary exclusions and selection
flags. Conditional leaning questions are not independent full-field polls.

The main comparison uses fieldwork ending 0–60 days before election day, complete
response coverage, general vote intention, and named candidates all present in
the official election outcome. This removes non-final hypothetical candidacies
but does not assert that every final candidate was offered in the question.
One reading per respondent sample is selected: widest named field first, then
lean-inclusive decided, decided-only, all-respondent, and other denominators;
remaining ties follow source CSV order. Source rounding is normalized away.
Different populations and turnout screens remain; this is descriptive, not a
harmonized estimate of the electorate. Final 60 days is an explicit comparison
window, not a claim of identical election stages.

## Results

| Election | Independent samples | Pollsters | Mean per poll | Median | Firm-balanced mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 3 | 3 | 3.38 | 3.60 | 3.38 |
| 2006 | 2 | 2 | 1.75 | 1.75 | 1.75 |
| 2010 | 9 | 5 | 2.93 | 2.67 | 2.97 |
| 2014 | 17 | 4 | 2.81 | 2.82 | 2.78 |
| 2018 | 9 | 3 | 1.85 | 1.83 | 1.86 |
| 2022 | 1 | 1 | 2.15 | 2.15 | 2.15 |
| 2023 | 26 | 5 | 4.89 | 4.92 | 4.72 |

Firm-balanced mean first averages each firm's selected per-poll scores, then
averages firms equally. It limits influence from prolific firms; neither it nor
the poll mean is a time-weighted election-day estimate. Unequal archive coverage,
field breadth and survey conventions limit comparisons. Partial sources are
retained in the per-reading output but excluded from the summary.

2022's one complete sample reports Tory 56%, Penalosa 20%, Brown 6%, Acton 6%,
Other 12%. Renormalizing the four named candidates yields 2.146 effective named
candidates. Thus the data support lower fragmentation than 2023, but do not
support describing that poll as a pure two-candidate field.

## Aggregation recommendation

Compute per poll first for “how fragmented was the field in this election's
polling?” Show median and mean, and use a common time window. For a single
cross-election covariate, consider the firm-balanced per-poll mean with explicit
coverage caveats. Do not automatically translate this descriptive quantity into
forecast variance without validation.

Computing the index from average candidate shares answers a different question:
“how fragmented is the average support distribution?” Poll-to-poll changes in
which candidates are strongest can make this look more fragmented than typical
individual polls. There is no universal ordering of the two statistics because
the reciprocal concentration index is nonlinear.

Average shares only across identical named fields and compatible survey
populations/denominators. The same-field CSVs demonstrate the arithmetic on
selected readings, not a publishable polling estimate: survey screens and
leaner treatment are not further harmonized. Never fill an unreported candidate
with zero. For the largest identical-field group in 2023 (10 samples), the mean
per-poll index is 5.207 versus 5.375 from average shares. For 2014 (16 samples),
the corresponding figures are 2.790 and 2.819.

For fragmentation at a particular analysis cutoff, compute the index from a
validated contemporaneous joint support estimate; for an election-day forecast,
compute it separately in every joint outcome draw to preserve uncertainty.

## 2026 through September 29

`python3 compute_2026.py` uses the current archive's designated descriptive
reading per sample, restricts to citywide mayoral polling, and writes all 25
archived samples to `2026_per_poll.csv`. Earlier hypothetical candidate fields
are retained there for context, not pooled into the current summary.

The available part of the final-60-day window for the October 26 election is
August 27–September 29. Six complete samples from five firms have fieldwork ends
in this window: mean 2.346, median 2.340, firm-balanced mean 2.337. These are not
a completed late-campaign average: October polls have not yet occurred.

| Fieldwork end | Firm | Effective named candidates |
| --- | --- | ---: |
| September 5 | Liaison | 2.38 |
| September 8 | Ipsos | 2.12 |
| September 17 | Mainstreet | 2.63 |
| September 20 | Liaison | 2.41 |
| September 23 | Forum | 2.24 |
| September 24 | Canada Pulse | 2.30 |

Mainstreet measures five named candidates; the other five readings measure three.
Its wider field partly explains its higher score. Ipsos is all-respondent support,
renormalized over named candidates; the other readings are decided-and-leaning.
Accordingly the descriptive averages are useful comparisons, not a harmonized
polling estimate. Relative to historical firm-balanced scores, 2026 so far is
well below 2023 (4.72), below 2014 (2.78), and moderately above 2018 (1.86) and
the single complete 2022 sample (2.15).

## Joint closeness–fragmentation plot

`compute_joint.py` (NumPy required) calculates each selected poll's top-two gap
on the same named-candidate denominator as fragmentation, then averages both
coordinates within firm and across firms equally. It writes `joint_plot_data.json`.
The x axis is reversed so closer races sit to the right; no arbitrary closeness
score replaces the gap. Poll leaders and runners-up are identified per reading.

Regions use 20,000 seeded resamples of whole firms, jointly resampling the two
coordinates. Ellipses use bootstrap covariance and the empirical 95th percentile
of squared Mahalanobis distance around the point estimate. They depict bootstrap
concentration, not empirically calibrated 95% coverage of a population parameter
or election-day outcome. Only 1–5 firms are available, archival coverage is
nonrandom, and respondent sampling/model error is not included. With two firms
(2006) the region degenerates to a line; with one firm (2022), it is unavailable.
The regions capture sensitivity to firm composition; they do not fix differences
in candidate menus or survey populations. Historical windows are completed;
2026 remains partial. The current dots are descriptive full-window summaries,
not estimates of support on election day or at one common point in the campaign.

### Vega-Altair figure

`figure_altair.py` renders the joint plot using Altair 6.3.0 and
vl-convert-python 1.9.0.post1. It exports self-contained interactive HTML,
Vega-Lite JSON, SVG, a 2× PNG, and PDF. To reproduce, install those two packages
in an isolated Python environment and run the script after `compute_joint.py`.
The static image was visually inspected for labels, axes and uncertainty regions.

### Result dots matched to polling fields

Run `python3 compute_matched_results.py` before `figure_altair.py`. For each
selected historical reading, the script looks up official votes for exactly
that reading's individually measured candidates, renormalizes within that field,
and computes effective candidate count and the top-two margin. It then averages
within pollster and across pollsters equally, exactly as for the polling regions.
The two highest actual vote totals within each matched field define its result
margin; these need not be the two leaders in the corresponding poll.

`matched_results_per_reading.csv` preserves every field and its result metrics;
`matched_result_metrics.json` provides the plotted coordinates. The script checks
candidate counts, index bounds and matching sample/firm counts. Full-ballot
metrics in `actual_result_metrics.json` are retained as a separate reference,
not used for the dots. There is no 2026 result dot. Colour pairs each dot with
its unchanged polling region; there are no connectors.

Both axes now compare the same candidate fields, normalization and firm weights.
Result dots are weighted summaries of restricted-field official results, rather
than full-ballot electoral metrics. Differences still reflect timing, populations
and polling errors. Bootstrap regions describe polling summaries, not prediction
intervals for these outcome dots.

### Recency sensitivity

`python3 check_recency.py` writes `recency_comparison.csv`. It applies prespecified
60/30/21/14/7-day windows, 14/7-day exponential half-lives within the 60-day window,
and latest-per-firm within 30 days. All use fieldwork end, one selected reading
per sample, matched result fields, identical polling/result weights, and equal
firm weights. Exponential weights operate within each firm's samples; firms
remain equally weighted. Thus they do not suppress an old firm's sole poll.
These are descriptive sensitivity comparisons, not independently validated
hyperparameter selection.

All seven cycles have at least one eligible sample in the final 21 days. Their
margin/fragmentation mean absolute errors are 7.716/0.471 at 60 days,
8.614/0.417 at 30 days, 8.659/0.425 at 21 days, 7.765/0.442 with a 14-day
half-life, 7.646/0.426 with a 7-day half-life, and 7.941/0.397 using the latest
sample per firm within 30 days. Firm composition changes when windows narrow.

Only 2010, 2014 and 2023 have final-week samples. Comparing those same three
cycles, 60-day versus final-week margin MAE falls from 7.475 to 3.873 pp;
fragmentation MAE falls from 0.650 to 0.483. Final-week coverage is sparse:
2010 has two samples from one firm, 2014 four samples from three firms, 2023
four samples from four firms. The 2023 final-week summary still has a 12.56 pp
gap versus 5.03 pp in matched results and effective count 4.73 versus 3.43.

Temporal proximity is a principled way to better align polling with final
results, but these data do not establish an optimal cutoff or decay rate. For
2026 comparisons before election day, use a historical cutoff at the same days
remaining and exclude later historical polls; the completed historical final
week cannot be treated as evidence already available at the 2026 cutoff.

### Removing equal firm weights

`python3 check_firm_weights.py` writes `firm_weight_comparison.csv` and
`firm_weight_summary.csv`. For each identical sample/window selection, it compares
firm-balanced weights with weights directly over all independent poll samples.
The latter gives every poll weight one, or weight 2^(-days/half_life) for recency
variants. Matched result coordinates always receive identical weights. Sample
size is not used. Reported errors average equally across elections, so elections
with denser archives do not dominate validation.

Across seven elections, equal-poll weighting changes 60-day margin MAE from
7.716 to 7.383 pp and fragmentation MAE from 0.471 to 0.486. At 30 days the
corresponding changes are 8.614 to 8.374 pp and 0.417 to 0.443. At 21 days they
are 8.659 to 8.262 pp and 0.425 to 0.443. Thus removing firm balancing modestly
improves margin agreement for unweighted windows and worsens fragmentation.

With a 7-day half-life across the 60-day window, margin MAE changes from 7.646
to 7.747 pp and fragmentation MAE from 0.426 to 0.411. In the final week, the
same three elections yield 3.873 versus 4.092 pp and 0.483 versus 0.486. Latest
per firm within 30 days is identical under both schemes by construction.
No method dominates both metrics. These sensitivity checks do not validate an
optimal method, calibrated outcome regions, or election-day predictions.

### Final-week figure with tentative 2026 region

`compute_final_week.py`, `compute_final_week_results.py`, and
`figure_final_week_altair.py` produce the separate
`competitiveness-fragmentation-final-week` exports. Historical selection is
restricted to fieldwork ending 0–7 days before voting, yielding 2010 (2 samples,
1 firm), 2014 (4 samples, 3 firms), and 2023 (4 samples, 4 firms). Dots are
recomputed from those same final-week named candidate fields and equal firm
weights. 2010 has no firm-bootstrap region because only one firm is represented.

The 2026 region is copied unchanged from the available August 27–September 29
summary, with transparent diagonal stripes clipped to its polygon. Stripes
indicate the incomplete campaign window, not quantified additional uncertainty;
there is no 2026 result dot. The selected final-week historical regions are
recomputed with the same illustrative bootstrap procedure. The plot does not
claim the 2026 evidence is at the same campaign stage as historical final-week
polling. PNG exports were visually checked for labels, clipping and hatching.

### Polling-only comparison at the October 5 equivalent cutoff

`compute_stage_matched.py` and `figure_stage_matched_altair.py` produce the
`competitiveness-fragmentation-stage-matched` exports. The 2026 target cutoff is
Monday, October 5, 21 days before October 26. Each historical cutoff is likewise
21 days before election day. Use fieldwork ending within 60 days before each
cutoff (inclusive) and require the canonical `evidence_available_at` calendar
date to be on or before that cutoff. Availability is interpreted through the
end of the cutoff day. Later historical evidence is excluded.

Selection retains complete citywide general vote intention and one reading per
independent sample, preferring the widest named field, then lean-inclusive,
decided-only, raw readings. Historical fields retain the previous restriction
that every named candidate appears on the final ballot; this excludes early
non-final/hypothetical fields rather than claiming a pure real-time reconstruction
of the candidate pool. For 2026, use the archive's designated descriptive reading.
Means and joint bootstrap regions use equal firm weights. Both coordinates
are polling summaries; no election-result dots enter this figure.

The minimum threshold applies within this selected window: at least three
independent samples and three distinct source-labelled pollsters. Included:
2010 (3/3), 2014 (9/4), 2018 (7/3), 2023 (18/4), 2026 (10/6 after the October 2 refresh).
Excluded: 2003 (0/0), 2006 (1/1), 2022 (0/0). These are audited archive coverage
counts, not statements that no other polls occurred.

`stage_matched_selection.csv` records exclusions and selected readings;
`stage_matched_polls.csv` records the coordinates; `stage_matched_coverage.csv`
records thresholds and cutoffs; `stage_matched_plot_data.json` records centroids
and regions. The script verifies threshold and sample uniqueness. Bootstraps use
20,000 resamples with fixed cycle-specific seeds. Exports were visually checked.

2026 is provisional, marked with transparent diagonal stripes: the available
archive is only through October 2, before the target October 5 cutoff.
Rerunning the scripts after authorized ingestion will incorporate newly available
eligible polls. This plot does not ingest or publish feeds and does not schedule
a refresh. The time window, normalized named support, and aggregation rules are
shared, but candidate menus and survey populations still differ.

### Stage-matched polling regions with election-result dots

`compute_stage_matched_results.py` and `figure_stage_matched_results_altair.py`
produce the separate `competitiveness-fragmentation-stage-matched-results`
exports. The original polling-centroid figure remains intact. Historical dots
show the official result restricted, for each selected poll, to the candidates
that poll named. This follows the earlier matched-result comparison: Other,
undecided and final candidates absent from a poll's named field do not enter that
poll's result metric. Each poll's matched result margin and effective candidate
count are first averaged within firm and then firms are weighted equally,
mirroring the region centroids. The candidate fields can differ between polls,
so a dot summarizes several field-matched views of the same official outcome.

Dashed colour-matched lines run from each polling centroid to its historical
result dot. The polling centroids themselves are not drawn as dots. The striped
2026 polling region has a year label but no result dot or connector. The x-axis
extends to a 47-point gap so the 2018 result remains visible. Historical
result coordinates (margin, effective count): 2010 (12.075, 2.505), 2014
(6.725, 2.866), 2018 (44.731, 1.735), 2023 (5.223, 3.206). The unchanged
polling regions retain the stage-matched inclusion rule, equal-firm averaging
and illustrative bootstrap interpretation documented above. Outputs include
PNG, PDF, SVG, interactive HTML and Vega-Lite JSON.


### Stage-matched axis revision

Both stage-matched exports use the actual top-two gap in percentage points on
the same horizontal scale (0 to 47), so larger frontrunner leads lie farther
right. Effective candidate count increases upward. The upper-left direction
therefore means a smaller lead and more candidates. This is a descriptive
orientation, not a win-probability scale. The original broader
`competitiveness-fragmentation` plot has not been revised.

### June 2023 polling timelines

`figure_2023_fragmentation_altair.py` produces
`toronto-2023-fragmentation-over-time` in PNG, PDF, SVG, interactive HTML and
Vega-Lite JSON, plus `toronto_2023_fragmentation_timeline.csv` and
`toronto_2023_fragmentation_trailing_average.csv`. It plots the
effective number of named candidates for 13 independent samples from five
pollsters, using one complete general vote-intention reading per sample from
June 1–25. The reading-selection priority is
the same as `compute.py`: widest named field, then lean-inclusive, decided, or
all-respondent denominator. The final-60-day exclusions also apply.

The line is a backward-looking exponentially weighted average that updates when
a poll ends. Each earlier sample loses half its weight per day, without using
future polls or equal-firm weighting. Each dated update is
visually eased over the following 24 hours; the line is unchanged before a
poll's fieldwork end. This easing is a display choice, not a fitted campaign
trajectory. The vertical marker
is Tory's June 21 endorsement of Bailão, independently documented in
`toronto-election-poll-tracker-backend/docs/research/john-tory-2023-endorsement-evidence.md`
on the backend's `research/tory-endorsement-scenarios` branch. The marker is a
date reference, not a causal estimate. Candidate menus differ across polls,
so the per-poll metric is not perfectly field-matched. Only three selected
samples ended after June 21 (two on June 23 and one on June 25), which limits
what the post-endorsement period can show.

`figure_2023_late_support_altair.py` uses the same complete-reading selection
for June 1–25. It produces
`toronto-2023-late-campaign-support` in PNG, PDF, SVG, interactive HTML and
Vega-Lite JSON, plus `toronto_2023_late_support_groups.csv` and
`toronto_2023_late_support_trailing_average.csv`. For each of 13
independent samples, it sums support for all named candidates other than Chow
and Bailão and normalizes all three groups over total named support. This is
the same denominator used for fragmentation; Other and undecided are excluded.
Each series has a backward-looking line that updates only when a poll ends.
At each update every previous sample receives half as much weight per day of
age; no future polls enter the average and firms are not weighted equally.
The update is visually eased over the following 24 hours, so the line is
continuous but cannot begin moving before the poll's fieldwork end. This easing
is a display choice rather than an estimate of within-day opinion change.
As the three categories sum to 100 in each poll, their displayed averages also
sum to 100. The plot displays the decline in other named candidates and
Bailão's rise while Chow is comparatively steady. Different candidate menus and
survey populations remain, and the aggregate trajectories do not identify
individual vote transfers or an endorsement effect.


## October 2 refresh

Reran both preferred stage-matched figures using the audited archive available
on October 2, including Liaison September 26–27 and Mainstreet September 28–29.
The October 5 target and all historical cutoffs, candidate normalization,
equal-firm averaging and bootstrap seeds remain unchanged. Current coverage is
now **10 independent samples from six firms**. The 2026 polling centroid is
**13.9881 percentage points** of top-two gap and **2.33036 effective named
candidates**; the 2023 centroid remains 14.7704 / 4.90390. The two new questions
come from two new samples; Mainstreet's same-sample head-to-head is excluded
from these full-field summaries by the designated-reading rule.

The date-only Mainstreet publication has conservative canonical availability
at October 3 midnight. It is eligible for the October 5 target; this manual
October 2 refresh knowingly uses the report already supplied and audited today.
It does not change the canonical timestamp or historical availability rule.
The stripe and figure notes still identify 2026 as provisional before October 5.
`refresh-2026-10-02.json` records the archive file hashes. Prior stage-matched
figures and data are preserved under `snapshots/2026-09-29/`.

`compute_2026.py` was also refreshed. The available final-60-day portion has
eight samples from five firms: mean per-poll effective count 2.38300, median
2.38775 and equal-firm mean 2.33361. These use a different window from the
preferred stage-matched centroid above. No new 2023 evidence was ingested, so
its June timelines and the historical consolidation calculation are unchanged.
