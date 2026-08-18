# Is the Mayoral Endpoint's Dirichlet concentration over-confident?

**Research date:** 2026-08-18
**Scope:** The four reconstructed historical Toronto mayoral cycles, firm-balanced bridge endpoint (post-ADR-0038)
**Purpose:** Test the over-confidence hypothesis raised by [candidate-tail-margin-coupling.md](candidate-tail-margin-coupling.md): the fitted Dirichlet concentration swings from ~28 to ~111 across folds and appears too confident. Establish whether this is a structural defect or a small-sample instability, and decide whether a fix is warranted for the 2026 forecast. This note changes no model code or publication gate; it records a disposition and a revisit trigger.

## Findings in brief

- The endpoint is **not globally over-confident.** Across folds, the realized winning margin lands inside the central-80% predictive interval for three of the four cycles, with well-spread PITs (2014: 0.27, 2018: 0.71, 2022: 0.66). The over-confidence is **entirely the 2023 by-election** (PIT 0.01–0.04; realized 4.72% margin below the 5th percentile of the predicted margin).
- The cause is **concentration instability, not a structural flaw.** The global concentration `kappa = (1 - sum p^2) / MSE - 1` is a method-of-moments precision matching the Dirichlet's total variance to the training cycles' average candidate-share squared error. In leave-one-cycle-out, 2023's realized share error (0.044, roughly nine times the generals' ~0.005) is the only large value; when 2023 is a training cycle, `kappa` is ~28, but when it is the held-out target and thus excluded from its own fit, the three calm general elections drive `kappa` to ~111. Dropping any general election barely moves `kappa`; dropping 2023 quadruples it.
- The single miscalibrated fold is **fixable by a stabler concentration.** Re-scoring the 2023 fold at `kappa` = 34.6 (all four cycles) or lower brings the realized margin back inside the 90% interval (PIT 0.19–0.23); only the fitted `kappa` = 110.8 excludes it. No change to the point estimate is required for coverage.
- **The production 2026 forecast is unaffected.** The pathological `kappa` arises only in the leave-one-out fold that holds 2023 out of its own fit. A forecast for a new target trains on *every* historical cycle, so it uses `kappa` = 34.6, at which all four realized margins — including 2023's close 4.72% — fall inside the central-80% interval. The over-confidence is therefore a leave-one-out validation artifact of the held-out volatile cycle, not a property of the forecast that will actually run. This is the decisive fact for whether a fix is needed now, and it argues against one.
- A secondary, separate issue: the 2023 **point** estimate misranks second place (Chow 0.324, Saunders 0.148, Bailao 0.147, versus the realized Chow 0.372 and Bailao 0.324). That is late poll-to-result drift — precisely the irreducible error the concentration is meant to absorb — and it reinforces that the endpoint needs *more* spread on volatile cycles, not less.

## Method

`scripts/diagnose_concentration_overconfidence.py` runs three read-only checks on the current endpoint. Part 1 fits each fold, draws the predictive winning-margin distribution as the qualification ladder does, and records the realized margin's percentile (PIT) and whether it lands in the central-80% interval. Part 2 refits `kappa` on all four cycles and on each leave-one-out triple, alongside each cycle's realized candidate-share squared error, to locate the leverage. Part 3 re-scores the 2023 fold's margin coverage across a range of concentrations, holding its point estimate fixed, to separate a concentration fix from a point-estimate fix.

The winning-margin CRPS and coverage score, for each Election Outcome Draw, the gap between the top two shares against the realized top-two gap; the concentration `kappa` is the Dirichlet precision, so a larger `kappa` is a tighter, more confident forecast.

## Results

### Winning-margin calibration (current endpoint)

| Cycle | Realized margin | Predicted p05 / p50 / p95 | Mean PIT | Central-80% | Fitted kappa |
|---|---:|---|---:|:--:|---:|
| 2014 general | 0.0654 | 0.011 / 0.128 / 0.357 | 0.27 | caught | 27.3 |
| 2018 general | 0.3990 | 0.049 / 0.312 / 0.560 | 0.71 | caught | 29.9 |
| 2022 general | 0.4415 | 0.123 / 0.382 / 0.602 | 0.66 | caught | 28.3 |
| 2023 by-election | 0.0472 | 0.054 / 0.153 / 0.253 | 0.02 | **missed** | 110.8 |

