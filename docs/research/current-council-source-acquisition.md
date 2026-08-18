# Acquisition audit: current 2026 Forum Council poll sources

**Acquisition date:** 2026-08-17  
**Scope:** Six publicly accessible first-party Forum Research respondent samples covering Toronto Wards 5, 11, 13, 19, and 20  
**Purpose:** Preserve source provenance and extract source-faithful Council and ward-level mayoral Poll Readings without changing the live legacy poll inputs, snapshots, or forecast code

## Result

All six known PDFs were recovered directly from Forum Research over HTTPS. They are valid, unencrypted, text-based PDFs. The local copies live under the gitignored `data/source_documents/current_council/` directory. Their normalized document, sample, reading, and response records are now tracked in the five source-contract CSVs under `data/raw/polls/`.

The corpus contains **six parent respondent samples**, **13 dependent readings**, and **49 published option rows**:

- five June samples or August samples contain both Council and ward-level mayoral readings, alternate Council scenarios, or both;
- the August Ward 19 release contains one Council reading only;
- the June and August Ward 19 surveys are separate respondent samples and therefore real within-ward replication, but both are from Forum Research; and
- multiple questions asked of one parent sample are not independent polls.

This acquisition introduced a model-neutral source contract, schema documentation, and validation tests. It did **not** change or feed the live legacy `polls.csv`, `ward_poll_readings.csv`, processed snapshots, or forecast code.

## Acquired first-party documents

