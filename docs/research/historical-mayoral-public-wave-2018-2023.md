# Historical mayoral public wave: 2018 and 2023

**Acquired and audited:** 2026-08-17  
**Scope:** DART and Probit in 2018; Viewpoints and Ipsos in 2023  
**Status:** four respondent samples represented by seven retained source artifacts, nine dependent mayoral vote readings, and 63 response rows

## Outcome

The 2018/2023 portion of the first public acquisition wave is usable. The four
respondent samples pass the generic five-table poll-source contract in strict
audited-source mode, and all seven local artifacts pass byte, checksum and
signature verification. No canonical or live-model CSV was changed; the
validated promotion draft remains isolated at
`/private/tmp/public_wave_2018_2023/`.

This batch repairs three material errors in the discovery-only historical
file:

1. Probit's named Faith Goldy result was previously folded into a combined
   residual. The source charts publish Goldy separately, so the draft keeps her
   as a candidate response and keeps `Other` separate.
2. Viewpoints' `780` is the decided-vote reading base, not its recruited sample
   size. The parent sample is `1,004`.
3. Ipsos' parent sample is `1,001`, not the legacy parser's `10010.0`. The
   detailed re-percentaged values also differ from the legacy normalization of
   rounded factum values.

The DART factum is admissible only as an honestly labelled source-grade partial
topline. It reports Tory 62% and Keesmaat 27%, but does not publish the exact
question, reading base or composition of the remaining 11 points. The draft
does not manufacture an 11% residual.

## Retrieval and integrity record

