# Add and Publish a 2026 Mayoral Poll

This is the operational sequence for moving one new **citywide Toronto mayoral
poll** from source evidence to production. Run commands from the repository named
in each section, keeping `RUN_ROOT` and the three tag variables in the same shell.
The release chain is `Results -> Polling -> Backend -> Frontend deployment`.
A poll-only update normally reuses the Results release pinned by production;
publish a new Results release only when upstream facts or identities need correcting.

The active mayoral forecast is the **v3 compact model**, publishing forecast feed
**schema 5** with policy `margin-first-joint-draws-v1`. Its current specification
is [ADR 0054](../../../toronto-election-poll-tracker-backend/docs/adr/0054-publish-the-compact-joint-model-election-day-distributions.md)
as amended by [ADR 0055](../../../toronto-election-poll-tracker-backend/docs/adr/0055-model-election-day-as-a-dirichlet-reading-of-the-latent-support.md)
(Dirichlet election-day discrepancy),
[ADR 0056](../../../toronto-election-poll-tracker-backend/docs/adr/0056-publish-the-uncertainty-ladder.md)
(uncertainty breakdown), and
[ADR 0057](../../../toronto-election-poll-tracker-backend/docs/adr/0057-select-and-weight-current-cycle-readings-like-the-historical-corpus.md)
(current-cycle reading selection),
[ADR 0061](../../../toronto-election-poll-tracker-backend/docs/adr/0061-learn-where-a-suspended-campaigns-support-goes.md)
(Suspended Campaigns and Post-Suspension Readings), and ADR 0062 (Excluded Polls).
The model version, forecast feed schema, and deployment source-manifest schema
(v2) are separate version numbers.

Before each release build or deployment, check `git status --short`, fetch
`origin`, and confirm `git rev-list --left-right --count HEAD...origin/main`
returns `0 0` from a `main` checkout. Commit and merge the Polling ingestion before
building its release. Preserve unrelated work and use a clean checkout when needed;
the publishers refuse a dirty tree or a source commit different from remote `main`.
Use the full refresh checks; do not pass `--skip-tests` for a production release.

## 0. Establish the source and immutable inputs

Use the pollster's first-party release/table book. Retain the source artifact under
the gitignored `data/source_documents/`, render and inspect every page, and record
its URL, retrieval timestamp, MIME type, size, SHA-256, page/sheet count, access
class, redistribution status, and visual-QA status. `passed` means every page and
every extracted value was visually checked; public availability is not permission
to redistribute the file ([`data/raw/polls/SCHEMA.md`](../../data/raw/polls/SCHEMA.md),
[`.gitignore`](../../.gitignore)). Preserve published values and
rounding; do not normalize them.

For a PDF, `tmp/new-poll-documents.json` can use the `doc_id`, `cycle`, `firm`,
`publisher_url`, `retrieval_url`, and `local_path` fields consumed by the prep
script; fetch, hash, and render it with:

```bash
uv run python scripts/ingest_prep.py tmp/new-poll-documents.json
```

The script renders every page at 175 DPI and emits computed metadata, but visual
inspection and the `visual_qa_status=passed` attestation remain human gates
([`scripts/ingest_prep.py`](../../scripts/ingest_prep.py)).

Read the deployed `/data/source-manifest.json` and record the current Backend,
Polling, and Results tags and the known-good Vercel deployment for rollback. Choose
its exact Results tag and download the complete release. Local `dist/` and
`.release-data/` can belong to earlier builds; confirm their provenance before
using them as evidence of production state.

```bash
RESULTS_TAG=results-YYYY-MM-DD.N
RUN_ROOT="$(mktemp -d)"
gh release download "$RESULTS_TAG" \
  --repo alexwolson/toronto-election-results --dir "$RUN_ROOT/results"
```

Required access: the source document (including any legitimate licensed access),
network access, and authenticated `gh` (`gh auth login` or `GH_TOKEN`) for release
publication. The Results release must contain `release_manifest.json`,
`person_aliases.json`, `election_results.csv`, and a `mayoral_candidates.json`
whose `ballot_certified` is true (its `candidates` are the Final Ballot for
Head-to-Head Readings); Polling refuses a different repository or an unknown
2026 contest ([`polling_data/release_bundle.py`](../../polling_data/release_bundle.py)).
Every candidate response must resolve by canonical name to exactly one Results
person. The Polling build fails closed on absent or ambiguous aliases and reports
the reading ID, source candidate ID, and candidate name. If the gate fails,
publish a corrected Results release first, then use that new tag throughout the
chain.

