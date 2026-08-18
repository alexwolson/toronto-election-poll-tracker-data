# Acquisition audit: current Toronto mayoral poll sources

**Acquisition and QA date:** 2026-08-17

**Scope:** the 19 distinct respondent samples represented by the 22 current-cycle mayoral rows in `data/raw/polls/polls.csv`

**Purpose:** determine whether the current full-detail source corpus can be assembled from first-party public sources, preserve a local audit corpus, and document source-to-sample lineage without changing the live legacy poll inputs, snapshots, or model code

## Result

The current-cycle corpus is highly recoverable: **18 of 19 distinct respondent samples have a public first-party full-detail artifact**. The remaining sample, Abacus Data's January 2026 fieldwork, has a first-party article behind Substack's claim-a-free-post access gate but no publicly exposed table book or downloadable artifact. The gate was not bypassed.

The recovered local corpus contains **24 first-party files** totalling **80,838,635 bytes**:

- 22 PDFs, totalling 80,681,612 bytes and 450 pages;
- one Canada Pulse media-release DOCX; and
- one Canada Pulse full-tables XLSX.

The 22 PDFs are valid and unencrypted. All 450 pages rendered successfully and every rendered page was visually inspected. Twelve PDFs have a meaningful, though sometimes limited, text layer; ten Liaison PDFs are image-only and will require OCR or table vision plus verification for automated ingestion. No corrupt, blank, clipped, or unreadable pages were found.

The source files are retained under the gitignored `data/source_documents/current_mayoral/` directory. Their normalized acquisition metadata is now tracked in `data/raw/polls/source_documents.csv`, `poll_sample_documents.csv`, and `poll_samples.csv`: 25 document leads/artifacts, 25 links, and 19 respondent samples. Eighteen recovered samples have completed audited candidate-choice extraction; the Abacus lead is explicitly `access_pending` and its sample is `blocked`. Forty-three readings are general vote intention and the Canada Pulse consideration question is explicitly context-only. The 44 extracted readings remain dependent products of 18 respondent samples, not 44 polls.

This acquisition introduced a model-neutral source contract, schema documentation, and validation tests. It did **not** change or feed the live legacy `polls.csv`, `ward_poll_readings.csv`, processed snapshots, or forecast code.

## Distinct sample to production-reading join

One local document can support several dependent Poll Readings. In particular, the September 2025 Forum report contains four extracted ballot readings from one respondent sample, and the March 2026 Pallas report contains four extracted readings across two ballot fields and two denominators from one sample. Those eight readings are not eight independent polls.

`Source date` below is the date printed in the source report or first-party release, not a correction silently applied to production data.

