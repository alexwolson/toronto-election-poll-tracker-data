# Lightweight mayoral forecast — methodology

> **Superseded (2026-09-21).** The published forecast is now produced by the compact joint
> model in the Backend repository (ADR 0054, `docs/mayoral-forecast-methodology.md` there).
> The runtime premise below was a hardware artifact: the heavy model ran at ~3 s/iteration
> on CPU. This document is kept as the record of the forecast shipped in `backend-2026-09-21.3`.

Built 2026-09-18/19 as the Sept-21 publication forecast after the heavy Monte-Carlo model
proved too slow to fit in time (~100–140 s/iteration → weeks). This model is deliberately
simple, transparent, and fits in ~0.1 s. Its distinguishing feature is that uncertainty is
**decomposed into three explicit, separately-calibrated mechanisms**, so the forecast can
show *why* the challenger has a chance rather than emitting one opaque probability.

## Code
- Model: `scripts/lightweight_mayoral/model.py` (pure NumPy; 8 unit tests in `test_model.py`).
- Pipeline: `scripts/build_lightweight_mayoral_forecast.py` → writes
  `data/processed/mayoral_forecast.json` (frontend feed, schema v3).
- Run: `uv run scripts/build_lightweight_mayoral_forecast.py`.

## Inputs
- Current-cycle polls: `data/raw/polls/polls.csv`.
- Viable field + election date: `data/raw/elections/live_cycle.json` (chow / bradford /
  alexander; election 2026-10-26; incumbent chow). Only polls covering the full viable field
  are used (6 polls, Forum 2026-07-29 → Mainstreet 2026-09-17; incl. Sarah McVie and Odessa
  Paloma Parker as recorded minor candidates, folded into the residual for the three-way forecast).

## Method
1. **Central support** = recency- and precision-weighted poll average (weight =
   sample size × 0.5^(days_old / 21)), renormalised over {field} + other.
2. **Three uncertainty mechanisms**, Monte-Carlo'd (200k draws), plurality winner among the
   named field ("other" is a residual bucket, never a winner):
   - **(1) Polling error** — symmetric per-candidate share shock (~4.5 pt); the polls are
     wrong about the race *now*.
   - **(2) Campaign drift** — symmetric shock for genuine opinion movement to election day
     (~3.5 pt/candidate).
   - **(3) Alexander consolidation** — *directional*. Each draw moves a soft fraction of
     Alexander's ~10% (drawn 30–70%, forced high with a small dropout probability) and splits
     it **55% Bradford / 20% Chow / 25% stays home**; the stay-home share leaves the voting
     electorate. Applied to the per-draw centre before the symmetric shocks.
3. The forecast returns win probabilities, vote-share bands, the Chow–Bradford margin
   distribution, and a **decomposition of the challenger's win probability** across the three
   mechanisms (nested, common-random-number attribution).

## Calibration (all evidence-anchored)
- **Polling error** ← *terminal* poll-vs-result error (final polls, ≤10 days out, 2014/18/23):
  margin RMSE ~6.5 pt. Isolates "polls wrong now" from movement.
- **Campaign drift** ← residual of the 5-weeks-out margin error (~8.7 pt total) beyond the
  terminal error, trimmed toward the quiet end (the race has been stable across 5 polls).
