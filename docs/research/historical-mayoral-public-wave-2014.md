# Historical mayoral public wave: 2014 source audit

**Research date:** 2026-08-17  
**Scope:** four unresolved Ipsos samples, the July 2014 Nanos sample, and the July 2014 Maple Leaf Strategies sample  
**Output boundary:** source-faithful draft only; no canonical historical CSVs or forecast inputs changed

## Outcome

The six respondent samples are recoverable from public first-party or
archived-original PDFs. They support **13 dependent mayoral vote-intention
readings and 67 published response rows**. The extraction deliberately excludes
unrelated survey questions and demographic crosstabs.

All six files returned HTTP 200 PDF bytes. Each passed signature, byte-size,
SHA-256, page-count, text-layer, and artifact-contract checks. All 51 physical
pages were rendered at 140 DPI and visually inspected; no clipping, corruption,
or unreadable page was observed.

The generic five-table poll-source draft is in
`/private/tmp/public_wave_2014/`. It contains `source_documents.csv`,
`poll_sample_documents.csv`, `poll_samples.csv`, `poll_readings.csv`, and
`poll_responses.csv`. The underlying PDFs are in the gitignored audit corpus at
`data/source_documents/historical_mayoral/public_wave_2014/`.

## Artifact record

| Document | Primary or archived-original source | Bytes | Pages | SHA-256 | What was actually recovered |
|---|---|---:|---:|---|---|
| `ipsos_2013-11-12_tables` | [Ipsos release](https://www.ipsos.com/en-ca/rob-fords-road-re-election-long-and-bumpy-prospects-another-victory-look-bleak) and [table attachment](https://www.ipsos.com/sites/default/files/publication/2013-11/6317-tb1.pdf) | 140,576 | 15 | `75698aa1aafccc1e6649b9e11afcdd89ea729dc9a42a4de3ebe01a6f40c00891` | Table attachment containing four ballot-scenario tables plus unrelated tables. |
| `ipsos_2014-09-16_tables` | [Ipsos release](https://www.ipsos.com/en-ca/doug-and-rob-out-toronto-mayoral-race-john-torys-43-lose-olivia-chow-29-doug-ford-28-trail) and [table attachment](https://www.ipsos.com/sites/default/files/publication/2014-09/6599-tb1.pdf) | 106,113 | 2 | `889441a1db960020c5178a5f3e90e12c59d036a26b38f6e25a5a7e0aa0ad8e21` | Two-page table attachment; the ballot table is complete. |
| `ipsos_2014-09-26_table_excerpt` | [Ipsos release](https://www.ipsos.com/en-ca/four-weeks-left-until-toronto-mayoral-vote-tory-48-soars-while-chow-26-ford-26-sputter) and [table attachment](https://www.ipsos.com/sites/default/files/publication/2014-09/6609-tb1.pdf) | 60,449 | 1 | `063ffc0e067eddf87a46843e6e59ec2e52de9709b088cf5050a5e52553421a6d` | One ballot-table page, printed as page 4 of 58; not a complete table book. |
| `ipsos_2014-10-23_table_excerpt` | [Ipsos release](https://www.ipsos.com/en-ca/john-tory-42-headed-toronto-mayors-chain-office-over-ford-31-chow-25) and [table attachment](https://www.ipsos.com/sites/default/files/publication/2014-10/6648-tb1.pdf) | 24,686 | 4 | `255c397a6fa7fd154e453beca66d69dd0935fb54d481674782476dada1827dd1` | Selected pages printed as 1, 4, 6, and 7 of 27. The result table survives, but the B/C ballot-question pages do not. |
| `nanos_2014-07-05_full` | [Nanos first-party report](https://nanos.co/wp-content/uploads/2017/07/2014-541-OCSA-Report-FINAL-w-tabs-R-1.pdf) and [reports index](https://nanos.co/reports-2/) | 764,920 | 27 | `cca2efad67a3478ad600e69cfe36e36d23761c2609641f35cb62334769456a2a` | Full report, methodology, summary charts, and stat sheets. |
| `maple_leaf_2014-07-30_release` | [Wayback replay of the original first-party PDF](https://web.archive.org/web/20140808050914id_/http://mapleleafstrategies.com/wp-content/uploads/2014/07/Tory-Leads-Ford-No-Growth-Room.pdf) | 766,957 | 2 | `b5eb05990f05b45499b0e2166db9ba29102bd4a1d63b2a93cbcca3a07d5c5920` | Complete two-page release with all-voter and decided-voter toplines, but no crosstabs. |

The acquisition plan described the Ipsos links collectively as table books.
That is too broad: the September 26 file is a one-page excerpt, and the October
23 file is a four-page selected-table attachment. The draft records their real
extent instead of treating omitted pages as recovered.

## Samples and retained readings

| Pollster and fieldwork | Parent sample | Direct vote-intention readings retained | Important source boundary |
|---|---:|---|---|
| Ipsos, 2013-11-08 to 2013-11-12 | 665 Torontonians, online | Four hypothetical candidate-field scenarios | One recruited sample, not four independent polls. Each scenario reports all 665 weighted and unweighted respondents. |
| Ipsos, 2014-09-12 to 2014-09-16 | 596 decided voters, online | Published Ford/Chow/Tory field | The release says undecided voters were screened out. The unexplained table-base label `416 or 647` is preserved as a note, not interpreted. |
| Ipsos, 2014-09-23 to 2014-09-26 | 1,252 Torontonians, online | Decided plus leaners, unweighted and weighted base 1,105 | The one-page artifact preserves the exact combined ballot/leaning wording and full three-candidate result. |
| Ipsos, 2014-10-21 to 2014-10-23 | 1,201 Torontonians, online plus live telephone | Decided plus leaners, unweighted base 1,066 and weighted base 1,048 | The result is complete, including `Some other candidate`, but exact B/C question wording is unavailable from the public excerpt and remains `not_reported`. |
| Nanos, 2014-07-02 to 2014-07-05 | 600 eligible voters, dual-frame live telephone | Raw first-ranked response; leaning among respondents initially unsure; source-labelled Vote Profile; source-labelled decided-voter Ballot | These are dependent products of one sample. Precise stat-sheet values are used instead of rounded chart labels. The source spelling `Karen Stinz` is retained while canonical identity maps to Karen Stintz. |
| Maple Leaf Strategies, 2014-07-28 to 2014-07-30 | 800 Toronto citizens, live telephone | All Voters and Decided columns | Neither reading-level base is printed. No base is derived from the parent `n=800` or rounded undecided share. Undecided, would-not-vote, don't-know, and refusal remain separate responses. |

Reported percentages are preserved exactly. They are not renormalized when a
column totals 99%, 100.1%, or 101% because of published rounding. Candidate IDs
are canonical mappings, while response labels retain source wording.

## Legacy reconciliation

The source evidence explains the relevant legacy proxies without promoting
alternate candidate fields or denominators into independent samples:

- the four November 2013 legacy IDs map to the four Ipsos scenarios;
- the September 16, September 26, and October 23 legacy IDs each map to one
  Ipsos reading and one parent sample;
- the two Maple Leaf legacy IDs are the All Voters and Decided readings from
  one sample; and
- the Nanos proxy maps to the source's decided-voter `Ballot` reading. Its
  apparently anomalous legacy shares are reproducible from the old scraper's
  unit bug: the source's 1.0% Soknacki value was read as 100% before the row
  was normalized. The canonical reading keeps the source-published values and
  supersedes that corrupted legacy vector.

## Verification and remaining blockers

The audited bundle loader accepted 6 source documents, 6 samples, 13 readings,
and 67 responses with audited-source enforcement enabled. The artifact verifier
then reproduced every PDF's byte size and SHA-256 from the repository-relative
paths.

No purchase, institutional login, or direct pollster request was needed. The
remaining limitations are source limitations rather than retrieval failures:

- exact October 23 Ipsos ballot wording and order are unavailable because the
  public attachment omits the relevant pages;
- Maple Leaf does not publish reading-level bases; and
- public availability is not an affirmative redistribution licence. This is
  especially worth preserving for the Nanos report, whose pages bear a
  `Confidential` footer despite the report being hosted publicly by Nanos. Raw
  files therefore remain in the gitignored audit corpus, with redistribution
  status recorded as unknown.

These gaps do not prevent using the recovered toplines as source evidence. They
should remain explicit fields rather than be filled by inference.