| Parent sample | Fieldwork | Overall sample | PDF | Pages | SHA-256 |
|---|---|---:|---|---:|---|
| Ward 20, Scarborough Southwest | 2026-06-22 to 2026-06-23 | 311 | [Forum PDF](https://www.forumresearch.com/news/attachments/080be964-71ac-48a6-8358-fb7e8eb60aa3.pdf) | 3 | `fec6284fbdbcd1bd692c02889e22b1a0a3b6a9fc8be0b6070a4c336a639f8e01` |
| Ward 5, York South-Weston | 2026-06-22 to 2026-06-23 | 301 | [Forum PDF](https://www.forumresearch.com/news/attachments/e1d73221-747d-4f97-bfa1-4aad42c7c537.pdf) | 3 | `0031ddbcd6eed4bf62676b839d81bd55d7e16c11e8485a6abd4611308412e133` |
| Ward 13, Toronto Centre | 2026-06-22 to 2026-06-23 | 355 | [Forum PDF](https://www.forumresearch.com/news/attachments/aeaf5831-d6be-47b8-9653-30061bcb2368.pdf) | 3 | `c2df3e54d17747f96a122c5157fb0d82754c90929066a1400fa17e577f384f9f` |
| Ward 19, Beaches-East York | 2026-06-22 to 2026-06-23 | 367 | [Forum PDF](https://www.forumresearch.com/news/attachments/490d62fe-a2c1-4987-992d-a1e162ce826f.pdf) | 3 | `49330e59afbef0074c4720cb9633c43becc220a08c9262c9879eddb55bc62488` |
| Ward 19, Beaches-East York replication | 2026-08-11 to 2026-08-12 | 386 | [Forum PDF](https://www.forumresearch.com/news/attachments/bfc438f8-9618-4981-8413-d784810cd4b7.pdf) | 2 | `58c07def8aa1a6cc47c916c31fcbc3c9b2b47fedb7605ce5adaf18a43552e9a1` |
| Ward 11, University-Rosedale | 2026-08-12 | 449 | [Forum PDF](https://www.forumresearch.com/news/attachments/5a055d21-dc54-4bfa-838d-efa840f9704a.pdf) | 4 | `6b0668ca9c61c12cb86ca37c9d4e8941d62c9f3f7b24ce5d8fe0da01b6a701c0` |

The four June documents are dated June 24 in the releases, while their attachment `Last-Modified` timestamps and current Forum page/API availability are June 29. Both dates are retained because the documents do not establish that the files were publicly downloadable on June 24. The August documents and web availability are both dated August 13.

## Source-faithful reading inventory

Percentages below are the published total column. They are not renormalized. `u/w` and `w/t` are Forum's reported unweighted and age/gender-weighted reading bases, not the overall recruited sample.

| Parent sample and reading | Denominator | Base, u/w / w/t | Published shares | Separately reported undecided |
|---|---|---:|---|---:|
| Ward 20 Council | Decided/leaning | 201 / 225 | De Baeremaeker 28; Kandavel 37; Rupasinghe 25; Other 10 | 28 |
| Ward 20 mayor | Decided/leaning | 265 / 275 | Chow 43; Bradford 31; Other 27 | 11 |
| Ward 5 Council | Decided/leaning | 229 / 223 | Padovani 20; DiGiorgio 24; Nunziata 42; Other 13 | 26 |
| Ward 5 mayor | Decided/leaning | 270 / 255 | Chow 29; Bradford 58; Other 13 | 15 |
| Ward 13 Council | Decided/leaning | 215 / 195 | Moise 35; Stikuts 6; Tate 19; Other 40 | 45 |
| Ward 13 Wong-Tam scenario | Not stated; prose only | Not published | Wong-Tam 67; Moise 33 | Not published |
| Ward 13 mayor | Decided/leaning | 324 / 319 | Chow 55; Bradford 34; Other 11 | 10 |
| Ward 19 June Council, hypothetical Erskine-Smith field | Decided/leaning | 277 / 267 | Dann 9; Erskine-Smith 69; Johnson 16; Other 5 | 27 |
| Ward 19 June mayor | Decided/leaning | 333 / 349 | Chow 50; Bradford 35; Other 15 | 5 |
| Ward 19 August Council, hypothetical Erskine-Smith field | Decided/leaning | 292 / 316 | Dann 7; Erskine-Smith 53; Johnson 19; Other 21 | 23 |
| Ward 11 Council, then-current field | Decided/leaning | 312 / 286 | Blanc 5; Fisher 8; Saxe 41; Yoon 9; Other 37 | Not published |
| Ward 11 Council, hypothetical Layton field | Not reported; leaning follow-up printed | 385 / 386 | Blanc 6; Fisher 2; Layton 44; Saxe 17; Yoon 5; Other 26 | Not published |
| Ward 11 mayor | Not reported; leaning follow-up printed | 414 / 353 | Chow 63; Bradford 25; Alexander 5; Other 7 | Not published |

The tracked readings retain parent-sample IDs, reading IDs, exact fieldwork and release dates, question-text status, scenario labels, reading-specific bases, published table row order when present, response type, source locator, and caveats. The Wong-Tam result is explicitly `question_text_status=not_reported`: its release outcome prose is retained in notes without being recast as questionnaire wording, and no response-option order is inferred from prose. `Other` is explicitly typed as a Poll Residual, not as an Unmeasured Candidate Tail estimate.

## Source defects and modelling cautions

1. **Two geography errors are in the source.** The Ward 20 and June Ward 19 methodology paragraphs say the respondents were York South-Weston residents. Their titles, toplines, questions, and detailed tables identify Scarborough-Southwest and Beaches-East York respectively. The manifest preserves the conflict; no silent correction was made.
2. **One sample cannot be represented by one reading base.** Ward 11's three dependent readings have unweighted bases of 312, 385, and 414. Using the overall sample of 449 as the likelihood count for all three would overstate their information.
3. **A leaning follow-up does not establish the table denominator label.** Ward 11 page 4 prints the Layton and mayoral questions, leaning follow-ups, and reading bases, but unlike page 3 it does not print `[Decided/ Leaning]`. Both denominator types therefore remain `not_reported`; the questions and bases are retained independently.
4. **Question scenarios are not replication.** Ward 11's Saxe-current, Layton-hypothetical, and mayoral tables come from one sample. The Ward 13 Wong-Tam scenario likewise remains part of its parent sample, and supplies no denominator or base.
5. **Published percentages contain ordinary rounding discrepancies.** Ward 5 Council and June Ward 19 Council sum to 99%; Ward 20 mayor sums to 101%. The extract preserves the source values rather than forcing them to 100%.
6. **Undecided is not interchangeable with `Other`.** Several releases report an undecided percentage in prose while their decided/leaning tables contain an `Other` row. Ward 13, for example, reports 10% undecided and a separate 11% `Other` among decided/leaning respondents.
7. **Some undecided/base relationships are not reconstructible from the release.** Ward 11 publishes no undecided percentage. The August Ward 19 release reports 23% undecided, while its two reading bases do not provide a documented conversion rule that should be reverse-engineered.
8. **The June Council questions say “by-election.”** This wording is retained verbatim even though the project concerns the 2026 regular election. It is a questionnaire-comparability fact, not a typo for the extractor to repair.
9. **The PDFs do not establish full tested-option order or questionnaire routing.** Published table row order is retained only as published row order; it is not asserted to be the IVR presentation order.

## QA performed

- Each URL returned HTTP 200 with `Content-Type: application/pdf`.
- `file` and Poppler identified six valid, unencrypted PDF 1.7 documents totalling 18 pages.
- SHA-256 and byte size were recalculated after download and rechecked against every manifest row.
- `pdftotext -layout` produced non-empty text for every document, from 5,779 to 10,889 characters.
- Every page was rendered to PNG at 110 DPI with Poppler and visually inspected. Tables, footnotes, headings, page numbers, and methodology text were legible; no clipping, missing glyphs, black boxes, or other rendering defects were found.
- The option-level CSV parses as 49 rows grouped into 13 readings and six parent samples. Reading totals reproduce the published rounding: 0.99, 1.00, or 1.01 as applicable.

## Access and reuse

The PDFs were downloadable without authentication. Neither the documents nor the retrieved response metadata supplied an explicit reuse or redistribution licence. The local corpus is therefore retained for internal audit under the gitignored source-document directory. Redistribution, repository commitment, or republication of the PDFs should wait for a rights determination or Forum Research's permission.

## Implication

These documents confirm that the redesigned poll data contract needs a parent **Distinct Poll Sample** separated from child **Poll Readings**, with a reading-specific denominator and base. They also show why source defects, unknown questionnaire details, hypothetical fields, Poll Residual, and candidate-tail support must remain separate rather than being silently normalized into a single flat ward-poll row.
