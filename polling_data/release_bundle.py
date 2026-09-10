"""Build and publish a polling-only release pinned to canonical Results data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from polling_data.descriptive_polls import validate_descriptive_polls

RELEASE_MANIFEST_SCHEMA_VERSION = 1
REPOSITORY = "alexwolson/toronto-election-poll-tracker-data"
RESULTS_REPOSITORY = "alexwolson/toronto-election-results"
POLLING_TAG_PATTERN = re.compile(r"^polling-\d{4}-\d{2}-\d{2}\.\d+$")
GIT_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_POLL_METADATA = {
    "poll_id",
    "firm",
    "date_conducted",
    "date_published",
    "sample_size",
    "methodology",
    "field_tested",
    "notes",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _name_key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _load_results_dependency(
    results_bundle: Path,
) -> tuple[dict, dict[str, tuple[str, ...]], dict[str, str]]:
    manifest_path = results_bundle / "release_manifest.json"
    aliases_path = results_bundle / "person_aliases.json"
    results_path = results_bundle / "election_results.csv"
    for required in (manifest_path, aliases_path, results_path):
        if not required.is_file():
            raise FileNotFoundError(f"missing Results release asset: {required}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("repository") != RESULTS_REPOSITORY:
        raise ValueError("Results manifest names an unexpected repository")

    aliases = json.loads(aliases_path.read_text(encoding="utf-8"))
    alias_ids: dict[str, set[str]] = {}
    ambiguous_aliases: set[str] = set()
    for row in aliases["aliases"]:
        key = _name_key(row.get("normalized_name", ""))
        if not key:
            continue
        alias_ids.setdefault(key, set())
        if not row.get("is_unambiguous") or not row.get("person_id"):
            ambiguous_aliases.add(key)
        else:
            alias_ids[key].add(row["person_id"])
    people = {
        key: tuple(sorted(ids))
        if key not in ambiguous_aliases and len(ids) == 1
        else ()
        for key, ids in alias_ids.items()
    }

    contests: dict[str, str] = {}
    for row in _read_csv(results_path):
        if (
            row["election_year"] != "2026"
            or row["represented_body"] != "toronto_city_council"
            or row["result_status"] != "pending"
        ):
            continue
        if row["office_type"] == "mayor":
            legacy = "toronto-mayor-2026"
        elif row["office_type"] == "councillor" and row[
            "official_district_id"
        ].startswith("ward-"):
            ward = int(row["official_district_id"].removeprefix("ward-"))
            legacy = f"toronto-ward-{ward}-2026"
        else:
            continue
        previous = contests.setdefault(legacy, row["contest_id"])
        if previous != row["contest_id"]:
            raise ValueError(
                f"Results release has conflicting contest IDs for {legacy}"
            )
    return manifest, people, contests


def _canonical_poll_readings(
    source: Path, contests: dict[str, str]
) -> tuple[list[dict[str, str]], list[str]]:
    rows = _read_csv(source)
    columns = list(rows[0]) if rows else []
    columns.insert(columns.index("contest_id") + 1, "source_contest_id")
    for row in rows:
        source_id = row["contest_id"]
        if source_id not in contests:
            raise ValueError(
                f"poll reading references a contest absent from Results: {source_id}"
            )
        row["source_contest_id"] = source_id
        row["contest_id"] = contests[source_id]
    return rows, columns


def _canonical_poll_responses(
    source: Path, people: dict[str, tuple[str, ...]]
) -> tuple[list[dict[str, str]], list[str]]:
    rows = _read_csv(source)
    source_columns = list(rows[0]) if rows else []
    columns = [column for column in source_columns if column != "candidate_id"]
    insertion = columns.index("candidate_name")
    columns[insertion:insertion] = ["person_id", "source_candidate_id"]
    identity_failures: list[str] = []
    for row in rows:
        source_id = row.pop("candidate_id", "")
        row["source_candidate_id"] = source_id
        row["person_id"] = ""
        if row["response_kind"] != "candidate":
            continue
        candidate_name = row["candidate_name"]
        matches = people.get(_name_key(candidate_name)) if candidate_name else None
        if matches is None or len(matches) != 1:
            reason = "absent" if matches is None else "ambiguous"
            identity_failures.append(
                f"({reason}) poll_reading_id={row['poll_reading_id']!r}, "
                f"source_candidate_id={source_id!r}, candidate_name={candidate_name!r}"
            )
            continue
        row["person_id"] = matches[0]
    if identity_failures:
        raise ValueError(
            "poll candidate identities did not resolve to exactly one Results person: "
            + "; ".join(identity_failures)
        )
    return rows, columns


def _build_mayoral_polling_feed(
    polls_path: Path, responses: list[dict[str, str]]
) -> dict[str, object]:
    """Build a descriptive, canonical-person-keyed frontend feed."""

    candidate_keys: dict[str, set[str]] = {}
    for row in responses:
        if row["response_kind"] == "candidate" and row["source_candidate_id"]:
            candidate_keys.setdefault(row["source_candidate_id"], set()).add(
                row["person_id"]
            )
    conflicting = {
        key: values for key, values in candidate_keys.items() if len(values) > 1
    }
    if conflicting:
        source_id = min(conflicting)
        raise ValueError(
            f"polling source candidate ID maps to multiple people: {source_id}"
        )
    resolved = {key: next(iter(values)) for key, values in candidate_keys.items()}

    polls: list[dict[str, object]] = []
    for row in _read_csv(polls_path):
        shares: dict[str, float] = {}
        for key, value in row.items():
            if key in _POLL_METADATA or not value.strip():
                continue
            output_key = resolved.get(key, f"response:{key}")
            shares[output_key] = float(value)
        tested = [
            resolved.get(key, f"response:{key}")
            for key in row["field_tested"].split(",")
            if key
        ]
        if set(tested) != set(shares):
            raise ValueError(
                f"poll field_tested/share key mismatch: poll_id={row['poll_id']!r}, "
                f"missing_from_field_tested={sorted(set(shares) - set(tested))!r}, "
                f"missing_from_shares={sorted(set(tested) - set(shares))!r}"
            )
        polls.append(
            {
                "poll_id": row["poll_id"],
                "firm": row["firm"],
                "date_conducted": row["date_conducted"],
                "date_published": row["date_published"],
                "sample_size": int(row["sample_size"])
                if row["sample_size"].strip()
                else None,
                "methodology": row["methodology"],
                "field_tested": tested,
                "shares": shares,
                "notes": row["notes"],
            }
        )
    polls.sort(
        key=lambda row: (str(row["date_published"]), str(row["poll_id"])), reverse=True
    )
    candidates = sorted({key for poll in polls for key in poll["shares"]})
    trend: dict[str, list[dict[str, object]]] = {key: [] for key in candidates}
    for poll in sorted(
        polls, key=lambda row: (str(row["date_conducted"]), str(row["poll_id"]))
    ):
        for candidate, share in poll["shares"].items():
            trend[candidate].append(
                {
                    "date_conducted": poll["date_conducted"],
                    "poll_id": poll["poll_id"],
                    "share": share,
                }
            )
    return {
        "schema_version": 2,
        "candidates": candidates,
        "polls": polls,
        "latest": polls[0] if polls else None,
        "trend": trend,
    }


def build_polling_release_bundle(
    source_dir: str | Path,
    results_bundle: str | Path,
    destination: str | Path,
    *,
    results_release: str,
    source_commit: str,
    dirty: bool,
    generated_at: str | None = None,
) -> Path:
    """Build an atomic polling release with canonical identities and contests."""

    source = Path(source_dir)
    results = Path(results_bundle)
    target = Path(destination)
    results_manifest, people, contests = _load_results_dependency(results)
    required = [source / "poll_readings.csv", source / "poll_responses.csv"]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"missing polling release input: {path}")
    if not results_release.strip():
        raise ValueError("results_release must be an immutable release tag")

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{target.name}.stage-", dir=target.parent
    ) as tmp:
        staging = Path(tmp)
        for path in sorted(source.glob("*.csv")):
            shutil.copy2(path, staging / path.name)
        readings, reading_columns = _canonical_poll_readings(required[0], contests)
        responses, response_columns = _canonical_poll_responses(required[1], people)
        validate_descriptive_polls(source, source / "polls.csv")
        _write_csv(staging / "poll_readings.csv", readings, reading_columns)
        _write_csv(staging / "poll_responses.csv", responses, response_columns)
        polling_feed = _build_mayoral_polling_feed(source / "polls.csv", responses)
        (staging / "mayoral_polling.json").write_text(
            json.dumps(
                polling_feed, ensure_ascii=False, separators=(",", ":"), sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )

        assets = sorted(staging.iterdir(), key=lambda path: path.name)
        manifest = {
            "schema_version": RELEASE_MANIFEST_SCHEMA_VERSION,
            "repository": REPOSITORY,
            "generated_at": generated_at
            or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "source_commit": source_commit,
            "source_dirty": dirty,
            "dependencies": {
                "results": {
                    "repository": RESULTS_REPOSITORY,
                    "release": results_release,
                    "source_commit": results_manifest["source_commit"],
                    "manifest_sha256": _sha256(results / "release_manifest.json"),
                }
            },
            "assets": [
                {
                    "filename": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
                for path in assets
            ],
            "tables": {
                "poll_readings": "poll_readings.csv",
                "poll_responses": "poll_responses.csv",
            },
            "table_versions": {"poll_readings": 2, "poll_responses": 2},
            "feeds": {"mayoral_polling": "mayoral_polling.json"},
            "feed_versions": {"mayoral_polling": 2},
        }
        (staging / "release_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        backup = target.with_name(f".{target.name}.backup")
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            target.replace(backup)
        try:
            shutil.copytree(staging, target)
        except Exception:
            if backup.exists() and not target.exists():
                backup.replace(target)
            raise
        finally:
            if backup.exists():
                shutil.rmtree(backup)
    return target


def _git(
    *args: str,
    cwd: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    result = runner(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _validate_results_pin(manifest: dict) -> dict:
    dependencies = manifest.get("dependencies")
    pin = dependencies.get("results") if isinstance(dependencies, dict) else None
    if (
        not isinstance(pin, dict)
        or pin.get("repository") != RESULTS_REPOSITORY
        or not isinstance(pin.get("release"), str)
        or not pin["release"].strip()
        or not GIT_COMMIT_PATTERN.fullmatch(str(pin.get("source_commit", "")))
        or not SHA256_PATTERN.fullmatch(str(pin.get("manifest_sha256", "")))
    ):
        raise RuntimeError("polling release manifest has an invalid Results pin")
    return pin


def _verify_manifest_assets(directory: Path, manifest: dict) -> None:
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        raise RuntimeError("polling release manifest declares no assets")
    seen: set[str] = set()
    for record in assets:
        if not isinstance(record, dict):
            raise TypeError("polling release manifest has an invalid asset record")
        filename = record.get("filename")
        expected = record.get("sha256")
        if (
            not isinstance(filename, str)
            or not filename
            or Path(filename).name != filename
            or filename in seen
            or not SHA256_PATTERN.fullmatch(str(expected or ""))
        ):
            raise RuntimeError("polling release manifest has an invalid asset record")
        seen.add(filename)
        path = directory / filename
        if not path.is_file():
            raise RuntimeError(f"released asset is missing: {filename}")
        if _sha256(path) != expected:
            raise RuntimeError(f"released asset checksum mismatch: {filename}")


def _release_exists(
    tag: str,
    *,
    project: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> bool:
    result = runner(
        ["gh", "release", "view", tag, "--repo", REPOSITORY, "--json", "tagName"],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True
    error = f"{result.stdout}\n{result.stderr}".lower()
    if "release not found" in error or "http 404" in error:
        return False
    raise RuntimeError(
        f"could not determine whether release {tag} exists: {error.strip()}"
    )


def _verify_published_release(
    tag: str,
    *,
    project: Path,
    local_manifest_path: Path,
    expected_source_commit: str,
    expected_results_pin: dict,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"verify-{tag}-") as tmp:
        downloaded = Path(tmp)
        runner(
            [
                "gh",
                "release",
                "download",
                tag,
                "--repo",
                REPOSITORY,
                "--dir",
                str(downloaded),
            ],
            cwd=project,
            check=True,
        )
        manifest_path = downloaded / "release_manifest.json"
        if not manifest_path.is_file():
            raise RuntimeError("published release is missing release_manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("source_commit") != expected_source_commit:
            raise RuntimeError(
                "published release manifest source commit changed after upload"
            )
        if _validate_results_pin(manifest) != expected_results_pin:
            raise RuntimeError(
                "published release manifest Results pin changed after upload"
            )
        if manifest_path.read_bytes() != local_manifest_path.read_bytes():
            raise RuntimeError(
                "published release manifest bytes differ from the uploaded bundle"
            )
        _verify_manifest_assets(downloaded, manifest)


def publish_polling_release(
    tag: str,
    bundle: str | Path,
    *,
    root: str | Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    if not POLLING_TAG_PATTERN.fullmatch(tag):
        raise ValueError(
            f"polling release tag must match polling-YYYY-MM-DD.N; received {tag!r}"
        )
    project = Path(root)
    if _git("status", "--porcelain", cwd=project, runner=runner):
        raise RuntimeError(
            "refusing to publish a polling release from a dirty working tree"
        )
    bundle_path = Path(bundle)
    if not bundle_path.is_absolute():
        bundle_path = project / bundle_path
    manifest_path = bundle_path / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    head = _git("rev-parse", "HEAD", cwd=project, runner=runner)
    if manifest.get("source_dirty") or manifest.get("source_commit") != head:
        raise RuntimeError("release bundle was not built from the current clean commit")
    results_pin = _validate_results_pin(manifest)
    _verify_manifest_assets(bundle_path, manifest)

    remote_main = _git(
        "ls-remote", "origin", "refs/heads/main", cwd=project, runner=runner
    ).split()
    if not remote_main or not GIT_COMMIT_PATTERN.fullmatch(remote_main[0]):
        raise RuntimeError("could not resolve the remote main commit")
    if head != remote_main[0]:
        raise RuntimeError(
            f"source commit {head} is not the current remote main commit {remote_main[0]}"
        )
    if _git(
        "ls-remote",
        "--tags",
        "origin",
        f"refs/tags/{tag}",
        cwd=project,
        runner=runner,
    ):
        raise RuntimeError(f"remote tag already exists: {tag}")
    if _release_exists(tag, project=project, runner=runner):
        raise RuntimeError(f"GitHub release already exists: {tag}")

    try:
        runner(
            [
                "gh",
                "release",
                "create",
                tag,
                "--repo",
                REPOSITORY,
                "--target",
                head,
                "--title",
                f"Toronto election polling {tag}",
                "--generate-notes",
                *sorted(str(path) for path in bundle_path.iterdir() if path.is_file()),
            ],
            cwd=project,
            check=True,
        )
        _verify_published_release(
            tag,
            project=project,
            local_manifest_path=manifest_path,
            expected_source_commit=head,
            expected_results_pin=results_pin,
            runner=runner,
        )
    except Exception as error:
        raise RuntimeError(
            f"polling release {tag} failed or could not be verified: {error}. "
            "Inspect the GitHub release and tag, keep any partial publication "
            "immutable, and publish a correction under a new tag; never reuse this tag."
        ) from error
    print(f"published and verified polling release {tag} at source commit {head}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--source", type=Path, default=Path("data/raw/polls"))
    build.add_argument("--results-bundle", type=Path, required=True)
    build.add_argument("--results-release", required=True)
    build.add_argument("--output", type=Path, default=Path("dist"))
    publish = subparsers.add_parser("publish")
    publish.add_argument("tag")
    publish.add_argument("--bundle", type=Path, default=Path("dist"))
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "build":
        output = build_polling_release_bundle(
            args.source,
            args.results_bundle,
            args.output,
            results_release=args.results_release,
            source_commit=_git("rev-parse", "HEAD", cwd=root),
            dirty=bool(_git("status", "--porcelain", cwd=root)),
        )
        print(f"polling release bundle written to {output}")
    else:
        publish_polling_release(args.tag, args.bundle, root=root)


if __name__ == "__main__":
    main()
