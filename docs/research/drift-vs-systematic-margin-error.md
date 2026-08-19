# Is the endpoint's margin uncertainty over-wide, and does it converge as the election nears?

**Research date:** 2026-08-19
**Scope:** The six regular Toronto mayoral cycles (2003/2006/2010/2014/2018/2022), firm-balanced bridge endpoint, LOOCV. The 2023 by-election is report-only (ADR 0040) and excluded.
**Purpose:** A from-first-principles interrogation of whether the Dirichlet endpoint is the right uncertainty model asked: could a Markov / Gaussian-process / hidden-Markov *trajectory* model — which make forecast uncertainty shrink natively as steps-to-election run out — beat the single-concentration Dirichlet? This note records the two measurements that settled it and motivated the ADR 0042 recalibration. It supersedes the n=4-era [mayoral-concentration-overconfidence.md](mayoral-concentration-overconfidence.md).

## Findings in brief

- **A trajectory model buys nothing here, because there is no convergence to model.** The intuition that a poll→election has a shrinking number of step changes (which Markov/GP encode natively) is correct in general but does not bite on Toronto data: the poll-to-result margin miss is **systematic** (house effects, turnout-model error, undecided allocation), locked in weeks out, not **drift** the final poll resolves. All three predictions of the "drift structure exists" hypothesis come back null (below). A **lead-flat concentration is vindicated**; no κ(t).
- **But the concentration is uniformly over-dispersed.** The margin 80% band half-width is ≈2.4× the mean absolute margin error (a calibrated near-Gaussian band sits near 1.6×), and the central-80% margin interval covers all six realizations. This is the *opposite* reading of the same 100%-coverage the prior note saw at n=4 and mis-read as good calibration — 100% coverage of an 80% interval is over-width, not calibration.
- **The cause is the moment-match estimator, and it cannot self-correct.** `_fit_concentration` matched model simplex spread to mean squared point error, which includes the ≈0.06 systematic point bias; absorbing bias into variance deflates κ and widens draws. Re-deriving κ by the same estimator on held-out training data picks a scale that goes *wider still* (t≈−8.5 worse margin CRPS) — it reads the bias as more variance to cover.
- **The fix is a uniform tightening, and decoupling is unnecessary.** A global κ scale of ≈1.5–3× improves margin CRPS ~8%; crucially it also *improves* the guard metrics (share CRPS, and winner log-score) rather than breaking them, so the margin need not be decoupled from the share vector. ADR 0042 adopts a **margin-PIT-calibrated** scale (not a proper-score objective, to avoid circularity with the reliability gate).

## Method

Three throwaway probes, each reusing the real endpoint fit under LOOCV over the six regular cycles at the (12, 7, 3, 1)-day lead grid:

1. **Drift vs systematic** — per (cycle, lead): point margin, realized margin, Dirichlet 80% band, coverage, PIT. Tests: (a) does over-coverage concentrate at short lead; (b) does the miss correct as the poll nears (corr and magnitude ratio of err@L12 vs err@L1); (c) a floor+slope fit of squared margin error on days-remaining.
2. **Margin tightening** — a global-κ scale sweep (all draws), a decoupled sweep (margin/close draws only, guards held at κ), and a leakage-free scale fit by matching training margin-error variance, scored on margin CRPS, 80% coverage, winner log-score, share CRPS, close Brier.
3. Confirmation via `scripts/evaluate_mayoral_endpoint.py` after implementing the ADR 0042 concentration.

The winning-margin is top1−top2 of each Election Outcome Draw; CRPS scores it against the realized gap; PIT dispersion is mean |PIT − 0.5| (0.25 under a calibrated/uniform forecast).

## Results

### (1) Drift vs systematic — no convergence to recover

| lead | 80% coverage | mean 80% width | mean \|margin err\| |
|---|---|---|---|
| 12d | 6/6 | 0.294 | 0.062 |
| 7d | 6/6 | 0.286 | 0.056 |
| 3d | 6/6 | 0.292 | 0.065 |
| 1d | 6/6 | 0.288 | 0.059 |

Over-coverage is uniform across lead (not worse at short lead); the actual error does not shrink toward election day. Within-cycle, the miss does not correct: **corr(err@L12, err@L1) = +0.73**, mean|err@L1|/mean|err@L12| = **0.95** (only 2010 shows a genuine drift sign-flip). The floor+slope fit gives a systematic floor 0.00456 (RMSE 0.068) and a drift slope of **−0.00005/day** — essentially zero and wrong-signed. Systematic error dominates.

### (2) Margin tightening — the whole simplex is under-confident

Global scale (λ on all draws): margin CRPS 0.03771 (λ1.0) → ~0.0346 (λ1.5–2.5) → 0.0356 (λ4.0); winner log-score 0.165→0.081; share CRPS 0.00470→0.00455; coverage 24/24 until λ4 (22/24). Every metric improves with tightening. The decoupled sweep holds the guards constant by construction but is unnecessary given the global result. The leakage-free variance-match fit picks λ<1 for five of six folds and **worsens** margin CRPS (0.0377→0.0447, t≈−8.5) — the estimator matches spread to bias-inflated error, confirming the moment-match is the culprit.

### (3) Post-ADR-0042 confirmation

Calibrated κ rises ≈34–38 → ≈90–120 on over-wide folds, loosens the drop-2003 fold 93→77 (cross-fold spread 2.8×→1.6×). Regular-population qualification: margin CRPS **0.03585** vs comparator 0.04001 (5/6 improved); reliability **0.11452 / 0.05061 / 0.00436** ≤ frozen 0.24100 / 0.07463 / 0.00501. Still qualified, by more.

## Disposition

Implemented as **ADR 0042**: the concentration is a PIT-calibrated moment anchor, lead-flat, guarded. Adversarial caveats carried into the ADR: **n=6**; the winner log-score gain is **confounded by a zero-upset sample** (every regular cycle won by the poll leader) and is discounted — margin CRPS, close Brier, and share CRPS carry the case; and at n=6 realized coverage cannot independently confirm the tightening is calibrated (nothing misses until the scale exceeds ×4), so the scale is bounded and the qualification ladder, not the PIT statistic, is the arbiter. Trajectory families (Markov/GP/HMM) are rejected for this corpus — no drift structure and n=6 cannot identify sequence dynamics — and remain candidates only if the corpus later gains dense within-cycle polling. Probes were throwaway (scratch); this note is their primary record.
