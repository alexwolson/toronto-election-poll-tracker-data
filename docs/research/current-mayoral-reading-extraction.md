# Current mayoral candidate-choice reading extraction

**Extraction and QA date:** 2026-08-17  
**Scope:** 18 recovered current-cycle citywide Toronto mayoral respondent samples  
**Output:** 44 dependent Poll Readings and 202 published response rows

## Result

The project now has source-audited, model-neutral candidate-choice readings for
all 18 current mayoral samples with recovered first-party detail. Forty-three
are vote-intention products. The Canada Pulse reading asks whom respondents
would consider for mayor and is explicitly `context_only`, so it cannot be
mistaken for support. The remaining Abacus sample is explicitly `blocked`: its
first-party article is access-gated and no public detailed table or complete
response set was recovered.

The 44 readings are **not 44 polls**. They are alternate ballot fields,
denominators, and source-specific transformations produced by 18 separately
recruited respondent samples. `poll_sample_id` remains the distinct evidence
unit. Every alternate reading stays attached to its parent sample so a future
consumer cannot accidentally count a head-to-head, a decided-only table, or an
adjusted presentation as an independent poll.

This work populates only the normalized source contract. It does not change or
feed `polls.csv`, `ward_poll_readings.csv`, processed snapshots, or mayoral or
Council forecast code.

## Per-sample extraction matrix

| Parent `poll_sample_id` | Readings | Responses | Extracted reading products |
|---|---:|---:|---|
| `pallas-2025-06-07` | 3 | 17 | All Voters; Leaning Voters With Undecided Totals; Decided And Leaning Voters |
| `liaison-2025-07-06` | 4 | 28 | Including John Tory and Without John Tory fields, each for All Voters and Decided Only |
| `ipsos-2025-08-29` | 1 | 4 | Q19, all respondents |
| `forum-2025-09-04` | 4 | 14 | Primary decided/leaning field; Chow-Tory, Chow-Bradford, and Chow-Bailão head-to-heads |
| `canadapulse-2025-10-06` | 1 | 6 | Context-only candidate-consideration field from the detailed workbook |
| `liaison-2025-10-23` | 2 | 11 | All Voters; Decided Only |
| `liaison-2025-12-21` | 2 | 11 | All Voters; Decided Only |
| `liaison-2026-02-02` | 2 | 11 | All Voters; a second five-option result whose denominator is not reported |
| `mainstreet-2026-02-22` | 3 | 14 | All voters; Decided and Undecided; Decided voters |
| `liaison-2026-03-08` | 2 | 11 | All Voters; Decided and Leaning |
| `pallas-2026-03-08` | 4 | 16 | Two ballot fields, each for All Voters and Decided Voters Only; one field includes Michael Ford |
| `liaison-2026-04-13` | 2 | 9 | All Voters; Decided and Leaning |
| `liaison-2026-05-11` | 2 | 7 | Unlabelled all-like field; Decided and Leaning |
| `mainstreet-2026-06-18` | 4 | 13 | Raw; leaner-adjusted; Only undecideds removed; forced two-way |
| `liaison-2026-06-30` | 2 | 7 | All voters; Decided voters |
| `liaison-2026-07-26` | 2 | 7 | All voters; Decided and Leaning voters |
| `forum-2026-07-29` | 2 | 7 | Primary field; Chris Alexander added |
| `liaison-2026-08-05` | 2 | 9 | All voters; Decided and Leaning voters, both including Chris Alexander |
| **Total** | **44** | **202** | **18 distinct respondent samples** |

Together with the six previously extracted Council samples, the complete
tracked contract contains 25 respondent samples, 57 readings, and 251 response
rows.

## Inspection approach

The extraction was split into three independent batches: seven early Liaison
samples, three late Liaison samples with companion graph/table books, and eight
non-Liaison samples. Each batch produced production-schema CSV fragments and a
page-level audit before promotion.

- All relevant PDF pages were rendered and visually inspected. Text-layer
  extraction or OCR was used only to locate or draft content; no numeric value
  was accepted without checking the rendered source page.
- Image-only Liaison reports were inspected first as complete contact sheets,
  then their methodology, base, vote-intention chart, and table pages were
  inspected at readable or high resolution.