## 1. Ingest in the Polling repository

Add one coherent sample to all five tables in `data/raw/polls/`:

1. `source_documents.csv`: one row per physical artifact.
2. `poll_sample_documents.csv`: link every artifact and respondent sample.
3. `poll_samples.csv`: one row per independently recruited sample, with
   `election_cycle_id=toronto-2026`, `geography_type=citywide`,
   `geography_id=toronto`, fieldwork/publication dates, collection mode, recruited
   size, and `extraction_status=extracted`.
4. `poll_readings.csv`: one row per question/scenario/denominator, always linked to
   the sample and an auditable page/table locator, with `denominator_semantics`
   set by hand (`decided_plus_leaners`, `decided_only`, `all_respondents`, or
   `other`); the model ranks a sample's readings by it.
5. `poll_responses.csv`: every published option, keeping candidates, other,
   undecided, refusals, and non-voters distinct. A candidate uses a stable local
   key, canonical display name, source-exact `response_label`, and an explicit
   observation status.

The complete field definitions and relational/rounding rules are authoritative
([`data/raw/polls/SCHEMA.md`](../../data/raw/polls/SCHEMA.md)). When using a
five-section JSON spec, append atomically with the supported current-cycle command:

```bash
uv run python scripts/ingest_poll_source.py current-cycle tmp/new-poll.json
```

The command computes and checks available artifact metadata without assigning
`visual_qa_status`, validates with `require_audited_sources=False`, prints the new
inventory counts and downstream checks, and restores all five CSVs after any
contract or artifact failure. If local artifacts for the full current corpus are
present, optionally verify the complete archive too:

```bash
uv run python -c 'from backend.model.poll_sources import load_poll_source_bundle, verify_poll_source_artifacts; b=load_poll_source_bundle("data/raw/polls"); verify_poll_source_artifacts(b, ".")'
```

If the sample has a complete `general_vote_intention` mayoral reading, add exactly
one `(poll_sample_id, poll_reading_id)` row to
`data/raw/polls/descriptive_poll_readings.csv`. Choose the source's established
public comparison, normally its decided or decided-and-leaning topline and the
broadest contemporaneously relevant published field. This editorial selection is
explicit because dependent alternate fields and denominators remain separate
Poll Readings; they must never become additional polls.

If the sample publishes a complete `all_respondents` general vote-intention
reading, also add one `(poll_sample_id, poll_reading_id)` selection to
`data/raw/polls/all_respondent_poll_readings.csv`. Choose the published counterpart
of the archive field and leaner treatment where available. The release builder
requires one selection for every eligible all-respondent sample and exposes the
source-exact shares and reading ID in the alternate chart feed. Do not derive
missing all-respondent values or count this reading as a second poll.

Classify every new citywide mayoral reading in
`data/raw/polls/reading_classification.csv`. Each row is `(poll_reading_id,
citywide_mayoral, measurement_class)`; the rule is in
[`data/raw/polls/SCHEMA.md`](../../data/raw/polls/SCHEMA.md). A deliberately
changed field, such as a Chow-or-Bradford-only question, is `alternative_ballot`.
The release build fails on a missing, duplicate or unknown reading. The polling
feed's `head_to_head` array and flag are derived from this class, so they are
never edited by hand.

If the maintainer decides a sample must not be used in the forecast, add one row
to `data/raw/polls/model_exclusions.csv` with the decision date, its reasons and
the public explanation (rule in
[`data/raw/polls/SCHEMA.md`](../../data/raw/polls/SCHEMA.md); Backend ADR 0062).
Ingest the sample in full regardless: exclusion keeps it in the record and the
archive, and only Backend's reading selection skips it. Never exclude a poll on
your own judgement.

This selection controls the archive display only. The compact model selects its
own reading from `poll_samples.csv`, `poll_readings.csv`, and `poll_responses.csv`
in the released Polling bundle. Ingest all published readings and their actual
bases even when they are not the archive selection; do not choose archive rows
to influence the forecast.

