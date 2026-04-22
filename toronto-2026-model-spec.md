# Toronto 2026 Municipal Election Projection Model

## Model Specification v0.2

---

## Overview

This document describes the projection model for the 2026 Toronto municipal election, covering both the mayoral race and all 25 ward-level council races. The model is designed to be transparent about its assumptions, honest about its limitations, and useful to voters trying to understand which races matter.

The model draws methodological inspiration from Philippe J. Fournier's 338Canada for federal and provincial projections, and from Matt Elliott's Council Defeatability Index for ward-level incumbent vulnerability assessment. Elliott's methodology is used with credit.

### Design Principle: Field Agnosticism

The model is designed to be robust to different mayoral fields. As of the time of writing, Brad Bradford is the only declared mayoral candidate. Olivia Chow is widely expected to seek re-election but has not declared. John Tory, who had been widely speculated as a potential entrant, has confirmed he will not run. Anthony Furey has also confirmed he will not run. Other potential candidates include Ana Bailao, Josh Matlow, and Marco Mendicino.

Rather than building the model around an assumed two-candidate matchup, the model is parameterised to work with whatever mayoral field materialises. Ward-level lean is computed for any candidate with historical ward-level data. The coattail mechanism is anchored on the incumbent mayor's record, not on a specific challenger. The model can produce projections under different field scenarios and adapts as the field takes shape.

---

## What the Model Produces

For each ward, the model outputs:

- A **race classification**: safe incumbent, competitive, or open seat
- For competitive and open races, **approximate win probabilities** for viable candidates, presented with wide uncertainty bands
- The **key factors** driving the classification (vulnerability score, challenger strength, mayoral coattail direction)

At the city level, the model produces:

- **Mayoral polling aggregation** with trend lines for all tracked candidates
- **Council composition projections** under different mayoral outcome scenarios

The model does not produce precise vote share estimates for individual candidates. The available data does not support that level of precision, and presenting false precision would be misleading.

---

## Data Sources

**Electoral history (Toronto Open Data)**
- 2018 and 2022 ward-level council results by candidate
- 2023 mayoral by-election results by ward
- 2018 and 2022 mayoral results by ward
- Candidate registrations and financial filings for 2026

All electoral data uses the current 25-ward boundaries, which took effect in 2018. Pre-2018 data on the former 44-ward boundaries is excluded to avoid the complexity and noise of boundary reaggregation.

**Council voting and analysis data (City Hall Watcher)**
- Matt Elliott's council voting scorecard, covering both the Chow mayoralty and the Tory mayoralty, providing quantitative alignment scores for each sitting councillor under both mayors
- Matt Elliott's Council Defeatability Index, providing incumbent vulnerability scores based on vote share, electorate share, and ward growth

**Polling data**
- Published mayoral polls from all firms, collected manually

**Census and demographic data**
- Ward population estimates and growth since 2022

---

## Part 1: Ward Mayoral Lean

Each ward receives a lean score for every mayoral candidate who has historical ward-level data on the current 25-ward boundaries (2018 onward). The lean measures how much more or less support a candidate receives in a given ward relative to their city-wide result.

For each election where a candidate ran, compute the ward-level deviation from their city-wide result:

$$
\delta_{w,e}^c = S_{w,e}^c - S_{\text{city},e}^c
$$

Where $S_{w,e}^c$ is candidate $c$'s vote share in ward $w$ in election $e$, and $S_{\text{city},e}^c$ is their city-wide vote share in that election.

Average across all available elections for each candidate. All elections are weighted equally.

**Available data by candidate (25-ward boundaries only):**
- **Olivia Chow**: 2023 (1 election, ~37% city-wide)
- **John Tory**: 2018, 2022 (2 elections, ~63% and ~62% city-wide)
- **Brad Bradford**: 2023 (1 election, ~4% city-wide)
- **Ana Bailao**: 2023 (1 election, ~18% city-wide)
- **Josh Matlow**: 2023 (1 election, ~3% city-wide)
- **Anthony Furey**: 2023 (1 election, ~6% city-wide)

