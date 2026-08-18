# Poll-document extraction pilot

## Outcome

The pilot and one subsequent historical restoration produced a source-faithful
draft of **11 selected parent samples, 25 vote-intention readings, and 125
response rows**. The normalized working files are:

- [`samples.csv`](poll-document-extraction-pilot/samples.csv)
- [`readings.csv`](poll-document-extraction-pilot/readings.csv)
- [`responses.csv`](poll-document-extraction-pilot/responses.csv)

These are tracked extraction fixtures. The three source-verified historical
samples now feed the isolated, non-live historical reconstruction seam; they do
not feed the live model or snapshots.

The extraction result is encouraging but does not justify unattended ingestion:

- **Nine of eleven poll documents** have a usable text layer and are candidates for automated cell extraction followed by mandatory semantic and visual QA.
- **Liaison July 2025** exposes headings and questions as text but not the plotted or tabulated values reliably; it required visual/manual extraction.
- **Liaison August 2026** is image-only; it requires OCR/table vision or manual entry.
- **Zero of eleven** are safe to accept without a human source-page check. The common failures are semantic rather than OCR failures: duplicated toplines, alternate ballots, denominator transformations, comparison waves, and conflicting prose/table values.

## Method

For each PDF, I checked its text layer, identified the vote-intention source pages, and independently inspected the relevant rendered pages. Values were taken from the most detailed source table available. A rounded chart or release paragraph was not allowed to override a detailed table. Source oddities were retained; totals were not forced to 100 and missing bases were not inferred.

This is a focused extraction pilot rather than an exhaustive transcription of every crosstab or every historic comparison contained in the ten PDFs.

## Document results

`u/w` means the source's unweighted base and `w` means its weighted base. A bare `n` means the artifact reports a base without identifying which kind it is.