Regenerate and validate the public archive from that audited selection:

```bash
uv run python scripts/sync_descriptive_polls.py
```

The generator copies source dates, method, field, and exact shares without
renormalizing. A blocked sample or one containing only `context_only`, conditional,
or routed readings receives no selection. `scripts/fetch_polls.py` is a discovery
aid only: it preserves an identical curated collision and stops without writing
when any colliding date, share, field, or metadata differs.

Update the intentional inventory/order/latest guards and the inventory prose:

- counts, citywide order, and poll-specific facts in
  [`tests/model/test_poll_sources.py`](../../tests/model/test_poll_sources.py);
- newest poll, field, and latest share in
  [`tests/model/test_mayoral_polling_feed.py`](../../tests/model/test_mayoral_polling_feed.py);
- the opening counts in [`data/raw/polls/SCHEMA.md`](../../data/raw/polls/SCHEMA.md).

Run `uv run pytest -q`, review the diff, and commit the Polling changes. Do **not**
include source bytes, `tmp/`, or `dist/`.

## 2. Build, pin, and publish Polling

From a clean, up-to-date, committed Polling `main` tree:

```bash
uv run python scripts/refresh_all.py \
  --results-bundle "$RUN_ROOT/results" --results-release "$RESULTS_TAG"
jq '.dependencies.results,.feeds,.assets' dist/release_manifest.json
POLLING_TAG=polling-YYYY-MM-DD.N
```

```bash
uv run python -m polling_data.release_bundle publish "$POLLING_TAG" --bundle dist
```

The refresh reruns the full test suite, canonicalizes contest IDs and candidate
names against Results, builds `mayoral_polling.json`, hashes every asset, and pins
the exact Results tag, source commit, and manifest hash
([`scripts/refresh_all.py`](../../scripts/refresh_all.py),
[`polling_data/release_bundle.py`](../../polling_data/release_bundle.py)).
Publication validates the `polling-YYYY-MM-DD.N` tag, refuses an existing remote
tag or GitHub Release, requires the bundle commit to equal the current remote
`main`, and passes that exact commit to `gh release create --target`. It then
downloads the completed release into a fresh temporary directory and verifies
the released manifest bytes, source commit, Results pin, and every declared
asset checksum. It reports success only after those checks pass.

If creation or verification fails, inspect the named GitHub Release and remote
tag. Keep any partial publication immutable and publish the correction under a
new tag; never retry by reusing the failed tag. After success, download the
verified release for the Backend build:

```bash
mkdir "$RUN_ROOT/polling"
gh release download "$POLLING_TAG" \
  --repo alexwolson/toronto-election-poll-tracker-data --dir "$RUN_ROOT/polling"
```

## 3. Rerun and publish the Backend model

No Backend source edit is normally required for a new current-cycle poll.
From its clean, up-to-date `main` checkout:

```bash
cd ../toronto-election-poll-tracker-backend
BACKEND_TAG=backend-YYYY-MM-DD.N  # unused: check `gh release list` first
uv run python scripts/refresh_all.py \
  --results-bundle "$RUN_ROOT/results" \
  --polling-bundle "$RUN_ROOT/polling" \
  --results-release "$RESULTS_TAG" --polling-release "$POLLING_TAG" \
  --release-tag "$BACKEND_TAG"
jq '{schema_version,publication_policy,analysis_cutoff,evidence_tier,final_field_samples,model,election_day,uncertainty,sensitivity,history}' \
  dist/mayoral_forecast.json
jq '.dependencies,.feeds,.forecast_draws,.assets' dist/release_manifest.json
jq '{release_tag,draws,candidates}' dist/mayoral_forecast_draws.json
```

Choose the tag before the build: the bundle records it beside the final
forecast's Election Outcome Draws (`mayoral_forecast_draws.npz` and its record
`mayoral_forecast_draws.json`), and the publisher refuses a bundle built for
another tag. A taken tag means a rebuild, and a rebuild's draws differ by CPU.

