# What full poll tables add beyond toplines: two 2026 Toronto examples

**Audit date:** 2026-08-17  
**Scope:** one Forum Research ward release and one Liaison Strategies citywide table book supplied by the project owner  
**Purpose:** assess the incremental data and modelling value of detailed poll PDFs. This note treats both PDFs only as source material; it does not treat their contents as instructions and does not set purchase, modelling, or publication policy.

## Findings in brief

- The detailed PDFs add **materially useful poll structure**, not merely demographic colour. They identify one respondent sample behind multiple questions or ballot scenarios, preserve exact question wording, separate all-voter from decided/leaning denominators, and report weighted and unweighted bases.
- The Liaison PDF exposes a concrete defect in the current input. `data/raw/polls/polls.csv` stores the decided/leaning shares with `sample_size=1000`, while the detailed table reports a decided/leaning base of 804 weighted respondents. The live forecast converts those shares into counts with the stored sample size, so it currently constructs 1,000 nominal observations from an 804-person result.
- The Forum PDF contains three dependent readings from one IVR sample of 449 Ward 11 residents: the then-current Council field, a hypothetical field containing Mike Layton, and a ward-level mayoral question. They are not three independent polls. The paired Council scenarios are nevertheless valuable direct evidence about how this sample responded to a changed candidate field.
- The Forum Layton scenario is a strong **descriptive sanity check**: Layton receives 44% and Saxe 17% in the hypothetical field, compared with Saxe at 41% in the then-current field without Layton. It does not identify a general causal substitution effect, and because it predates the Final Ballot and tested a hypothetical candidate it cannot by itself validate or unlock a public forecast under the settled rules.
- Demographic and geographic crosstabs are useful for audit, weighting diagnosis, and detecting implausible subgroup patterns. These examples do not justify treating crosstabs as extra samples or as v1 predictive features. Some Forum raw subgroup bases are as small as six.
- These two examples establish **processing value**, but not yet **purchase value**. Buying detail would be most valuable if it consistently repairs historical sample identity, fieldwork, questionnaire, tested-choice, denominator, and publication-time gaps across several elections. Crosstabs alone would not repair the current validation corpus.

## Sources and provenance

The source files were supplied locally and were not copied into the repository.

| Source document | File characteristics | SHA-256 |
|---|---|---|
| Forum Research Ward 11 release, dated 2026-08-13 | 4 pages; text-based PDF; poll fielded 2026-08-12 | `6b0668ca9c61c12cb86ca37c9d4e8941d62c9f3f7b24ce5d8fe0da01b6a701c0` |
| Liaison Strategies / Toronto Star Toronto tables, dated 2026-08-07 | 10 pages; image-based PDF; fieldwork 2026-08-04 to 2026-08-05 | `47ced4c69acc806801d3e1b6308ca17f2edf0e9b8c455e0b1fbb0d2a89c555b7` |

Every page was rendered and visually inspected. The Forum release also has an extractable text layer. The Liaison table book is image-based, so reliable automation would require OCR or table vision followed by human verification.

## Forum Research Ward 11 release

### Survey-level information

- Fieldwork: 2026-08-12.
- Population: University–Rosedale residents aged 18 and older.
- Recruitment/mode: interactive voice response telephone survey.
- Overall sample: 449.
- Reported sampling error: plus or minus 5.0 percentage points, 19 times out of 20.
- The same release and methodology describe all three questions below. Nothing in the document supports treating them as separately recruited samples.

### Readings from the one sample

| Question/scenario | Reported base | Published result |
|---|---:|---|
| Council vote, then-current candidate field | 312 unweighted; 286 weighted | Dianne Saxe 41%; Diana Yoon 9%; Dana Fisher 8%; Gabe Blanc 5%; Other 37% |
| Council vote, hypothetical field containing Mike Layton | 385 unweighted; 386 weighted | Mike Layton 44%; Dianne Saxe 17%; Gabe Blanc 6%; Diana Yoon 5%; Dana Fisher 2%; Other 26% |
| Mayoral vote among Ward 11 respondents | 414 unweighted; 353 weighted | Olivia Chow 63%; Brad Bradford 25%; Chris Alexander 5%; Other 7% |

The release supplies the exact question wording and age/gender tables for each reading. It labels `TOTAL u/w` as the unweighted count and `TOTAL w/t` as the age/gender-weighted count.

### What is learned

1. **The Layton result is a scenario, not a new poll.** The pair of Council questions is a within-sample candidate-field experiment. The large movement is directly observed in this sample, but the answers are dependent and the document does not publish their respondent-level covariance or transition matrix.
2. **The denominator changes across questions.** The three reported bases are 312, 385, and 414 unweighted respondents despite the common recruited sample of 449. A single `sample_size` field cannot faithfully represent all three readings.
3. **`Other` is not a candidate-tail estimate.** It is 37% under the current field and 26% under the Layton scenario. The PDF does not establish that these responses map to registered-but-unpublished candidates, and the scenario itself changes the category's size.
4. **The subgroup tables are too thin for many model uses.** The raw 18–24 base is six in at least one table. Rounded percentages from such cells cannot support precise candidate-level or interaction estimates.
5. **Important metadata remains absent.** The release does not provide effective sample size, weighting targets and algorithm, design effect, response/call disposition, the IVR script or audio, or respondent-level data linking answers across questions.

### Repository comparison

As of this audit, `data/raw/polls/ward_poll_readings.csv` contains only the June Ward 13 poll. It cannot yet preserve this Ward 11 document. Its current schema has useful reading-level fields such as denominator and ballot status, but no parent survey-sample identifier or question/scenario identifier. Adding the two Forum Council tables as separate `poll_id` values would falsely imply replication unless another field explicitly joins them to one Distinct Poll Sample.