| Document | Selected sample and reading lineage | Extracted reading bases | Automation classification | Material QA finding |
|---|---|---:|---|---|
| [Forum citywide, July 29, 2026](../../data/source_documents/current_mayoral/forum_2026-07-29_full.pdf) | One parent sample, `n=1,011`; two dependent decided/leaning ballot scenarios | `887 u/w, 888 w`; `889 u/w, 890 w` | Text-table, semiautomated | Detailed table says Bradford 36 where release prose says 35; added-candidate table says “Someone else” 10 where prose says 11. Draft uses tables and records conflicts. |
| [Mainstreet, Feb. 20–22, 2026](../../data/source_documents/current_mayoral/mainstreet_2026-02-22_full.pdf) | One parent sample, `n=802`; raw all-voter, source-labelled “Decided and Undecided,” and decided-only readings | `802/802`; `802/802`; `690/690` | Text-table, semiautomated | The middle transformation is not documented beyond its label. It cannot be treated as raw or decided-only by assumption. |
| [Mainstreet, June 12–18, 2026](../../data/source_documents/current_mayoral/mainstreet_2026-06-18_full.pdf) | One parent sample, `n=1,157`; raw, leaner-adjusted, undecideds-removed, and forced two-way readings | `1,157/1,157`; `1,157/1,157`; `985/960`; `1,157/1,157` | Text-table, semiautomated | Four products from one sample must not be counted as four polls. “Someone Else” and “Undecided” remain distinct. |
| [Liaison, July 2–6, 2025](../../data/source_documents/current_mayoral/liaison_2025-07-06_full.pdf) | One parent sample, `n=1,000`; with-Tory and without-Tory ballot scenarios | `1,000/1,000`; not repeated | Sparse-text, manual visual | The without-Tory table does not repeat a base. Its sample lineage is clear, but the reading base is left pending instead of copied by inference. |
| [Liaison, Aug. 4–5, 2026](../../data/source_documents/current_mayoral/liaison_2026-08-05_tables.pdf) | Tables-only artifact; one apparent parent sample, `n=1,000`; all-voter and decided/leaning readings | `1,000/1,000`; `803 u/w, 804 w` | Image-only, manual/OCR | The all-voter percentages sum to 101. Mode, target population, and weighting method are absent from this artifact and remain pending. |
| [Ipsos, Aug. 25–29, 2025](../../data/source_documents/current_mayoral/ipsos_2025-08-29_full.pdf) | One online parent sample, `n=1,001`; all-respondent hypothetical choice | reported `n=1,001` | Text-chart, semiautomated | “I wouldn't vote” is a nonvoter response, not undecided or an unmeasured-candidate tail. |
| [Pallas, March 7–8, 2026](../../data/source_documents/current_mayoral/pallas_2026-03-08_full.pdf) | One parent sample, `n=735`; two dependent all-voter ballot scenarios | `735/735` for each | Text-table, semiautomated | Weighted subgroup frequencies are internally impossible even in the all-voter tables; decided-voter tables are worse, and one says “party” in a mayoral candidate question. Only total-column readings were retained; nothing was repaired. |
| [Forum Ward 11, Aug. 12, 2026](../../data/source_documents/current_council/ward11_2026-08-12_forum.pdf) | One parent sample, `n=449`; baseline council, Layton counterfactual, and ward-level mayoral readings | `312/286`; `385/386`; `414/353` | Text-table, semiautomated | All three readings are dependent. The different bases show why parent sample size cannot stand in for question base. Page 4 prints leaning follow-ups and bases for the Layton and mayoral readings but does not print the page-3 `[Decided/ Leaning]` denominator label, so those two denominator labels remain unreported. |
| [Nanos, Sept. 16–20, 2014](../../data/source_documents/pilot_historical/nanos_2014-09_full.pdf) | One selected September parent sample, `n=1,000`; first-choice including unsure and decided-only ballot | reported `n=1,000`; reported `n=925` | Text-table, semiautomated | Precise stat-sheet values differ from rounded summary charts. The PDF also embeds August results from a different parent sample. |
| [Viewpoints, Apr. 29–May 2, 2023](../../data/source_documents/pilot_historical/viewpoints_2023-05-02_full.pdf) | One parent sample, `n=400`; raw and decided readings | reported `n=400`; reported `n=264` | Text-table, semiautomated | Raw values sum to 100.2 and decided values to 101 after source rounding. The PDF header says May 3 while the accompanying first-party article is dated May 4; the later publication date is retained. |
| [Viewpoints, June 15–19, 2023](../../data/source_documents/pilot_historical/viewpoints_2023-06-15_19_full.pdf) | Selected June 19 parent sample, `n=1,007`; raw and decided-plus-leaning readings | reported `n=1,007`; reported `n=881` | Text-table, semiautomated | The PDF's June 2 and May 2 columns are different samples, not crosstabs of the June 19 sample. The selected final reading sums to 101 after source rounding. |

## Source fidelity and validation findings

The draft validates structurally: 11 samples, 25 unique reading IDs, 125
response rows, no orphan responses, and at least one response for every
reading. Source totals range from 99.9 to 101.0. That range is preserved and
flagged; it is not evidence that values should be renormalized.

The pilot establishes several concrete precedence rules:

1. Prefer a detailed table over a release paragraph or decorative chart, but retain the disagreement as a QA event.
2. Preserve both source label and normalized response type. “Someone else,” undecided, unsure, and “I wouldn't vote” are different observations.
3. Do not infer a question base from the parent sample. A base may be smaller, weighted differently, or simply unreported.
4. Treat alternate ballots, leaner allocation, undecided removal, and forced choice as distinct readings sharing a parent sample.
5. Treat comparison-wave columns as separate parent samples even when printed in one PDF.
6. Permit bounded rounding residuals and store the observed total. Do not silently rescale to 100.
7. A source inconsistency remains a source inconsistency. It must produce `pending` or a QA flag, not a guessed correction.

## Schema consequences

The minimum durable hierarchy is:

