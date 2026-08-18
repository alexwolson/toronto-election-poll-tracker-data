"""Source-backed comparison population for the Mayoral Incumbency Prior.

This module owns the small frozen Ontario comparison population.  It does not
assign the prior any forecast weight: it exposes the observed incumbent trials,
derived summaries, and leave-one-city-out partitions for later qualification.
"""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Final, Literal


SOURCE_COLUMNS: Final = (
    "source_document_id",
    "city_id",
    "election_year",
    "publisher_url",
    "retrieval_url",
    "media_type",
    "sha256",
    "local_path",
    "byte_size",
    "verification_status",
    "notes",
)

TRIAL_COLUMNS: Final = (
    "trial_id",
    "city_id",
    "city_name",
    "election_date",
    "population_group",
    "term_length_years",
    "incumbent_candidate_id",
    "incumbent_name",
    "incumbent_votes",
    "strongest_opponent_candidate_id",
    "strongest_opponent_name",
    "strongest_opponent_votes",
    "valid_votes",
    "final_candidate_count",
    "source_document_id",
    "source_locator",
    "notes",
)

_EXPECTED_V1_CITY_COUNTS: Final = {
    "toronto": 3,
    "ottawa": 4,
    "hamilton": 3,
    "mississauga": 4,
    "brampton": 5,
}
_SHA256 = re.compile(r"[0-9a-f]{64}")


class MayoralIncumbencyDataError(ValueError):
    """Raised when the frozen comparison population is malformed."""


@dataclass(frozen=True, slots=True)
class IncumbencySourceDocument:
    source_document_id: str
    city_id: str
    election_year: int
    publisher_url: str
    retrieval_url: str
    media_type: Literal[
        "application/pdf",
        "application/vnd.ms-excel",
        "text/html",
    ]
    sha256: str | None
    local_path: Path | None
    byte_size: int | None
    verification_status: Literal[
        "verified_artifact",
        "verified_official_dynamic_source",
        "corroborated_secondary",
        "source_gap",
    ]
    notes: str | None


@dataclass(frozen=True, slots=True)
class MayoralIncumbencyTrial:
    trial_id: str
    city_id: str
    city_name: str
    election_date: date
    population_group: Literal[
        "v1_regular",
        "toronto_pre_2006_sensitivity",
    ]
    term_length_years: int
    incumbent_candidate_id: str
    incumbent_name: str
    incumbent_votes: int
    strongest_opponent_candidate_id: str
    strongest_opponent_name: str
    strongest_opponent_votes: int
    valid_votes: int
    final_candidate_count: int
    source_document_id: str
    source_locator: str
    notes: str | None

    @property
    def incumbent_won(self) -> bool:
        return self.incumbent_votes > self.strongest_opponent_votes

    @property
    def incumbent_share(self) -> Decimal:
        return Decimal(self.incumbent_votes) / Decimal(self.valid_votes)

    @property
    def strongest_opponent_share(self) -> Decimal:
        return Decimal(self.strongest_opponent_votes) / Decimal(self.valid_votes)

    @property
    def incumbent_margin_share(self) -> Decimal:
        return Decimal(
            self.incumbent_votes - self.strongest_opponent_votes
        ) / Decimal(self.valid_votes)


@dataclass(frozen=True, slots=True)
class MayoralIncumbencySummary:
    attempts: int
    wins: int
    losses: int
    empirical_win_rate: Decimal
    median_incumbent_share: Decimal
    median_incumbent_margin_share: Decimal


@dataclass(frozen=True, slots=True)
class MayoralIncumbencyFold:
    held_out_city_id: str
    training_trials: tuple[MayoralIncumbencyTrial, ...]
    held_out_trials: tuple[MayoralIncumbencyTrial, ...]


