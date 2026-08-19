"""The canonical historical seam must not bless legacy discovery tables."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from backend.model.historical_mayoral import (
    audit_historical_mayoral_corpus,
    build_legacy_crosswalk_rows,
    build_mayoral_election_rows,
    build_mayoral_outcome_rows,
    load_historical_mayoral_corpus,
)

ROOT = Path(__file__).resolve().parents[2]


def _rows(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_committed_tables_equal_a_fresh_source_reconstruction() -> None:
    assert _rows("data/raw/elections/mayoral_elections.csv") == (
        build_mayoral_election_rows()
    )
    assert _rows("data/raw/elections/mayoral_outcomes.csv") == (
        build_mayoral_outcome_rows(
            ROOT / "data/raw/elections/mayoral_results_2014_official.csv",
            ROOT / "data/raw/elections/mayoral_results.csv",
        )
    )
    assert _rows("data/raw/polls/legacy_historical_poll_crosswalk.csv") == (
        build_legacy_crosswalk_rows(
            ROOT / "data/raw/polls/historical_mayoral_polls.csv"
        )
    )


def test_outcomes_are_complete_candidate_level_official_results() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    expected = {
        "toronto_2014": (65, 981_054, "John Tory"),
        "toronto_2018": (35, 755_493, "John Tory"),
        "toronto_2022": (31, 551_890, "John Tory"),
        "toronto_2023": (102, 724_638, "Olivia Chow"),
    }

    for cycle, (candidate_count, valid_votes, winner_name) in expected.items():
        outcome = corpus.outcome_universe(cycle)
        vector = corpus.outcome_share_vector(cycle)
        assert len(outcome) == candidate_count
        assert sum(row.votes for row in outcome) == valid_votes
        assert {row.valid_vote_total for row in outcome} == {valid_votes}
        assert [row.candidate_name for row in outcome if row.is_winner] == [winner_name]
        assert tuple(row.candidate_id for row in outcome) == tuple(
            candidate_id for candidate_id, _ in vector
        )
        assert abs(sum((share for _, share in vector), Decimal()) - 1) <= Decimal(
            "0.00000000000000001"
        )
        assert "residual" not in {row.candidate_id for row in outcome}

    assert (
        next(
            row
            for row in corpus.outcome_universe("toronto_2014")
            if row.candidate_name == "Doug Ford"
        ).candidate_id
        == "doug-ford"
    )
    assert (
        next(
            row
            for row in corpus.outcome_universe("toronto_2018")
            if row.candidate_id == "tory"
        ).candidate_name_as_reported
        == "Tory John"
    )
    assert (
        next(
            row
            for row in corpus.outcome_universe("toronto_2023")
            if row.candidate_id == "chow"
        ).candidate_name_as_reported
        == "Chow Olivia"
    )
    assert all("_" not in row.candidate_id.split(":", 1)[-1] for row in corpus.outcomes)


def test_2014_sidecar_preserves_the_verified_declaration_provenance() -> None:
    rows = _rows("data/raw/elections/mayoral_results_2014_official.csv")
    assert len(rows) == 65
    assert sum(int(row["votes"]) for row in rows) == 981_054
    assert [row["candidate_name"] for row in rows if row["is_winner"] == "true"] == [
        "John Tory"
    ]
    assert {row["source_locator"] for row in rows} == {
        "PDF pages 2-3 (printed pages 1-2)"
    }
    assert {row["source_sha256"] for row in rows} == {
        "007f5055da03ce1df17cb85c6c1871a1de822c55966e4518f845905fa4b12158"
    }


def test_final_ballot_known_by_dates_are_conservative_replay_boundaries() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    elections = {row.election_cycle_id: row for row in corpus.elections}

    assert elections["toronto_2014"].nomination_close_date == date(2014, 9, 12)
    assert elections["toronto_2014"].final_ballot_known_by_date == date(2014, 9, 15)
    assert (
        elections["toronto_2014"].final_ballot_known_by_status == "statutory_deadline"
    )
    assert elections["toronto_2014"].final_ballot_evidence_available_at == (
        datetime.fromisoformat("2014-09-16T00:00:00-04:00")
    )
    assert elections["toronto_2018"].final_ballot_known_by_date == date(2018, 7, 30)
    assert (
        elections["toronto_2018"].final_ballot_known_by_status
        == "certification_date_reported"
    )
    assert elections["toronto_2022"].final_ballot_known_by_date == date(2022, 8, 20)
    assert (
        elections["toronto_2022"].final_ballot_known_by_status == "publicly_announced"
    )
    assert elections["toronto_2022"].final_ballot_evidence_available_at == (
        datetime.fromisoformat("2022-08-21T00:00:00-04:00")
    )
    assert elections["toronto_2022"].notes is not None
    assert "publicly known by August 20" in elections["toronto_2022"].notes
    assert elections["toronto_2023"].final_ballot_known_by_date == date(2023, 5, 12)

    nanos = next(
        sample
        for sample in corpus.poll_samples
        if sample.poll_sample_id == "nanos_city_2014_09_16_20_n1000"
    )
    assert nanos.fieldwork_start > elections["toronto_2014"].final_ballot_known_by_date


def test_only_audited_poll_sources_enter_the_canonical_seam() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)

    assert len(corpus.poll_samples) == 83
    assert len(corpus.poll_readings) == 202
    assert len(corpus.poll_responses) == 1214
    assert len(corpus.source_documents) == 104
    assert len(corpus.poll_sample_documents) == 106
    assert all(
        sample.extraction_status == "extracted" for sample in corpus.poll_samples
    )
    assert all(
        document.retrieval_status == "retrieved"
        and document.visual_qa_status in {"passed", "not_applicable"}
        for document in corpus.source_documents
    )
    assert {"dont_know", "refusal", "would_not_vote"} <= {
        response.response_kind for response in corpus.poll_responses
    }
    purposes = {
        reading.poll_reading_id: reading.reading_purpose
        for reading in corpus.poll_readings
    }
    assert sum(value == "general_vote_intention" for value in purposes.values()) == 199
    assert purposes["nanos_jul_initially_unsure_leaning"] == (
        "conditional_lean_followup"
    )
    assert purposes["ipsos_2023_conditional_lean"] == "conditional_lean_followup"
    assert purposes["mainstreet_2023_apr13_no_chow"] == "routed_subgroup"

    nanos = corpus.readings_for_sample("nanos_city_2014_09_16_20_n1000")
    nanos_sample = next(
        sample
        for sample in corpus.poll_samples
        if sample.poll_sample_id == "nanos_city_2014_09_16_20_n1000"
    )
    assert nanos_sample.publication_date == date(2014, 9, 23)
    assert nanos_sample.evidence_available_at == datetime.fromisoformat(
        "2014-09-24T00:00:00-04:00"
    )
    nanos_document_ids = {
        link.source_document_id
        for link in corpus.poll_sample_documents
        if link.poll_sample_id == nanos_sample.poll_sample_id
    }
    assert nanos_document_ids == {
        "nanos_2014-09_full",
        "nanos_reports_archive_2021-07-30",
    }
    timing_document = next(
        document
        for document in corpus.source_documents
        if document.source_document_id == "nanos_reports_archive_2021-07-30"
    )
    assert timing_document.publisher_url == "https://nanos.co/reports-2/"
    assert timing_document.sha256 == (
        "5f16a5a93a1707bfc66c9e33af04806ec6897ccb505ef978eb075f7c346e36ea"
    )
    assert {reading.poll_reading_id for reading in nanos} == {
        "nanos_sep_all",
        "nanos_sep_decided",
    }
    assert {
        tuple(
            response.candidate_id
            for response in corpus.responses_for_reading(reading.poll_reading_id)
            if response.candidate_id is not None
        )
        for reading in nanos
    } == {
        ("chow", "doug-ford", "tory"),
    }


def test_viewpoints_may_sample_keeps_timing_conflict_and_reported_rounding() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    sample = next(
        row
        for row in corpus.poll_samples
        if row.poll_sample_id == "viewpoints_city_2023_04_29_05_02_n400"
    )

    assert sample.sponsor == "Broadbent Institute"
    assert sample.fieldwork_start == date(2023, 4, 29)
    assert sample.fieldwork_end == date(2023, 5, 2)
    assert sample.publication_date == date(2023, 5, 4)
    assert sample.evidence_available_at == datetime.fromisoformat(
        "2023-05-05T00:00:00-04:00"
    )
    article = next(
        document
        for document in corpus.source_documents
        if document.source_document_id == "viewpoints_2023-05-02_article"
    )
    assert "viewpoints.ca/2023/05/" in article.publisher_url
    assert article.sha256 == (
        "d1d48fdb5c7230923eb21735ba68d75eea57fa60bc8fd1346f703cd333d13312"
    )
    assert sample.notes is not None and "header says May 3" in sample.notes

    raw = corpus.responses_for_reading("viewpoints_may2_raw")
    decided = corpus.responses_for_reading("viewpoints_may2_decided")
    assert all(row.share is not None for row in raw + decided)
    assert sum((row.share or Decimal() for row in raw), Decimal()) == Decimal("1.002")
    assert sum((row.share or Decimal() for row in decided), Decimal()) == Decimal(
        "1.01"
    )
    assert "furey" not in {row.candidate_id for row in raw}
    assert "Not sure" in {row.response_label for row in raw}


def test_forum_and_liaison_waves_preserve_source_semantics() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)

    forum = corpus.readings_for_sample("forum_city_2023_05_26_n1007")
    assert {reading.poll_reading_id for reading in forum} == {
        "forum_2023_may26_all",
        "forum_2023_may26_decided_leaning",
    }
    decided = corpus.responses_for_reading("forum_2023_may26_decided_leaning")
    assert (
        sum(
            response.candidate_observation_status
            == "offered_not_individually_published"
            for response in decided
        )
        == 5
    )
    perruzza = next(
        response
        for response in corpus.responses_for_reading("forum_2023_may26_all")
        if response.candidate_id == "toronto_2023:perruzza-anthony"
    )
    assert perruzza.response_label == "Anthony Perruza"
    assert perruzza.candidate_name == "Anthony Perruzza"

    liaison_sample = next(
        sample
        for sample in corpus.poll_samples
        if sample.poll_sample_id == "liaison_city_2023_05_12_13_n1318"
    )
    assert liaison_sample.recruited_sample_size == 1318
    assert {
        link.source_document_id
        for link in corpus.poll_sample_documents
        if link.poll_sample_id == liaison_sample.poll_sample_id
    } == {
        "liaison_2023_05_12_13_release",
        "liaison_2023_05_12_13_tables",
    }
    liaison_decided = corpus.responses_for_reading("liaison_2023_06_22_23_decided")
    assert [response.option_order for response in liaison_decided] == list(range(1, 10))
    bailao = next(
        response for response in liaison_decided if response.candidate_id == "bailao"
    )
    assert bailao.share == Decimal("0.17")


def test_recovered_forum_and_mainstreet_boundaries_are_cutoff_faithful() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)

    forum_sep22 = next(
        sample
        for sample in corpus.poll_samples
        if sample.poll_sample_id == "forum_city_2014_09_22_n1164"
    )
    assert forum_sep22.evidence_available_at == datetime.fromisoformat(
        "2014-09-30T00:00:00-04:00"
    )
    assert {
        reading.poll_reading_id
        for reading in corpus.readings_for_sample(forum_sep22.poll_sample_id)
    } >= {
        "forum_2014_sep22_current_field_trend",
        "forum_2014_sep22_two_way_tory_doug",
    }

    mainstreet_feb = next(
        sample
        for sample in corpus.poll_samples
        if sample.poll_sample_id == "mainstreet_city_2023_02_13_14_n1947"
    )
    assert mainstreet_feb.evidence_available_at == datetime.fromisoformat(
        "2023-02-17T17:45:19.612-05:00"
    )
    mapping = next(
        row
        for row in corpus.legacy_crosswalk
        if row.legacy_poll_id == "toronto_2023-2023-02-14-f879a53a"
    )
    assert mapping.disposition == "mapped"
    assert mapping.poll_reading_id == "mainstreet_2023_feb14_all"


def test_legacy_discovery_data_stays_explicitly_unresolved() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    dispositions = Counter(row.disposition for row in corpus.legacy_crosswalk)

    assert dispositions == {"unresolved": 50, "mapped": 102, "non_poll": 1}
    false_poll = next(
        row
        for row in corpus.legacy_crosswalk
        if row.legacy_poll_id == "toronto_2014-2010-10-25-6a933a5f"
    )
    assert false_poll.disposition == "non_poll"
    assert false_poll.poll_sample_id is None
    legacy_outcomes = _rows("data/raw/polls/historical_mayoral_outcomes.csv")
    assert len(legacy_outcomes) == 21
    assert all("wikipedia.org" in row["source_url"] for row in legacy_outcomes)
    assert {row["election_id"] for row in legacy_outcomes if row["is_residual"]} == {
        "toronto_2014",
        "toronto_2018",
        "toronto_2022",
        "toronto_2023",
    }


def test_legacy_sample_token_is_not_promoted_to_a_recruited_sample_size() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    june_two = next(
        row
        for row in corpus.legacy_crosswalk
        if row.legacy_poll_id == "toronto_2023-2023-06-02-85a96bf1"
    )

    assert june_two.disposition == "mapped"
    assert june_two.legacy_sample_proxy_key.endswith("|7800.0")
    canonical_sample = next(
        sample
        for sample in corpus.poll_samples
        if sample.poll_sample_id == june_two.poll_sample_id
    )
    assert canonical_sample.recruited_sample_size == 1004


def test_audit_counts_inventory_without_calling_it_calibration_ready() -> None:
    audit = audit_historical_mayoral_corpus(load_historical_mayoral_corpus(ROOT))

    assert audit.election_count == 4
    assert audit.outcome_candidate_count == 233
    assert audit.source_verified_sample_count == 83
    assert audit.source_verified_reading_count == 202
    assert audit.legacy_poll_id_count == 153
    assert audit.historical_sample_inventory_count == 112
    assert audit.unresolved_sample_proxy_count == 29
    assert audit.blocker_codes == ("unresolved_legacy_poll_samples",)