(Values shown at lead = 1; the other lead times differ negligibly within a cycle. Across all 16 folds the central-80% interval caught the realized margin 12 times, and all four misses are 2023's lead times.)

### Concentration leverage (fit at lead = 1)

`kappa`(all four cycles) = 34.6. Leave-one-out:

| Training set | Fitted kappa | Dropped cycle's share squared error |
|---|---:|---:|
| drop 2014 | 27.4 | 0.00465 |
| drop 2018 | 29.9 | 0.00620 |
| drop 2022 | 28.4 | 0.00487 |
| drop 2023 | **111.6** | **0.04384** |

### Is the 2023 miss fixable by a stabler kappa?

2023 point top-three: Chow 0.324, Saunders 0.148, Bailao 0.147; realized winning margin 0.0472.

| kappa | p05 / p50 / p95 | PIT | 90% interval |
|---:|---|---:|:--:|
| 110.8 (fitted) | 0.054 / 0.153 / 0.253 | 0.04 | missed |
| 34.6 | 0.012 / 0.128 / 0.310 | 0.19 | caught |
| 28.0 | 0.010 / 0.124 / 0.325 | 0.21 | caught |
| 15.0 | 0.010 / 0.119 / 0.377 | 0.23 | caught |

### Production concentration (all four cycles in training)

A forecast for a new target trains on every historical cycle and so uses `kappa` = 34.6, never the leave-one-out value. Coverage of each historical margin at that concentration:

| Cycle | Realized margin | Predicted p05 / p50 / p95 | PIT | Central-80% |
|---|---:|---|---:|:--:|
| 2014 general | 0.0654 | 0.011 / 0.124 / 0.333 | 0.28 | caught |
| 2018 general | 0.3990 | 0.059 / 0.301 / 0.538 | 0.74 | caught |
| 2022 general | 0.4415 | 0.141 / 0.378 / 0.579 | 0.69 | caught |
| 2023 by-election | 0.0472 | 0.013 / 0.131 / 0.312 | 0.18 | caught |

This is in-sample coverage — each cycle is in the fit — so it is optimistic by construction. It shows the production concentration spans the observed margin range, not that it is robust to a genuinely novel cycle.

## What can and cannot be inferred

### Supported by the observed record

- The endpoint's predictive spread is well-calibrated on three of four cycles; the over-confidence is confined to the one fold whose held-out concentration is set entirely by the calm general elections.
- The concentration estimator is fragile at this sample size: a single high-variance cycle's presence or absence in a three-cycle training set moves `kappa` roughly fourfold, and its absence produces a forecast that misses the one genuinely close, volatile result.

### Not established by these data

- **The entire over-confidence signal is one cycle.** With four cycles and leave-one-out, mishandling the sole outlier is nearly built in; this is evidence of an unstable estimator at n = 4, not of a deep structural over-confidence that would persist with more cycles.
- **The kappa sensitivity is not a fitted value.** Showing that `kappa` <= 34.6 catches 2023 is diagnostic, not a recommendation to set `kappa` = 28; choosing a concentration to catch a known outcome would be retrospective tuning. The defensible target is an estimator that no small subset can drive to over-confident levels.
- **The point-estimate miss is separate.** The second-place misranking is poll-to-result drift, distinct from the concentration question, and should not be conflated with it.

## Disposition

No change to the concentration estimator is warranted now. The over-confidence exists only in the leave-one-out fold that excludes the sole volatile cycle from its own fit; the forecast that will actually run trains on every historical cycle and uses `kappa` = 34.6, which covers all four realized margins including 2023's. Fixing the estimator would optimize against a validation artifact, and at n = 4 any pooling prior or cap would itself be doing most of the work.

This is recorded as a **characterized, bounded limitation with an explicit revisit trigger**, not an open fix:

- **Scope of validity.** The concentration is calibrated for a target inside the observed 2014–2023 margin envelope. 2026 is expected to sit there: it is an incumbent general election, structurally like 2018 and 2022, not like the 2023 open by-election whose held-out fold produced the pathology.
- **What we cannot claim.** With four cycles and leave-one-out, the one time the endpoint faced an out-of-distribution cycle it was over-confident, and n = 4 cannot show the production concentration is robust to a genuinely novel target. The in-sample coverage above is reassurance that `kappa` = 34.6 is consistent with the cycles we have, not proof it survives a fifth.
- **Revisit trigger.** If the 2026 race shapes up as unusually close, volatile, or structurally novel — a new-style field, a late collapse, or evidence unlike anything in 2014–2023 — revisit the concentration before publishing any Mayoral margin or Close-Result quantity. This is ADR 0024 (retain a non-zero error floor) and ADR 0022 (new evidence may withdraw a forecast) operating as intended.
- **Deferred fixes, if the trigger fires.** The candidate specifications remain a regularized or partially-pooled concentration (ADR 0013 precedent) or an irreducible-error cap (ADR 0024), each requiring its own spec and whole-cycle evaluation under ADR 0030. Neither is undertaken now.

The point-estimate second-place misranking is logged as a distinct, lower-priority follow-up, independent of the concentration.

## Reproducibility notes

- `scripts/diagnose_concentration_overconfidence.py` — reproduces every number above (`uv run scripts/diagnose_concentration_overconfidence.py`).
- Folds, corpus, and lead-time grid are built exactly as in [candidate-tail-margin-coupling.md](candidate-tail-margin-coupling.md); the concentration and point-estimate helpers are imported from `backend/model/mayoral_endpoint.py` so the measured quantities match the fitter.
