# Mainstreet ward polls published October 22, 2026

Mainstreet Research surveyed Wards 4, 10 and 25 on October 14–16, 2026 by IVR
(894 respondents in all) and published the results on October 22 in the post
[Key ward races to watch](https://www.mainstreetresearch.ca/post/key-ward-races-to-watch).
The PDF supplied in `~/Downloads` is byte-identical to the full edition linked
from that post (SHA-256 `216064d4…04e1`, 35 pages). The bytes stay in the
gitignored `data/source_documents/current_council/` audit corpus. Footers
prohibit distribution without permission.

## Sample identity

Each ward was weighted separately to its own 2021 Census profile and keeps its
own sample size, and each ward's councillor questions were asked only of that
ward's respondents. These are three samples sharing one document, not one
894-person poll. Each sample has two dependent readings: council (pages 4, 10
and 16) and ward mayoral (page 23, ward column). The combined Total column on
the mayoral pages mixes three wards and is not extracted.

| Ward | n | MoE (95%) |
|---|---:|---:|
| 4 Parkdale–High Park | 262 | ±6.1% |
| 10 Spadina–Fort York | 292 | ±5.7% |
| 25 Scarborough–Rouge Park | 340 | ±5.3% |

`publication_at` is the post's HTTP Last-Modified time (2026-10-22 15:02:08
UTC). The PDF was uploaded at 15:01:56 UTC.

## Extracted readings

Shares are the Total column of all respondents, kept at one decimal place and
not renormalized. Unweighted and weighted bases equal the ward n.

| Ward / question | Published shares (%) |
|---|---|
| 4 council | Guerrera 35.2; King 3.3; Chan McNally 29.2; Ogundipe 0.4; Pham 15.5; Raponi 3.4; Weber 3.4; No preferred candidate 9.5 |
| 4 mayor | Chow 62.5; Bradford 33.7; Parker 2.3; McVie 0.0; Someone else 1.5 |
| 10 council | Cunningham 37.6; Ding 1.6; Hoàng-Lefranc 0.7; Kassir 1.6; Malik 39.1; Nash 2.9; Neemuchwala 3.2; No preferred candidate 13.4 |
| 10 mayor | Chow 54.2; Bradford 45.1; Parker 0.0; McVie 0.0; Someone else 0.7 |
| 25 council | Allen 37.1; Casinathen 5.7; Lumley 1.3; Patel 11.6; Shan 29.4; Another candidate 15.0 |
| 25 mayor | Chow 42.4; Bradford 53.2; Parker 0.6; McVie 0.6; Someone else 3.1 |

"No preferred candidate" is recorded as undecided, and as `undecided_share` in
`ward_poll_readings.csv`. Ward 25 offered no undecided option, so its undecided
share is blank, not zero. Ward 4 did not list Corcoran, Potega or Yuen, and
Ward 10 did not list Vashistha. Neither ward had an other-candidate row, so
those council readings are `partial` choice sets. No mayoral table offers an
undecided option.

Every value was read from the rendered pages and cross-checked against the PDF
text layer; the two reads agree on all four tables. Every named council
candidate is on the pinned 2026 Final Ballot. Malik (Ward 10) and Shan (Ward
25) are the incumbents; Ward 4 is an open seat.

## The post quotes a different question for Wards 10 and 25

For Ward 4 the post quotes the vote-intention table. For Wards 10 and 25 it
quotes the follow-up question, "regardless of who you indicated you might vote
for above, who do you think would be the best councillor" (pages 13 and 19):
Malik 43.2, Cunningham 35.8, Nash 9.2; Allen 37.7, Shan 28.5, Patel 12.9. This
ingestion uses vote intention for all three wards (maintainer decision,
2026-10-23), because it is the same question every other ward poll asks. The
best-councillor, best-mayor, right-track, responsibility and issue questions are
not extracted.

## Handling in the current pipeline

The five-table contract gains one document, three links, three samples, six
readings and 37 responses. `ward_poll_readings.csv` gains 20 rows. Wards 10 and
25 get their first ward polls. The Backend models each ward's latest
final-field poll by fieldwork end. In Ward 4, Forum's October 15–18 poll stays
the modelled one and Mainstreet's appears as an earlier published result. The
two disagree sharply: Forum has King 16 and Raponi 17 (decided/leaning), against
Mainstreet's 3.3 and 3.4, and Forum did not name Pham, whom Mainstreet has at
15.5. Ward mayoral readings keep `geography_type=ward` and stay out of the
citywide archive and the compact mayoral model.
