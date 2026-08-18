# Does omitted-candidate mass scale with choice-set size? Historical Toronto evidence

**Research date:** 2026-08-18
**Scope:** The four reconstructed historical Toronto mayoral cycles in the endpoint corpus (2014, 2018, 2022, 2023 by-election)
**Purpose:** Test whether the Mayoral Endpoint's per-omitted-candidate tail-odds model is empirically justified, and whether a choice-set-size-invariant allocation is better calibrated out of sample. This note measures evidence; the resulting policy is recorded in ADR 0038.

## Findings in brief

- The current endpoint learns one **per-omitted-candidate odds** and allocates it through a `1 + m·odds` normalizer, so a Poll Reading omitting `m` Final-Ballot candidates receives total tail mass `m·odds / (1 + m·odds)`, which **rises with the number of omitted candidates**. The realized record does not support that relationship.
- Across the four reconstructed cycles, the number of omitted candidates `m` ranges from **27 to 94** while realized total omitted mass `T` ranges from **2.85% to 12.36%**, and the two **largest-field** cycles have among the **smallest** tails: 2014 (`m`≈62) realized 2.85% and the 2023 by-election (`m`≈94) realized ~8.1%, versus 2022 (`m`=27) at 12.23% and 2018 (`m`≈33) at 12.36%. Total omitted mass does not increase with `m`; the cross-cycle association is slightly negative.
- Under **leave-one-cycle-out**, the per-candidate count-scaling model **over-predicts** tail mass on the two large-field cycles (2014: predicts 17.7% vs 2.85%; 2023: predicts 23.9% vs 8.1%) and **under-predicts** on the two small-field cycles — the signature of spurious scaling. Its mean absolute error in total tail mass is **10.9 percentage points**. A constant-total allocation (one total omitted mass per election, independent of `m`) has a mean absolute error of **4.5 points**, roughly a 2.4× reduction.
- The evidence argues that per-candidate count-scaling is **unjustified**, not that a constant total is a law. `m` is confounded with ballot size, the honest sample is four cycles, and pollster preselection makes the realized unnamed share endogenous. See [unmeasured-candidate-tail.md](unmeasured-candidate-tail.md) for the underlying record and its limits.

## The two allocations

Notation: for one Poll Reading, `m` is the number of Final-Ballot candidates with no individual poll row; `T` is those candidates' combined realized election-day vote share (their Unmeasured Candidate Tail).

- **Per-candidate count-scaling (current).** `_fit_tail_odds` averages `o = T / ((1 − T)·m)` — the odds credited to a *single* omitted candidate — across training readings and cycles. `_reading_point` then gives each of the `m` omitted candidates `o / (1 + m·o)`, for a total tail of `m·o / (1 + m·o)`. Because the total is increasing in `m`, a reading that names fewer candidates is assumed to leave more election-day mass in the tail.
- **Constant-total (candidate-tail-invariant).** Learn one total omitted mass per training cycle (the realized `T`), average across cycles, and allocate that total evenly among whichever `m` candidates a reading omits. Total tail mass is the same regardless of how many names the reading happens to carry.

Both keep every tail candidate distinct in every Election Outcome Draw and treat undistinguished candidates as exchangeable (ADR 0004); neither converts a Poll Residual into candidate support (ADR 0010).

## Method

The diagnostic reproduces the endpoint's exact selection path. It loads the canonical historical corpus, builds the whole-election evaluation cycles at the frozen lead-time grid (12, 7, 3, 1 days, 12:00 America/Toronto), and reads the same **fit snapshot** — the closest post-Final lead time — that `_fit_tail_odds` consumes. For every selected reading that omits at least one Final-Ballot candidate it records `(m, T)`, then:

1. fits an ordinary least squares line of `log(T / (1 − T))` on `log(m)` (slope `+1` is the behaviour implied by the current per-candidate model; `0` is constant total); and
2. runs leave-one-cycle-out, fitting each model on the other three cycles and comparing each held-out cycle's predicted total tail mass to its realized total.

Realized shares use votes credited to candidates as the denominator, consistent with the corpus and with [unmeasured-candidate-tail.md](unmeasured-candidate-tail.md).

## Results

### Realized omitted mass by cycle (fit snapshot)

| Cycle | Omitted candidates `m` | Realized total tail `T` (mean; range) |
|---|---:|---|
| 2014 general | 62 | 2.85% (2.85–2.85%) |
| 2018 general | 32–33 | 12.36% (9.53–12.92%) |
| 2022 general | 27 | 12.23% (single reading) |
| 2023 by-election | 94–96 | 8.11% (7.31–12.68%) |

Within a cycle `m` is near-constant, so the identifying variation is the four cross-cycle points. Ordered by `m` (27, 33, 62, 94), realized `T` is (12.23%, 12.36%, 2.85%, 8.11%): not increasing.

### Slope of tail mass on choice-set size