| Document | Retrieval result | Integrity and visual QA | Use |
|---|---|---|---|
| [DART archived-original factum](https://web.archive.org/web/20181023234340id_/http://dartincom.ca/wp-content/uploads/2018/10/Sun-Toronto-Election-Factum-1-Oct-2018.pdf) | `200 application/pdf`; 217,873 bytes | SHA-256 `0c927c3dde3e8d12e300038fcd0f3ed0fb4dfb97cfa9f7928f86de06f1b7460a`; clean five-page PDF; text layer present; all five pages rendered and inspected | Sample metadata and partial head-to-head outcome |
| Probit [all-response chart](https://pbs.twimg.com/media/Dmg-TpGXcAU_j3-.jpg:large) | `200 image/jpeg`; 24,537 bytes | SHA-256 `4d420c07fa1713ae74c96757cc1740d79be36fadbf2227bc6091fea7737a34a4`; 533x524; inspected at native resolution | All-response candidate chart including undecided |
| Probit [undecideds-removed chart](https://pbs.twimg.com/media/Dmg-TobW4AEnYm2.jpg:large) | `200 image/jpeg`; 26,691 bytes | SHA-256 `56aae6d80ba137a504b6f7420afbfbbab13dbb495b239b8f2981134d991714d4`; 492x495; inspected at native resolution | Dependent restricted-denominator chart |
| Viewpoints [June 2 marginals](https://www.viewpoints.ca/wp-content/uploads/2023/06/Toronto-Mayoral-By-Election-Marginals-Report-20230608-1.pdf) | `200 application/pdf`; 87,081 bytes | SHA-256 `8e280ec08e8b41076759b6783a6dd4d9ee286a798de74c52ef0bae82671db044`; clean one-page PDF; text layer present; rendered and inspected | Raw and decided June 2 readings |
| Viewpoints [June 8 release](https://www.viewpoints.ca/2023/06/chows-lead-grows-in-new-viewpoints-poll/) | `200 text/html`; 302,568 bytes | SHA-256 `6bd8966309d96f576cde3a4d4b796bcb42412df3f99447a6fad9dcf04b89ab53`; HTML signature and text verified | Publication, fieldwork, population, mode, turnout-intent screen and sponsor |
| Ipsos [detailed tables](https://www.ipsos.com/sites/default/files/ct/news/documents/2023-06/Toronto%20Mayoral%20Race%20Tables%202.pdf) | `200 application/pdf`; 1,672,113 bytes | SHA-256 `d789caaa787035ff35e4489223c6b1c9ccf331a0adbf6167b6875a10467b5e1a`; clean 23-page PDF; text layer present; all physical pages rendered and inspected | Four dependent vote-intention products |
| Ipsos [factum](https://www.ipsos.com/sites/default/files/ct/news/documents/2023-06/22-003004-01%20GN%20Media%20Release%20%283%29.pdf) | `200 application/pdf`; 1,318,733 bytes | SHA-256 `642d9caf77be2f33e42e0cf6c04e0a91b5f1bd3d6f58b1e95f763780ae1deef5`; clean seven-page PDF; text layer present; all seven pages rendered and inspected | Publication, sponsor, fieldwork, population, mode and achieved sample |

The Ipsos table object contains 23 physical pages internally numbered 3-25 of
33. It is a valid first-party table extract and contains the complete
vote-intention sequence needed here, but it is not described as a complete
33-page table book. The extraction therefore claims completeness only for the
retained mayoral readings.

Public availability is not a redistribution licence. Ipsos' factum expressly
restricts reproduction without prior written consent; all source bytes remain
under the repository's gitignored internal audit corpus. No affirmative reuse
licence was found for the other six artifacts.

## Parent samples and dependent readings

| Parent sample | Source-faithful metadata | Retained dependent readings |
|---|---|---|
| `dart_city_2018_10_12_15_n669` | DART Insight for Toronto Sun/National Post; Toronto adults; National Maru/Blue online panel; fieldwork Oct. 12-15; `n=669`; released Oct. 19 | One partial head-to-head outcome: Tory 62, Keesmaat 27. Exact question, denominator, base and remainder are unreported. |
| `probit_city_2018_08_20_09_05_n1635` | Probit Inc.; fieldwork Aug. 20-Sept. 5; overall chart sample `1,635`; first-party post dated Sept. 7; date-only evidence conservatively available Sept. 8; study-specific mode unreported | All chart: Tory 43, Keesmaat 21, Goldy 2, Other 1, Undecided 33. Dependent `undecideds removed` chart with generic base `1,152`: 64, 31, 3, 2. |
| `viewpoints_city_2023_06_01_02_n1004` | Viewpoints for Broadbent Institute; online; Torontonians 18+ who said they intended to vote; June 1-2; `n=1,004`; released June 8 | Raw vote with generic base `1,004`; decided vote with generic base `780`. The May 2 comparison column is a separate sample and is not duplicated here. |
| `ipsos_city_2023_06_09_13_n1001` | Ipsos for Global News and Toronto Star; eligible Toronto voters 18+; June 9-13; `n=1,001`; 701 online and 300 live telephone; released June 19 | Raw first choice; conditional lean among initial `I don't know`; pollster-combined total; and source re-percentaging over `Base: Total Valid Response` 861. All remain one dependent evidence unit. |

The archived [first-party Probit post](https://web.archive.org/web/20220108203612id_/https://twitter.com/ProbitInc/status/1038148223423184896)
is dated September 7 and contains epoch timestamp `1536348798`. Because the
supporting post HTML is not linked as an artifact in this promotion bundle, the
normalized sample deliberately stores publication timing as date-only and uses
September 8 as its conservative evidence cutoff. The charts themselves provide
the fieldwork range and bases. They do not provide a study-specific recruitment
or mode statement, so those fields remain unreported rather than being inferred
from Probit's general company profile.

## Reading-level source decisions

### DART

The [factum](https://web.archive.org/web/20181023234340id_/http://dartincom.ca/wp-content/uploads/2018/10/Sun-Toronto-Election-Factum-1-Oct-2018.pdf)
describes a head-to-head choice and explicitly cautions against presenting it
as a real voting-day outcome. It does not reproduce the questionnaire. The
draft therefore uses `question_text_status=not_reported`,
`denominator_type=not_reported`, `tested_choice_set_status=unknown`, and
`response_coverage=partial`. The legacy 11% residual is not source-supported.

### Probit

Both source images are linked to one respondent sample. Their `Sample` labels
are generic, so `1,635` and `1,152` populate `reported_base`; they are not
silently relabelled weighted or unweighted. The second chart's exact source
label is `undecideds removed`, retained as a custom denominator rather than
rewritten as `decided voters`. Both published response distributions sum to
100 and are complete as charts, but the tested questionnaire choice set and
exact question wording remain unknown.

### Viewpoints

The [release](https://www.viewpoints.ca/2023/06/chows-lead-grows-in-new-viewpoints-poll/)
states that the online survey ran June 1-2 among 1,004 Torontonians aged 18+
who said they intended to vote, and that Broadbent Institute commissioned it.
The [marginals](https://www.viewpoints.ca/wp-content/uploads/2023/06/Toronto-Mayoral-By-Election-Marginals-Report-20230608-1.pdf)
print the exact vote question, raw and decided denominators, generic bases and
complete response distributions. The raw values total 99.9% because of source
rounding; they are not rescaled. The source-exact `Not sure` row is retained as
an undecided response and is absent from the dependent decided-vote reading.

### Ipsos

The [factum's methodology](https://www.ipsos.com/sites/default/files/ct/news/documents/2023-06/22-003004-01%20GN%20Media%20Release%20%283%29.pdf)
establishes fieldwork June 9-13, 1,001 eligible Toronto voters aged 18+, mixed
online/live-telephone collection, and the June 19 release. The detailed tables
provide a lineage the rounded factum alone cannot:

1. raw first choice, including `Other` and `I don't know`;
2. a conditional lean question asked of the initial `I don't know` group;
3. Ipsos' dependent combined `Who would you vote for - Total`; and
4. `Total (Re-percentaged)` using `Base: Total Valid Response` 861.

For example, the detailed valid-response values are Bailao 11.5, Bradford 5.5,
Chow 38.2, Furey 7.4, Hunter 5.6, Matlow 8.0, Saunders 14.1, and Other 9.7.
These replace neither the raw reading nor the intermediate total; all four are
stored as dependent readings from one sample. The factum's rounded top line is
corroboration, not a competing sample.

## Legacy reconciliation

| Legacy proxy | Canonical disposition |
|---|---|
| `toronto_2018-2018-10-15-00471a65` | Maps to `dart_city_2018_10_12_15_n669` / `dart_2018_head_to_head`; legacy 11% residual is withdrawn because it is not published by the surviving source. |
| `toronto_2018-2018-09-05-87b8c045` | Maps to `probit_city_2018_08_20_09_05_n1635` / `probit_2018_undecideds_removed`; Goldy 3% is restored as a named candidate and Other remains 2%, instead of one combined 5% residual. The all-response chart is retained as a second dependent reading. |
| `toronto_2023-2023-06-02-85a96bf1` | Maps to `viewpoints_city_2023_06_01_02_n1004` / `viewpoints_2023_06_02_decided`; legacy `7800.0` is a parser error based on the decided base 780, not the recruited sample. Raw vote is retained dependently. |
| `toronto_2023-2023-06-13-a85f2b10` | Maps to `ipsos_city_2023_06_09_13_n1001` / `ipsos_2023_total_repercentaged`; legacy `10010.0` is a comma-parsing error. Canonical detailed values supersede normalized rounded factum shares. Raw, conditional lean and combined total remain dependent readings. |

## Validation

The strict generic loader and local artifact verifier completed successfully:

```text
documents: 7
sample_document_links: 7
samples: 4
readings: 9
responses: 63
```

Every sample is `extracted`; every reading cites a retrieved source artifact
whose visual QA passed; all foreign keys, candidate identities, reading totals,
reported-value normalization, source paths, byte sizes, SHA-256 hashes and
practical media signatures validate.

The repository's `uv run` launcher could not initialize under this sandbox
(first a protected cache path, then a macOS system-configuration panic). The
same project loader and verifier ran successfully with the system Python;
`backend/model/poll_sources.py` uses only the standard library for this path.
This is an environment-launcher issue, not a draft-validation failure.

## Remaining limits

- DART's detailed tables remain unavailable because the known Wayback body is
  truncated. The factum is sufficient only for a partial head-to-head reading.
- Probit remains chart-only. Mode, exact question wording, weighting and the
  tested questionnaire field are not published in the recovered objects.
- No source in this batch is redistributed through git; local source bytes are
  audit evidence only.
- Promotion into the shared historical bundle and crosswalk is a separate
  integration step. The live forecast inputs remain unchanged.
