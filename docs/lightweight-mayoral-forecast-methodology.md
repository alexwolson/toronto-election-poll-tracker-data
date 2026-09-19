# Lightweight mayoral forecast — methodology

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
  are used (5 polls, Forum 2026-07-29 → Liaison 2026-09-05).

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

## Result (as of 2026-09-19, 37 days out)
| Candidate | Share | Win probability | Band |
|---|---|---|---|
| Chow | 49 % | **~85.5 %** | 70–<90 % |
| Bradford | 38 % | **~14.5 %** | 10–<30 % |
| Alexander | 10 % | **~0 %** | 0–<5 % |

**Bradford's ~14.5% decomposes as** ≈ +4.7 pt polling error, +4.6 pt campaign drift, +5.2 pt
Alexander consolidation. Chow–Bradford margin median +9 pt (90% CI [−5, +23]); close-result ~27%.

## Sensitivity & robustness
- **Assumption variants** (published as schema-v3 sensitivity): stable → Chow ~96 %, central →
  85.5 %, volatile → ~76 %. Variants scale the three components together.
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
