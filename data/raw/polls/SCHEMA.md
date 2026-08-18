# Poll source contract (model-neutral; not yet consumed by the live model)

These five CSVs normalize newly acquired poll evidence without changing or
feeding `polls.csv`, `ward_poll_readings.csv`, the live snapshot, or any legacy
model input. The tracked current-cycle inventory contains 31 source documents,
31 document/sample links, 25 respondent samples, 57 total readings, and 251
response rows. Eighteen citywide mayoral samples have completed extraction into
44 dependent readings and 202 response rows; the unrecovered Abacus sample is
explicitly `blocked` with no invented reading. Six Council samples contribute
the other 13 Council/ward-mayoral readings and 49 response rows. The 44 mayoral
readings are alternate questions, fields, denominators, or transformations from
18 sample units, not 44 polls.
The identities are deliberately separate:

- a **source document** is one physical or known-but-unretrieved artifact;
- a **poll sample** is one separately recruited respondent sample;
- `poll_sample_documents.csv` is their many-to-many junction, because one
  report can contain several separately recruited waves;
- a **poll reading** is one question, scenario, population, or denominator from
  a sample; and
- every reading with the same `poll_sample_id` is dependent evidence, never
  another Distinct Poll Sample.

`load_poll_source_bundle()` requires exact headers and validates without silent
coercion. Default manifest mode permits retrieval and extraction gaps when
their statuses are explicit. `require_audited_sources=True` additionally
requires every sample to be `extracted` and every reading's source to be
`retrieved` with `visual_qa_status=passed` exactly. This is a source-audit
requirement, not a decision that a reading is comparable or forecast-eligible.
`verify_poll_source_artifacts()` checks local existence, containment, byte size,
SHA-256 and practical signatures for PDF, HTML, legacy XLS, and ZIP-based XLSX
and DOCX files. OOXML verification opens the ZIP, checks every member's CRC, and
requires `[Content_Types].xml` plus `word/document.xml` for DOCX or
`xl/workbook.xml` for XLSX.

## source_documents.csv

| Column | Type | Required | Description |
|---|---|---|---|
| `source_document_id` | normalized string | yes | Stable physical/expected artifact identifier |
| `document_role` | enum | yes | `release`, `article`, `questionnaire`, `tables`, `methodology`, `microdata`, or `other` |
| `publisher_url` | HTTP(S) URL | yes | Original publisher URL, including a dead original when recovery used an archive |
| `retrieval_url` | HTTP(S) URL | conditional | Exact acquisition URL; required for a retrieved artifact |
| `retrieval_status` | enum | yes | `retrieved`, `not_retrieved`, `access_pending`, `dead_link`, or `corrupt` |
| `retrieved_at` | offset-aware timestamp | conditional | Required for a retrieved artifact |
| `media_type` | MIME type | conditional | Required for a retrieved artifact; optional when only a lead is known |
| `sha256` | 64 lowercase hex | conditional | Required for a retrieved artifact |
| `local_path` | relative POSIX path | conditional | Gitignored path below `data/source_documents/`; required when retrieved |
| `byte_size` | positive integer | conditional | Archived byte count; required when retrieved |
| `page_count` | positive integer | conditional | Required for a retrieved PDF |
| `sheet_count` | positive integer | conditional | Required for a retrieved spreadsheet |
| `text_layer_status` | enum | conditional | `present`, `partial`, `absent`, or `not_applicable`; required when retrieved |
| `visual_qa_status` | enum | yes | `pending`, `passed`, `failed`, or `not_applicable`; unretrieved artifacts are not applicable except that an inspected corrupt copy may be `failed` |
| `access_class` | enum | yes | `public`, `licensed`, or `institutional_restricted` |
| `redistribution_status` | enum | yes | `permitted`, `prohibited`, or `unknown` |
| `reuse_terms_url` | HTTP(S) URL | no | Published licence/reuse terms |
| `notes` | string | conditional | Required for gaps, non-public access, or anything not known redistributable |

The manifest records rights; it does not grant them. Restricted or licensed
bytes remain outside git. A `corrupt` row may retain any known artifact metadata
without pretending recovery succeeded.

## poll_sample_documents.csv

| Column | Type | Required | Description |
|---|---|---|---|
| `poll_sample_id` | normalized string | yes | Linked respondent sample |
| `source_document_id` | normalized string | yes | Linked physical/expected artifact |
| `sample_locator` | string | no | Wave name, page range, sheet, or other within-document locator |
| `notes` | string | no | Relationship qualifications |

Each pair is unique. Every sample and every document must have a link. A
reading may cite a document only when its sample/document pair exists.

## poll_samples.csv