- **Alexander consolidation** ← three independent signals, then hedged:
  - Mainstreet **forced two-way** (Bradford 52 / Chow 48 in June 2026) ⇒ ~76% of the non-major
    vote would go to Bradford *if forced to choose* — an upper bound.
  - Alexander's entry **hurt Bradford** (Bradford ~40→32 on his July entry) ⇒ his base is
    Bradford-adjacent, so it flows back to Bradford if he fades.
  - **Conservative lane** (`challengers.csv` realigns down-ballot Conservatives into "Alexander's
    lane") ⇒ ideologically closest to Bradford.
  - **Hedge:** the race's own pollster (David Valentin, Liaison) argues his "anti-both" voters
    would largely *disperse or stay home*, not consolidate. So the split is set to 55% Bradford
    (well below the forced-choice 76%) with 25% staying home. Formal dropout is treated as
    low-probability / low-impact (he can't leave the ballot post-Aug-21; "I'm not going anywhere").
  - **Soft fraction — data-anchored** ← the Mainstreet Sept 2026 subscriber crosstab measures
    Alexander's vote as materially softer: only **33% "completely certain"** (vs Chow 50.5% /
    Bradford 47.5%) and **~29% movable** (might change / very likely / not sure) vs ~16–18% for the
    majors. So the movable ("soft") fraction is drawn over **0.29–0.55**: floor at the self-reported
    ~29%, ceiling for strategic consolidation as he fades. Note the nuance — his vote is *softer but
    still ~two-thirds firm*, so the movable pool is a minority.

## Result (as of 2026-09-19, 37 days out; polls through Mainstreet Sept 14–17)
| Candidate | Share | Win probability | Band |
|---|---|---|---|
| Chow | 46 % | **~84 %** | 70–<90 % |
| Bradford | 38 % | **~16 %** | 10–<30 % |
| Alexander | 10 % | **~0 %** | 0–<5 % |

**Bradford's ~16% decomposes as** ≈ +6.3 pt polling error, +5.0 pt campaign drift, +4.8 pt
Alexander consolidation. Chow–Bradford margin median ~+8 pt; close-result ~29%. The fresh
Mainstreet poll (Chow +8 decided) pulled the race tighter (Bradford up ~3 pt from 85.5/14.5);
the certainty data (Alexander mostly firm) then nudged consolidation down ~1 pt.

## Fundamentals / adversarial check (June 2026 subscriber report)
The horse-race lead likely *overstates* Chow's security — an independent counterweight to the
certainty finding above (which said her lead is firm). In June, Chow was **underwater on approval**
(~41% approve / 56% disapprove, net −15), **46% of voters were "definitely not voting for" her**
(vs only **25%** for Bradford — Bradford has far more headroom), and the city was **62% wrong-track**.
The field has also restructured hugely since February (John Tory era → Alexander three-way),
confirming high within-cycle volatility. These are **June (dated)** and September did *not* re-ask
approval, so we have **no current fundamentals** — the key gap to fill from the next poll. Not
hard-coded: used only to (a) cap confidence (argues against Chow much above ~85%), (b) corroborate
component 3's Bradford-ward direction, and (c) note Chow's realistic ceiling ~54% (her p95 band
~58% is a touch generous). Net effect: *higher confidence in ~84/16*, not a different number, since
the weak-fundamentals and firm-certainty signals roughly cancel.

## Sensitivity & robustness
- **Assumption variants** (published as schema-v3 sensitivity): stable → Chow ~94 %, central →
  ~84 %, volatile → ~75 %. Variants scale the three components together.
- **Robust to data choices**: half-life 14–35 d, dropping the latest poll, only-3-latest, and
  leave-one-firm-out keep Chow in the mid-80s (checked on the prior lumped model; re-verify if
  parameters change materially).

## Limitations / adversarial notes
- Calibration rests on only 3 historical races with comparable polls; the terminal/5-weeks
  split is thin.
- The Alexander split (55/20/25) is the most contested input and the one that most moves
  Bradford; it is a deliberate hedge between the forced-two-way (Bradford-heavy) and the
  pollster's "disperse/stay home" read. Sources:
  [CP24](https://www.cp24.com/local/toronto/2026/07/31/first-toronto-mayoral-poll-with-chris-alexander-suggests-his-candidacy-hurts-bradford/),
  [NOW Toronto / Valentin](https://nowtoronto.com/news/chris-alexander-suggests-leaving-mayoral-race-expert-weighs-in/).
- Named-composition polls vs full-ballot election shares differ in denominator; treated as
  comparable here (small residual in the current cycle).
