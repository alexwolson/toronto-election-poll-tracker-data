# The incumbency-informed endpoint: v1 specification and qualification

**Research date:** 2026-08-18
**Scope:** The four reconstructed historical Toronto mayoral cycles; firm-balanced bridge baseline
**Purpose:** Specify the v1 incumbency-informed endpoint (ADR 0013) and record whether it qualifies against the polling-only baseline under the whole-election protocol (ADR 0030). Evidence for ADR 0039.

## Findings in brief

- The v1 incumbency-informed variant enters through a single mean-shift of the incumbent's point share: a precision-weighted blend of the polling point and a comparison-population prior mean, `p_post = (w·p_prior + κ·p_poll) / (w + κ)`, where `κ` is the fitted polling concentration and `w` a prior pseudo-count. Non-incumbent shares rescale proportionally; open races are the bridge unchanged.
- It **does not qualify** over the firm-balanced bridge, in both the all-elections and regular-elections-only populations. Winning-margin CRPS worsens from 0.05929 to 0.06136 (all elections) at `w = 8`, and the log-score guard does not improve. The polling-only bridge remains authoritative and the incumbency-informed specification is retained as the Mandatory Sensitivity Variant (ADR 0013).
- The variant behaves exactly as designed: only the two incumbent cycles change (2018 and 2022), open races are byte-identical to the bridge, `w = 0` reduces exactly to the bridge, and larger `w` shifts the incumbent share monotonically. The prior is overwhelmed by the strong post-Final polls — its effect is small — but it points the wrong way on these two landslides.
- This is the expected outcome, not a defect. The only two incumbent cycles in the corpus are Tory landslides (realized share 0.635 and 0.620) that the polls already captured, and the leave-one-trial-out prior mean (0.583) sits below them, so the prior can only pull the incumbent's share down. The prior's value is in sparse-evidence regimes, which the post-Final lead-time grid does not exercise.

## Method

The prior mean is the median incumbent share of the Mayoral Comparison Population under **leave-one-trial-out** partial pooling: the single trial matching the target election is removed, while every other trial — including Toronto's other defences — stays in the pool (ADR 0013). For the historical Toronto folds this yields 0.583 from 18 trials. A live 2026 forecast matches no trial and so pools all 19 (median 0.596), including Toronto's three wins.

`incumbency_prior_share`, `apply_incumbency_prior`, and `IncumbencyInformedPredictor` live in `backend/model/mayoral_incumbency_endpoint.py`, wrapping the firm-balanced bridge fit without modifying the polling-only baseline; both predictors share `mayoral_endpoint.draws_from_point`. `scripts/evaluate_incumbency_endpoint.py` runs the frozen harness and the ADR 0030 ladder. The prior pseudo-count `w` is a judgment parameter (default 8), reported as a sensitivity and deliberately not tuned to qualify.

## Results

The blend at the closest lead time (`κ ≈ 28–30`, prior 0.583):

| Cycle | Incumbent polled share | Prior mean | Blended (`w=8`) | Realized |
|---|---:|---:|---:|---:|
| 2018 (Tory) | 0.605 | 0.583 | 0.601 | 0.635 |
| 2022 (Tory) | 0.587 | 0.583 | 0.586 | 0.620 |

Both blends move away from the realized share. Qualification against the bridge:

| Population | Winning-margin CRPS (primary) | Winner log score (guard) | Qualifies? |
|---|---|---|:--:|
| all elections | 0.05929 → 0.06136 (+0.00207) | 0.07599 → 0.07676 (+0.00077) | No |
| regular only | 0.04511 → 0.04648 (+0.00138) | 0.01868 → 0.01868 (+0.00000) | No |

Per-cycle winning-margin CRPS (all elections): 2018 0.05523 → 0.06278; 2022 0.04454 → 0.04527; 2014 and 2023 unchanged (open races). Prior-strength sensitivity (all-elections primary): `w=0` → 0.05929 (identical to the bridge), `w=4` → 0.06070, `w=8` → 0.06136, `w=16` → 0.06144 — every non-zero weight worsens the score.

## What can and cannot be inferred

### Supported by the observed record

- The v1 blend is a correct, minimal realization of ADR 0013: incumbency enters only as a prior on the incumbent's share, overwhelmed by strong polls, never a win bonus, and reducing to the baseline in open races and at zero weight.
- On the current corpus the prior does not earn operational weight; the polling-only bridge is authoritative.

### Not established by these data

- **The verdict rests on two cycles, both landslides.** The variant differs from the bridge only on 2018 and 2022, both Tory wins the polls already forecast well. This cannot show the prior is unhelpful in general — only that it does not help when strong polls already pin a winning incumbent.
- **The regime that motivates the prior is untested here.** The prior regularizes sparse evidence; the post-Final grid (12–1 days) has relatively rich polling, so the prior is always overwhelmed. Its value for an early, thinly-polled 2026 is not measured by this evaluation.
- **The live direction may differ.** The 2026 forecast pools all cities (prior mean 0.596, versus 0.583 here) and applies to a different incumbent; nothing here fixes a directional effect for 2026.

## Disposition

Retain the incumbency-informed variant as the Mandatory Sensitivity Variant (ADR 0013); the polling-only bridge remains authoritative. Do not tune `w` to force qualification. Revisit if the corpus gains incumbent cycles that are not landslides — especially any incumbent defeat, which the comparison population carries but the Toronto validation cycles do not. Recorded as ADR 0039.

## Reproducibility notes

- `scripts/evaluate_incumbency_endpoint.py` — reproduces the qualification verdict, per-cycle deltas, and `w` sensitivity (`uv run scripts/evaluate_incumbency_endpoint.py`).
- The prior and blend are unit-tested in `tests/model/test_mayoral_incumbency_endpoint.py`; the comparison population loads via `backend/model/mayoral_incumbency.load_mayoral_incumbency_population`.