This produces a lean value $L_w^c$ for each candidate $c$ in each ward $w$. Positive means the ward over-indexes for that candidate relative to the city; negative means it under-indexes.

### Data Quality by Candidate

The reliability of ward lean estimates varies substantially by candidate. Candidates with higher city-wide vote shares produce more meaningful ward-level deviations: a candidate who received 37% city-wide has enough votes in each ward to produce a reliable geographic pattern. A candidate who received 3-4% city-wide may show ward-level variation that is largely noise rather than signal.

For this reason, ward lean estimates are categorised by reliability:
- **High reliability**: Tory (two elections, high vote share), Chow (one election, high vote share), Bailao (one election, moderate vote share)
- **Moderate reliability**: Furey (one election, low-moderate vote share)
- **Low reliability**: Bradford, Matlow (one election, very low vote share)

Low-reliability lean estimates should be used with caution. For candidates with very low vote shares, the model may treat ward lean as effectively uniform (no meaningful geographic pattern) rather than using noisy estimates that could mislead.

### Pairwise Ward Lean

For any two-candidate comparison, the relative ward lean is:

$$
L_w^{a \text{ vs } b} = L_w^a - L_w^b
$$

This can be computed for any pair of candidates who both have ward-level data. It is not hard-coded to any specific matchup. Pairwise leans are most meaningful when both candidates have high- or moderate-reliability individual leans.

---

## Part 2: Incumbent Vulnerability

For each incumbent seeking re-election, compute a vulnerability score based on the methodology developed by Matt Elliott's Council Defeatability Index. The score is a composite of three factors:

1. **Vote share in 2022**: Lower vote share indicates higher vulnerability.
2. **Electorate share in 2022**: Votes received as a proportion of all eligible voters in the ward (not just those who turned out). A low electorate share means the incumbent won with the support of a small fraction of the ward's population.
3. **Ward growth since 2022**: Population growth in the ward since the last election, which may have changed the composition of the electorate in ways that erode the incumbent's previous margin.

These three factors are combined into a single defeatability score $D_w$. Higher scores indicate greater vulnerability.

### By-Election Incumbents