| Column | Type | Required | Description |
|---|---|---|---|
| `poll_sample_id` | normalized string | yes | Stable respondent-sample identifier |
| `election_cycle_id` | normalized string | yes | Election cycle, e.g. `toronto-2026` |
| `pollster` | string | yes | Polling organization |
| `sponsor` | string | no | Commissioning organization |
| `geography_type` | enum | yes | `citywide` or `ward` |
| `geography_id` | normalized string | yes | Stable sampled geography |
| `fieldwork_start` | YYYY-MM-DD | yes | First fieldwork date |
| `fieldwork_end` | YYYY-MM-DD | yes | Last fieldwork date; cannot follow publication |
| `publication_date` | YYYY-MM-DD | yes | Publisher-local release date |
| `publication_at` | offset-aware timestamp | conditional | Actual time when known |
| `publication_time_precision` | enum | yes | `exact` or `date_only` |
| `evidence_available_at` | offset-aware timestamp | yes | Earliest safe Analysis Cutoff |
| `collection_mode` | normalized string | yes | Source-reported mode category |
| `recruited_sample_size` | positive integer | no | Overall recruited sample, not a reading base |
| `extraction_status` | enum | yes | `pending`, `in_progress`, `extracted`, or `blocked` |
| `notes` | string | no | Source qualifications |

`pending` samples have no readings; `extracted` samples require readings.
`in_progress` and `blocked` can retain partial work without becoming
source-audited. A date-only publication leaves `publication_at` blank and uses
no earlier than the next Toronto calendar day for `evidence_available_at`.

## poll_readings.csv

One row per candidate-choice question/scenario/denominator. It records source
semantics without deciding comparability or forecast eligibility. Most rows are
vote intention; the explicit `reading_purpose` field keeps the few conditional,
routed, and context-only readings from being mistaken for general support.

| Column | Type | Required | Description |
|---|---|---|---|
| `poll_reading_id` | normalized string | yes | Stable reading identifier |
| `poll_sample_id` | normalized string | yes | Respondent sample and dependence unit |
| `source_document_id` | normalized string | yes | Supporting linked artifact |
| `source_locator` | string | yes | Auditable page/table/sheet/range, e.g. `pages 3-4` or `sheet Q5!A1:J12` |
| `contest_type` | enum | yes | `mayoral` or `council` |
| `contest_id` | normalized string | yes | Contested office |
| `question_order_status` | enum | yes | `reported` or `not_reported` |
| `question_order` | positive integer | conditional | Questionnaire order, only when actually reported |
| `document_display_order` | positive integer | no | Table/page presentation order; never substitutes for questionnaire order |
| `question_text_status` | enum | yes | `reported` or `not_reported` |
| `question_text` | string | conditional | Exact wording when reported; blank rather than reconstructed from outcome prose when not reported |
| `scenario_label` | string | no | Alternate ballot/presentation label |
| `population` | string | yes | Exact source population definition |
| `turnout_screen` | enum | yes | `none`, `eligible_voters`, `registered_voters`, `likely_voters`, `past_voters`, `custom`, or `not_reported` |
| `turnout_screen_text` | string | conditional | Required for `custom` |
| `denominator_type` | enum | yes | `all_respondents`, `decided_respondents`, `valid_responses`, `custom`, or `not_reported` |
| `denominator_text` | string | conditional | Exact wording unless unreported |
| `unweighted_base_status` | enum | yes | `reported` or `not_reported` |
| `unweighted_base` | positive integer | conditional | Reading-level respondent count |
| `weighted_base_status` | enum | yes | `reported` or `not_reported` |
| `weighted_base` | positive decimal | conditional | Reading-level weighted base |
| `reported_base_status` | enum | yes | `reported` or `not_reported` |
| `reported_base` | positive decimal | conditional | Source base when it is reported only as generic `n`, without identifying weighted/unweighted kind |
| `tested_choice_set_status` | enum | yes | `complete`, `partial`, or `unknown` |
| `response_coverage` | enum | yes | `complete`, `partial`, or `unknown` |
| `reported_share_unit` | enum | yes | `percent` or `proportion` |
| `reported_share_precision` | non-negative integer | yes | Decimal places used by the source in its reported unit |
| `notes` | string | no | Source qualifications |
| `reading_purpose` | enum | yes | `general_vote_intention`, `conditional_lean_followup`, `routed_subgroup`, or `context_only` |

Missing bases stay explicitly `not_reported`; they are never copied from a
headline sample size. An unweighted base cannot exceed a known recruited size.

`general_vote_intention` is a first-choice support distribution for the stated
reading population, including pollster-derived decided or decided-and-leaning
products and alternate candidate fields. `conditional_lean_followup` is asked
only of initially unsure respondents. `routed_subgroup` is asked only of a
subgroup selected by a substantive earlier answer. `context_only` covers
candidate consideration or other non-vote support evidence. Final-Ballot and
scenario compatibility remain separate, cutoff-dependent eligibility checks.

