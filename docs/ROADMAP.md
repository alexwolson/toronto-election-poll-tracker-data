# Rebuild Roadmap

Living plan for the from-first-principles rebuild of the Toronto election forecasting model. Unlike the ADRs (frozen decisions) and the research notes (dated findings), this file is updated as work lands. It orients an agent picking up the work: what exists, what the design is, what to build next, and the disciplines to follow. Terminology is defined in [CONTEXT.md](../CONTEXT.md); decisions in [docs/adr/](adr/); evidence in [docs/research/](research/).

**Status as of 2026-08-19.**

## Orientation — read first

- The project is being rebuilt into two statistically independent forecasts — a Mayoral Forecast and a Council Forecast (ADR 0014) — plus a shared publication layer that gates what may be shown.
- **The rebuild is not wired to anything published.** It lives in the untracked modules `backend/model/mayoral_*.py`, `historical_mayoral*.py`, `poll_sources.py`, `polling_estimate.py`, `ward_polling.py`. The currently published model is the **legacy** tracked pipeline (`run.py` → `forecast.py` / `mayoral.py` / `council.py` / `snapshot.py`, with `simulation.py`, `coattails.py`, `pool.py`, `aggregator.py`, `lean.py`). Do not confuse the two, and do not edit the legacy model as if it were the rebuild. Nothing in the rebuild may publish until registration closes and the Final Ballot is set (ADR 0002).
- **The rebuild sits at one milestone:** the polling-only Mayoral baseline is built and validated, and the incumbency-informed variant (rung 3) is now built and evaluated — it does not qualify, so it is retained as the Mandatory Sensitivity Variant (ADR 0013, 0039). Everything richer — the dynamic mayoral model, the whole Council forecast, and the entire publication layer — is designed in the ADRs but **not built**.

## The design is a model-selection ladder

The Mayoral Forecast is a ladder of specifications, each of which must earn its place over the simpler one on whole Held-Out Election Cycles (ADR 0029, 0030):

1. **Latest-sample comparator** — the simplest polling-only forecast; the naive benchmark.
2. **Firm-balanced Mayoral Endpoint Bridge** — the Qualification Baseline (ADR 0030, 0034). Must beat the comparator.
3. **Incumbency-informed endpoint** — the Mayoral Incumbency Prior (ADR 0013) gets operational weight only if this variant qualifies against the polling-only baseline.
4. **Dynamic / refined specification** — endorsements (ADR 0008), campaign path, dynasties. May replace the endpoint only by qualifying against it; no particular toolkit is assumed.

Reading the ladder is essential: **a lower rung failing to beat a simpler one is the ladder working (ADR 0030: "the simpler specification remains authoritative"), not a defect.** This is the correct reading of today's `not_qualified` status — see below.

## Current state (OBSERVED, 2026-08-19)

### Mayoral track

| Component | Status | File(s) |
|---|---|---|
| Poll evidence schema (sample → reading → response) | Built | `poll_sources.py` |
| Historical corpus + reconstruction | Built; **2010–2023 complete** (proxies resolved, blocker cleared; 2010 added 2026-08-19); **2000–2006 pending** | `historical_mayoral.py`, `scripts/reconstruct_historical_mayoral.py` |
| Evaluation-cycle construction | Built | `historical_mayoral_evaluation.py` |
| LOOCV scoring (margin CRPS, Brier, log score, close-result, incumbent-defeat) | Built | `mayoral_evaluation.py` |
| Comparator + firm-balanced bridge endpoints | Built | `mayoral_endpoint.py` |
| Qualification ladder (comparator vs bridge) | Built; **result: not_qualified** | `mayoral_endpoint_qualification.py`, `scripts/evaluate_mayoral_endpoint.py` |
| Mayoral descriptive polling estimate | Built | `polling_estimate.py` (ADR 0034) |
| Mayoral Incumbency comparison population | Built | `mayoral_incumbency.py` |
| Incumbency-informed endpoint variant | Built; **Mandatory Sensitivity Variant** (does not qualify, ADR 0039) | `mayoral_incumbency_endpoint.py`, `scripts/evaluate_incumbency_endpoint.py` |
| Dynamic / refined model | **Not built** | — |
| Live snapshot integration | **Not built** (standalone; not authorised to publish) | — |