Several current councillors were elected in mid-term by-elections rather than in 2022 (e.g., Kandavel in Ward 21, Shan in Ward 24, and whoever holds Ward 15 following Robinson's death). These councillors do not have 2022 results, so the standard defeatability score cannot be computed.

For by-election incumbents, the model substitutes:
- **By-election vote share and electorate share** in place of 2022 figures. By-elections typically have lower turnout and different competitive dynamics than general elections, so these figures are noisier proxies. This is acknowledged in the ward's projection.
- **Ward growth since the by-election** rather than since 2022.

By-election incumbents are flagged as having higher baseline uncertainty in their defeatability scores. In practice, they are also likely to be more vulnerable than general-election incumbents simply because they have had less time to build the incumbency advantages (name recognition, constituent service record, fundraising base) that protect long-serving councillors.

---

## Part 3: Mayoral Coattail Adjustment

The mayoral race creates a city-wide dynamic that can help or hurt ward-level candidates. The coattail mechanism is anchored on the incumbent mayor's record and popularity, not on a specific two-candidate matchup. This makes it robust to different mayoral fields.

### Core Logic

The incumbent mayor's record is the thing council candidates are most likely to be judged against. Councillors who have been strong allies of the mayor benefit when the mayor is popular in their ward and suffer when the mayor is unpopular. This dynamic exists regardless of who challenges the mayor.

### Councillor Alignment Scores

Matt Elliott's council voting scorecard covers both the Chow mayoralty and the Tory mayoralty. This gives us two alignment scores for each sitting councillor:

- $A_w^{\text{Chow}}$: how often the councillor voted with Mayor Chow
- $A_w^{\text{Tory}}$: how often the councillor voted with Mayor Tory

These serve two distinct purposes in the model.

**For the coattail calculation**, the councillor's alignment with the incumbent mayor ($A_w^{\text{Chow}}$ when Chow is the incumbent) is the direct input. Councillors who vote with the mayor more often are more exposed to the mayor's popularity or unpopularity.

**For understanding councillor ideology**, the differential between the two scores is more informative:

$$
\Delta_w = A_w^{\text{Chow}} - A_w^{\text{Tory}}
$$

This differential characterises where the councillor sits on the ideological spectrum that the two mayoralties define:
- A large positive differential means the councillor is genuinely on the Chow end of the spectrum.
- A large negative differential means they are genuinely on the Tory end.
- A differential near zero means they are pragmatic centrists who vote with whoever is mayor, and are largely insulated from coattail effects.

The differential is useful for understanding councillor positioning regardless of the mayoral field. Although Tory is not running in 2026, the Tory-era voting record tells us something real about where each councillor sits ideologically. The differential also informs the candidate alignment classification in Part 4: a councillor with a strong Tory-era differential facing a Chow-aligned challenger is a meaningfully different race from the reverse.

### Coattail Calculation

The coattail adjustment depends on the incumbent mayor's estimated popularity in each ward.

$$
C_w = (A_w^{\text{incumbent}} - \bar{A}^{\text{incumbent}}) \times P_w^{\text{incumbent}} \times \gamma
$$

Where:
- $A_w^{\text{incumbent}}$ is the councillor's alignment with the incumbent mayor (currently Chow)
- $\bar{A}^{\text{incumbent}}$ is the average alignment across all councillors (subtracting this centres the score so that a councillor with average alignment gets no coattail effect, while those above or below average are helped or hurt)
- $P_w^{\text{incumbent}}$ is the incumbent mayor's estimated relative strength in the ward compared to their city-wide average, derived from the ward mayoral lean (Part 1) adjusted by current polling. Specifically: the mayor's base ward lean $L_w^{\text{incumbent}}$ is scaled by the mayor's current polling position relative to a neutral baseline. When the mayor is polling well city-wide, positive-lean wards get a boost and negative-lean wards are penalised less. When the mayor is polling poorly, the reverse applies.
- $\gamma$ is the coattail strength parameter

**The coattail strength parameter $\gamma$ is set editorially at a "medium" level.** This is a journalistic judgment, not a statistically estimated quantity. We do not have sufficient data to estimate coattail effects in Toronto municipal elections empirically.

In practical terms, "medium" is calibrated so that a councillor with well-above-average alignment with the incumbent mayor, in a ward that leans 10+ points against the mayor, would see their win probability shift by roughly 5-10 percentage points compared to a model with no coattail effect. For centrist councillors or wards near the city-wide average, the effect is negligible. This means coattails can push a borderline race from "leaning safe" to "competitive," but cannot on their own turn a safe seat into a likely loss.

The parameter is documented here for transparency.

The coattail adjustment can help or hurt an incumbent councillor:
- A Chow-aligned councillor in a ward where Chow is popular receives a boost.
- A Chow-aligned councillor in a ward where Chow is unpopular receives a penalty.
- A centrist councillor ($A_w^{\text{incumbent}} \approx \text{average}$) receives minimal coattail effect.
- The differential alignment score provides additional context: a councillor who was highly aligned with Tory and poorly aligned with Chow is implicitly anti-incumbent and may benefit from anti-Chow sentiment.

### Behaviour Under Different Mayoral Fields

**If Chow runs for re-election (most likely scenario):** The coattail mechanism operates at full strength. Chow's record is the reference point. Councillor alignment with Chow is the primary driver. The ward lean for whichever candidate(s) challenge her provides the geographic pattern.

**If Chow does not run (unlikely but possible):** There is no incumbent on the ballot. The coattail mechanism weakens substantially, as an open mayoral race does not create the same "referendum on the mayor" dynamic. The model reduces $\gamma$ or sets the coattail adjustment to near zero.

**Tory-era scorecard data remains valuable despite Tory not running:** The Tory-era scorecard data is not dependent on Tory being a candidate. It remains useful for understanding councillor ideology. The differential alignment tells us who is ideologically committed versus who is a centrist, which informs vulnerability regardless of the mayoral field.

---

## Part 4: Challenger Viability Classification

Each challenger is classified into one of three tiers based on two signals: fundraising and name recognition.

### Fundraising

Fundraising totals and donor counts are drawn from the City of Toronto's public financial filings. The key metric is the challenger's fundraising relative to the incumbent and to other challengers in the ward.

Fundraising thresholds for tier classification are calibrated against historical data from 2018 and 2022 Toronto elections, examining what levels of fundraising were associated with competitive challengers versus also-rans.

### Name Recognition Tier

Each candidate is assigned a name recognition tier through editorial judgment:

- **Well-known**: Has held elected office in the area, has run city-wide before with significant vote share, or is a current school board trustee in the ward.
- **Known**: Has run for office before at any level, is publicly active in a recognised community organisation, or has significant media presence.
- **Unknown**: Default tier for candidates with no prior public profile.

These assignments are published with justifications and are subject to revision as campaigns develop.

### Tier Matrix

Viability is determined by the combination of fundraising and name recognition:

|                | Low fundraising | High fundraising |
|----------------|-----------------|------------------|
| **Unknown**    | Also-ran        | Competitive      |
| **Known**      | Competitive     | Frontrunner      |
| **Well-known** | Frontrunner     | Frontrunner      |

The specific fundraising thresholds that define "low" and "high" will be calibrated from historical data and documented separately.

### Candidate Mayoral Alignment

Each viable council candidate is assigned a position on the mayoral spectrum through editorial judgment, based on endorsements, public statements, and campaign positioning.

Because the model does not assume a specific two-candidate mayoral matchup, alignment is expressed relative to the actual mayoral candidates in the race. If the field is Chow vs Bradford vs Bailao, a council candidate might be described as Chow-aligned, Bradford-aligned, Bailao-aligned, or unaligned. If the field narrows or changes, the alignment categories adapt.

This alignment interacts with the ward's mayoral lean (for the relevant candidate) to produce a strength signal: a candidate aligned with a mayoral contender who is strong in the ward gets a boost.

### Vote Splitting Penalty

When multiple viable challengers share a similar mayoral alignment, the strongest among them receives a penalty to their effective strength score, reflecting the likelihood that they are competing for the same pool of voters. This penalty is applied as a reduction to the candidate's strength in the simulation, not as a precise vote-splitting calculation.

---

## Part 5: Ward Race Model

### Ward Classification

Each ward is classified into one of three categories:

- **Safe incumbent**: Incumbent is running for re-election to council, has low defeatability, and faces no frontrunner or competitive challengers. The incumbent is assigned a high win probability directly. No simulation is run.
- **Competitive incumbent**: Incumbent is running for re-election to council and at least one challenger is classified as frontrunner or competitive. The full model runs.
- **Open seat**: No incumbent is running for re-election to council. The open seat sub-model runs.

Under Ontario municipal election rules, candidates cannot run for both mayor and councillor simultaneously. When a sitting councillor enters the mayoral race, their ward is automatically classified as an open seat. Currently, Bradford's entry into the mayoral race makes Ward 19 (Beaches-East York) an open seat. If other sitting councillors (e.g., Matlow) enter the mayoral race, their wards would similarly become open seats.

### Stage 1: Incumbent Win Probability (Competitive Wards)

For competitive incumbent wards, the probability the incumbent wins is:

$$
P(\text{inc wins}) = \text{logit}^{-1}(\beta_0 + \beta_1 D_w + \beta_2 C_w + \beta_3 F_w^* + \epsilon_w)
$$

Where:
- $D_w$ is the defeatability score
- $C_w$ is the coattail adjustment (see Part 3)
- $F_w^*$ is the effective strength of the top challenger (incorporating fundraising, name recognition, alignment with ward lean, and any vote-splitting penalty)
- $\epsilon_w$ is a noise term calibrated to the historical base rate of incumbent defeat in Toronto municipal elections
- $\beta_0$ encodes the base rate of incumbent victory

The parameters are set through informed judgment based on political science literature on municipal incumbency advantage, calibrated against historical Toronto results as a sanity check. They are not formally fitted to Toronto data, as the sample size (approximately 50 ward-elections on current boundaries, with very few incumbent defeats) is insufficient for reliable statistical estimation.

### Stage 2: Challenger Win Distribution (Conditional on Incumbent Losing)

When the simulation produces an incumbent loss, the winning challenger is determined by a softmax over viable challengers:

$$
P(\text{challenger } j \text{ wins} \mid \text{inc loses}) = \frac{e^{\mu_j}}{\sum_k e^{\mu_k}}
$$

Where $\mu_j$ is challenger $j$'s strength score. The strength function is:

$$
\mu_j = \mu_{\text{tier}(j)} + w_f \cdot \log(F_j) + w_a \cdot (L_w^{m(j)}) + \text{split}_j
$$

Where:
- $\mu_{\text{tier}(j)}$ is a baseline value determined by the candidate's viability tier (frontrunner > competitive; also-rans are excluded)
- $F_j$ is the candidate's fundraising total, log-transformed (the difference between \$5K and \$50K matters more than between \$150K and \$200K)
- $L_w^{m(j)}$ is the ward's lean toward the mayoral candidate that challenger $j$ is aligned with (see Parts 1 and 4). For unaligned candidates, this term is zero.
- $\text{split}_j$ is the vote-splitting penalty (negative or zero), applied when another viable candidate shares the same mayoral alignment
- $w_f$ and $w_a$ are weights set by editorial judgment

The same strength function is used in the open seat sub-model. The tier baselines, weights, and splitting penalty magnitude are set through informed judgment, documented separately, and calibrated against historical Toronto results as a sanity check.

Also-ran candidates are excluded from this stage. Their collective vote share is a source of noise but they are not modelled as potential winners.

### Open Seat Sub-Model

Open seat races use the same challenger strength function but with no incumbent baseline. All viable candidates compete directly:

$$
P(\text{candidate } j \text{ wins}) = \frac{e^{\mu_j}}{\sum_k e^{\mu_k}}
$$

With wider noise terms reflecting the genuinely higher uncertainty in these races.

Additional signals for open seats:
- **Departing councillor endorsement**: A boost to the endorsed candidate's strength score, reflecting the transfer of name recognition, campaign infrastructure, and voter trust.
- **Ward mayoral lean**: Plays a larger role than in incumbent races, since voters have less candidate-specific information and the mayoral race provides a stronger framing effect.

Open seat projections carry higher uncertainty than incumbent race projections. This is stated explicitly on the site.

---

## Part 6: Ward-Level Polling Override

Ward-level polling is rare in Toronto municipal elections, but if it becomes available for any ward, it provides direct evidence of voter preferences that is far more informative than the structural model's indirect signals. The model includes an optional override mechanism that activates when ward-level polling data exists.

### Blending Polls with the Structural Model

When a ward-level poll is available, the model blends the poll-based estimate with the structural estimate:

$$
P(\text{inc wins})_w^{\text{final}} = \alpha_w \cdot P(\text{inc wins})_w^{\text{poll}} + (1 - \alpha_w) \cdot P(\text{inc wins})_w^{\text{structural}}
$$

Where $\alpha_w$ is the polling weight for ward $w$, and ranges from 0 (no polling, structural model only) to near 1 (recent, high-quality polling dominates).

The polling weight $\alpha_w$ depends on:
- **Recency**: A poll from the past week receives high weight. Weight decays over time, following the same exponential decay logic as the mayoral aggregator.
- **Sample size**: A larger sample produces a more reliable estimate. Smaller samples receive proportionally less weight.

When no ward-level polling exists (the default case for most or all wards), $\alpha_w = 0$ and the model relies entirely on the structural estimate.

### Indirect Calibration

A ward-level poll also serves as a calibration check on the structural model. If polling reveals that a ward the model classified as "safe" is actually competitive, this may indicate:

- The coattail effect is stronger or weaker than assumed
- A challenger is stronger than their fundraising and name recognition suggest
- There is a city-wide mood shift the model is not capturing
- There are ward-specific local dynamics the model cannot observe

If the discrepancy appears to be systematic (e.g., the model is consistently underestimating incumbent vulnerability), this may warrant an editorial adjustment to global parameters. If it appears idiosyncratic to the specific ward, only that ward's projection is updated.

Any such adjustments are documented and published.

### Application to Open Seats and Challenger Distributions

If ward-level polling provides candidate-level support estimates (not just incumbent win/lose), these can also inform the Stage 2 challenger distribution and the open seat sub-model. Polled candidate support levels would replace the fundraising and name-recognition-based strength estimates for that ward, with the same recency and sample-size weighting.

---

## Part 7: Simulation Engine

The simulation runs thousands of Monte Carlo draws to produce win probabilities and council composition distributions.

For each draw:

1. **Draw a mayoral outcome** from the polling distribution (see Part 8). The aggregated mayoral vote shares are used as the mean of a Dirichlet distribution, which ensures the drawn vote shares for all candidates sum to 100%. The concentration of the Dirichlet (controlling how much variance there is around the polling average) is derived from the polling average's effective sample size, which increases as more polls are aggregated. This draw includes all tracked mayoral candidates.
2. **Compute coattail adjustments** for each ward given this mayoral draw. When the drawn outcome shows the incumbent mayor performing poorly, councillors aligned with the incumbent are penalised. The magnitude depends on the councillor's alignment score and the ward's lean.
3. **For each competitive incumbent ward**, draw whether the incumbent wins or loses based on the adjusted win probability.
4. **If the incumbent loses**, draw which challenger wins from the conditional distribution.
5. **For each open seat**, draw the winner from the candidate strength distribution.
6. **Record the full council composition** for this draw.

Across all draws, the model produces:
- Per-ward win probabilities for each viable candidate
- Distribution over council composition under different mayoral outcome scenarios
- Sensitivity analysis showing how council composition shifts depending on who wins the mayoralty

The correlation structure is important: ward outcomes are not independent across the city. They are linked through the shared mayoral draw. In simulations where the incumbent mayor performs poorly, all mayor-aligned councillors are penalised simultaneously. This produces realistic joint distributions over council composition.

### Scenario Modelling

Because the mayoral field may not be finalised until well into the campaign, the simulation engine supports scenario analysis. Before the field is set, the model can produce projections under different assumptions:

- "If the field is Chow vs Bradford..."
- "If Bailao enters and the field is Chow vs Bradford vs Bailao..."
- "If Chow does not run..."

This allows the site to be useful and informative even while the mayoral field remains uncertain, rather than being dependent on a specific matchup materialising.

---

## Part 8: Mayoral Polling Aggregator

The mayoral polling aggregator tracks all declared and likely mayoral candidates. It is a recency-weighted average of published polls.

Each poll receives a weight that decays exponentially with age:

$$
w_i = e^{-\lambda \cdot \text{age}_i}
$$

Where age is measured in days and $\lambda$ is set to produce a half-life of approximately 10-14 days.

The aggregated vote share for each candidate is:

$$
\hat{V}_c = \frac{\sum_i w_i \cdot V_{c,i}}{\sum_i w_i}
$$

The aggregator also produces a trend line (simple moving average or LOESS) to show whether candidates are gaining or losing support over time.

**Design decisions:**
- No house effects adjustment. With a limited number of polls from a small number of firms, there is insufficient data to estimate systematic firm-level biases. If obvious patterns emerge during the campaign, adjustments may be applied editorially and documented.
- No likely voter adjustment. Differences in polling methodology (all adults vs. likely voters) are noted alongside each poll but not adjusted for.
- Polls testing different candidate fields are tracked separately. The site displays aggregations for the current most likely field, with scenario alternatives accessible. As candidates declare or withdraw, the primary aggregation updates to reflect the actual field.
- All tracked candidates are included. Bradford, as the only declared candidate, is tracked from the outset. Other candidates are added as they declare or as polling firms begin testing them.

Individual polls are displayed on the chart alongside the aggregated trend, so users can see the raw data.

---

## Part 9: Temporal Phasing

The model operates in three phases corresponding to the availability of data over the campaign timeline. The current phase is displayed prominently on the site.

**Phase 1 (pre-registration period):** The model shows structural factors only: incumbent vulnerability scores, ward mayoral leans (for all candidates with historical data), and councillor alignment differentials. Output is limited to identifying which wards are structurally most likely to be competitive. No challenger data is available. Mayoral scenario analysis is available based on early or hypothetical polling.

**Phase 2 (registration through early financial filings):** Candidates have registered. The model incorporates name recognition tiers and any early fundraising signals. Ward classifications (safe/competitive/open) begin to take shape, but with high uncertainty due to incomplete financial data.

**Phase 3 (financial filings onward):** Full financial data is available. The model runs at full capacity with all inputs. Ward classifications firm up and win probabilities narrow.

The model's structure does not change between phases. It simply operates with fewer inputs in earlier phases and more in later phases. The phase label communicates to the user how much data is informing the projections.

---

## Assumptions, Limitations, and Editorial Judgments

This model makes several editorial judgments that are not derived from data:

1. **Coattail strength ($\gamma$)** is set at a "medium" level. There is no empirical basis for estimating this parameter in Toronto municipal elections.
2. **Name recognition tiers** are assigned by editorial judgment based on published criteria.
3. **Candidate mayoral alignment** is assigned by editorial judgment based on endorsements and public positioning, and adapts to the actual mayoral field.
4. **Model parameters** (weights on defeatability, challenger strength, etc.) are set through informed judgment, not statistical fitting, due to insufficient historical data.

Key limitations:

- The model has very few historical data points to learn from: approximately 50 ward-elections on current boundaries across two cycles, with a small number of incumbent defeats.
- Ward-level polling is essentially nonexistent. The model relies primarily on structural factors and campaign-period signals (fundraising, endorsements), not on direct measurement of voter preferences at the ward level. If ward-level polling becomes available for any ward, the model blends it with the structural estimate (see Part 6), and uses it as a calibration check on the broader model.
- The model cannot capture late-breaking dynamics: debate performances, scandals, last-minute endorsements, or get-out-the-vote efforts.
- Open seat projections carry substantially higher uncertainty than incumbent race projections.
- The coattail mechanism is anchored on the incumbent mayor. If the incumbent does not run, the coattail effect is substantially weakened and the model loses one of its key signals for ward-level projections.
- Ward mayoral lean estimates vary substantially in reliability. Candidates with low city-wide vote shares in their only election (Bradford, Matlow) produce lean estimates that may be indistinguishable from noise. See the data quality discussion in Part 1.
- The mayoral field may not be finalised until well into the campaign. Projections produced under scenario assumptions should be interpreted as conditional ("if the field is X, then..."), not as unconditional forecasts.
- By-election incumbents have noisier defeatability scores and likely weaker incumbency advantages than councillors elected in general elections. See Part 2.
- The model does not explicitly account for **turnout variation** across wards. Low-turnout wards may behave differently from high-turnout wards, and turnout interacts with incumbency advantage (incumbents may benefit more from low turnout). Turnout modelling is a potential future enhancement but is not included in the current version.

All editorial judgments are documented and published. The model's methodology is open for scrutiny and the projection outputs should be interpreted in light of these stated limitations.

---

## Credits and Acknowledgments

- **Matt Elliott / City Hall Watcher**: Council Defeatability Index methodology and council voting scorecard data, used with permission.
- **338Canada / Philippe J. Fournier**: Methodological inspiration for the overall projection framework.
- **City of Toronto Open Data**: Electoral results, candidate registrations, and financial filings.
- **Liaison Strategies and other polling firms**: Published mayoral polling data.