@dataclass(frozen=True, slots=True)
class MayoralIncumbencyPopulation:
    source_documents: tuple[IncumbencySourceDocument, ...]
    trials: tuple[MayoralIncumbencyTrial, ...]

    @property
    def v1_trials(self) -> tuple[MayoralIncumbencyTrial, ...]:
        return tuple(
            trial for trial in self.trials if trial.population_group == "v1_regular"
        )

    @property
    def toronto_2000_sensitivity_trial(self) -> MayoralIncumbencyTrial:
        sensitivity = tuple(
            trial
            for trial in self.trials
            if trial.population_group == "toronto_pre_2006_sensitivity"
        )
        if len(sensitivity) != 1:
            raise MayoralIncumbencyDataError(
                "expected exactly one Toronto pre-2006 sensitivity trial"
            )
        return sensitivity[0]

    @property
    def source_gaps(self) -> tuple[IncumbencySourceDocument, ...]:
        source_by_id = {
            source.source_document_id: source for source in self.source_documents
        }
        used_ids = {trial.source_document_id for trial in self.trials}
        return tuple(
            source_by_id[source_id]
            for source_id in sorted(used_ids)
            if source_by_id[source_id].verification_status == "source_gap"
        )

    @property
    def corroborated_secondary_trials(self) -> tuple[MayoralIncumbencyTrial, ...]:
        """Trials retained with strong corroboration but no certified payload."""

        status_by_source_id = {
            source.source_document_id: source.verification_status
            for source in self.source_documents
        }
        return tuple(
            trial
            for trial in self.v1_trials
            if status_by_source_id[trial.source_document_id]
            == "corroborated_secondary"
        )

    @property
    def is_v1_ready(self) -> bool:
        source_by_id = {
            source.source_document_id: source for source in self.source_documents
        }
        return all(
            source_by_id[trial.source_document_id].verification_status != "source_gap"
            for trial in self.v1_trials
        )

    def summary(self, *, include_toronto_2000: bool = False) -> MayoralIncumbencySummary:
        trials = self.v1_trials
        if include_toronto_2000:
            trials = trials + (self.toronto_2000_sensitivity_trial,)
        if not trials:
            raise MayoralIncumbencyDataError("cannot summarize an empty population")
        wins = sum(trial.incumbent_won for trial in trials)
        return MayoralIncumbencySummary(
            attempts=len(trials),
            wins=wins,
            losses=len(trials) - wins,
            empirical_win_rate=Decimal(wins) / Decimal(len(trials)),
            median_incumbent_share=_median(
                tuple(trial.incumbent_share for trial in trials)
            ),
            median_incumbent_margin_share=_median(
                tuple(trial.incumbent_margin_share for trial in trials)
            ),
        )

    def leave_one_city_out_folds(self) -> tuple[MayoralIncumbencyFold, ...]:
        trials = self.v1_trials
        cities = tuple(sorted({trial.city_id for trial in trials}))
        return tuple(
            MayoralIncumbencyFold(
                held_out_city_id=city_id,
                training_trials=tuple(
                    trial for trial in trials if trial.city_id != city_id
                ),
                held_out_trials=tuple(
                    trial for trial in trials if trial.city_id == city_id
                ),
            )
            for city_id in cities
        )


def load_mayoral_incumbency_population(
    project_root: str | Path,
) -> MayoralIncumbencyPopulation:
    root = Path(project_root)
    sources = tuple(
        _parse_source(row, row_number)
        for row_number, row in _read_csv(
            root / "data/raw/elections/mayoral_incumbency_sources.csv",
            SOURCE_COLUMNS,
        )
    )
    trials = tuple(
        _parse_trial(row, row_number)
        for row_number, row in _read_csv(
            root / "data/raw/elections/mayoral_incumbency_trials.csv",
            TRIAL_COLUMNS,
        )
    )
    population = MayoralIncumbencyPopulation(sources, trials)
    _validate_population(population)
    return population


def verify_mayoral_incumbency_artifacts(
    population: MayoralIncumbencyPopulation,
    project_root: str | Path,
) -> None:
    """Recheck optional local audit copies against tracked size and SHA-256."""

    root = Path(project_root).resolve()
    corpus_root = (root / "data/source_documents").resolve()
    for source in population.source_documents:
        if source.local_path is None:
            continue
        assert source.local_path is not None
        assert source.sha256 is not None
        assert source.byte_size is not None
        artifact = (root / source.local_path).resolve()
        if not artifact.is_relative_to(corpus_root):
            raise MayoralIncumbencyDataError(
                f"source {source.source_document_id!r} resolves outside source corpus"
            )
        if not artifact.is_file():
            raise MayoralIncumbencyDataError(
                f"source {source.source_document_id!r} artifact is missing"
            )
        if artifact.stat().st_size != source.byte_size:
            raise MayoralIncumbencyDataError(
                f"source {source.source_document_id!r} byte size mismatch"
            )
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != source.sha256:
            raise MayoralIncumbencyDataError(
                f"source {source.source_document_id!r} SHA-256 mismatch"
            )
        prefix = artifact.read_bytes()[:16].lstrip()
        if source.media_type == "application/pdf" and not prefix.startswith(b"%PDF-"):
            raise MayoralIncumbencyDataError(
                f"source {source.source_document_id!r} is not a PDF"
            )
        if source.media_type == "text/html" and not (
            prefix.lower().startswith(b"<!doctype html")
            or prefix.lower().startswith(b"<html")
        ):
            raise MayoralIncumbencyDataError(
                f"source {source.source_document_id!r} is not HTML"
            )
        if source.media_type == "application/vnd.ms-excel" and not prefix.startswith(
            bytes.fromhex("d0cf11e0a1b11ae1")
        ):
            raise MayoralIncumbencyDataError(
                f"source {source.source_document_id!r} is not an OLE Excel workbook"
            )