The corpus holds **five reconstructed cycles (2010, 2014, 2018, 2022, 2023), 105 samples / 243 readings**. The 2014–2023 legacy-proxy backlog is **fully resolved** (2026-08-19): every proxy is `mapped` (143) or `no_public_source` (9, documented-unavailable), zero `unresolved`, and the `unresolved_legacy_poll_samples` calibration blocker is **cleared** (`blocker_codes == ()`). Sources span Forum, Mainstreet, Nanos, Ipsos, Angus Reid, Pollara, and EKOS first-party reports plus, where no first-party PDF survives, newspaper/CP24 toplines (`document_role` article). What remains for M1 is the **older cycles 2000–2006** (not the 2010–2023 corpus). Restricted Forum/Borealis material is optional. See [unresolved-proxy-source-hunt.md](research/unresolved-proxy-source-hunt.md) and the `historical-mayoral-*` notes.

**2010 scope (added 2026-08-19).** 2010 was built fresh (no legacy proxies). Ingested **9 samples spanning the Final-Ballot window (Sep 10 → Oct 22)** — every poll the endpoint scores: EKOS ×2 (first-party PDFs, decided/leaning), Ipsos ×2 and Angus Reid ×2 (first-party releases), Nanos ×2 and Pollara ×1 (news toplines). **Deliberately not ingested:** the nine Jan–Aug 2010 polls (P1–P9), which are **pre-Final-Ballot** (fieldwork ended before nomination close, Sep 10) and are therefore structurally excluded by `select_mayoral_endpoint_readings` (`sample.fieldwork_end < boundary_date`); sourcing them would add zero qualification value. **Unrecoverable (documented):** the Forum (Oct 14) and Léger (Oct 15–18) October polls — the primaries have decayed off the public web (Forum's archive holds no 2010 mayoral release; Léger's Oct-18-2010 PDF survives only as a CDX 302 stub). The 2010 open race (Miller did not run; incumbent `None`) is a healthy cycle — winning-margin CRPS 0.030 (comparator) / 0.026 (bridge), mid-pack, no degeneracy.

**Qualification status: `not_qualified`** (re-run 2026-08-19 on the five-cycle 2010–2023 corpus). The firm-balanced bridge still does not qualify over the latest-sample comparator on primary winning-margin CRPS. Adding 2010 shifted it further toward the bridge: on **regular elections (4 cycles: 2010/2014/2018/2022)** the bridge now beats the comparator *in aggregate* (**0.0357 vs 0.0385**) and improves **2/4 cycles** (was 1/3 on three cycles), but 2/4 is not a majority, so it fails ADR 0030's majority-of-cycles rule; on **all 5 cycles** the bridge is worse in aggregate (0.0498 vs 0.0422), still dragged by the 2023 by-election outlier (CRPS 0.091). Per ADR 0030 the comparator stays authoritative — the ladder working, not a broken model, and still an n=5 result. **Do not treat it as a bug to chase.** More whole cycles (2000–2006) is the lever on the majority-of-cycles criterion.

### Council track

| Component | Status | File(s) |
|---|---|---|
| Ward Polling Estimate (descriptive, sparse-ward handling) | Built | `ward_polling.py` (ADR 0034, 0037) |
| Candidate-level Council Forecast, Officeholding-History Prior, council evaluation/qualification | **Not built** | — |

The Council Forecast is fully designed in the ADRs (0009, 0012, 0016, 0019, 0020, 0025–0028, 0036, 0037) but only its descriptive polling estimate exists.

### Publication layer (shared) — not built

No code implements Publication Gates (ADR 0003, 0005), Probability Bands (ADR 0006, 0018), Frequency Statements (CONTEXT.md), the Mayoral/Council Evidence Tiers as a shared mechanism (M0–M3 / C0–C2; ADR 0025, 0033), Candidate Win Probability gating, or Close-Result / Incumbent-Defeat publication. Until this exists, **nothing can be published even if a forecast qualifies.**

## Remaining work (dependency order)

Build each item only after a short spec is approved (see Disciplines). TDD. Record the investigation as a research note and any decision as an ADR. Re-run the qualification ladder and report before/after **without tuning to it**.