- The Canada Pulse DOCX and XLSX were opened read-only. The workbook block
  `Toronto Civic 10 25!A333:C370`, including result and Sigma rows, was checked
  directly; neither Office artifact was re-saved or re-exported.
- Exact question wording, denominator labels, typed bases, response labels,
  displayed row order, percent precision, and rounding totals were retained.
- Approval, favourability, issue, direction, safety, federal-vote, subgroup,
  redistribution, and historical-series results were excluded. A source page
  can contain those products without turning them into mayoral readings.
- Every promoted artifact already had `visual_qa_status=passed`, and local
  files were checked against their tracked byte size, SHA-256, and practical
  media signature.

## Classification policy

The extraction records what the source says, without using labels to imply a
turnout model or forecast decision. `reading_purpose` separately identifies
general vote intention, a conditional lean follow-up, a routed subgroup, or
context-only evidence; model consumers do not infer that purpose from prose.

| Published denominator evidence | Structured classification |
|---|---|
| Exact `All Voters`, `All voters`, `All respondents`, or an explicit all-respondent base | `all_respondents`, with the source-exact label retained |
| Exact `Decided Only`, `Decided voters`, or `Decided Voters Only` | `decided_respondents`, with the source-exact label retained |
| `Decided and Leaning`, leaner allocation, `Decided and Undecided`, `[Decided/ Leaning]`, or another source-specific transform | `custom`, with the exact transformation label retained |
| No printed denominator | `not_reported`; no denominator is inferred from response rows, a sample total, or a graph shape |

`All Voters` and `Decided and Leaning` do not themselves establish a
registered-, eligible-, likely-, or past-voter turnout screen. A turnout screen
is recorded only when independently reported. Similarly, an equal parent and
reading base is not used to invent an all-respondent label.

Candidate identities are normalized separately from source labels. One
`candidate_id` must map to one canonical `candidate_name` across the complete
bundle. In particular, Michael Ford is always `michael-ford` / `Michael Ford`,
and Ana Bailão is always canonicalized with the accent. `response_label`
remains source-exact, so Liaison's printed `Ana Bailao` is preserved there.
`Someone Else`, `Other`, and similar residuals remain response kind `other`,
not an Unmeasured Candidate Tail estimate. `Undecided` and published nonvoter
responses remain distinct kinds.

`option_order` is only visible document row/bar order. Except for the explicit
Ipsos Q19 marker, questionnaire order is not reported and is never inferred
from page order. `tested_choice_set_status` remains `unknown` where the source
does not establish the complete offered ballot or its rotation, even when all
published outcome rows are present.

## Material source conflicts and conservative resolutions

### Sample and base conflicts

1. **Forum September 2025 parent size:** methodology reports `n=1,000`, while
   each of the three head-to-head tables prints both `TOTAL (u/w)=1001` and
   `TOTAL (w/t)=1001`. The three table bases remain 1001. The parent
   `recruited_sample_size` is blank so the contract preserves both statements
   without selecting one as correct. The primary decided/leaning reading has
   its separately printed 909 unweighted and 904 weighted bases.
2. **Reading bases are not copied across fields:** Liaison July 2025 prints
   1,000 unweighted and weighted only for the Including John Tory all-voter
   table. Those bases are not copied to its decided-only or Without John Tory
   readings. Other unprinted decided/leaning bases likewise remain absent.
3. **Pallas frequency defects:** several Pallas subgroup frequency rows do not
   reconcile with printed total bases. Only the directly printed Total-column
   bases and shares are encoded; subgroup frequencies are not used to repair
   or reinterpret them.
4. **Generic versus typed bases:** Ipsos's generic `n=1,001` is stored as a
   generic reported base. Explicit `TOTAL (u/w)`, `TOTAL (w/t)`, Unweighted
   Frequency, and Weighted Frequency labels populate their typed fields.

### Wording and denominator conflicts

5. **Liaison June 2026:** the table's restricted result says `Decided voters`
   and its question ends `Decided voters only.`, while the companion graph says
   `Decided and Leaning`. Both artifacts show 49/40/10. The table-backed
   reading is classified `decided_respondents`, and the graph conflict is
   preserved in its notes.
6. **Liaison July and August 2026:** each restricted table question ends
   `Decided voters only.` while its subtitle says `Decided and Leaning voters`.
   The exact question and exact subtitle occupy separate fields; the
   denominator is classified `custom` rather than silently simplified.
