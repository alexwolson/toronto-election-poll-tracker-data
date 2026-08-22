#!/usr/bin/env python3
"""Unified data-refresh runner (manual; nothing is scheduled).

Runs every data-refresh step in dependency order with per-step feedback and
fail-fast, then a forecast checkpoint and a "what to do next" summary. It
rebuilds the sibling source repos, refreshes every upstream input, runs the
gates, and rebuilds the four published feeds.

It deliberately DOES NOT:
  - commit or push (you review `git diff`, then commit) ; and
  - set the editorial gates (live_cycle.field_certified, poll ingestion) — it
    only surfaces their state so you can confirm them.

Run:
  uv run scripts/refresh_all.py                # full refresh
  uv run scripts/refresh_all.py --dry-run      # print the ordered plan, run nothing
  uv run scripts/refresh_all.py --skip-tests   # skip the (slow) pytest gate
  uv run scripts/refresh_all.py --skip-download # reuse the toronto-election-results raw cache
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # this data repo
TER = ROOT.parent.parent / "toronto-election-results"  # sibling: canonical results
DEF = ROOT.parent / "defeatability-index"  # sibling: historical-hint catalog
PY = sys.executable  # this repo's venv python (we run under `uv run`)
PROC = ROOT / "data" / "processed"

_TTY = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text


def bold(t: str) -> str:
    return _c("1", t)


def green(t: str) -> str:
    return _c("32", t)


def red(t: str) -> str:
    return _c("31", t)


def yellow(t: str) -> str:
    return _c("33", t)


class StepError(Exception):
    pass


_STEP = 0
_TOTAL = 0


def header(label: str) -> None:
    global _STEP
    _STEP += 1
    print(f"\n{bold(f'━━ [{_STEP}/{_TOTAL}] {label}')}")


def run_cmd(
    label: str,
    argv: list[str],
    *,
    cwd: Path | None = None,
    fatal: bool = True,
    expect: str | None = None,
    dry: bool = False,
) -> None:
    """Run one step, streaming its output. On non-zero exit: raise (fatal) or warn.

    `expect`: a substring the output must contain; captured + checked (else streamed).
    """
    header(label)
    shown = " ".join(argv)
    where = f"  (cwd: {cwd})" if cwd else ""
    print(f"  $ {shown}{where}")
    if dry:
        print(f"  {yellow('[dry-run] not executed')}")
        return
    start = time.monotonic()
    if expect is not None:
        res = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)
        out = (res.stdout or "") + (res.stderr or "")
        print("\n".join(f"    {line}" for line in out.strip().splitlines()[-40:]))
    else:
        res = subprocess.run(argv, cwd=cwd, check=False)
        out = ""
    dt = time.monotonic() - start
    if res.returncode != 0:
        msg = f"  {red('✗ FAILED')} (exit {res.returncode}, {dt:.0f}s)"
        if fatal:
            print(msg)
            raise StepError(label)
        print(f"{msg}  {yellow('— non-fatal, continuing')}")
        return
    if expect is not None and expect not in out:
        print(
            f"  {yellow(f'⚠ expected to see {expect!r} in output — verify above')} ({dt:.0f}s)"
        )
        return
    print(f"  {green('✓ ok')} ({dt:.0f}s)")


def editorial_checkpoint(dry: bool) -> None:
    header("Editorial checkpoint (report only — never changed by this script)")
    if dry:
        print(f"  {yellow('[dry-run] would report live_cycle + poll-bundle state')}")
        return
    lc = json.loads((ROOT / "data/raw/elections/live_cycle.json").read_text())
    certified = lc.get("field_certified")
    print(f"  field_certified : {certified}")
    print(f"  viable_field    : {lc.get('viable_field')}")
    print(f"  incumbent       : {lc.get('incumbent_candidate_id')}")
    bundle = [
        "poll_samples.csv",
        "poll_readings.csv",
        "poll_responses.csv",
        "source_documents.csv",
        "poll_sample_documents.csv",
        "ward_poll_readings.csv",
    ]
    existing = [
        ROOT / "data/raw/polls" / f
        for f in bundle
        if (ROOT / "data/raw/polls" / f).exists()
    ]
    if existing:
        newest = max(existing, key=lambda p: p.stat().st_mtime)
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(newest.stat().st_mtime))
        print(
            f"  poll bundle     : newest hand-ingested file is {newest.name} @ {when}"
        )
    print(
        f"  {yellow('→ Poll ingestion is manual (double-read workflow); confirm the bundle is current.')}"
    )
    if not certified:
        print(
            f"  {red('⚠ field_certified is FALSE — the mayoral forecast will build DARK (all Unavailable).')}"
        )


def _load(name: str) -> dict:
    return json.loads((PROC / name).read_text())


def forecast_checkpoint(dry: bool) -> None:
    header("Forecast checkpoint (did it come out right?)")
    if dry:
        print(
            f"  {yellow('[dry-run] would parse + print tier, quantities, open seats')}"
        )
        return
    fc = _load("mayoral_forecast.json")
    print(f"  mayoral tier: {bold(fc.get('evidence_tier', '?'))}")
    for cid, q in fc.get("candidate_win", {}).items():
        avail = q.get("availability")
        detail = q.get("frequency_statement") or q.get("reason") or ""
        mark = green("●") if avail == "Forecast Available" else yellow("○")
        print(f"    {mark} {cid:10} {avail:20} {detail}")
    for key in ("incumbent_defeat", "close_result"):
        q = fc.get(key, {})
        avail = q.get("availability")
        detail = q.get("frequency_statement") or q.get("reason") or ""
        mark = green("●") if avail == "Forecast Available" else yellow("○")
        print(f"    {mark} {key:10} {avail:20} {detail}")

    cc = _load("council_race_cards.json")
    wards = cc.get("wards", {})
    open_seats = sorted((w for w, c in wards.items() if c.get("is_open_seat")), key=int)
    disagree = sorted(
        (w for w, c in wards.items() if c.get("incumbency_flag_disagrees")), key=int
    )
    print(f"  council schema_version: {cc.get('schema_version')}  ({len(wards)} wards)")
    print(f"    open seats: {open_seats}")
    if disagree:
        print(f"    {yellow(f'incumbency flag disagrees (review): {disagree}')}")
    man = _load("manifest.json")
    print(f"  manifest feed_versions: {man.get('feed_versions')}")


def summary(dry: bool) -> None:
    header("Summary + next steps")
    if not dry:
        print(bold("  changed files (git diff --stat):"))
        res = subprocess.run(
            ["git", "-C", str(ROOT), "diff", "--stat"],
            text=True,
            capture_output=True,
            check=False,
        )
        print(
            "\n".join(f"    {line}" for line in res.stdout.strip().splitlines())
            or "    (none)"
        )
    print(bold("\n  Next (manual, deliberate):"))
    print("    1. Review the diff above.")
    print(
        "    2. Commit + push to main:  git add <files by name> && git commit && git push"
    )
    print("    3. Redeploy the frontend:  (in the frontend repo)  vercel --prod")


def main() -> None:
    global _TOTAL
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dry-run", action="store_true", help="print the ordered plan; run nothing"
    )
    ap.add_argument("--skip-tests", action="store_true", help="skip the pytest gate")
    ap.add_argument(
        "--skip-download",
        action="store_true",
        help="reuse the toronto-election-results raw cache (no re-download)",
    )
    args = ap.parse_args()
    dry = args.dry_run

    for sib, gen in ((TER, "toronto-election-results"), (DEF, "defeatability-index")):
        if not sib.is_dir():
            print(red(f"✗ sibling repo not found: {sib}  (needed to rebuild {gen})"))
            sys.exit(1)

    ter_pipeline = ["uv", "run", "python", "-m", "toronto_election_results.pipeline"]
    if args.skip_download:
        ter_pipeline.append("--skip-download")

    # Count steps for the [n/total] display (2 siblings + 5 inputs + editorial +
    # 2 gates + optional pytest + 2 builds + forecast + summary).
    _TOTAL = 2 + 5 + 1 + (3 if not args.skip_tests else 2) + 2 + 1 + 1

    print(bold("Toronto election — unified data refresh"))
    print(f"  data repo : {ROOT}")
    print(f"  siblings  : {TER}  |  {DEF}")
    if dry:
        print(yellow("  DRY RUN — showing the ordered plan; nothing will execute.\n"))

    try:
        # 1) Rebuild the sibling sources (their generators, in their own envs).
        run_cmd("Sibling: rebuild canonical results", ter_pipeline, cwd=TER, dry=dry)
        run_cmd(
            "Sibling: rebuild historical-hint catalog",
            [
                "uv",
                "run",
                "python",
                "-m",
                "defeatability_index.candidate_history_study",
            ],
            cwd=DEF,
            dry=dry,
        )

        # 2) Refresh this repo's upstream inputs.
        run_cmd(
            "Fetch candidate registrations (city API)",
            [PY, "scripts/fetch_candidates.py"],
            cwd=ROOT,
            dry=dry,
        )
        run_cmd(
            "Fetch descriptive poll series (Wikipedia)",
            [PY, "scripts/fetch_polls.py"],
            cwd=ROOT,
            dry=dry,
        )
        run_cmd(
            "Vendor canonical results",
            [PY, "scripts/sync_canonical_results.py"],
            cwd=ROOT,
            dry=dry,
        )
        run_cmd(
            "Vendor historical-hint catalog",
            [PY, "scripts/sync_historical_hints.py"],
            cwd=ROOT,
            dry=dry,
        )
        run_cmd(
            "Rebuild historical mayoral corpus",
            [PY, "scripts/reconstruct_historical_mayoral.py", "--write"],
            cwd=ROOT,
            dry=dry,
        )

        # 3) Editorial state (surfaced, not changed).
        editorial_checkpoint(dry)

        # 4) Gates.
        run_cmd(
            "Gate: mayoral endpoint qualification",
            [PY, "scripts/evaluate_mayoral_endpoint.py"],
            cwd=ROOT,
            expect="qualified",
            dry=dry,
        )
        run_cmd(
            "Gate: incumbency endpoint (expected NOT to qualify)",
            [PY, "scripts/evaluate_incumbency_endpoint.py"],
            cwd=ROOT,
            fatal=False,
            dry=dry,
        )
        if not args.skip_tests:
            run_cmd(
                "Gate: full test suite", [PY, "-m", "pytest", "-q"], cwd=ROOT, dry=dry
            )

        # 5) Build the four published feeds.
        run_cmd(
            "Build mayoral + polling + manifest feeds",
            [PY, "scripts/build_publication_snapshot.py"],
            cwd=ROOT,
            dry=dry,
        )
        run_cmd(
            "Build council race cards",
            [PY, "scripts/build_council_snapshot.py"],
            cwd=ROOT,
            dry=dry,
        )

        # 6) Checkpoints + summary.
        forecast_checkpoint(dry)
        summary(dry)
    except StepError as e:
        print(red(f"\n✗ Refresh halted at: {e}. Fix the failure above and re-run."))
        sys.exit(1)

    print(
        green(bold("\n✓ Refresh complete."))
        if not dry
        else yellow(bold("\n(dry run — nothing executed)"))
    )


if __name__ == "__main__":
    main()