- **M1 — Finish the historical poll corpus** (target cycles 2000–2023, 1997 excluded). **2010–2023 done** (2026-08-19): 2014–2023 backlog resolved and blocker cleared; 2010 built fresh (9 Final-Ballot-window polls; pre-Sep-10 polls intentionally out-of-window; qualification re-run). **Remaining: older cycles 2000–2006.**
  - **The free/public queue is not exhausted** — the prior "Borealis-only" verdict was a `WebFetch`-can't-reach-`web.archive.org` artifact; `curl` + the Wayback CDX/`id_` API recover most pre-2019 Forum and Mainstreet releases (following Forum `PollsDownload.asp?docid=` redirects). Borealis is optional, for the few genuinely-missing items.
  - **Method (one-time, historical):** per-document extraction is **LLM-driven, not a parser** — read the PDF's `[All Respondents]` crosstab Totals (the admissibility source; full demographic crosstabs are not required — acquisition plan line 22). Then ingest via the thin `scripts/ingest_poll_source.py` (core `backend/model/poll_ingest.py`), which appends schema-exact rows and validates the audited contract all-or-nothing. Visual QA is **full-document** (SCHEMA `visual_qa_status`): render and inspect every page.
  - **Retiring the legacy backlog** (`unresolved` crosswalk rows) is a *separate* step: add `legacy_id → (sample, reading)` entries to `_MAPPED_LEGACY_READINGS` in `historical_mayoral.py` (matched via the discovery CSV's fields), then `reconstruct --write`. Adding a sample alone does not retire its proxies.
  - Trackers/queue: [historical-mayoral-poll-acquisition-plan.md](research/historical-mayoral-poll-acquisition-plan.md); 2006 turnkey (official results + Wikipedia poll tables), 2003 partial (news-archive dig), 2000 results-only. **Method note from 2010:** for older cycles the endpoint only scores polls fielded after the Final Ballot is set (nomination close), so prioritise the post-nomination window; first-party pollster PDFs mostly survive only for EKOS (ekospolitics.com) and via Wayback, with newspaper toplines as the admissible fallback.
- **M2 — Incumbency-informed endpoint variant. Done (ADR 0039).** Built as `mayoral_incumbency_endpoint.py` and evaluated against the bridge; does not qualify on the four-cycle corpus, so it is retained as the Mandatory Sensitivity Variant (ADR 0013). Reopen only if the corpus gains a non-landslide or incumbent-defeat cycle, or to add the incumbent's dispersion (the deferred defeat-tail widening). Evidence: [mayoral-incumbency-endpoint.md](research/mayoral-incumbency-endpoint.md).
- **M3 — Mayoral publication layer.** Evidence Tier M0–M3 (ADR 0033), Probability Bands (ADR 0006, 0018), Frequency Statements, and the gate machinery (ADR 0003, 0005, 0032). Required before any mayoral quantity can be shown.
- **M4 — Dynamic / refined mayoral model.** Only if it qualifies against the endpoint (ADR 0030). Future.
- **C1 — Council Forecast.** The entire second forecast: candidate-level modelling, Officeholding-History Prior (ADR 0028), C-tier publication (ADR 0025), whole-cycle evaluation (ADR 0026). Large; mirrors the mayoral track.
- **INT — Snapshot integration.** Wire a qualified forecast into the build/snapshot pipeline behind the Final-Ballot gate (ADR 0002), replacing the legacy model. Not before qualification.

Lower-priority open findings (non-blocking): the 2023 point-estimate second-place misranking ([candidate-tail-margin-coupling.md](research/candidate-tail-margin-coupling.md)); the concentration over-confidence, dispositioned as a bounded n=4 limitation with a revisit trigger ([mayoral-concentration-overconfidence.md](research/mayoral-concentration-overconfidence.md)).

## Working disciplines (for agents)

- **Spec → gate → TDD.** Before a feature or behaviour change, write a short spec (requirement, constraints, files touched, chosen design, one-line justification) and get approval. Failing test first, then implement to green.
- **Record findings.** Investigations become dated research notes in `docs/research/`; decisions become terse, declarative ADRs in `docs/adr/` (next number **0040**). Cross-link them.
- **Report metrics, never tune to them.** Re-run `scripts/evaluate_mayoral_endpoint.py` before and after a change and report the deltas. Tail, margin, and calibration scores are reported quantities, not optimisation targets (ADR 0030).
- **Honour the small sample.** There are four reconstructed cycles. Leave-one-cycle-out is the honest unit; row-level statistics across lead times are pseudo-replicated. Prefer robustness to anything a single cycle can swing, and state the confound.
- **Keep the rebuild and the legacy model separate.** The legacy pipeline is live; the rebuild is not. Do not wire the rebuild to the snapshot until it qualifies and the Final Ballot is set (ADR 0002).
- **Diagnostics are reproducible scripts** under `scripts/` (`diagnose_candidate_tail_scaling.py`, `diagnose_margin_regression.py`, `diagnose_concentration_overconfidence.py`), each printing its own correctness check.

## Pointers

- Terminology — [CONTEXT.md](../CONTEXT.md)
- Decisions — [docs/adr/](adr/) 0001–0039
- Findings — [docs/research/](research/) (start with `unmeasured-candidate-tail`, `candidate-tail-choice-set-scaling`, `candidate-tail-margin-coupling`, `mayoral-concentration-overconfidence`, `mayoral-incumbency-endpoint`)
- Run mayoral qualification — `uv run scripts/evaluate_mayoral_endpoint.py`; incumbency variant — `uv run scripts/evaluate_incumbency_endpoint.py`
- Tests — `uv run pytest` (395 passing as of this writing)