`source document -> parent sample -> reading -> response`

A production schema should therefore add or preserve:

- document identity, original URL, retrieval timestamp, SHA-256, page count, rights status, and extraction class;
- parent-sample identity, pollster/client, full fieldwork range, geography, target population, mode, achieved sample, weighting, and methodology completeness;
- reading identity, exact question, contest, geography, ballot/scenario, denominator/transformation, unweighted base, weighted base, generic reported base, source page, and dependence on the parent sample;
- response order, verbatim label, normalized candidate ID where resolvable, response type, published share, and rounding/source notes;
- explicit `pending`, `unreported`, and `conflicted` states. Empty does not mean zero;
- a QA-event table capable of recording prose/table conflicts, impossible bases, duplicate toplines, OCR confidence, and reviewer disposition.

The schema must allow multiple samples in one document and multiple dependent readings in one sample. A flat `poll_id + candidate + share` table cannot represent this corpus without either double-counting polls or deleting source meaning.

## Rights and reuse

All eleven poll artifacts were retained from public first-party routes, but
public availability is not a reuse licence.

- Both Mainstreet reports expressly reserve ownership and prohibit reproduction without written authorization.
- Ipsos, Pallas, and Nanos display copyright notices but no affirmative reuse licence in the inspected artifact.
- The Forum, Liaison, and Viewpoints artifacts do not provide an affirmative reuse licence in the inspected pages.

The safe corpus policy is to retain source files for internal verification, store rights status per document, and avoid redistributing full reports or reproduced tables until permission or a legal/editorial basis is recorded. Publication of derived numeric facts should be governed separately from republication of the source layout.

## QA time

No defensible minutes-per-document result is reported. The pre-existing full-document render/review and this extraction pass were not instrumented from a common start, and reconstructing a duration after the fact would be false precision. A second pilot should log acquisition, machine extraction, semantic review, visual verification, and repair time separately for each document. This pilot therefore tests feasibility and failure modes, not the earlier corpus-wide time estimate.

## File-integrity record

| Document ID | SHA-256 |
|---|---|
| `forum_2026-07-29_full` | `3e00274591e7db0191b71b3ffe05c4733a2d6e48b630459bf58d0f09e62bdad9` |
| `mainstreet_2026-02-22_full` | `75ad0c94f0b75f1de66d94744e79430b9c831c97d23adc9f449a6634468783b9` |
| `mainstreet_2026-06-18_full` | `9ff554329604bd43dc07d97e37e38a3153b4e2c3256f0ddb6cfbeff17c1261a9` |
| `liaison_2025-07-06_full` | `4d02e180be24d3d44dc5e5eb5ab5d94a82dc0a44105baa4b30a48d168d80ee02` |
| `liaison_2026-08-05_tables` | `47ced4c69acc806801d3e1b6308ca17f2edf0e9b8c455e0b1fbb0d2a89c555b7` |
| `ipsos_2025-08-29_full` | `fe94c43b5ecbcc0a97ba84851fbecae6fd1acf3cfd52cdbfce0e121694cce95a` |
| `pallas_2026-03-08_full` | `005426a871db36dbbcbd876540c2cb6438bb26efab9f3850ac1233e3a50de82c` |
| `ward11_2026-08-12_forum` | `6b0668ca9c61c12cb86ca37c9d4e8941d62c9f3f7b24ce5d8fe0da01b6a701c0` |
| `nanos_2014-09_full` | `a62f7fbfed51c4e2b07f2aa63d63d87ba246c997ae62d33ad7ae805869fcd1c4` |
| `viewpoints_2023-05-02_full` | `5ef807c7fe31194b21b6f1400883052d9deab082fd92e4ffae7a01706e4fae6c` |
| `viewpoints_2023-06-15_19_full` | `ab75fd2d30f4adcdf3ee8f1b0182bea238496a21845f1eb4b702735ec0b75e8c` |
