# Toronto Council Race Model v1

## What the public product means

The Council product deliberately separates two questions:

1. **Race assessment:** an evidence-based label — Safe, Competitive, or Open — describing how seriously a ward merits attention today.
2. **Election forecast:** a calibrated probability of each candidate winning. This is published only when the historical and current-election evidence passes every release gate.

Race status is not a probability. “Safe” means the current evidence does not trigger the Competitive rules; it is not a guarantee that the incumbent will win.

## Evidence retained for every ward

The public snapshot reports the incumbent or open-seat status, the registered candidate field, relevant prior ward results, structural vulnerability inputs, credible challenger evidence, and any published ward polling in its original denominator. Mayoral support is displayed only as electoral context. It does not currently change a ward’s race status or produce ward win probabilities.

### Ward polling

Polls are stored in long form. Candidates omitted from a poll are unobserved, not zero. Residual and undecided responses remain explicit and the reported ballot field is preserved.

For example, the current Ward 13 reading reports Chris Moise 35%, Daniel Tate 19%, Curran Stikuts 6%, and Other 40% among decided voters, with 45% undecided among all respondents. The model does not convert those figures into a synthetic “incumbent win share.”

## Race-assessment rule

Open wards are labelled **Open**. An incumbent ward is labelled **Competitive** when at least one documented trigger is present:

- structural defeatability is at least 55;
- structural defeatability is at least 40 and the ward has either a well-known challenger or a strong returning runner-up;
- a well-known challenger is registered;
- a returning runner-up has a sufficiently strong prior ward result; or
- an exact-current-field ward poll is available.

All other incumbent wards are labelled **Safe**. A generic editorial “known” label, registration alone, endorsement, or mayoral alignment alone cannot trigger Competitive status. Each public ward record includes the exhaustive reasons for its status. With the current data this produces 14 Safe, 9 Competitive, and 2 Open wards.

## Forecast research model

Historical councillor results from the City of Toronto were normalized across the 2003, 2006, 2010, 2014, 2018, and 2022 general elections. Only incumbent re-election cases with comparable ward boundaries are used: 2003→2006, 2006→2010, 2010→2014, and 2018→2022.

The current research set contains 121 incumbent cases and 8 defeats. A regularized logistic model uses only features that can be reconstructed consistently across those elections: prior vote share, prior margin, candidate-field size, returning-runner-up status, and first-term status. Leave-one-election-out validation currently gives:

| Method | Winner Brier score | Log loss |
|---|---:|---:|
| Research model | 0.0673 | 0.2897 |
| Incumbent base-rate baseline | 0.0643 | 0.2636 |

Lower is better. The research model does not beat the simple historical baseline, so it is not suitable for public candidate odds.

## Publication gates

Ward win probabilities and Council composition simulations remain unavailable unless all of these are true:

- nominations have closed and the candidate field is final;
- the calibration set contains at least 10 incumbent defeats;
- rolling/leave-one-election-out performance beats the incumbent base-rate baseline on the required scoring rules;
- probability calibration and uncertainty checks pass; and
- current ward evidence can be mapped to the calibrated features without undocumented editorial substitutions.

A failed gate produces an explicit unavailable status and reasons. It never produces zeroes, fixed caps, or editorially chosen probabilities. Because the same ward probabilities would feed a Council composition simulation, composition is suppressed whenever ward forecasts are unavailable.

## Public contract

Council snapshot schema version 3 contains:

- `race_class` and exhaustive `race_status_reasons`;
- structured `evidence` for prior results, registration, ward polling, and mayoral context;
- a per-ward `forecast` status with unavailable reasons and nullable probabilities; and
- a top-level `council_model` block containing assessment definitions, release gates, validation diagnostics, and composition availability.

The former fixed-coefficient probabilities, 97% caps, synthetic Ward 13 probability, and deterministic coattail adjustment are not part of the v3 public contract.

## Sources and reproducibility

Historical results are imported from the City of Toronto’s official [general-election results](https://www.toronto.ca/city-government/elections/election-results-reports/election-results/general-election-results/) and [by-election results](https://www.toronto.ca/city-government/elections/election-results-reports/election-results/by-election-results/). The importer preserves the downloaded candidate-level result rows and writes a normalized long-form table. Calibration output records the model version, input elections, sample size, event count, held-out metrics, and every failed gate.