The refresh validates the Polling→Results pin, hydrates the released inputs, runs
Ruff lint, formatting checks and all Backend tests, rebuilds mayoral/council/trustee
feeds, and creates a Backend manifest pinning both upstream releases
([`scripts/refresh_all.py`](../../../toronto-election-poll-tracker-backend/scripts/refresh_all.py),
[`backend/release_bundle.py`](../../../toronto-election-poll-tracker-backend/backend/release_bundle.py)).
The compact fit reads both the current poll tables and the historical corpus (98
polls across seven campaigns) from the same pinned Polling release (Backend ADR 0060);
Backend refuses a Polling release without the historical assets. A current-cycle
ingestion does not touch the historical corpus or its
`historical_mayoral/reading_classification.csv`.

### Verify the compact forecast before publication

- **Reading eligibility and selection.** The sample must be extracted, citywide,
  and in `toronto-2026`. An eligible mayoral `general_vote_intention` reading must
  publish numeric shares for Chow, Bradford, and Alexander; a Post-Suspension
  Reading (fieldwork ending on or after Oct 6) needs only Chow and Bradford, any
  Alexander share is set aside, and the full field beats a head-to-head in the
  same sample (ADR 0061). A sample in `model_exclusions.csv` never enters the fit
  (ADR 0062). Among eligible readings,
  prefer `decided_plus_leaners`, then `decided_only`, then `all_respondents`, then
  `other`; ties go to more modelled named candidates, then reading ID. An earlier
  fieldwork date does not itself exclude a reading covering these three. An
  alternate field or an additional minor candidate does not exclude the sample.
  Blocked samples, ward polls, context-only readings and two-name readings do not
  enter the main fit. The widened-field sensitivity permits any two of the three.
- **Base and shares.** Confirm the chosen reading and base in
  `model.current_readings`, and one entry per included sample in
  `final_field_samples`. The base preference is weighted, reported, unweighted,
  then recruited only if no reading base is reported. Modelled shares are
  renormalized over the three named candidates; their effective base is the
  chosen base times their summed published share. Source and archive values
  remain unchanged. Additional certified candidates stay in the residual pool.
- **Numerical qualification.** The main fit and uncached historical snapshots use
  four chains, 1,000 warmup and 4,000 retained draws per chain. They must have zero
  divergences, worst R-hat below 1.01, and minimum ESS at least 400 on non-constant
  coordinates. A divergent fit gets one retry at target acceptance 0.99 and
  seed + 1. Failure stops the build; keep the previous release live.
- **Output and sensitivities.** Require schema 5, policy
  `margin-first-joint-draws-v1`, `model.name=compact_mayoral`,
  `model.specification.discrepancy=dirichlet`, and `model.qualification_passed=true`.
  Review the full-ballot vote medians and central 80% intervals, pairwise margin
  and its three outcomes, candidate win probabilities, and uncertainty breakdown
  against the previous verified release. The `isotropic-discrepancy` and
  `with-pre-certification-polls` refits carry probabilities and diagnostics as
  audit metadata; they do not apply the retired probability-band stability gate
  and are not numerically qualified by the production gate.
- **Dates and history.** Fieldwork end determines a current poll's model time;
  publication date determines when it enters `history`. Confirm the new sample
  appears at its publication-date snapshot, including a late publication of older
  fieldwork. Earlier snapshots are qualified with the same production settings
  and can be reused from an input/code/settings-keyed cache. Refresh timing does
  not shorten campaign uncertainty without new evidence; `analysis_cutoff` is
  metadata, not a model time node. The feed is built from the supplied bundle,
  so do not use a backdated cutoff to try to exclude a poll.

The operative selection, fit and feed contracts are in
[`compact_mayoral/readings.py`](../../../toronto-election-poll-tracker-backend/backend/model/compact_mayoral/readings.py),
[`compact_mayoral/qualification.py`](../../../toronto-election-poll-tracker-backend/backend/model/compact_mayoral/qualification.py),
and [`compact_mayoral_feed.py`](../../../toronto-election-poll-tracker-backend/backend/model/compact_mayoral_feed.py).
Build time depends on how many historical snapshots need refitting;
`COMPACT_HISTORY_CACHE` selects the cache directory (`off` disables it), and
`COMPACT_FIT_WORKERS` controls concurrent fits.

After these checks pass, publish the immutable output:

