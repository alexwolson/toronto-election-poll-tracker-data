# Mainstreet ward polls published October 23, 2026

Mainstreet Research's second ward report from its October 14–16 IVR fieldwork covers Wards 3, 5
and 13 (1,018 respondents in all). It was published on October 23 in the post
[Toronto ward races to watch](https://www.mainstreetresearch.ca/post/toronto-ward-races-to-watch).
The October 22 report covered Wards 4, 10 and 25 ([note](mainstreet-ward-polls-2026-10-22.md)).
The PDF supplied in `~/Downloads` is byte-identical to the full edition on Mainstreet's CDN
(SHA-256 `6aad83c2…f6678`, 33 pages). The bytes stay in the gitignored
`data/source_documents/current_council/` audit corpus. The post quotes no figures.

Handling follows the October 22 note exactly. There are three separately weighted ward
samples, each with a council reading (pages 4, 8 and 14) and a ward mayoral reading (page 21,
ward column). Shares are the Total column of all respondents, kept at one decimal place and not
renormalized. "No preferred candidate" is undecided. Best-councillor and the other
non-vote-intention questions are not extracted.

| Ward | n | Council vote intention (%) | Ward mayoral (%) |
|---|---:|---|---|
| 3 Etobicoke–Lakeshore | 342 | Opitz 46.4; Morley 32.1; Andrei 6.9; Internicola 2.3; no preference 12.3 | Bradford 62.3; Chow 33.7; McVie 0.6; Parker 0.0; someone else 3.4 |
| 5 York South–Weston | 328 | Nunziata 38.5; Padovani 20.7; Di Giorgio 19.6; Mawel 8.1; Boateng 3.2; Obasogie 1.8; Ali 0.7; Phillips 0.7; no preference 6.8 | Chow 41.6; Bradford 39.3; McVie 3.7; Parker 0.7; someone else 14.7 |
| 13 Toronto Centre | 348 | Moise 43.8; Tate 16.9; Stikuts 15.8; Cadeau 4.4; Ward 4.3; Khogali Ali 2.6; Davis 0.9; no preference 11.5 | Chow 57.2; Bradford 34.4; McVie 0.0; Parker 0.0; someone else 8.3 |

Every named candidate is on the pinned Final Ballot. Ward 3 names the whole ballot. Ward 5
omits Maryama Farah, and Ward 13 omits Tom Cai, Morgan Harris, Norman MacLeod and Cleveland
Marshall; neither has an other-candidate row. The text layer and the rendered pages agree on all
four tables.

The Backend models each ward's latest final-field poll by fieldwork end. Ward 3's modelled poll
becomes this one, replacing Forum's September 25–27 poll. Wards 5 and 13 keep Forum's October
15–18 polls as the modelled ones, and Mainstreet's appear beside them. The ward mayoral
readings stay out of the citywide archive and compact model, so the mayoral draws are
unchanged and this is a ward-polls-only release (docs/forecast-only-release.md in the
live-projection repository).