## poll_responses.csv

| Column | Type | Required | Description |
|---|---|---|---|
| `poll_reading_id` | normalized string | yes | Parent reading |
| `response_option_id` | normalized string | yes | Identifier unique within the reading |
| `response_kind` | enum | yes | `candidate`, `undecided`, `other`, `refusal`, `dont_know`, `would_not_vote`, `none_of_the_above`, `no_answer`, or `combined_residual` |
| `candidate_id` | normalized string | conditional | Candidate rows only |
| `candidate_name` | string | conditional | Candidate rows only |
| `candidate_observation_status` | enum | conditional | Candidate rows only; see below |
| `response_label` | string | conditional | Exact published/offered label |
| `option_order` | positive integer | no | Published response-row order when shown; never implies questionnaire presentation order |
| `reported_value` | string | conditional | Exact numeric token as published, optionally including `%` |
| `share` | decimal in [0,1] | conditional | Normalized value, required when a numeric value was published |
| `notes` | string | no | Suppression/rounding qualifications |

Candidate status is exactly `individually_published`,
`offered_not_individually_published`, `known_not_offered`, or
`tested_ballot_unknown`. None implies zero. Non-candidate kinds remain separate
and never automatically become the Unmeasured Candidate Tail.

Across the complete bundle, one nonblank `candidate_id` must map to exactly one
canonical `candidate_name`. Source-exact spelling remains in `response_label`,
which may legitimately vary between documents; for example, canonical
`Ana Bailão` can retain a published `Ana Bailao` label.

For each numeric row, `reported_value` must normalize exactly to `share` under
the reading's unit. Complete totals are checked using a tolerance derived from
the number of published rows and declared precision, so legitimate whole-point
rounding totals such as 99%, 101%, or (with enough rows) 102% are retained
without permitting arbitrary discrepancies.

---

# polls.csv Schema (legacy live input)

