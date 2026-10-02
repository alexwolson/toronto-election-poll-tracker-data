# Forum ward polls published October 2, 2026

Five first-party PDFs supplied in `~/Downloads/Forum Ward Polling` were matched
byte-for-byte to Forum's public attachments. Every page was rendered at 175 DPI
and visually checked, including all extracted totals, shares, dates and wording.
The source bytes remain in the gitignored `data/source_documents/current_council/`
audit corpus; the manifests retain sizes, checksums, URLs and acquisition times.
No affirmative redistribution permission was observed.

## Publication and sample identity

All five surveys were conducted September 25–27. The PDFs are dated September 29,
but Forum's [news API](https://www.forumresearch.com/api/news/paginated?page=1&pageSize=30)
records October 2 publication. `publication_at` preserves the API's UTC go-live
time; `evidence_available_at` conservatively uses the later attachment upload.
The September 29 PDF date is retained in notes, not used to backdate availability.

| Ward | API go-live (UTC, Oct 2) | Attachment upload (UTC, Oct 2) | Recruited sample | First-party release |
|---|---|---|---:|---|
| 3 | 15:45 | 15:47:58 | 535 | [Etobicoke–Lakeshore](https://www.forumresearch.com/news/2026/10/amber-morley-leads-etobicokelakeshore-city-councillor-race) |
| 4 | 15:48 | 15:49:34 | 464 | [Parkdale–High Park](https://www.forumresearch.com/news/2026/10/debbie-king-leads-parkdalehigh-park-city-councillor-race) |
| 13 | 15:51 | 15:52:11 | 519 | [Toronto Centre](https://www.forumresearch.com/news/2026/10/chris-moise-holds-narrow-lead-over-daniel-tate-in-toronto-centre) |
| 19 | 15:42 | 15:44:16 | 474 | [Beaches–East York](https://www.forumresearch.com/news/2026/10/nate-erskine-smith-leads-beacheseast-york-city-councillor-race) |
| 23 | 15:49 | 15:50:58 | 368 | [Scarborough North](https://www.forumresearch.com/news/2026/10/shaun-chen-holds-narrow-lead-over-jamaal-myers-in-scarborough-north) |

The collection mode is a mix of random IVR telephone interviewing and non-random
online panel surveying, with results weighted for age and gender. Each ward is
one respondent sample with a council reading on page 2 and a mayoral reading on
page 3. These are five polls, not ten independent polls.

## Extracted readings

Every table is labelled `[Decided/ Leaning]`. Shares below are published whole
percentages, retained without normalization. No undecided percentage is published;
none is inferred from the difference between recruited and reading bases.

| Ward / question | Unweighted / weighted base | Published shares (%) |
|---|---|---|
| 3 council | 406 / 416 | Morley 40; Opitz 27; Andrei 7; Internicola 14; Other 12 |
| 3 mayor | 493 / 487 | Chow 36; Bradford 43; Alexander 14; Other 7 |
| 4 council | 307 / 331 | Guerrera 23; King 37; Chan McNally 18; Raponi 6; Other 16 |
| 4 mayor | 433 / 443 | Chow 55; Bradford 35; Alexander 6; Other 4 |
| 13 council | 362 / 370 | Moise 29; Stikuts 13; Tate 26; Khogali Ali 8; Other 25 |
| 13 mayor | 476 / 446 | Chow 51; Bradford 36; Alexander 7; Other 5 |
| 19 council | 417 / 395 | Dann 6; Erskine-Smith 52; Johnson 24; Worden 6; Other 12 |
| 19 mayor | 452 / 440 | Chow 52; Bradford 30; Alexander 14; Other 4 |
| 23 council | 298 / 293 | Dong 12; Li 8; Myers 31; Chen 37; Oleh 6; Other 7 |
| 23 mayor | 329 / 324 | Chow 60; Bradford 32; Alexander 4; Other 4 |

Ward 13 council and Ward 23 council sum to 101%; Ward 13 mayor sums to 99%.
These are ordinary whole-point rounding differences. The mayoral Ward 3 table
prints the age-65+ unweighted base as a wrapped `33` / `9`; its Total is clearly
493. The extracted reading bases above use the Total column, not subgroup sums.
All tables heavily reweight small young-age samples; no design effect or effective
sample size is published. Question order and the full tested choice set are not
established by table placement.

## Handling in the current pipeline

The normalized five-table source contract gains five documents, five links, five
samples, ten readings and 46 response rows. The ward corpus now has 12 samples,
26 readings and 112 response rows. The complete current-cycle inventory has
52 documents, 52 links, 41 samples, 92 readings and 424 response rows.

The council readings also add 26 response rows to `ward_poll_readings.csv`, the
input consumed by Backend's Council race-card builder. Existing readings stay
individual and chronological, including older and hypothetical fields. This
follows [ADR 0037](../adr/0037-preserve-sparse-ward-polling.md) and
[ADR 0043](../adr/0043-council-v1-is-a-descriptive-race-card-not-a-forecast.md):
raw observed evidence, without a poll average or predictive council probabilities.

Every named council candidate resolves on the Final Ballot in the production
Results pin, `results-2026-09-30.2`. The new display rows use
`ballot_status=final_ballot_candidates`; this describes named-candidate validity,
not complete individual reporting of the final field. Ward 3 names all four
registered candidates. Wards 4, 13, 19 and 23 name subsets and retain `Other`.
Incumbent flags are true only for Amber Morley, Chris Moise and Jamaal Myers.

Both questions retain `geography_type=ward` through the parent sample. The ward
mayoral readings are stored as source evidence and excluded from the citywide
archive and compact model. They do not change the number of citywide polls or
supply independent council forecasting evidence.