7. **Alternate Liaison graph wording:** the late graph books ask, `If an
   election were held today, for whom would you cast your vote for mayor?`,
   while the tables ask, `If a Toronto mayoral election were held today, who
   would you vote for?` The table wording is primary because the table contains
   bases and complete response rows. Matching graph values are corroboration,
   not extra readings.
8. **Unlabelled Liaison results:** February's second five-option result and
   May's all-like result never print a denominator. They remain
   `not_reported`; the presence or absence of Undecided is not enough to label
   a denominator.
9. **Excluded non-mayoral and subgroup questions:** Liaison October's federal
   All Voters/Decided and Leaning tables and July's Tory-supporter
   redistribution follow-up are not citywide mayoral readings.
10. **Source population shorthand:** Forum opening prose sometimes says
    Toronto or Canadian voters, while detailed methodology says randomly
    selected Toronto residents age 18+. The detailed methodology definition is
    used without inferring voter eligibility. Liaison's multi-city report says
    Toronto where other methodologies say Torontonians; that source wording is
    retained.
11. **Pallas headings and markers:** several mayoral headings say `party`
    rather than candidate, and June 2025 repeats a `[1]` marker on unrelated
    questions. Exact wording is retained; `[1]` is not promoted to
    questionnaire order.

### Published result conflicts

12. **Canada Pulse workbook versus release:** the workbook reports Olivia Chow
    at 27% (108) while release prose reports 29%. It also reports 6% (24) for
    `Nobody, I won't vote`, which the release omits. The detailed workbook's
    complete 27/24/8/2/33/6 result is encoded, with 406 unweighted and 406
    weighted respondents; the release disagreement remains documented.
13. **Forum September residual:** the detailed primary table labels 13% as
    `Other`, while release prose calls 13% undecided. The table label is
    encoded as `other`; it is not relabelled to make the prose agree.
14. **Forum July 2026:** the primary detailed table reports Bradford at 36%
    where release prose says 35%; the Alexander-added table reports Someone
    else at 10% where prose says 11%. Detailed-table tokens are retained.
15. **Rounding:** complete published rows range from 99% to 101% at whole-point
    precision, with more precise sources ranging from 99.9% to 100.1%. June
    Liaison's restricted result totals 99%; August Liaison's all-voter result
    totals 101%. No result is renormalized. Liaison explicitly warns that
    totals may differ from 100% because of rounding.
16. **Graph legends are historical:** late Liaison graph legends contain
    historical candidates who are absent from the current table. Only the
    current table's outcome rows are encoded; legend history is not treated as
    a current choice list or a zero-valued candidate observation.

### Source-specific transformations and access

17. **Mainstreet transformations:** February's `Decided and Undecided` result
    is not explained beyond its label. June separately publishes raw,
    undecided-leaner, `Only undecideds removed`, and forced two-way products.
    They remain dependent readings with exact labels; none is assumed to be a
    universally comparable decided-voter measure.
18. **Mainstreet editions and rights:** public and full editions describe one
    respondent sample, not duplicate polls. Full static PDFs were technically
    reachable but are marked Subscriber Exclusive and prohibit unauthorized
    reproduction. Their manifest remains `redistribution_status=prohibited`.
19. **Abacus gap:** no access control was bypassed. The unrecovered source is
    retained as `access_pending`; the sample is `blocked` and has no invented
    reading or response rows.
20. **Publication cutoffs:** date-only releases retain next-Toronto-day
    `evidence_available_at` values. Extraction does not move evidence earlier
    or replace publisher-page dates with report filenames.
21. **No blanket reuse licence:** public availability is not treated as
    permission to redistribute source documents. The recovered corpus remains
    gitignored and internal, and every artifact retains its manifest access and
    redistribution classification.

## Verification boundary

The source contract validates headers, enums, chronology, document/sample
links, candidate identity, response semantics, exact reported-value/share
normalization, typed bases, and rounding-aware complete totals. Artifact
verification checks existence, containment, byte size, SHA-256, PDF/media
signatures, and OOXML ZIP structure and CRC.

Passing those checks means the source evidence was transcribed and linked
consistently. It does **not** mean every reading is comparable, forecast-ready,
or eligible for candidate-win probabilities. Those decisions remain downstream
numeric gates in the separate mayoral model.
