# Why the constant-total tail worsened winning-margin CRPS

**Research date:** 2026-08-18
**Scope:** The four reconstructed historical Toronto mayoral cycles, firm-balanced bridge endpoint
**Purpose:** Explain the winning-margin CRPS regression introduced by ADR 0038's constant-total tail allocation, and decide whether it is a defect in that decision or a symptom of a separate one. Follows [candidate-tail-choice-set-scaling.md](candidate-tail-choice-set-scaling.md).

## Findings in brief

- The regression is **almost entirely the 2023 by-election**. Bridge winning-margin CRPS rose 0.06294 → 0.09511 there (+0.032), while the three general elections each moved by at most +0.004. Candidate-share CRPS — the metric ADR 0038 targeted — improved in all four cycles.
- The 2023 race was **close** (Chow 37.17%, Bailão 32.45%, realized margin **4.72%**) inside a **102-candidate field**. Both tail allocations badly **over-predict** the winning margin: the old allocation's mean predicted margin was 14.2%, the new one's is **17.6%**. The new allocation over-predicts more because it leaves the two leaders more mass (skimming ~9% into the tail instead of ~24%), which widens the gap between them.
- The 2023 fold is also **over-confident**: the fitted Dirichlet concentration is ~88 under the old allocation and **~111 under the new one**, versus ~25–30 in every other fold. A tighter distribution around an already-too-wide margin is penalised harder, so the mean predicted margin moving from 14.2% to 17.6% and the concentration rising from 88 to 111 together drive the CRPS up.
- The regression is therefore **not a defect in ADR 0038**. The endpoint over-predicts the winning margin in close, large-field races; the discarded count-scaling was accidentally masking that by compressing the leaders. Removing a miscalibrated tail exposed a pre-existing over-confidence in the margin. The old model's lower 2023 margin CRPS was the right number for the wrong reason.

## Method

`scripts/diagnose_margin_regression.py` reconstructs the superseded per-omitted-candidate allocation (by temporarily restoring its per-reading rule inside the module) and the current constant-total allocation, then generates the endpoint's seeded Dirichlet draws and scores winning-margin CRPS across all four lead times exactly as `scripts/evaluate_mayoral_endpoint.py` does. As its own correctness check, the reconstructed `newCRPS` reproduces the after-change bridge per-cycle numbers and `oldCRPS` the before-change numbers.

The winning-margin CRPS scores, for each Election Outcome Draw, the gap between the top two shares in that draw (whichever candidates they are) against the realized top-two gap. Because that gap is an order statistic bounded below by zero, its mean sits well above the point difference of the two leaders; the comparison below is between allocations, holding that definition fixed.

## Results

| Cycle | Realized margin | Old predicted margin mean | New predicted margin mean | Old concentration | New concentration | Old margin CRPS | New margin CRPS |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2014 general | 0.0654 | 0.1448 | 0.1512 | 24.7 | 27.3 | 0.03837 | 0.04229 |
| 2018 general | 0.3990 | 0.3162 | 0.3115 | 28.2 | 29.9 | 0.05512 | 0.05523 |
| 2022 general | 0.4415 | 0.3847 | 0.3743 | 27.0 | 28.3 | 0.04238 | 0.04454 |
| 2023 by-election | 0.0472 | 0.1423 | 0.1759 | 88.4 | 110.8 | 0.06294 | 0.09511 |

Two structural facts explain why 2023 is the outlier:

1. **Field size.** With 102 candidates and a large omitted set, the difference between allocating ~24% to the tail (old) and ~9% (new) is large, so the leaders' shares — and their gap — move much more than in the small general-election fields, where the two allocations nearly coincide.
2. **Concentration instability.** The single global Dirichlet concentration is fit on the training cycles. When 2023 is held out, training is the three general elections, whose smaller candidate-share errors imply a very tight distribution (~88–111). When 2023 is *in* training (every other fold), its poll-to-result volatility pulls the fitted concentration down to ~28. The endpoint is thus most over-confident on exactly the cycle whose result was least like the generals.

## What can and cannot be inferred

### Supported by the observed record

- ADR 0038's allocation improves candidate-share calibration in every cycle and does not, on its own, create the margin problem; it removes a compression that was offsetting a separate over-prediction.
- The endpoint over-predicts the winning margin and is over-confident for the one close, large-field contest in the corpus. The prior count-scaling's better 2023 margin score depended on a tail mass the evidence does not support ([candidate-tail-choice-set-scaling.md](candidate-tail-choice-set-scaling.md)).

### Not established by these data

- **This rests on one contest.** The margin regression is concentrated in a single by-election with an unusually long ballot and a late-tightening race. Its magnitude cannot be generalised from n=4 cycles, one of which is the case in question.
- **The concentration diagnosis is provisional.** A global concentration that swings from ~28 to ~111 depending on whether one cycle is in-fold is unstable, but four cycles cannot separate "concentration model is wrong" from "2023 is genuinely more volatile than the generals."
- **No new tail policy follows.** Nothing here argues for re-inflating the tail; that would re-introduce the calibration defect ADR 0038 fixed in order to mask a different one.

## Recommendation

ADR 0038 stands. The winning-margin regression is a symptom of a distinct, pre-existing defect — the endpoint's over-confident, over-wide winning-margin forecast in close large-field races — and should be pursued as its own investigation rather than patched by the tail. The two candidate levers, each warranting its own spec and ADR, are: (1) the global single Dirichlet concentration, which is field-size-sensitive and unstable across folds and is the larger contributor to the 2023 penalty; and (2) the point margin itself, which may not model enough poll-to-result compression. Both should be evaluated on whole Held-Out Election Cycles under ADR 0030, and neither should be tuned to the 2023 number in isolation.

## Reproducibility notes

- `scripts/diagnose_margin_regression.py` — reproduces every number above (`uv run scripts/diagnose_margin_regression.py`), including the old/new correctness check against `scripts/evaluate_mayoral_endpoint.py`.
- Realized margins and leader identities are read from the canonical historical corpus via `backend/model/historical_mayoral.load_historical_mayoral_corpus` and `build_historical_mayoral_evaluation_cycles` at the ADR 0030 lead-time grid.