```bash
uv run python -m backend.release_bundle publish "$BACKEND_TAG" --bundle dist
mkdir "$RUN_ROOT/backend"
gh release download "$BACKEND_TAG" \
  --repo alexwolson/toronto-election-poll-tracker-backend --dir "$RUN_ROOT/backend"
```

The publisher validates the tag, clean source commit, remote `main` target and
both upstream pins and the draws record's tag, then downloads and checks the
released manifest, every asset and the draws before reporting success. A failure or partial upload consumes the tag;
publish corrections under a new tag.

## 4. Resolve, verify, and deploy the Frontend

Do not hand-copy production feeds into `fixtures/`. Those are offline contract/dev
fixtures and change only when a test scenario or feed contract intentionally
changes; ordinary production resolution writes the gitignored `.release-data/`
([`fixtures/README.md`](../../../toronto-election-poll-tracker/fixtures/README.md),
[`frontend .gitignore`](../../../toronto-election-poll-tracker/.gitignore)).

Preflight the exact verified Backend tag from the clean, up-to-date Frontend
`main` repository. It does not need to be GitHub's latest release:

```bash
cd ../toronto-election-poll-tracker
npm ci
npm test
npm run lint
unset BACKEND_RELEASE_MODE
BACKEND_RELEASE_TAG="$BACKEND_TAG" npm run vercel-build
jq . .release-data/source_manifest.json
```

`vercel-build` resolves the exact Backend release, follows its
exact Results and Polling tags, verifies upstream manifest hashes and downloaded
feed checksums, writes the resolved feeds and source manifest, then statically
builds with `FEED_LOCAL_DIR=.release-data`
([`package.json`](../../../toronto-election-poll-tracker/package.json),
[`scripts/resolve-releases.mjs`](../../../toronto-election-poll-tracker/scripts/resolve-releases.mjs)).
Confirm the source manifest names `$BACKEND_TAG`, `$POLLING_TAG`, and `$RESULTS_TAG`.
Then inspect `out/` at `/`, `/polls/`, `/candidates/`, `/wards/`, and
`/how-it-works/`. Check the new archive metadata, denominator label and exact
shares; the forecast evidence date and sample list; margin outcomes, vote ranges,
win probabilities, uncertainty breakdown and history against the resolved feed.

Before promotion, update the persistent Vercel Production `BACKEND_RELEASE_TAG`
to `$BACKEND_TAG` (and Preview when previewing the release). Configure server-only
`GH_TOKEN` or `GITHUB_TOKEN` for the resolver and ensure `BACKEND_RELEASE_MODE`
is unset in Production. A local shell assignment does not update Vercel's
project environment. Do not persist `DEPLOY_BACKEND_RELEASE_TAG`.

Promote with authenticated Vercel CLI access (linked project or `VERCEL_TOKEN`):

```bash
npm run deploy:production -- "$BACKEND_TAG"
```

The wrapper supplies `DEPLOY_BACKEND_RELEASE_TAG` as the intent for this build.
Production rejects a missing intent or a mismatch with the persistent
`BACKEND_RELEASE_TAG`; direct `vercel --prod` fails this check. Follow the current
[`production deployment guide`](../../../toronto-election-poll-tracker/docs/v2-release.md).

After Vercel reports `READY`, verify the deployed pages above and
`/data/source-manifest.json`; confirm the new poll metadata/shares, forecast
evidence date/sample list, forecast views, and the three pinned tags, source
commits and checksums. The deployed `resolved_at` belongs to the Vercel build and
may differ from local preflight; `backend_generated_at` belongs to the pinned
Backend release. Record the Vercel deployment URL in the release notes or PR.

## Failure and rollback rules

- **Never overwrite a release asset or reuse a tag.** Publish a corrected Polling
  release, then a new Backend release pinning it. Existing releases are the audit
  trail.
- A bad poll can change the joint distributions and all derived probabilities.
  Stop before Backend publication if changes are not understood or numerical
  qualification fails.
- If Backend was published but not deployed, leave it immutable and publish a
  corrected later release; preflight and deploy its exact tag, updating the
  persistent Vercel tag to match.
- If deployed, immediately promote the prior known-good Vercel deployment. Then
  issue corrected Polling and Backend releases; do not mutate old ones. Before
  the next forward deployment, align the persistent Vercel tag with the verified
  release being promoted.
