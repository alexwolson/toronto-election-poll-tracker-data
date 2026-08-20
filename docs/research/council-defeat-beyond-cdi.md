# Can any available signal beat Matt Elliott's CDI for council incumbent defeat?

**Research date:** 2026-08-20
**Scope:** Toronto council incumbent defeat, backtested on the `defeatability-index` project's 154 incumbent-councillor races (2006–2022; 18 defeats, 7 outside 2018). Building on that project's finding that the equal-weight CDI is a weak screen (AUC 0.643, 95% CI [0.485, 0.782] — straddling chance) and that *fitting* weights makes prediction worse than a coin flip.
**Purpose:** Before committing to the candidate-level probabilistic Council Forecast designed in ADR 0009/0012/0019/0025/0026/0027, test whether any signal *available for 2026* adds **robust out-of-sample lift** over the CDI, on the boundary-stable cycles that 2026 resembles. If nothing does, a publishable incumbent-defeat probability cannot validate and Council v1 must take a different shape. Feeds ADR 0043.

**Pre-registered bar (fixed before running):** a lift counts only if it is *robust and consistent ex-2018* (2026 runs on stable boundaries; the 44→25 merger produced 11 of 18 defeats and will not recur), **and** the signal actually fires in enough 2026 wards to matter. A within-CI bump or an all-years artifact of 2018 is a *no*. **Guardrail:** with ~7 non-2018 defeats, even a real lift buys a sharper *screen* and better *description*, never a calibrated probability.

## Findings in brief

- **No available signal beats the CDI on the honest 2026 analog.** Four candidate signals were tested; all four are null or negative ex-2018. The CDI's chance-straddling ~0.64 is the frontier.
- **The ceiling is the data, not the features.** 5–7 incumbent defeats across four normal cycles (5.7% base rate) leaves almost nothing to learn; every ex-2018 bootstrap CI is enormous (the CDI itself cannot be distinguished from a coin flip). This is why *fitting* overfits and why no feature clears the bar.
- **Consequence:** a publishable incumbent-defeat probability cannot validate for 2026. Council v1 ships a descriptive race card + the CDI screen, not a forecast (ADR 0043).

## Method

Reused the `defeatability-index` backtest (`data/out/defeatability_index.csv`) joined to `historical_council_results.csv` for the full candidate field per ward-year. Cross-year candidate identity by token-set name matching (share ≥2 name tokens). Outcome: incumbent ran and was not re-elected. AUC (Mann–Whitney), 95% bootstrap CIs, all-years and ex-2018. Parameter-free equal-weight combinations only (per-year z-sum) — no fitted weights, which the source project already showed overfit. **Pipeline validated** by reproducing the project's published CDI AUC of 0.643 exactly. Only pre-election-knowable features were used (candidate *counts* and *prior* shares; year-Y vote shares are the outcome, never a predictor).

## Results (ex-2018 = 2026 analog; CDI baseline AUC 0.606)

| signal | AUC alone | CDI + signal | verdict |
|---|---|---|---|
| **Challenger quality** (faces a former/sitting councillor) | 0.478 | 0.566 | null — **worse** than CDI; 0 of 7 ex-2018 defeats faced one; fires in 1 of 25 wards for 2026 |
| **Field size** (candidates on the ballot) | 0.571 | 0.622 | within noise |
| **Field growth** (Δ candidates vs prior) | 0.450 | 0.612 | within noise |
| **Trajectory** (declining prior vote-share) | 0.279 / 0.354 | 0.434 / 0.538 | **worse** (n=66, 5 defeats) |
| **Mayoral coattails** | — | — | not run — see below |

Challenger quality *looked* additive all-years (combo AUC 0.685 vs CDI 0.643) but the entire lift is **2018** (2018-only combo 0.810; 8 of 11 defeats faced a former-councillor challenger — the forced incumbent-vs-incumbent merger). It vanishes ex-2018.

**Mayoral coattails were not run**, on three independent grounds: (1) ADR 0014 forbids the Council Forecast consuming mayoral polling/coattail estimates; (2) 2026 mayoral evidence is citywide-only, so it is identical across all 25 wards and cannot differentiate council races even in principle; (3) ward-level mayoral results in the tracker cover only 2018/2022/2023, so the sole ex-2018 normal cycle with ward mayoral data (2022) has a single council defeat — nothing to learn, and reconstructing the 44-ward cycles from raw poll-by-poll was not worth it for a result usable on none of those grounds.

**Illustration (Ward 11, University-Rosedale).** The archetypal "beyond-CDI" race — incumbent Saxe (won 2022 with 35.4%, by 123 votes in a 14-candidate open scramble) vs former councillor Layton (held this ward at 69.6% in 2018; three wins). The facts *look* like a strong challenger, but history says otherwise: **former-councillor challengers went 0-for-5 against sitting incumbents in normal cycles**. The facts cannot be adjudicated into a number — which is exactly why the product presents facts, not a call.

## Disposition

Recorded as **ADR 0043**: Council v1 is a descriptive race card + CDI screen, no probabilistic forecast. The probabilistic Council Forecast (ADR 0009 et al.) is not reversed — it is *deferred* behind genuinely new signal (the source project names challenger strength [tested here, null], fundraising [not published in-cycle], open-seat structure). Reopen this only when such signal is acquired and evaluated. Throwaway probes in scratch; this note is their durable record.