| Distinct respondent sample | Production `poll_id` values | Source fieldwork | Source date | Local first-party artifacts | Status |
|---|---|---|---|---|---|
| [Pallas 2025-06-07](https://pallas-data.ca/2025/06/12/pallas-toronto-poll-chow-leads-with-a-year-to-go/) | `pallas-2025-06-07` | 2025-06-07 | 2025-06-12 | `pallas_2025-06-07_full.pdf` | Full detail recovered |
| [Liaison 2025-07-06](https://press.liaisonstrategies.ca/toronto-poll-chow-39-tory-35/) | `liaison-2025-07-06` | 2025-07-02 to 2025-07-06 | 2025-07-14 | `liaison_2025-07-06_full.pdf` | Full detail recovered |
| [Ipsos 2025-08-29](https://www.ipsos.com/en-ca/toronto-city-poll-what-residents-think-about) | `ipsos-2025-08-29` | 2025-08-25 to 2025-08-29 | report 2025-09-19; publisher page 2025-09-20 | `ipsos_2025-08-29_full.pdf` | Full detail recovered |
| [Forum 2025-09-04](https://www.forumresearch.com/news/2025/09/one-year-out-chow-leads-in-toronto-mayoral-race) | `forum-2025-09-04`; `forum-2025-09-04-chow-v-tory`; `forum-2025-09-04-bradford-v-chow` | 2025-09-04 | 2025-09-05 | `forum_2025-09-04_full.pdf` | Full detail recovered; four extracted dependent readings, including Chow-Bailão |
| [Canada Pulse 2025-10-06](https://canadapulseinsights.com/post/toronto-civic-politics-2025) | `canadapulse-2025-10-06` | 2025-09-30 to 2025-10-06 | media release dated 2025-10-21 | `canadapulse_2025-10-06_release.docx`; `canadapulse_2025-10-06_tables.xlsx` | Full detail recovered |
| [Liaison 2025-10-23](https://press.liaisonstrategies.ca/toronto-chow-leads-tory-52-to-36/) | `liaison-2025-10-23` | 2025-10-22 to 2025-10-23 | 2025-10-27 | `liaison_2025-10-23_full.pdf` | Full detail recovered |
| [Liaison 2025-12-21](https://press.liaisonstrategies.ca/toronto-chow-leads-tory-39-3-to-35-1/) | `liaison-2025-12-21` | 2025-12-19 to 2025-12-21 | 2025-12-23 | `liaison_2025-12-21_full.pdf` | Full detail recovered |
| [Abacus 2026-01-27](https://davidcoletto.substack.com/p/with-tory-out-torontos-mayoral-race) | `abacus-2026-01-27-bradford-v-chow` | 2026-01-22 to 2026-01-27 | first-party article dated 2026-03-04 | none | **Blocked:** gated first-party article; no public table book/download or complete extractable result |
| [Liaison 2026-02-02](https://press.liaisonstrategies.ca/toronto-chow-40-tory-33-bradford-18/) | `liaison-2026-02-02` | 2026-01-31 to 2026-02-02 | 2026-02-12 | `liaison_2026-02-02_full.pdf` | Full detail recovered; image-only |
| [Mainstreet 2026-02-22](https://www.mainstreetresearch.ca/post/latest-mainstreet-poll-of-toronto-shows-uncertain-choice-for-mayor-in-2026) | `mainstreet-2026-02-22` | 2026-02-20 to 2026-02-22 | report 2026-02-22; publisher page 2026-02-24 | `mainstreet_2026-02-22_full.pdf`; `mainstreet_2026-02-22_public.pdf` | Full detail recovered; access caveat below |
| [Liaison 2026-03-08](https://press.liaisonstrategies.ca/toronto-chow-44-bradford-26-ford-16/) | `liaison-2026-03-08` | 2026-03-06 to 2026-03-08 | 2026-03-10 | `liaison_2026-03-08_full.pdf` | Full detail recovered; image-only |
| [Pallas 2026-03-08](https://pallas-data.ca/2026/03/10/pallas-toronto-poll-chow-leads-bradford-35-to-29-but-most-think-city-is-going-in-the-wrong-direction/) | `pallas-2026-03-08`; `pallas-2026-03-08-bradford-v-chow` | 2026-03-07 to 2026-03-08 | 2026-03-10 | `pallas_2026-03-08_full.pdf` | Full detail recovered; four dependent readings across two ballot fields and two denominators |
| [Liaison 2026-04-13](https://press.liaisonstrategies.ca/toronto-chow-46-bradford-35-voters-split-on-island-airport/) | `liaison-2026-04-13` | 2026-04-12 to 2026-04-13 | 2026-04-17 | `liaison_2026-04-13_full.pdf` | Full detail recovered; image-only |
| [Liaison 2026-05-11](https://press.liaisonstrategies.ca/toronto-chow-50-bradford-37-traffic-frustration-dominates-city-mood/) | `liaison-2026-05-11` | 2026-05-10 to 2026-05-11 | 2026-05-14 | `liaison_2026-05-11_full.pdf` | Full detail recovered; image-only |
| [Mainstreet 2026-06-18](https://www.mainstreetresearch.ca/post/bradford-and-chow-matchup-could-be-close) | `mainstreet-2026-06-18` | 2026-06-12 to 2026-06-18 | report 2026-06-18; publisher page 2026-06-23 | `mainstreet_2026-06-18_full.pdf`; `mainstreet_2026-06-18_public.pdf` | Full detail recovered; access caveat below |
| [Liaison 2026-06-30](https://press.liaisonstrategies.ca/toronto-chow-49-bradford-40-world-cup-gets-positive-reviews/) | `liaison-2026-06-30` | 2026-06-28 to 2026-06-30 | documents 2026-07-06; publisher page 2026-07-07 | `liaison_2026-06-30_graphs.pdf`; `liaison_2026-06-30_tables.pdf` | Full detail recovered; image-only |
| [Liaison 2026-07-26](https://press.liaisonstrategies.ca/toronto-chow-49-bradford-41-city-split-on-direction/) | `liaison-2026-07-26` | 2026-07-24 to 2026-07-26 | 2026-07-29 | `liaison_2026-07-26_graphs.pdf`; `liaison_2026-07-26_tables.pdf` | Full detail recovered; image-only |
| [Forum 2026-07-29](https://www.forumresearch.com/news/2026/07/chow-leads-bradford-maintains-advantage-with-alexander-added-to-ballot) | `forum-2026-07-29` | 2026-07-29 | report dated 2026-07-30 | `forum_2026-07-29_full.pdf` | Full detail recovered |
| [Liaison 2026-08-05](https://press.liaisonstrategies.ca/toronto-chow-47-bradford-40-alexander-10/) | `liaison-2026-08-05` | 2026-08-04 to 2026-08-05 | 2026-08-07 | `liaison_2026-08-05_graphs.pdf`; `liaison_2026-08-05_tables.pdf` | Full detail recovered; image-only |

## Exact local file inventory

`Text words` is the word count returned by a direct Poppler text extraction. Zero means that the PDF has no meaningful text layer, not that its visible pages are blank.

| Local filename | Bytes | Pages | Text layer | Text words | SHA-256 |
|---|---:|---:|---|---:|---|
| `canadapulse_2025-10-06_release.docx` | 129,997 | — | Structured DOCX | — | `9e9c3aff692dc7894932445ed8f6d290d6e19654d9c68b700580bb3f650a0d7d` |
| `canadapulse_2025-10-06_tables.xlsx` | 27,026 | — | Structured XLSX | — | `d94dfcc3043ed7932d1a103af0294e0ec8ac20cc3ed3296f79b929a97a40376f` |
| `forum_2025-09-04_full.pdf` | 549,535 | 7 | Meaningful | 1,452 | `7b66a67ee269c9f2e509ef2defd6928710dc57b7529d30cbf0b27b8e9e51ac3a` |
| `forum_2026-07-29_full.pdf` | 660,663 | 9 | Meaningful | 2,313 | `3e00274591e7db0191b71b3ffe05c4733a2d6e48b630459bf58d0f09e62bdad9` |
| `ipsos_2025-08-29_full.pdf` | 2,258,639 | 29 | Meaningful | 3,738 | `fe94c43b5ecbcc0a97ba84851fbecae6fd1acf3cfd52cdbfce0e121694cce95a` |
| `liaison_2025-07-06_full.pdf` | 13,819,814 | 29 | Limited but meaningful | 1,104 | `4d02e180be24d3d44dc5e5eb5ab5d94a82dc0a44105baa4b30a48d168d80ee02` |
| `liaison_2025-10-23_full.pdf` | 6,051,966 | 53 | Limited but meaningful | 763 | `529323a302533fcaa3bebebb0ea4716e5d67d1ca315ce89cc531d81fd0e0cfe6` |
| `liaison_2025-12-21_full.pdf` | 1,898,847 | 13 | Limited but meaningful | 374 | `ce3acbca5ee3eba87f7f1ab011d332d9302e077601e92ab5743f8903c24e85ba` |
| `liaison_2026-02-02_full.pdf` | 5,778,558 | 35 | Image-only | 0 | `6bf5490ca7a703540e3ccd5422e139a4a21952529f18b81287e608ec02e11d1a` |
| `liaison_2026-03-08_full.pdf` | 2,208,004 | 13 | Image-only | 0 | `7a4fa7f2e26ef51fdbc3d68315d0b9e8ed2f953a4a988d37a9b1772a969456c5` |
| `liaison_2026-04-13_full.pdf` | 6,096,434 | 34 | Image-only | 0 | `5038760daa8c77d6a42a3c1975d982c21060b6b494da237ebfa838c04ffd07e6` |
| `liaison_2026-05-11_full.pdf` | 6,959,824 | 35 | Image-only | 0 | `e3317590e5b3c73d21da1c47a2a709b3dbd462c8cd19f315c5ad2317dd645f0a` |
| `liaison_2026-06-30_graphs.pdf` | 1,250,859 | 12 | Image-only | 0 | `19fb7507131a4ea5ca4a7e8a7cd1ad92755faad5192cbd048e366e715b90bbcb` |
| `liaison_2026-06-30_tables.pdf` | 2,846,930 | 9 | Image-only | 0 | `ee316256c4e6e95fdfcc8b7d23d373e5539a3e8a6dbf0687eca6239a92c70445` |
| `liaison_2026-07-26_graphs.pdf` | 777,764 | 8 | Image-only | 0 | `fc8788944149116b04971cf2d38e4c74d3a70c9a03bcd2b13e2ea938d7091197` |
| `liaison_2026-07-26_tables.pdf` | 1,459,079 | 5 | Image-only | 0 | `2ecdc398768844da1c51fa9069cc886ffc244317b6add2adf36ae559a08ec253` |
| `liaison_2026-08-05_graphs.pdf` | 1,212,875 | 13 | Image-only | 0 | `91865e15ada9599cf8cc6e1902c9fcf7148f3e40ee4a4991c09f666f91c91884` |
| `liaison_2026-08-05_tables.pdf` | 3,289,212 | 10 | Image-only | 0 | `47ced4c69acc806801d3e1b6308ca17f2edf0e9b8c455e0b1fbb0d2a89c555b7` |
| `mainstreet_2026-02-22_full.pdf` | 1,095,481 | 17 | Meaningful | 2,069 | `75ad0c94f0b75f1de66d94744e79430b9c831c97d23adc9f449a6634468783b9` |
| `mainstreet_2026-02-22_public.pdf` | 1,092,769 | 17 | Meaningful | 1,493 | `6d8dd66cfe2a73b75391610a50f605f1b2025a7ce279db3d60f2f542c4377c8d` |
| `mainstreet_2026-06-18_full.pdf` | 7,374,113 | 28 | Meaningful | 4,742 | `9ff554329604bd43dc07d97e37e38a3153b4e2c3256f0ddb6cfbeff17c1261a9` |
| `mainstreet_2026-06-18_public.pdf` | 7,366,869 | 28 | Meaningful | 3,622 | `5a30698bb85abb394f2b6d9d5823ff07fbaddba2eb202923c04d19686615d1f4` |
| `pallas_2025-06-07_full.pdf` | 2,842,506 | 19 | Meaningful | 1,740 | `98fe3381c205bdf669eb288df0fdea01e2431c5eb38bb3c53d76567729a2715b` |
| `pallas_2026-03-08_full.pdf` | 3,790,871 | 27 | Meaningful | 2,064 | `005426a871db36dbbcbd876540c2cb6438bb26efab9f3850ac1233e3a50de82c` |

## QA performed

- Every acquired URL returned HTTP 200 and the expected first-party file type.
- SHA-256 and byte size were recalculated locally after download.
- `file` and Poppler recognized all 22 PDFs as valid, unencrypted PDFs.
- `pdfinfo` reported 450 pages. Poppler rendered exactly 450 page images at 72 DPI.
- Contact sheets covering every page were inspected. Tables, charts, methods, headings, and footnotes were legible; no missing pages or visible rendering defects were found.
- Direct `pdftotext` extraction was tested on every PDF. Ten later Liaison documents yielded only page-break characters and are classified as image-only.
- Both Canada Pulse OOXML archives passed integrity tests.
- The Canada Pulse workbook was imported and inspected read-only with the bundled spreadsheet artifact runtime. It contains one sheet, `Toronto Civic 10 25`, with a used range of `A1:C449`. The relevant mayoral block is `A333:C370`, including the six published result rows and following Sigma rows. The Toronto base is 406 unweighted and 406 weighted. The workbook reports Chow at 27% and includes a 6% `Nobody, I won't vote` row.
- The Canada Pulse DOCX was text-extracted and checked against the workbook. It says the survey was administered online by Sago, fielded from 2025-09-30 to 2025-10-06, and released on 2025-10-21. Its prose reports Chow at 29% rather than the workbook's 27% and omits the workbook's 6% nonvoter response; the detailed workbook values are preserved in the reading table.

## Source differences that must not be silently normalized

1. **Canada Pulse mode:** legacy `polls.csv` stores `IVR`; the first-party media release says the survey was conducted online by Sago. The normalized source contract records `online`, while the live legacy row remains unchanged pending a deliberate consumer migration.
2. **Canada Pulse timing:** legacy `polls.csv` uses 2025-10-06 as both conducted and published date; the normalized source contract records the first-party 2025-09-30 to 2025-10-06 fieldwork range and 2025-10-21 release date.
3. **Abacus timing:** production uses 2026-01-27 as publication date; the first-party Coletto article is dated 2026-03-04 for fieldwork ending 2026-01-27.
4. **Other source dates:** several legacy rows use fieldwork end as publication date even though the first-party report is dated later. The normalized sample table preserves the source-backed dates without silently changing the live legacy input.
5. **Dependent readings:** Forum September 2025's four extracted ballot readings and Pallas March 2026's four readings share respondents within their respective samples. Their parent-sample lineage is explicit; reading count must never substitute for poll-sample count.
6. **Canada Pulse release/workbook results:** the detailed workbook reports Chow at 27% versus 29% in release prose and includes a 6% nonvoter row omitted from the release. The source contract preserves the workbook reading and documents the disagreement rather than forcing equivalence.
7. **Mainstreet editions:** the public and full PDFs are not separate evidence. The public editions retain questions, toplines, and bases but omit subgroup response cells that are present in the full editions.

## Access, rights, and operational difficulty

The acquisition itself is practical. Most artifacts live at stable first-party attachment or media-library URLs and can be downloaded directly once their release page is known. Current-cycle recovery required targeted discovery rather than a paid data relationship. Liaison is the largest automation cost: filenames and packaging change over time, and its 2026 PDFs are images rather than machine-readable tables. A recurring ingestion process should therefore combine release-page discovery, checksum-based local archiving, OCR/table extraction, and human verification.

There are three access caveats:

1. **Abacus:** the first-party article requests that the reader claim a free post. No access control was bypassed, no gated content was archived, and no full table book was found. This is the only unresolved current-sample document gap.
2. **Mainstreet:** the full static PDFs returned HTTP 200 without authentication, but the site UI labels them `Subscriber Exclusive`. They were retained only in the local audit corpus. Public redistribution, durable archival use, and model-audit use should be clarified with Mainstreet even though the files are technically reachable.
3. **No blanket reuse licence:** no recovered source displayed an explicit licence authorizing republication or redistribution of the full documents. Public accessibility is not itself a reuse grant. The corpus should remain gitignored and internal until rights are established.

## Bottom line

For the current mayoral cycle, getting the detailed source material is not the bottleneck: the project can recover full detail for **18/19 samples (94.7%)** without buying a package. The harder recurring work is provenance, OCR, dependent-reading lineage, and rights—not basic download availability. Before paying for pollster PDFs, the useful question is whether a purchase closes the one current Abacus gap or, more importantly, supplies a durable historical archive and machine-readable delivery that public first-party pages do not.