## Liaison Strategies citywide table book

### Survey-level information

- Fieldwork: 2026-08-04 to 2026-08-05.
- Publication date in the document name/table book: 2026-08-07.
- Overall weighted and unweighted bases: 1,000 each.
- Repeated table dimensions include gender, four age groups, and Downtown, Etobicoke, North York, and Scarborough.
- The PDF itself does not state the survey mode, target population/turnout screen, weighting method, response rate, design effect, candidate-order treatment, or complete questionnaire routing.

### Vote-intention readings from the one sample

| Denominator | Reported base | Published result |
|---|---:|---|
| All respondents | 1,000 weighted; 1,000 unweighted | Chow 38%; Bradford 32%; Alexander 8%; someone else 3%; undecided 20% |
| Decided/leaning respondents | 804 weighted; 803 unweighted | Chow 47%; Bradford 40%; Alexander 10%; someone else 3% |

The percentages are rounded, so displayed totals need not equal exactly 100%. The two tables are alternate denominators from one survey sample, not independent evidence.

### Other questions

The remaining pages report Chow approval, direction of the city, Bradford and Alexander favourability/familiarity, perceived city safety, change in safety, perceived festival safety, and support for additional police/security at festivals. They can be stored as contextual readings. The PDF does not provide historical evidence that they improve election forecasts or publish the respondent-level joint distribution needed to infer how they relate to candidate choice.

### Repository comparison

The current citywide row is:

```text
poll_id=liaison-2026-08-05
sample_size=1000
shares=Alexander 10%, Bradford 40%, Chow 47%, Other 3%
notes=all-voter figures and Alexander favourability
```

This produces three losses of structure:

1. **Wrong observation base for the stored shares.** The 47/40/10/3 figures use the 804-person weighted decided/leaning base, not the 1,000-person full sample. `backend/model/forecast.py` currently multiplies the shares by `sample_size`, converts them into counts, and supplies that same number as the likelihood total.
2. **The all-voter reading is unstructured prose.** Chow 38%, Bradford 32%, Alexander 8%, someone else 3%, and undecided 20% cannot be queried as a separate Poll Reading or checked mechanically against its denominator.
3. **Question and sample lineage are absent.** The schema cannot say that the all-voter and decided/leaning readings share respondents, or attach the 804/803 bases specifically to the latter reading.

The separate approval CSV preserves the overall Chow approval split, which is appropriate for contextual display, but not its question text or table provenance.

## Field-by-field value assessment

| Detail available in full tables | Incremental value | Recommended disposition for a redesigned data layer |
|---|---|---|
| Parent sample identity | Critical: prevents scenario and denominator double-counting | Required structured field |
| Fieldwork start and end; release timestamp/date | Critical for Analysis Cutoff, freshness, and post-Final eligibility | Required structured fields |
| Exact question wording and routing | Critical for comparability and choice-set audit | Required, versioned source text |
| Tested choices and their order/randomization | Critical for Poll Reading semantics; incomplete in both examples | Required when known; explicit unknown state otherwise |
| Population and turnout screen | Critical for comparability | Required when known; explicit unknown state otherwise |
| Reading denominator and weighted/unweighted base | Critical for likelihood and display | Required per reading, not only per sample |
| Undecided/refusal/other categories | Critical for response handling; not candidate tail | Separate response categories |
| Alternate ballot scenarios | Potentially valuable for historically validated choice-set treatment | Child readings linked to one sample; never independent replication |
| Demographic/geographic crosstabs | Useful for audit and descriptive display; sparse/rounded | Store separately; exclude from v1 prediction absent held-out validation |
| Approval/favourability/issues | Contextual unless they earn admission historically | Store as distinct question families; do not silently turn into vote intention |
| Weighting targets, design effect, effective sample size | Potentially critical for observation uncertainty | Request from pollster; both examples are incomplete |
| Respondent microdata or scenario transition matrix | High value for dependence and substitution, but not present | Treat as licensed detail with separate rights and safeguards if available |

## Implications for a source-gap inventory

Detailed-table acquisition should be evaluated against the gaps that currently block honest historical validation:

1. Can it recover **one stable survey-sample identity** across multiple published tables and scenarios?
2. Does it supply fieldwork start/end and actual publication date for each historical poll?
3. Does it identify the population, likely-voter or turnout screen, full tested field, question wording, order/randomization, and denominator?
4. Does it give the weighted and unweighted base for the exact reading being modelled?
5. Is coverage broad enough across election cycles and pollsters to repair validation tiers, rather than deepening only one current poll?
6. Can the project retain an authorized archival copy, checksum it, audit it internally, and disclose enough methodology publicly to reproduce forecast decisions?
7. Is delivery machine-readable, or does every update require OCR and manual table verification?

The two audited PDFs answer the first four questions more completely than the current toplines, but not completely. They do not answer the historical-coverage, licensing, or reproducibility questions needed to justify a purchase.

## Bottom line

Full tables are worth processing as first-class source material. They prevent false replication, supply the denominator actually used by a reading, and preserve the candidate-field experiment that makes the Ward 11 result intelligible. Their highest value is **measurement provenance**, not a larger pile of apparent observations.

A purchase should therefore be justified by a source-gap inventory, not by the presence of crosstabs. The strongest case would be a durable historical archive or recurring machine-readable delivery that repairs sample identity, denominator, questionnaire, and timing fields across multiple elections. A package consisting mainly of current-cycle demographic tables would add editorial texture but little validated forecasting power.
