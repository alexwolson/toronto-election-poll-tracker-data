# Council card surfaces per-candidate election history

The council race card (ADR 0043) is descriptive. Until now each candidate showed
only their council biography (the councillor-only match, ADR 0045) plus
historical-hint flags (ADR 0047). A candidate whose prior office was MP, MPP,
trustee, or mayor — invisible to the councillor-only biography match — showed
nothing legible about that past, even though the generous all-offices person
resolution introduced in ADR 0047 already resolves them. Han Dong (Ward 23) is
the exact case: `candidate_id: null` / `is_matched: false` (no council history),
yet a resolved record of two MP wins, an MPP win, an MPP loss, and a trustee run.
Perennial candidates — people who run repeatedly and never win — were likewise
invisible.

This ADR adds a **`past_elections`** array to every candidate on the card
(schema **v2 → v3**): the person's full prior candidacy history from the vendored
canonical all-offices fact table (ADR 0045), **won and lost**, most recent first.
Each entry carries year, office type, represented body, district, party (where
the source carries it — municipal races are non-partisan and carry none), result,
vote share, **placement rank, and field size** (so a second-place loss reads
differently from an eleventh-place one).

**Identity reuses the ADR 0047 resolver** — the generous single-`person_id` name
match over the all-offices history — not the councillor-only biography match.
`candidate_id` / `is_matched` keep their council-biography meaning (ADR 0045)
unchanged; this is a new additive field, not a change to what "matched" means.
Only `person_id`-linked candidacies contribute: unlinked minor candidacies (the
canonical's `candidacy_id` fallback) and names that resolve ambiguously produce
an empty history, so coverage is honestly "every candidate the canonical can
link," not literally every candidate.

Ranked-ballot contests (the canonical's `composite_municipal_ballot` intermediate
rounds) are collapsed to one entry per `contest_id`. Wins include acclamations,
consistent with the rest of the card. This stays squarely within ADR 0043:
observed, descriptive, non-predictive — it is the "future work" ADR 0045
anticipated ("trustee/MPP/MP rows are available for future work"), now consumed
for description. The sitting incumbent's council wins appear both here and in the
biography section; that duplication is left for the frontend presentation to
reconcile, not special-cased in the data.
