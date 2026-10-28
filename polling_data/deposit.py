"""Build the polling deposit (D2) from a Polling release under the toplines rule.

The deposit is the archival copy of the poll corpus behind the 2026 papers. Some
samples come only from sources that prohibit reproduction without the pollster's
permission. For those, the deposit keeps one topline reading per race, the one the
pollster released free, and withholds every other reading of the sample, its
responses, and the verbatim question text of the kept reading. The rule is curated
in ``data/deposit/toplines_rule.csv``; free sources that the release does not record
are listed in ``data/deposit/free_sources.csv``. Every other sample passes through
unchanged, and no source document bytes are deposited.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULE = ROOT / "data" / "deposit" / "toplines_rule.csv"
DEFAULT_FREE_SOURCES = ROOT / "data" / "deposit" / "free_sources.csv"

DEPOSIT_MANIFEST_SCHEMA_VERSION = 1
WITHHELD_STATUS = "withheld"
WITHHELD_REASON = (
    "Withheld under the toplines rule: not the pollster's free topline for this race."
)
CORPORA = ("current", "historical")

# Release assets the deposit carries, by corpus and by how the rule touches them.
INCLUDED = {
    "poll_samples.csv": ("current", "samples"),
    "poll_readings.csv": ("current", "readings"),
    "poll_responses.csv": ("current", "responses"),
    "poll_sample_documents.csv": ("current", "sample_documents"),
    "source_documents.csv": ("current", "source_documents"),
    "reading_classification.csv": ("current", "reading_rows"),
    "descriptive_poll_readings.csv": ("current", "descriptive"),
    "all_respondent_poll_readings.csv": ("current", "reading_rows"),
    "model_exclusions.csv": ("current", "passthrough"),
    "ward_poll_readings.csv": ("current", "passthrough"),
    "historical_mayoral_poll_samples.csv": ("historical", "samples"),
    "historical_mayoral_poll_readings.csv": ("historical", "readings"),
    "historical_mayoral_poll_responses.csv": ("historical", "responses"),
    "historical_mayoral_poll_sample_documents.csv": ("historical", "sample_documents"),
    "historical_mayoral_source_documents.csv": ("historical", "source_documents"),
    "historical_mayoral_reading_classification.csv": ("historical", "reading_rows"),
    "historical_mayoral_outcomes.csv": ("historical", "passthrough"),
}
# Release assets left out: legacy or derived formats that repeat corpus values in
# other shapes, the site feed, and approval questions outside vote intention.
EXCLUDED = (
    "approval_ratings.csv",
    "historical_mayoral_polls.csv",
    "legacy_historical_poll_crosswalk.csv",
    "mayoral_polling.json",
    "polls.csv",
    "ward_polls.csv",
)
RELEASE_MANIFEST = "release_manifest.json"
NUMBER = re.compile(r"^(?P<number>-?\d+(?:\.\d+)?)(?P<suffix>%?)$")


class DepositError(ValueError):
    """The release, the rule, or the built deposit breaks a deposit invariant."""


@dataclass(frozen=True)
class RuleRow:
    corpus: str
    poll_sample_id: str
    kept_reading_id: str
    source_document_id: str
    source_locator: str
    free_values: dict[str, str]
    basis: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def _write_table(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _parse_free_values(text: str, where: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for part in filter(None, (p.strip() for p in text.split(";"))):
        label, sep, token = part.partition("=")
        if not sep or not label.strip() or not NUMBER.match(token.strip()):
            raise DepositError(f"{where}: free value {part!r} is not 'label=number'")
        if label.strip() in values:
            raise DepositError(f"{where}: free value label {label.strip()!r} repeats")
        values[label.strip()] = token.strip()
    return values


def load_rule(path: Path) -> list[RuleRow]:
    _, rows = _read_table(path)
    rule: list[RuleRow] = []
    seen: set[tuple[str, str]] = set()
    for number, row in enumerate(rows, start=2):
        where = f"{path.name} line {number}"
        if row["corpus"] not in CORPORA:
            raise DepositError(f"{where}: corpus must be one of {CORPORA}")
        if (
            not row["poll_sample_id"]
            or not row["kept_reading_id"]
            or not row["basis"].strip()
        ):
            raise DepositError(f"{where}: sample, kept reading and basis are required")
        key = (row["corpus"], row["kept_reading_id"])
        if key in seen:
            raise DepositError(
                f"{where}: reading {row['kept_reading_id']} is listed twice"
            )
        seen.add(key)
        rule.append(
            RuleRow(
                corpus=row["corpus"],
                poll_sample_id=row["poll_sample_id"],
                kept_reading_id=row["kept_reading_id"],
                source_document_id=row["source_document_id"],
                source_locator=row["source_locator"],
                free_values=_parse_free_values(row["free_values"], where),
                basis=row["basis"].strip(),
            )
        )
    return rule


def _verify_release(release: Path) -> dict:
    manifest_path = release / RELEASE_MANIFEST
    if not manifest_path.is_file():
        raise DepositError(f"{release} has no {RELEASE_MANIFEST}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    names = {asset["filename"] for asset in manifest["assets"]}
    unknown = sorted(names - set(INCLUDED) - set(EXCLUDED))
    if unknown:
        raise DepositError(f"release assets with no deposit decision: {unknown}")
    missing = sorted(set(INCLUDED) - names)
    if missing:
        raise DepositError(f"release lacks deposit tables: {missing}")
    for asset in manifest["assets"]:
        path = release / asset["filename"]
        if not path.is_file() or _sha256(path) != asset["sha256"]:
            raise DepositError(
                f"{asset['filename']} does not match the release manifest"
            )
    return manifest


def _precision(token: str) -> int:
    number = NUMBER.match(token)["number"]
    return len(number.split(".")[1]) if "." in number else 0


def _share(token: str) -> str:
    number = Decimal(NUMBER.match(token)["number"])
    return format(number / 100, f".{_precision(token) + 2}f")


def build_polling_deposit(
    release: Path,
    output: Path,
    *,
    release_tag: str,
    rule_path: Path = DEFAULT_RULE,
    free_sources_path: Path = DEFAULT_FREE_SOURCES,
    generated_at: str | None = None,
) -> dict:
    """Write the deposit for ``release`` to ``output`` and return its manifest."""
    release, output = Path(release), Path(output)
    if output.exists() and any(output.iterdir()):
        raise DepositError(f"{output} exists and is not empty")
    source_manifest = _verify_release(release)
    rule = load_rule(rule_path)
    _, free_sources = _read_table(free_sources_path)

    tables = {name: _read_table(release / name) for name in INCLUDED}

    def table(corpus: str, kind: str) -> str:
        return next(n for n, spec in INCLUDED.items() if spec == (corpus, kind))

    withheld: list[dict[str, str]] = []
    withheld_ids: dict[str, set[str]] = {c: set() for c in CORPORA}
    kept_by_sample: dict[tuple[str, str], list[RuleRow]] = {}
    for row in rule:
        kept_by_sample.setdefault((row.corpus, row.poll_sample_id), []).append(row)

    for corpus in CORPORA:
        samples = {r["poll_sample_id"] for r in tables[table(corpus, "samples")][1]}
        readings = tables[table(corpus, "readings")][1]
        by_sample: dict[str, list[str]] = {}
        for r in readings:
            by_sample.setdefault(r["poll_sample_id"], []).append(r["poll_reading_id"])
        for (rule_corpus, sample), rows in sorted(kept_by_sample.items()):
            if rule_corpus != corpus:
                continue
            if sample not in samples:
                raise DepositError(f"{corpus} sample {sample} is not in the release")
            kept = {r.kept_reading_id for r in rows}
            absent = kept - set(by_sample.get(sample, []))
            if absent:
                raise DepositError(
                    f"{sample}: kept readings not in the sample: {sorted(absent)}"
                )
            for reading_id in by_sample[sample]:
                if reading_id not in kept:
                    withheld_ids[corpus].add(reading_id)
                    withheld.append(
                        {
                            "corpus": corpus,
                            "poll_sample_id": sample,
                            "poll_reading_id": reading_id,
                            "reason": WITHHELD_REASON,
                        }
                    )

    free_by_id = {r["source_document_id"]: r for r in free_sources}
    kept_rule = {(r.corpus, r.kept_reading_id): r for r in rule}

    out_tables: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for name, (corpus, kind) in INCLUDED.items():
        columns, rows = tables[name]
        drop = withheld_ids[corpus]
        rows = [dict(r) for r in rows]
        if kind == "readings":
            rows = [r for r in rows if r["poll_reading_id"] not in drop]
            for r in rows:
                spec = kept_rule.get((corpus, r["poll_reading_id"]))
                if spec is None:
                    continue
                r["question_text"] = ""
                r["question_text_status"] = WITHHELD_STATUS
                if spec.source_document_id:
                    r["source_document_id"] = spec.source_document_id
                if spec.source_locator:
                    r["source_locator"] = spec.source_locator
                if spec.free_values:
                    r["reported_share_precision"] = str(
                        max(_precision(t) for t in spec.free_values.values())
                    )
        elif kind == "responses":
            rows = [r for r in rows if r["poll_reading_id"] not in drop]
            for reading_id, spec in kept_rule.items():
                if spec.corpus != corpus or not spec.free_values:
                    continue
                used = set()
                for r in rows:
                    if (
                        r["poll_reading_id"] != spec.kept_reading_id
                        or r["reported_value"] == ""
                    ):
                        continue
                    token = spec.free_values.get(r["response_label"])
                    if token is None:
                        raise DepositError(
                            f"{spec.kept_reading_id}: no free value for {r['response_label']!r}"
                        )
                    r["reported_value"], r["share"] = token, _share(token)
                    used.add(r["response_label"])
                unused = set(spec.free_values) - used
                if unused:
                    raise DepositError(
                        f"{spec.kept_reading_id}: free values match no response: {sorted(unused)}"
                    )
        elif kind == "reading_rows":
            rows = [r for r in rows if r["poll_reading_id"] not in drop]
        elif kind == "descriptive":
            for r in rows:
                if r["poll_reading_id"] not in drop:
                    continue
                kept = kept_by_sample.get((corpus, r["poll_sample_id"]), [])
                if len(kept) != 1:
                    raise DepositError(
                        f"{r['poll_sample_id']}: representative reading withheld and no single "
                        "kept reading replaces it"
                    )
                r["poll_reading_id"] = kept[0].kept_reading_id
        elif kind == "source_documents":
            known = {r["source_document_id"] for r in rows}
            for r in rows:
                r["local_path"] = ""
            if corpus == "current":
                for doc in free_sources:
                    if doc["source_document_id"] in known:
                        raise DepositError(
                            f"free source {doc['source_document_id']} already exists"
                        )
                    added = {column: "" for column in columns}
                    added.update(
                        {
                            "source_document_id": doc["source_document_id"],
                            "document_role": doc["document_role"],
                            "publisher_url": doc["publisher_url"],
                            "retrieval_url": doc["retrieval_url"],
                            "retrieval_status": "not_retrieved",
                            "media_type": doc["media_type"],
                            "text_layer_status": "not_applicable",
                            "visual_qa_status": "not_applicable",
                            "access_class": "public",
                            "redistribution_status": "unknown",
                            "notes": doc["notes"],
                        }
                    )
                    rows.append(added)
        elif kind == "sample_documents" and corpus == "current":
            linked = {(r["poll_sample_id"], r["source_document_id"]) for r in rows}
            for doc in free_sources:
                for sample in filter(None, doc["poll_sample_ids"].split(";")):
                    if (sample, doc["source_document_id"]) in linked:
                        continue
                    added = {column: "" for column in columns}
                    added.update(
                        {
                            "poll_sample_id": sample,
                            "source_document_id": doc["source_document_id"],
                            "sample_locator": "entire document",
                            "notes": "Free source the deposit cites under the toplines rule.",
                        }
                    )
                    rows.append(added)
        out_tables[name] = (columns, rows)

    _validate(out_tables, withheld_ids, kept_by_sample, free_by_id, table)

    temp = Path(tempfile.mkdtemp(prefix=".polling-deposit-", dir=output.parent))
    try:
        for name, (columns, rows) in out_tables.items():
            _write_table(temp / name, columns, rows)
        _write_table(
            temp / "withheld_readings.csv",
            ["corpus", "poll_sample_id", "poll_reading_id", "reason"],
            withheld,
        )
        shutil.copyfile(rule_path, temp / "toplines_rule.csv")
        shutil.copyfile(free_sources_path, temp / "free_sources.csv")
        assets = [
            {"filename": p.name, "bytes": p.stat().st_size, "sha256": _sha256(p)}
            for p in sorted(temp.iterdir())
        ]
        manifest = {
            "schema_version": DEPOSIT_MANIFEST_SCHEMA_VERSION,
            "generated_at": generated_at or datetime.now(UTC).isoformat(),
            "source_release": {
                "tag": release_tag,
                "repository": source_manifest.get("repository"),
                "source_commit": source_manifest.get("source_commit"),
                "manifest_sha256": _sha256(release / RELEASE_MANIFEST),
            },
            "excluded_release_assets": sorted(EXCLUDED),
            "counts": {
                "samples_under_rule": len(kept_by_sample),
                "readings_kept_under_rule": len(rule),
                "readings_withheld": len(withheld),
            },
            "assets": assets,
        }
        (temp / "deposit_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        output.mkdir(parents=True, exist_ok=True)
        for path in temp.iterdir():
            shutil.move(str(path), output / path.name)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    return manifest


def _validate(out_tables, withheld_ids, kept_by_sample, free_by_id, table) -> None:
    for name, (_, rows) in out_tables.items():
        corpus = INCLUDED[name][0]
        drop = withheld_ids[corpus]
        for row in rows:
            leaked = drop.intersection(row.values())
            if leaked:
                raise DepositError(
                    f"{name} still refers to withheld readings {sorted(leaked)}"
                )
    for corpus in CORPORA:
        readings = out_tables[table(corpus, "readings")][1]
        reading_ids = {r["poll_reading_id"] for r in readings}
        documents = {
            r["source_document_id"]
            for r in out_tables[table(corpus, "source_documents")][1]
        }
        for (rule_corpus, sample), rows in kept_by_sample.items():
            if rule_corpus != corpus:
                continue
            remaining = {
                r["poll_reading_id"] for r in readings if r["poll_sample_id"] == sample
            }
            if remaining != {r.kept_reading_id for r in rows}:
                raise DepositError(f"{sample}: deposit readings differ from the rule")
        for r in readings:
            if r["source_document_id"] and r["source_document_id"] not in documents:
                raise DepositError(
                    f"{r['poll_reading_id']} cites unknown {r['source_document_id']}"
                )
        for kind in ("responses", "reading_rows"):
            for name, spec in INCLUDED.items():
                if spec != (corpus, kind):
                    continue
                orphans = {
                    r["poll_reading_id"] for r in out_tables[name][1]
                } - reading_ids
                if orphans:
                    raise DepositError(
                        f"{name} refers to readings not deposited: {sorted(orphans)}"
                    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--release", type=Path, required=True, help="downloaded Polling release"
    )
    parser.add_argument("--release-tag", required=True, help="that release's tag")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rule", type=Path, default=DEFAULT_RULE)
    parser.add_argument("--free-sources", type=Path, default=DEFAULT_FREE_SOURCES)
    args = parser.parse_args()
    manifest = build_polling_deposit(
        args.release,
        args.output,
        release_tag=args.release_tag,
        rule_path=args.rule,
        free_sources_path=args.free_sources,
    )
    counts = manifest["counts"]
    print(
        f"polling deposit written to {args.output}: {counts['samples_under_rule']} samples "
        f"under the toplines rule, {counts['readings_withheld']} readings withheld"
    )


if __name__ == "__main__":
    main()
