"""Build and publish a polling-only release pinned to canonical Results data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

RELEASE_MANIFEST_SCHEMA_VERSION = 1
REPOSITORY = "alexwolson/toronto-election-poll-tracker-data"
RESULTS_REPOSITORY = "alexwolson/toronto-election-results"
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
) -> tuple[dict, dict[str, str], dict[str, str]]:
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
    people = {
        row["normalized_name"]: row["person_id"]
        for row in aliases["aliases"]
        if row.get("is_unambiguous") and row.get("person_id")
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
    source: Path, people: dict[str, str]
) -> tuple[list[dict[str, str]], list[str]]:
    rows = _read_csv(source)
    source_columns = list(rows[0]) if rows else []
    columns = [column for column in source_columns if column != "candidate_id"]
    insertion = columns.index("candidate_name")
    columns[insertion:insertion] = ["person_id", "source_candidate_id"]
    for row in rows:
        source_id = row.pop("candidate_id", "")
        row["source_candidate_id"] = source_id
        row["person_id"] = ""
        if row["response_kind"] == "candidate" and row["candidate_name"]:
            row["person_id"] = people.get(_name_key(row["candidate_name"]), "")
    return rows, columns


def _build_mayoral_polling_feed(
    polls_path: Path, responses: list[dict[str, str]]
) -> dict[str, object]:
    """Build a descriptive, canonical-person-keyed frontend feed."""

    candidate_keys: dict[str, set[str]] = {}
    for row in responses:
        if row["response_kind"] == "candidate" and row["source_candidate_id"]:
            key = row["person_id"] or f"unresolved:{row['source_candidate_id']}"
            candidate_keys.setdefault(row["source_candidate_id"], set()).add(key)
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
            resolved.get(key, f"unresolved:{key}")
            for key in row["field_tested"].split(",")
            if key
        ]
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


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def publish_polling_release(tag: str, bundle: str | Path, *, root: str | Path) -> None:
    project = Path(root)
    if _git("status", "--porcelain", cwd=project):
        raise RuntimeError(
            "refusing to publish a polling release from a dirty working tree"
        )
    bundle_path = Path(bundle)
    manifest = json.loads(
        (bundle_path / "release_manifest.json").read_text(encoding="utf-8")
    )
    head = _git("rev-parse", "HEAD", cwd=project)
    if manifest.get("source_dirty") or manifest.get("source_commit") != head:
        raise RuntimeError("release bundle was not built from the current clean commit")
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            tag,
            "--repo",
            REPOSITORY,
            "--title",
            f"Toronto election polling {tag}",
            "--generate-notes",
            *sorted(str(path) for path in bundle_path.iterdir() if path.is_file()),
        ],
        cwd=project,
        check=True,
    )


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