def _read_csv(
    path: Path,
    expected_columns: tuple[str, ...],
) -> list[tuple[int, dict[str, str]]]:
    if not path.is_file():
        raise MayoralIncumbencyDataError(f"missing comparison-population table: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_columns:
            raise MayoralIncumbencyDataError(
                f"{path.name} columns do not match the comparison-population contract"
            )
        return [(row_number, row) for row_number, row in enumerate(reader, start=2)]


def _parse_source(row: dict[str, str], row_number: int) -> IncumbencySourceDocument:
    source_id = _required(row, "source_document_id", row_number)
    status = _required(row, "verification_status", row_number)
    if status not in {
        "verified_artifact",
        "verified_official_dynamic_source",
        "corroborated_secondary",
        "source_gap",
    }:
        raise MayoralIncumbencyDataError(
            f"source row {row_number} has invalid verification_status"
        )
    media_type = _required(row, "media_type", row_number)
    if media_type not in {
        "application/pdf",
        "application/vnd.ms-excel",
        "text/html",
    }:
        raise MayoralIncumbencyDataError(
            f"source row {row_number} has unsupported media_type"
        )
    sha256 = row["sha256"].strip() or None
    local_path = Path(row["local_path"].strip()) if row["local_path"].strip() else None
    byte_size = _optional_positive_int(row["byte_size"], "byte_size", row_number)
    artifact_statuses = {"verified_artifact", "corroborated_secondary"}
    if status in artifact_statuses and (
        sha256 is None
        or _SHA256.fullmatch(sha256) is None
        or local_path is None
        or byte_size is None
    ):
        raise MayoralIncumbencyDataError(
            f"verified source {source_id!r} lacks complete artifact metadata"
        )
    if status not in artifact_statuses and any(
        value is not None for value in (sha256, local_path, byte_size)
    ):
        raise MayoralIncumbencyDataError(
            f"source {source_id!r} has partial artifact metadata"
        )
    return IncumbencySourceDocument(
        source_document_id=source_id,
        city_id=_required(row, "city_id", row_number),
        election_year=_positive_int(row["election_year"], "election_year", row_number),
        publisher_url=_required(row, "publisher_url", row_number),
        retrieval_url=_required(row, "retrieval_url", row_number),
        media_type=media_type,  # type: ignore[arg-type]
        sha256=sha256,
        local_path=local_path,
        byte_size=byte_size,
        verification_status=status,  # type: ignore[arg-type]
        notes=row["notes"].strip() or None,
    )


def _parse_trial(row: dict[str, str], row_number: int) -> MayoralIncumbencyTrial:
    group = _required(row, "population_group", row_number)
    if group not in {"v1_regular", "toronto_pre_2006_sensitivity"}:
        raise MayoralIncumbencyDataError(
            f"trial row {row_number} has invalid population_group"
        )
    try:
        election_date = date.fromisoformat(_required(row, "election_date", row_number))
    except ValueError as exc:
        raise MayoralIncumbencyDataError(
            f"trial row {row_number} has invalid election_date"
        ) from exc
    return MayoralIncumbencyTrial(
        trial_id=_required(row, "trial_id", row_number),
        city_id=_required(row, "city_id", row_number),
        city_name=_required(row, "city_name", row_number),
        election_date=election_date,
        population_group=group,  # type: ignore[arg-type]
        term_length_years=_positive_int(
            row["term_length_years"], "term_length_years", row_number
        ),
        incumbent_candidate_id=_required(row, "incumbent_candidate_id", row_number),
        incumbent_name=_required(row, "incumbent_name", row_number),
        incumbent_votes=_positive_int(
            row["incumbent_votes"], "incumbent_votes", row_number
        ),
        strongest_opponent_candidate_id=_required(
            row, "strongest_opponent_candidate_id", row_number
        ),
        strongest_opponent_name=_required(
            row, "strongest_opponent_name", row_number
        ),
        strongest_opponent_votes=_positive_int(
            row["strongest_opponent_votes"],
            "strongest_opponent_votes",
            row_number,
        ),
        valid_votes=_positive_int(row["valid_votes"], "valid_votes", row_number),
        final_candidate_count=_positive_int(
            row["final_candidate_count"], "final_candidate_count", row_number
        ),
        source_document_id=_required(row, "source_document_id", row_number),
        source_locator=_required(row, "source_locator", row_number),
        notes=row["notes"].strip() or None,
    )


def _validate_population(population: MayoralIncumbencyPopulation) -> None:
    source_ids = [source.source_document_id for source in population.source_documents]
    if len(source_ids) != len(set(source_ids)):
        raise MayoralIncumbencyDataError("duplicate comparison source_document_id")
    sources = {source.source_document_id: source for source in population.source_documents}

    trial_ids = [trial.trial_id for trial in population.trials]
    if len(trial_ids) != len(set(trial_ids)):
        raise MayoralIncumbencyDataError("duplicate comparison trial_id")
    city_years: set[tuple[str, int]] = set()
    for trial in population.trials:
        if trial.source_document_id not in sources:
            raise MayoralIncumbencyDataError(
                f"trial {trial.trial_id!r} references an unknown source"
            )
        source = sources[trial.source_document_id]
        if source.city_id != trial.city_id or source.election_year != trial.election_date.year:
            raise MayoralIncumbencyDataError(
                f"trial {trial.trial_id!r} does not match its source city/year"
            )
        if trial.final_candidate_count < 2:
            raise MayoralIncumbencyDataError(
                f"trial {trial.trial_id!r} has fewer than two Final candidates"
            )
        if trial.incumbent_candidate_id == trial.strongest_opponent_candidate_id:
            raise MayoralIncumbencyDataError(
                f"trial {trial.trial_id!r} repeats one candidate on both sides"
            )
        if trial.incumbent_votes + trial.strongest_opponent_votes > trial.valid_votes:
            raise MayoralIncumbencyDataError(
                f"trial {trial.trial_id!r} selected votes exceed valid votes"
            )
        city_year = (trial.city_id, trial.election_date.year)
        if city_year in city_years:
            raise MayoralIncumbencyDataError("duplicate city/election-year trial")
        city_years.add(city_year)

    v1_counts: dict[str, int] = {}
    for trial in population.v1_trials:
        v1_counts[trial.city_id] = v1_counts.get(trial.city_id, 0) + 1
        if not 2006 <= trial.election_date.year <= 2022:
            raise MayoralIncumbencyDataError(
                "v1 regular comparison trials must fall within 2006-2022"
            )
        if trial.term_length_years != 4:
            raise MayoralIncumbencyDataError(
                "v1 regular comparison trials require four-year terms"
            )
    if v1_counts != _EXPECTED_V1_CITY_COUNTS:
        raise MayoralIncumbencyDataError(
            "v1 comparison population does not match the frozen city/cycle counts"
        )

    sensitivity = population.toronto_2000_sensitivity_trial
    if (
        sensitivity.city_id != "toronto"
        or sensitivity.election_date.year != 2000
        or sensitivity.term_length_years != 3
    ):
        raise MayoralIncumbencyDataError(
            "pre-2006 sensitivity must be Toronto 2000 under a three-year term"
        )


def _median(values: tuple[Decimal, ...]) -> Decimal:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / Decimal(2)


def _required(row: dict[str, str], column: str, row_number: int) -> str:
    value = row[column].strip()
    if not value:
        raise MayoralIncumbencyDataError(
            f"row {row_number} has blank required {column}"
        )
    return value


def _positive_int(raw: str, column: str, row_number: int) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise MayoralIncumbencyDataError(
            f"row {row_number} has invalid integer {column}"
        ) from exc
    if value <= 0:
        raise MayoralIncumbencyDataError(
            f"row {row_number} requires positive {column}"
        )
    return value


def _optional_positive_int(raw: str, column: str, row_number: int) -> int | None:
    if not raw.strip():
        return None
    return _positive_int(raw, column, row_number)