One row per published **citywide** mayoral poll. Ward-level subsamples do not
belong here (they would bias the citywide average toward that ward's lean) —
record their reported response options in `ward_poll_readings.csv` and list
their poll_id in `EXCLUDED_POLL_IDS`
in `scripts/fetch_polls.py` so the Wikipedia fetch doesn't re-add them.

## Fixed metadata columns

| Column | Type | Required | Description |
|---|---|---|---|
| `poll_id` | string | yes | Unique identifier, e.g. `liaison-2025-11-01` |
| `firm` | string | yes | Polling firm name |
| `date_conducted` | YYYY-MM-DD | yes | Date range end if a range was reported |
| `date_published` | YYYY-MM-DD | yes | Date the poll was publicly released |
| `sample_size` | integer | no | Blank if not reported |
| `methodology` | string | no | e.g. `online-panel`, `IVR`, `phone` |
| `field_tested` | string | yes | Comma-separated list of candidate keys tested in this poll (must match column names exactly) |
| `notes` | string | no | Anything noteworthy |

## Candidate share columns

Any numeric column not in the fixed metadata set above is treated as a candidate share column. Columns are added as candidates enter polling — there is no fixed set.

Use the candidate's short lowercase key as the column name (matching the key used in `field_tested`). For example: `chow`, `bradford`, `bailao`, `tory`, `doe`. Add `undecided` for the undecided share — it is treated as a share column like any other.

Older rows leave columns for candidates who weren't tested blank (empty cell, not `0`).

## Validation rules

- All share columns (candidate columns + `undecided`) per row must sum to ≤ 1.0
- Every key listed in `field_tested` must have a corresponding column in the CSV
- Every share column that has a value in a given row must be listed in `field_tested` for that row
- `date_conducted` must be ≤ `date_published`
- `sample_size` must be a positive integer if present
- `poll_id` must be unique across all rows

---

# ward_poll_readings.csv Schema (current)

One row per response option in a published ward-level councillor poll. This is
the only ward-poll input used by Council snapshot schema v3. It preserves the
source's candidate field and denominator; an absent candidate is unobserved,
not zero, and residual and undecided responses remain explicit.

Required fields are `ward`, `poll_id`, `firm`, `date_conducted`,
`date_published`, `sample_size`, `methodology`, `denominator`, `ballot_status`,
`candidate_id`, `candidate_name`, `share`, `is_incumbent`, `is_residual`,
`registration_status`, and `undecided_share`. Optional `source_url` and `notes`
fields preserve provenance and qualifications. Shares must be finite
proportions in `[0, 1]`; candidate IDs must be unique within a poll;
candidate/residual shares must sum to the stated denominator within tolerance;
and `undecided_share` must agree across every row for the poll.

---

# ward_polls.csv Schema (legacy, not consumed by v3)

This synthetic input is retained only to preserve repository history. Do not
add new records or use it for public forecasts. Converting vote intention into
an editorial `inc_win_share` was retired in Council schema v3.

One row per published **ward-level** councillor poll. Feeds the ward-level
polling override in the superseded v0.2 specification.

| Column | Type | Required | Description |
|---|---|---|---|
| `ward` | integer | yes | Ward number, 1–25 |
| `poll_id` | string | yes | Unique identifier, e.g. `forum-ward13-2026-06-23` |
| `firm` | string | no | Polling firm name |
| `date_conducted` | YYYY-MM-DD | no | Date range end if a range was reported |
| `date_published` | YYYY-MM-DD | yes | Date the poll was publicly released |
| `sample_size` | integer | yes | Ward respondents |
| `methodology` | string | no | e.g. `IVR`, `online-panel` |
| `inc_win_share` | float | yes | Retired synthetic probability used only by the superseded model; do not derive new values |
| `notes` | string | no | Topline shares, derivation notes, anything noteworthy |

## Validation rules

- `ward` must be 1–25
- `inc_win_share` must be in [0, 1]
- `sample_size` must be a positive integer
- `date_conducted` must be ≤ `date_published`
- (`ward`, `poll_id`) pairs must be unique

---

# approval_ratings.csv Schema

One row per published mayoral approval reading. Required columns are `date`,
`source`, `approve`, `disapprove`, and `not_sure`; `methodology` is optional.
The three response shares must be finite proportions in `[0, 1]` and sum to
`1 ± 0.01`. Source/date pairs must be unique. Approval is contextual evidence
and is never an input to candidate vote shares or win probabilities.

# Historical mayoral reconstruction (non-live)

`backend/model/historical_mayoral.py` is the bounded, adapter-ready historical
seam. `scripts/reconstruct_historical_mayoral.py --check` verifies its three
generated tables without changing the live model or snapshots:

- `data/raw/elections/mayoral_elections.csv` records election type/date,
  nomination close, a conservative Final Ballot known-by boundary with its
  evidence status, and official result provenance. The boundary may be an
  observed certification date, a public announcement, or a statutory deadline;
  it does not pretend to recover an irrelevant internal action instant.
  Because the source precision is a date, the derived safe replay cutoff is
  Toronto midnight at the start of the following calendar day.
- `data/raw/elections/mayoral_outcomes.csv` records every certified mayoral
  candidate in 2014, 2018, 2022, and 2023, with votes, valid-vote denominator,
  exact derived share, winner flag, and source locator. `candidate_name` is the
  canonical cross-cycle display name while `candidate_name_as_reported` keeps
  the source ordering/spelling; `candidate_id` defines identity. It has no
  aggregate residual row.
- `legacy_historical_poll_crosswalk.csv` covers every legacy poll ID and marks
  it `mapped`, `unresolved`, or `non_poll`. An unresolved staging ID is an
  inventory lead, not a source-verified sample or reading.

The canonical loader consumes a separate instance of the five-table source
contract under `data/raw/polls/historical_mayoral/`; it does not mix historical
rows into the current-cycle inventory above. The tracked historical bundle now
contains 86 source documents, 87 document/sample links, 64 respondent samples,
135 dependent readings, and 930 response rows from visually checked first-party
or archived sources. Sample, reading, and response identities remain separate,
and dependent scenarios never become additional polls.

The normalized tables and their hashes are tracked, while the underlying source
artifacts remain gitignored because their redistribution terms vary. Ordinary
historical loading therefore enforces the audited source contract without
requiring those private local bytes. Acquisition QA separately runs
`verify_poll_source_artifacts()` to reproduce every local artifact's size,
SHA-256, signature, and manifest relationship. A clean checkout can consume the
source-faithful normalized evidence without pretending it redistributes the
documents.

Published candidate rows do not by themselves establish a complete
questionnaire choice set. Each reading retains its explicit
`tested_choice_set_status`; missing or unknown fields are not upgraded by the
historical adapter.

## Legacy historical CSVs — discovery/staging only

`historical_mayoral_polls.csv` and `historical_mayoral_outcomes.csv` are the
lossy outputs of `scripts/fetch_historical_mayoral_polls.py`. **Do not use them
as calibration data.** Their `source_url` values point to Wikipedia inventory
pages; poll dates are last-fieldwork proxies rather than evidenced publication
times; sample tokens can be misparsed; shares were normalized; residual kinds
were combined; alternate readings can look independent; and the outcome table
collapses minor candidates. They remain tracked only for discovery and for the
complete legacy-ID crosswalk.