`log(T / (1 − T)) ~ log(m)` has slope **−0.285** (row-level r = −0.20 across 33 pseudo-replicated readings; four independent cycles). The current model implies **+1**; a constant total implies **0**. The point estimate is below even the constant-total null. Equivalently, `log(per-candidate odds) ~ log(m)` has slope **−1.285**, close to the **−1** implied by a fixed total and far from the **0** the current model assumes.

### Leave-one-cycle-out: predicted vs realized total tail mass

| Held-out cycle | `m` | Realized `T` | Current predicts | Current error | Constant-total predicts | Constant-total error |
|---|---:|---:|---:|---:|---:|---:|
| 2014 general | 62 | 2.85% | 17.68% | 14.83 | 10.90% | 8.05 |
| 2018 general | 33 | 12.36% | 6.74% | 5.62 | 7.73% | 4.63 |
| 2022 general | 27 | 12.23% | 4.88% | 7.35 | 7.77% | 4.46 |
| 2023 by-election | 95 | 8.11% | 23.92% | 15.81 | 9.14% | 1.03 |
| **Mean absolute error** | | | | **10.90** | | **4.54** |

Errors are in percentage points of valid-vote share. The current model's errors are largest and one-directional on the two large-field cycles, exactly where count-scaling inflates the total.

## What can and cannot be inferred

### Supported by the observed record

- Realized total omitted mass does **not** rise with the number of omitted candidates across these four cycles; the association is flat to slightly negative.
- The per-candidate count-scaling model is **materially miscalibrated out of sample**, over-predicting tail mass on large-field cycles by 12–16 points, and a choice-set-size-invariant total roughly halves the held-out error.

### Not established by these data

- **No proof that a constant total is correct.** With four cycles and `m` confounded with ballot size, this rules out count-scaling far more confidently than it endorses any specific replacement. A mild, shrunk ballot-size term cannot be distinguished from a flat total here and would risk over-fitting four points.
- **No natural tail law.** Pollster preselection means realized unnamed mass reflects which candidates firms judged worth naming, not a stable generative rate (see [unmeasured-candidate-tail.md](unmeasured-candidate-tail.md), "Data and archival limitations").
- **No headline-score claim.** This note measures tail-mass calibration only, deliberately separate from the endpoint's winning-margin CRPS and log-score. Whether the constant-total allocation preserves or improves the frozen qualification metrics (ADR 0030) is a separate check to run when the change is implemented, and must not be tuned toward.

## Post-implementation result (2026-08-18)

The constant-total allocation is implemented (ADR 0038) and the frozen qualification ladder (`scripts/evaluate_mayoral_endpoint.py`) was re-run before and after. The numbers are reported here, not tuned toward; nothing in the endpoint was adjusted to move them.

| Metric (firm-balanced bridge, all elections) | Before | After | |
|---|---:|---:|---|
| Winning-margin CRPS (ADR 0030 primary) | 0.04970 | 0.05929 | worse +0.0096 |
| Winner log score (overconfidence guard) | 0.08854 | 0.07599 | better −0.0126 |
| Mean candidate-share CRPS (tail-sensitive) | 0.00420 | 0.00394 | better −0.0003 |
| Close-result log loss | 0.748 | 1.066 | worse +0.318 |

The change improves the metric it targeted (candidate-share CRPS, the tail-sensitive score) and the overconfidence guard in every cycle, but worsens the primary winning-margin CRPS. The qualification outcome is unchanged: the endpoint is `not_qualified` before and after, because the firm-balanced bridge does not beat its own latest-sample comparator on the primary metric in either case.

The winning-margin regression is not spread evenly. It is almost entirely the 2023 by-election, whose 102-candidate field is where the two allocations differ most:

| Cycle | Bridge winning-margin CRPS before → after | Bridge candidate-share CRPS before → after |
|---|---:|---:|
| 2014 general | 0.03837 → 0.04229 (+0.004) | 0.00220 → 0.00178 (−0.0004) |
| 2018 general | 0.05512 → 0.05523 (+0.000) | 0.00433 → 0.00421 (−0.0001) |
| 2022 general | 0.04238 → 0.04454 (+0.002) | 0.00583 → 0.00541 (−0.0004) |
| 2023 by-election | 0.06294 → 0.09511 (**+0.032**) | 0.00445 → 0.00434 (−0.0001) |

On `regular_elections_only` (the three general elections, excluding 2023) the primary metric worsens only marginally (+0.0027) and the close-result metrics improve. The mechanism and its consequences are examined in [candidate-tail-margin-coupling.md](candidate-tail-margin-coupling.md).

## Reproducibility notes

- `scripts/diagnose_candidate_tail_scaling.py` — reproduces every number above (`uv run scripts/diagnose_candidate_tail_scaling.py`). It imports `_selected_for_cycle` and `_fit_tail_odds` from `backend/model/mayoral_endpoint.py` so the measured selection matches the fitter exactly.
- Corpus inputs are the canonical historical mayoral corpus loaded by `backend/model/historical_mayoral.load_historical_mayoral_corpus`; cycles are built by `backend/model/historical_mayoral_evaluation.build_historical_mayoral_evaluation_cycles` at the ADR 0030 lead-time grid.
