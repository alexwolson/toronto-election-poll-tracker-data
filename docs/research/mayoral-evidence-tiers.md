# Mayoral evidence tiers across the historical corpus, and the ≥3-cycle unlock

**Research date:** 2026-08-19
**Scope:** The seven historical mayoral cycles (2003–2023), classified by the Mayoral Evidence Tier (ADR 0033) at each cycle's Final-Ballot boundary; and the live 2026 cycle.
**Purpose:** Freeze the ADR 0005 historical-unlock counts for the M3 publication layer — a (quantity, tier) may publish only if that tier appeared in ≥3 distinct Held-Out Election Cycles — and record whether any mayoral quantity is history-blocked. Supports `backend/model/mayoral_publication_gates.py`.

## Findings in brief

- **No mayoral quantity is history-blocked.** The post-Final tier (M2) appeared in **7** cycles and the replicated-post-Final tier (M3) in **6**, both clearing the ≥3-cycle floor. So Close-Result and Incumbent-Defeat (M2 floor) and challenger Candidate-Win (M3 floor) are all unlocked in this model version.
- **The live 2026 cycle is M1 (Pre-Final Polling) today.** Nominations close 2026-08-21 18:00 UTC; all 19 citywide 2026 samples end by 2026-08-05, so every one is pre-Final. Per ADR 0033 **no 2026 mayoral predictive quantity may publish** until post-Final replicated polling arrives — the correct, fail-closed behaviour, not a defect.
- **Only 2022 fell short of M3** (a single post-Final sample that cycle), consistent with its thin post-nomination polling noted elsewhere.

## Method

`classify_mayoral_evidence_tier` (ADR 0033) applied per cycle, using each cycle's `final_ballot_known_by_date` from `_BALLOT_TIMING` as the boundary: a sample is post-Final when its fieldwork interval overlaps or follows that boundary. Field-level tier = M0 (no qualifying poll) → M1 (all pre-Final) → M2 (≥1 post-Final) → M3 (≥3 samples, ≥2 pollsters, ≥2 post-Final). Counts are frozen as literals in `mayoral_publication_gates.py` (ADR 0005); a gate change bumps the version and reruns this classification.

## Results

| cycle | qualifying samples | tier | post-Final (samples / pollsters) |
|---|---|---|---|
| 2003 | 3 | M3 | 3 / 3 |
| 2006 | 4 | M3 | 4 / 4 |
| 2010 | 9 | M3 | 9 / 5 |
| 2014 | 47 | M3 | 15 / 4 |
| 2018 | 11 | M3 | 10 / 4 |
| 2022 | 1 | **M2** | 1 / 1 |
| 2023 | 42 | M3 | 25 / 5 |
| **2026 (live)** | 19 | **M1** | 0 / 0 |

Cycles reaching **≥M2: 7**; **≥M3: 6**. Both ≥ 3 ⇒ every mayoral predictive quantity is history-unlocked.

## Disposition

Frozen into `MAYORAL_TIER_HISTORICAL_CYCLE_COUNTS` (M2→7, M3→6) with `MAYORAL_TIER_UNLOCK_MINIMUM_CYCLES = 3`. Re-examine when the corpus gains a cycle or when tier definitions change (new model version, ADR 0005). The 2026 M1 classification is the reason the finished M3 layer withholds every 2026 mayoral quantity today; it flips as post-Final replicated polling lands after 2026-08-21.
