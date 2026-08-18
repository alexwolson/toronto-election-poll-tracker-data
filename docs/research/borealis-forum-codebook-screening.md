# Borealis Forum public-codebook screening

**Checked:** 2026-08-17  
**Scope:** the 37 unrestricted DOCX codebooks in the Forum Research Toronto municipal collections for 2013, 2014, and 2018  
**Access boundary:** public metadata and public codebook files only; no credentials were used and no restricted respondent file was requested or downloaded

## Result

The public codebooks identify **31 relevant studies, 6 not-relevant studies, and 0 uncertain studies** under a narrow rule: a study is relevant when its codebook contains at least one contemporaneous, citywide mayoral vote-intention question. “Not relevant” here does not mean the survey has no research value; it means it cannot supply a pre-election citywide mayoral ballot reading.

The 31 relevant files represent **at most 30 distinct respondent samples**. Files [8633](https://borealisdata.ca/api/access/datafile/8633) and [8635](https://borealisdata.ca/api/access/datafile/8635) both say April 11, 2013 and `n=870`, but contain different scenario sets. Their shared-sample relationship cannot be resolved from the codebooks.

The screen supports **21 likely study-level matches** to the unresolved Forum proxy queue:

- 16 have the same codebook fieldwork date and legacy proxy date;
- 5 have a short, candidate-compatible date shift that is plausibly fieldwork-to-publication timing; and
- 10 relevant codebooks have no safe proxy match.

Those 21 studies touch 49 unresolved legacy reading rows because early Forum studies tested multiple hypothetical candidate fields in one sample. They are **not promoted mappings**. The codebooks contain question wording and value labels but no results, so respondent data must still reproduce each estimate before any canonical CSV changes.

## Acquisition and verification

The current published records are:

| Collection | DOI | Dataset ID | Published version | Release time | Codebooks |
|---|---|---:|---:|---|---:|
| 2013 | [10.5683/SP3/2ANYFR](https://doi.org/10.5683/SP3/2ANYFR) | 356 | 3.5 | 2018-04-24T18:37:27Z | 12 |
| 2014 | [10.5683/SP3/IM2A0R](https://doi.org/10.5683/SP3/IM2A0R) | 886 | 5.4 | 2017-11-30T12:07:43Z | 15 |
| 2018 | [10.5683/SP2/QCPM89](https://doi.org/10.5683/SP2/QCPM89) | 71163 | 3.1 | 2019-09-17T18:14:45Z | 10 |

All 37 unrestricted files were retrieved through Borealis's unauthenticated `/api/access/datafile/{file-id}` endpoint into the gitignored directory `data/source_documents/restricted_forum_borealis/codebooks/`. Each file passed all of the following checks:

- exact byte count against the current dataset metadata: **37/37**;
- exact metadata MD5: **37/37**;
- locally computed SHA-256 recorded in the draft manifest: **37/37**;
- valid OOXML ZIP container (`unzip -t`): **37/37**; and
- rendered-document visual review: **37/37 files and all 296 pages**.

The 2013 and 2014 metadata declares the codebooks as `application/octet-stream`; signature inspection identifies the downloads as valid OOXML Word documents. Every rendered page was legible. No clipping, corruption, blank page, or missing page was observed. Source pagination sometimes places a question stem at the bottom of one page and its labels on the next, but the content remains readable.

The full per-file bytes, MD5, SHA-256, paired restricted-data file ID, page count, ballot stems, candidate universe, completeness flags, source defects, and tentative proxy IDs are in the tracked [`borealis-forum-codebook-screening-manifest.csv`](borealis-forum-codebook-screening-manifest.csv). A JSON working copy is also retained for this session at:

- `/private/tmp/borealis_codebook_screening/borealis_codebook_screening_manifest.json`

The manifest is a screening record, not a canonical poll-source table. Its tentative proxy links cannot become model evidence until the paired respondent data reproduce the published values.

## What the codebooks establish

All 37 codebooks provide first-page study metadata, fieldwork dates, sample size, an IVR/random-digit-dialling method statement, the phrase “Representative Weighting,” questionnaire text, and response value labels. The relevant set contains 129 ballot scenarios in total:

| Year | Codebooks | Relevant | Not relevant | Ballot scenarios |
|---:|---:|---:|---:|---:|
| 2013 | 12 | 12 | 0 | 67 |
| 2014 | 15 | 13 | 2 | 56 |
| 2018 | 10 | 6 | 4 | 6 |
| **Total** | **37** | **31** | **6** | **129** |

The scenario count is not a poll count. Most 2013 and early-2014 codebooks test several hypothetical fields within one respondent sample. Those dependent readings must remain attached to a single sample. In contrast, the six relevant 2018 studies each contain one Tory–Keesmaat ballot and an undecided-voter leaning follow-up. The October 6, 2014 study also contains a leaning follow-up.

The codebooks do **not** provide:

- response counts or percentages;
- unweighted or weighted bases for the ballot questions;
- a usable weight-variable name;
- weighting targets, formula, or calibration details; or
- enough information to reproduce a decided-and-leaning estimate.

“Representative Weighting” is therefore a study-level claim, not an implementable weight. The restricted respondent file paired in public metadata is still required for every relevant study that is to become a model observation.

The twelve 2013 filenames include `(incomplete)`. Inspection shows that they do contain questionnaire wording and response value labels. For this project, the material incompleteness is the absence of results and an actionable weight definition—not missing mayoral ballot text.

## File-by-file screen

| Year | File | Fieldwork | n | Ballot scenarios | Screen | Proxy disposition |
|---:|---:|---|---:|---:|---|---|
| 2013 | [8636](https://borealisdata.ca/api/access/datafile/8636) | 2013-01-25 | 1143 | 7 | relevant | likely → 2013-01-25 (same date) |
| 2013 | [8637](https://borealisdata.ca/api/access/datafile/8637) | 2013-02-22 | 838 | 3 | relevant | no safe proxy match |
| 2013 | [8633](https://borealisdata.ca/api/access/datafile/8633) | 2013-04-11 | 870 | 4 | relevant | no safe proxy match |
| 2013 | [8635](https://borealisdata.ca/api/access/datafile/8635) | 2013-04-11 | 870 | 5 | relevant | no safe proxy match |
| 2013 | [8630](https://borealisdata.ca/api/access/datafile/8630) | 2013-05-10 | 1011 | 8 | relevant | likely → 2013-05-13 (date shift) |
| 2013 | [8638](https://borealisdata.ca/api/access/datafile/8638) | 2013-06-25 | 1260 | 10 | relevant | no safe proxy match |
| 2013 | [8631](https://borealisdata.ca/api/access/datafile/8631) | 2013-07-29 | 1414 | 4 | relevant | no safe proxy match |
| 2013 | [8634](https://borealisdata.ca/api/access/datafile/8634) | 2013-08-29 | 870 | 5 | relevant | likely → 2013-08-29 (same date) |
| 2013 | [8632](https://borealisdata.ca/api/access/datafile/8632) | 2013-09-20 | 1119 | 5 | relevant | no safe proxy match |
| 2013 | [8639](https://borealisdata.ca/api/access/datafile/8639) | 2013-10-28 | 1125 | 5 | relevant | no safe proxy match |
| 2013 | [8640](https://borealisdata.ca/api/access/datafile/8640) | 2013-11-04 | 1418 | 4 | relevant | likely → 2013-11-04 (same date) |
| 2013 | [8629](https://borealisdata.ca/api/access/datafile/8629) | 2013-12-09 | 914 | 7 | relevant | no safe proxy match |
| 2014 | [9028](https://borealisdata.ca/api/access/datafile/9028) | 2014-01-06 | 1105 | 7 | relevant | likely → 2014-01-06 (same date) |
| 2014 | [9033](https://borealisdata.ca/api/access/datafile/9033) | 2014-01-22 | 1063 | 7 | relevant | likely → 2014-01-22 (same date) |
| 2014 | [9030](https://borealisdata.ca/api/access/datafile/9030) | 2014-02-06 | 769 | 8 | relevant | likely → 2014-02-09 (date shift) |
| 2014 | [9034](https://borealisdata.ca/api/access/datafile/9034) | 2014-02-24 | 1063 | 5 | relevant | likely → 2014-02-24 (same date) |
| 2014 | [9026](https://borealisdata.ca/api/access/datafile/9026) | 2014-03-13 | 1271 | 3 | relevant | likely → 2014-03-13 (same date) |
| 2014 | [9027](https://borealisdata.ca/api/access/datafile/9027) | 2014-03-27 | 1271 | 2 | relevant | likely → 2014-03-27 (same date) |
| 2014 | [9029](https://borealisdata.ca/api/access/datafile/9029) | 2014-04-14 | 882 | 6 | relevant | likely → 2014-04-14 (same date) |
| 2014 | [9031](https://borealisdata.ca/api/access/datafile/9031) | 2014-05-01 | 888 | 3 | relevant | likely → 2014-05-01 (same date) |
| 2014 | [9032](https://borealisdata.ca/api/access/datafile/9032) | 2014-05-06 | 944 | 4 | relevant | no safe proxy match |
| 2014 | [9446](https://borealisdata.ca/api/access/datafile/9446) | 2014-07-02 | 1182 | 4 | relevant | likely → 2014-07-02 (same date) |
| 2014 | [9444](https://borealisdata.ca/api/access/datafile/9444) | 2014-08-06 | 1268 | 3 | relevant | likely → 2014-08-06 (same date) |
| 2014 | [9447](https://borealisdata.ca/api/access/datafile/9447) | 2014-09-08 | 1069 | 3 | relevant | likely → 2014-09-08 (same date) |
| 2014 | [9445](https://borealisdata.ca/api/access/datafile/9445) | 2014-10-06 | 1218 | 1 | relevant | likely → 2014-10-06 (same date) |
| 2014 | [9448](https://borealisdata.ca/api/access/datafile/9448) | 2014-11-25 | 950 | 0 | not relevant | not applicable |
| 2014 | [10271](https://borealisdata.ca/api/access/datafile/10271) | 2014-12-17–18 | 1001 | 0 | not relevant | not applicable |
| 2018 | [71165](https://borealisdata.ca/api/access/datafile/71165) | 2018-02-07–08 | 977 | 0 | not relevant | not applicable |
| 2018 | [72467](https://borealisdata.ca/api/access/datafile/72467) | 2018-06-26–30 | 2548 | 0 | not relevant | not applicable |
| 2018 | [72463](https://borealisdata.ca/api/access/datafile/72463) | 2018-07-26–29 | 2197 | 0 | not relevant | not applicable |
| 2018 | [72461](https://borealisdata.ca/api/access/datafile/72461) | 2018-07-27 | 1362 | 1 | relevant | likely → 2018-07-27 (same date) |
| 2018 | [72460](https://borealisdata.ca/api/access/datafile/72460) | 2018-08-23–26 | 1264 | 1 | relevant | likely → 2018-08-27 (date shift) |
| 2018 | [75076](https://borealisdata.ca/api/access/datafile/75076) | 2018-09-06 | 1206 | 1 | relevant | no safe proxy match |
| 2018 | [75072](https://borealisdata.ca/api/access/datafile/75072) | 2018-09-20–23 | 944 | 1 | relevant | likely → 2018-09-24 (date shift) |
| 2018 | [75078](https://borealisdata.ca/api/access/datafile/75078) | 2018-10-01–03 | 987 | 1 | relevant | likely → 2018-10-05 (date shift) |
| 2018 | [75077](https://borealisdata.ca/api/access/datafile/75077) | 2018-10-09–10 | 1206 | 1 | relevant | likely → 2018-10-10 (same date) |
| 2018 | [75074](https://borealisdata.ca/api/access/datafile/75074) | 2018-10-19 | 265 | 0 | not relevant | not applicable |

The five date-shift candidates are:

| Codebook fieldwork | Legacy proxy date | Why the link is plausible but unconfirmed |
|---|---|---|
| 2013-05-10 | 2013-05-13 | The proxy candidate fields are present among file 8630's eight scenarios; the three-day shift is publication-like. |
| 2014-02-06 | 2014-02-09 | Both proxy candidate fields are present among file 9030's eight scenarios; the three-day shift is publication-like. |
| 2018-08-23–26 | 2018-08-27 | Fieldwork ends one day before the proxy date; both use Tory–Keesmaat. |
| 2018-09-20–23 | 2018-09-24 | Fieldwork ends one day before the proxy date; both use Tory–Keesmaat. |
| 2018-10-01–03 | 2018-10-05 | The two-day shift is publication-like; both use Tory–Keesmaat. |

## Source and lineage issues

The machine-readable manifest records source-specific defects. The material ones are:

- Files 8633 and 8635 share a date and sample size but different study codes and scenario sets. Treating them as independent would risk double-counting.
- File 9032's title says June 2014 although its stated survey date is May 6.
- Files 9444–9448 retain “March 2014” in their titles despite July, August, September, October, and November survey dates.
- File 9445's October ballot stem says Rob Ford, but its response labels correctly encode the post-withdrawal field as Doug Ford, John Tory, and Olivia Chow. The labels govern the candidate field.
- File 9447's Q2b repeats a stem naming Olivia Chow, but its value labels omit her; the legacy two-candidate Ford–Tory reading is therefore plausible but still requires data verification.
- File 10271 describes a Toronto study as “National Adult”/“Ontario Provincial,” and its paired restricted filename contains 2015 although the codebook says December 17–18, 2014.
- File 75077 uses a federal-election eligibility screener in a municipal survey.
- File 75078 mislabels a geography screener as a mayoral ballot; Q1A, not S2, is the actual Tory–Keesmaat ballot.
- File 75074 is a Ward 7 council survey. It is not a citywide mayoral poll.

The restricted data filenames are also unreliable date evidence. In particular, the 2013 respondent filenames all include `20131219`; the codebook survey date and study code must remain authoritative until the data are inspected.

## Blockers and next action after approval

The public-codebook step is complete. The remaining blockers are empirical rather than documentary:

1. Download only the 31 paired restricted respondent files for relevant studies, preferably both ingested TAB and original SAV forms where available. The exact paired file IDs are already recorded in the draft manifest.
2. Identify the respondent weight and ballot variables from the data dictionaries/labels in the files themselves.
3. Reconstruct each decided-and-leaning reading from one respondent sample, preserving every tested scenario as a dependent reading.
4. Test whether files 8633 and 8635 share respondent records before assigning sample IDs.
5. Compare reconstructed values with the 49 tentative legacy proxy rows. Promote only exact reproductions or explicitly reconciled rounding differences; leave the ten unmatched studies as newly discovered evidence rather than forcing them onto unrelated proxies.

No shared canonical CSV was edited during this screening.

## Primary sources

- [2013 Borealis dataset](https://doi.org/10.5683/SP3/2ANYFR) and [public metadata API](https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi:10.5683/SP3/2ANYFR)
- [2014 Borealis dataset](https://doi.org/10.5683/SP3/IM2A0R) and [public metadata API](https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi:10.5683/SP3/IM2A0R)
- [2018 Borealis dataset](https://doi.org/10.5683/SP2/QCPM89) and [public metadata API](https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi:10.5683/SP2/QCPM89)
