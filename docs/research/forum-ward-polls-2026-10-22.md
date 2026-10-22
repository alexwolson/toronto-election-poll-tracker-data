# Forum ward polls published October 22, 2026

Seven first-party PDFs supplied in `~/Downloads` were matched byte-for-byte to
Forum's public attachments. Every page was rendered and visually checked, and
every extracted value was cross-checked against the PDF text layer; the two
reads agree on all fourteen tables. The source bytes remain in the gitignored
`data/source_documents/current_council/` audit corpus; the manifests retain
sizes, checksums, URLs and acquisition times. No affirmative redistribution
permission was observed.

## Publication and sample identity

Six surveys were conducted October 15–18 and the Ward 19 survey October 15–20.
The PDFs are dated October 19 (Ward 19: October 21), but Forum's
[news API](https://www.forumresearch.com/api/news/paginated?page=1&pageSize=30)
records October 22 publication. `publication_at` preserves the API's UTC go-live
time; `evidence_available_at` conservatively uses the later attachment upload.
The PDF dates are retained in notes, not used to backdate availability.

| Ward | API go-live (UTC, Oct 22) | Attachment upload (UTC) | Recruited sample | First-party release |
|---|---|---|---:|---|
| 4 | 16:54 | 16:56:01 | 594 | [Parkdale–High Park](https://www.forumresearch.com/news/2026/10/guerrera-and-mcnally-locked-in-tight-race-for-parkdalehigh-park-city-councillor) |
| 5 | 16:29 | 16:30:22 | 543 | [York South–Weston](https://www.forumresearch.com/news/2026/10/close-three-way-race-for-york-southweston-city-councillor) |
| 13 | 16:58 | 17:00:12 | 648 | [Toronto Centre](https://www.forumresearch.com/news/2026/10/moise-holds-narrow-lead-in-toronto-centre-city-councillor-race) |
| 14 | 16:30 | 16:31:28 | 604 | [Toronto–Danforth](https://www.forumresearch.com/news/2026/10/sara-ehrhardt-leads-toronto-danforth-city-councillor-race) |
| 19 | 16:26 | 16:28:42 | 1,084 | [Beaches–East York](https://www.forumresearch.com/news/2026/10/nate-erskine-smith-holds-lead-in-beacheseast-york-city-councillor-race) |
| 20 | 16:57 | 16:58:00 | 538 | [Scarborough Southwest](https://www.forumresearch.com/news/2026/10/kandavel-and-rupasinghe-in-tight-race-for-scarborough-southwest-city-councillor) |
| 23 | 17:00 | 17:01:22 | 512 | [Scarborough North](https://www.forumresearch.com/news/2026/10/shaun-chen-leads-scarborough-north-city-councillor-race) |

The collection mode is unchanged: random IVR telephone interviewing mixed with
non-random online panel surveying, weighted for age and gender. Each ward is one
respondent sample with a council reading on page 2 and a mayoral reading on
page 3. These are seven polls, not fourteen.

## Extracted readings

Every table is labelled `[Decided/ Leaning]`. Shares are published whole
percentages, retained without normalization. No undecided percentage is
published; none is inferred. The mayoral tables list only Chow, Bradford and
Other.

| Ward / question | Unweighted / weighted base | Published shares (%) |
|---|---|---|
| 4 council | 541 / 542 | Guerrera 32; King 16; Chan McNally 29; Raponi 17; Other 6 |
| 4 mayor | 576 / 577 | Chow 51; Bradford 46; Other 3 |
| 5 council | 469 / 477 | Padovani 28; Di Giorgio 30; Nunziata 34; Other 7 |
| 5 mayor | 509 / 515 | Chow 51; Bradford 44; Other 5 |
| 13 council | 556 / 583 | Moise 34; Stikuts 25; Tate 30; Other 11 |
| 13 mayor | 626 / 628 | Chow 58; Bradford 40; Other 2 |
| 14 council | 495 / 473 | Saxe 22; Fragedakis 26; Ehrhardt 40; Other 12 |
| 14 mayor | 556 / 541 | Chow 60; Bradford 34; Other 5 |
| 19 council | 997 / 990 | Dann 21; Erskine-Smith 32; Johnson 26; Worden 16; Other 4 |
| 19 mayor | 1,045 / 1,044 | Chow 60; Bradford 37; Other 3 |
| 20 council | 447 / 464 | Kandavel 41; Rupasinghe 38; Other 21 |
| 20 mayor | 515 / 515 | Chow 50; Bradford 47; Other 4 |
| 23 council | 472 / 476 | Myers 34; Chen 42; Dong 12; Other 12 |
| 23 mayor | 496 / 496 | Chow 62; Bradford 32; Other 6 |

Ward 5 council, Ward 14 mayor and Ward 19 council sum to 99%; Ward 20 mayor
sums to 101%. These are ordinary whole-point rounding differences.

The Ward 23 mayoral table's subgroup columns do not reconcile with its Total:
the age cells' unweighted bases sum to 710 against a Total of 496, and the
35–44 and 45–54 cells (13 and 43 respondents; Chow 31% and 98%) are implausible.
Its Total column (496 / 496; 62 / 32 / 6) is internally consistent and is the
only part extracted. The defect is recorded on the reading.

## Identity

Every named council candidate resolves on the 2026 Final Ballot in the Results
repository. Forum prints `Daniel DiGiorgio`; the ballot spelling is `Daniel Di
Giorgio`. Forum's June Ward 5 release printed `David DiGiorgio`, which had been
stored under its own `david-digiorgio` identity. Both readings now share
`daniel-di-giorgio` with the ballot spelling as the canonical name; the printed
labels are retained in `response_label`. Incumbent flags are true only for
Frances Nunziata, Chris Moise, Parthi Kandavel and Jamaal Myers. Dianne Saxe is
the Ward 11 councillor running in Ward 14 and is not flagged there.

## Handling in the current pipeline

The normalized five-table source contract gains seven documents, seven links,
seven samples, 14 readings and 50 response rows. The ward corpus now has 19
samples, 40 readings and 162 response rows. The complete current-cycle inventory
has 79 documents, 79 links, 61 samples, 145 readings and 634 response rows.

The council readings add 29 rows to `ward_poll_readings.csv`. Ward 14 gets its
first ward poll. Earlier readings stay individual and chronological, following
[ADR 0037](../adr/0037-preserve-sparse-ward-polling.md) and
[ADR 0043](../adr/0043-council-v1-is-a-descriptive-race-card-not-a-forecast.md).
The ward mayoral readings keep `geography_type=ward` and stay out of the
citywide archive and compact mayoral model.
