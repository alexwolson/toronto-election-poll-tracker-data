# Add and Publish a 2026 Mayoral Poll

This is the operational sequence for moving one new **citywide Toronto mayoral
poll** from source evidence to production. Run commands from the repository named
in each section. A poll-only update reuses the current stable Results release; it
does not create a Results release.

## 0. Establish the source and immutable inputs

Use the pollster's first-party release/table book. Retain the source artifact under
the gitignored `data/source_documents/`, render and inspect every page, and record
its URL, retrieval timestamp, MIME type, size, SHA-256, page/sheet count, access
class, redistribution status, and visual-QA status. `passed` means every page and
every extracted value was visually checked; public availability is not permission
to redistribute the file ([`data/raw/polls/SCHEMA.md:36-64`](../../data/raw/polls/SCHEMA.md#L36-L64),
[`data/.gitignore:12-18`](../../.gitignore#L12-L18)). Preserve published values and
rounding; do not normalize them.

For a PDF, `tmp/new-poll-documents.json` can use the `doc_id`, `cycle`, `firm`,
`publisher_url`, `retrieval_url`, and `local_path` fields consumed by the prep
script; fetch, hash, and render it with:

```bash
uv run python scripts/ingest_prep.py tmp/new-poll-documents.json
```

The script renders every page at 175 DPI and emits computed metadata, but visual
inspection and the `visual_qa_status=passed` attestation remain human gates
([`scripts/ingest_prep.py:24-87`](../../scripts/ingest_prep.py#L24-L87)).

Choose the stable Results tag already in production (for example the tag in the
current `dist/release_manifest.json`) and download its complete release:

```bash
RESULTS_TAG=results-YYYY-MM-DD.N
RUN_ROOT="$(mktemp -d)"
gh release download "$RESULTS_TAG" \
  --repo alexwolson/toronto-election-results --dir "$RUN_ROOT/results"
```

Required access: the source document (including any legitimate licensed access),
network access, and authenticated `gh` (`gh auth login` or `GH_TOKEN`) for release
publication. The Results release must contain `release_manifest.json`,
`person_aliases.json`, and `election_results.csv`; Polling refuses a different
repository or an unknown 2026 contest ([`polling_data/release_bundle.py:55-114`](../../polling_data/release_bundle.py#L55-L114)).
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
   the sample and an auditable page/table locator.
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
  [`tests/model/test_poll_sources.py:738-835`](../../tests/model/test_poll_sources.py#L738-L835);
- newest poll, field, and latest share in
  [`tests/model/test_mayoral_polling_feed.py:12-35`](../../tests/model/test_mayoral_polling_feed.py#L12-L35);
- the opening counts in [`data/raw/polls/SCHEMA.md:3-12`](../../data/raw/polls/SCHEMA.md#L3-L12).

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
([`scripts/refresh_all.py:26-53`](../../scripts/refresh_all.py#L26-L53),
[`polling_data/release_bundle.py:207-281`](../../polling_data/release_bundle.py#L207-L281)).
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

No Backend source edit is normally required. From its clean, up-to-date `main`
checkout:

```bash
cd ../toronto-election-poll-tracker-backend
uv run python scripts/refresh_all.py \
  --results-bundle "$RUN_ROOT/results" \
  --polling-bundle "$RUN_ROOT/polling" \
  --results-release "$RESULTS_TAG" --polling-release "$POLLING_TAG"
jq '{evidence_tier,final_field_samples,candidate_win,close_result,incumbent_defeat}' \
  dist/mayoral_forecast.json
jq '.dependencies,.feeds,.assets' dist/release_manifest.json
BACKEND_TAG=backend-YYYY-MM-DD.N
```

Publish the immutable output:

```bash
uv run python -m backend.release_bundle publish "$BACKEND_TAG" --bundle dist
mkdir "$RUN_ROOT/backend"
gh release download "$BACKEND_TAG" \
  --repo alexwolson/toronto-election-poll-tracker-backend --dir "$RUN_ROOT/backend"
```

This validates the Polling→Results pin, hydrates exact inputs, runs all Backend
tests, rebuilds mayoral/council/trustee feeds, and creates a Backend manifest that
pins both upstream releases
([`scripts/refresh_all.py:28-110`](../../../toronto-election-poll-tracker-backend/scripts/refresh_all.py#L28-L110),
[`backend/release_bundle.py:25-94`](../../../toronto-election-poll-tracker-backend/backend/release_bundle.py#L25-L94)).
The publisher validates the tag, remote `main` target and both upstream pins,
then downloads and checks the released manifest and every asset before reporting
success. A failure or partial upload consumes the tag; publish corrections under
a new tag.

Model verification is substantive, not just “command succeeded.” Confirm the new
sample appears in `final_field_samples` **only if** its measured candidate set
equals the certified three-person `viable_field`; otherwise it remains descriptive
evidence and does not affect the forecast
([`backend/model/mayoral_forecast_feed.py:296-351`](../../../toronto-election-poll-tracker-backend/backend/model/mayoral_forecast_feed.py#L296-L351)).
The measured set is the union of named candidates across **all** readings for the
sample, so one alternate scenario containing an extra candidate excludes the whole
sample from final-field modelling
([`backend/model/mayoral_forecast_feed.py:275-329`](../../../toronto-election-poll-tracker-backend/backend/model/mayoral_forecast_feed.py#L275-L329)).
Review every availability/band change: the model selects at most one maximal,
highest-priority eligible reading per sample and rejects tied endpoint readings
([`backend/model/mayoral_endpoint.py:373-438`](../../../toronto-election-poll-tracker-backend/backend/model/mayoral_endpoint.py#L373-L438));
publication can be withdrawn when any sensitivity variant crosses a band boundary.

## 4. Resolve, verify, and deploy the Frontend

Do not hand-copy production feeds into `fixtures/`. Those are offline contract/dev
fixtures and change only when a test scenario or feed contract intentionally
changes; ordinary production resolution writes the gitignored `.release-data/`
([`fixtures/README.md:10-18`](../../../toronto-election-poll-tracker/fixtures/README.md#L10-L18),
[`frontend .gitignore:38-41`](../../../toronto-election-poll-tracker/.gitignore#L38-L41)).

After the new Backend release is the latest stable release, preflight from the
clean, up-to-date Frontend `main` repository:

```bash
cd ../toronto-election-poll-tracker
npm test
npm run lint
BACKEND_RELEASE_TAG="$BACKEND_TAG" npm run vercel-build
jq . .release-data/source_manifest.json
```

`vercel-build` resolves the exact Backend release, follows its
exact Results and Polling tags, verifies upstream manifest hashes and downloaded
feed checksums, writes the resolved feeds and source manifest, then statically
builds with `FEED_LOCAL_DIR=.release-data`
([`package.json:5-11`](../../../toronto-election-poll-tracker/package.json#L5-L11),
[`scripts/resolve-releases.mjs:30-121`](../../../toronto-election-poll-tracker/scripts/resolve-releases.mjs#L30-L121)).
Confirm the source manifest names `$BACKEND_TAG`, `$POLLING_TAG`, and `$RESULTS_TAG`.
Then inspect `out/` at `/`, `/polls/`, `/candidates/`, `/wards/`, and
`/how-it-works/`.

Promote deliberately with authenticated Vercel CLI access (linked project or
`VERCEL_TOKEN`):

```bash
npm run deploy:production -- "$BACKEND_TAG"
```

Verify the deployed pages above and `/data/source-manifest.json`; confirm the new
poll metadata/shares, the forecast evidence date/sample list, and the three pinned
tags. The production action and dependency order are defined as manual
([`three-repo architecture:103-120`](../../../toronto-election-poll-tracker/docs/superpowers/specs/2026-08-26-three-repo-data-architecture-design.md#L103-L120)).

## Failure and rollback rules

- **Never overwrite a release asset or reuse a tag.** Publish a corrected Polling
  release, then a new Backend release pinning it. Existing releases are the audit
  trail.
- A bad poll can alter or withdraw published probability bands because sensitivity
  gates are rerun. Stop before Backend publication if changes are not understood.
- If Backend was published but not deployed, leave it immutable and publish a
  corrected later release; ensure the corrected release is latest before building.
- If deployed, immediately promote the prior known-good Vercel deployment. Then
  issue corrected Polling and Backend releases; do not mutate old ones
  ([`implementation plan:360-366`](../../../toronto-election-poll-tracker/docs/superpowers/plans/2026-08-26-three-repo-data-architecture.md#L360-L366)).
