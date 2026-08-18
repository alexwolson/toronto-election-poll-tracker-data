from dataclasses import replace
from datetime import time, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from backend.model.historical_mayoral import load_historical_mayoral_corpus
from backend.model.historical_mayoral_evaluation import (
    HistoricalMayoralEvidence,
    build_historical_mayoral_evaluation_cycles,
)


ROOT = Path(__file__).resolve().parents[2]


def _cycles(*lead_times: int):
    return build_historical_mayoral_evaluation_cycles(
        load_historical_mayoral_corpus(ROOT),
        lead_times=lead_times,
        analysis_time_local=time(12, 30),
    )


def _by_id(cycles):
    return {cycle.election_cycle_id: cycle for cycle in cycles}


def _snapshot(cycle, days_before_election: int):
    return next(
        snapshot
        for snapshot in cycle.snapshots
        if snapshot.days_before_election == days_before_election
    )


def test_adapter_builds_complete_outcomes_and_source_backed_incumbents() -> None:
    cycles = _by_id(_cycles(30))

    assert {
        cycle_id: len(cycle.outcome.candidate_ids)
        for cycle_id, cycle in cycles.items()
    } == {
        "toronto_2014": 65,
        "toronto_2018": 35,
        "toronto_2022": 31,
        "toronto_2023": 102,
    }
    assert {
        cycle_id: cycle.outcome.incumbent_candidate_id
        for cycle_id, cycle in cycles.items()
    } == {
        "toronto_2014": None,
        "toronto_2018": "tory",
        "toronto_2022": "tory",
        "toronto_2023": None,
    }
    assert all(
        set(cycle.outcome.candidate_ids)
        == {
            candidate_id
            for candidate_id, _ in load_historical_mayoral_corpus(
                ROOT
            ).outcome_share_vector(cycle.election_cycle_id)
        }
        for cycle in cycles.values()
    )


def test_cutoffs_use_caller_supplied_toronto_wall_clock_time() -> None:
    cycle = _by_id(_cycles(30))["toronto_2018"]
    cutoff = cycle.snapshots[0].analysis_cutoff

    assert cutoff.isoformat() == "2018-09-22T12:30:00-04:00"
    assert cutoff.utcoffset() is not None

    with pytest.raises(ValueError, match="naive Toronto wall-clock"):
        build_historical_mayoral_evaluation_cycles(
            load_historical_mayoral_corpus(ROOT),
            lead_times=(30,),
            analysis_time_local=time(12, tzinfo=timezone.utc),
        )


def test_cutoff_filters_samples_and_keeps_every_dependent_reading() -> None:
    toronto_2014 = _by_id(_cycles(34, 33))["toronto_2014"]
    before_nanos = _snapshot(toronto_2014, 34).evidence
    after_nanos = _snapshot(toronto_2014, 33).evidence

    assert isinstance(before_nanos, HistoricalMayoralEvidence)
    before_nanos_sample_ids = {
        sample.poll_sample_id for sample in before_nanos.poll_samples
    }
    after_nanos_sample_ids = {
        sample.poll_sample_id for sample in after_nanos.poll_samples
    }
    assert "nanos_city_2014_09_16_20_n1000" not in before_nanos_sample_ids
    assert after_nanos_sample_ids - before_nanos_sample_ids == {
        "nanos_city_2014_09_16_20_n1000"
    }
    assert {
        reading.poll_reading_id for reading in after_nanos.poll_readings
    } - {
        reading.poll_reading_id for reading in before_nanos.poll_readings
    } == {"nanos_sep_all", "nanos_sep_decided"}

    toronto_2023 = _by_id(_cycles(3, 2))["toronto_2023"]
    before_june = _snapshot(toronto_2023, 3).evidence
    after_june = _snapshot(toronto_2023, 2).evidence
    before_june_sample_ids = {
        sample.poll_sample_id for sample in before_june.poll_samples
    }
    after_june_sample_ids = {
        sample.poll_sample_id for sample in after_june.poll_samples
    }
    assert after_june_sample_ids - before_june_sample_ids == {
        "viewpoints_city_2023_06_15_19_n1007",
    }
    assert {
        reading.poll_reading_id for reading in after_june.poll_readings
    } - {
        reading.poll_reading_id for reading in before_june.poll_readings
    } == {
        "viewpoints_jun19_raw",
        "viewpoints_jun19_leaning",
    }
    reading_ids = {
        reading.poll_reading_id for reading in after_june.poll_readings
    }
    assert after_june.poll_responses
    assert all(
        response.poll_reading_id in reading_ids
        for response in after_june.poll_responses
    )


def test_one_sample_with_two_readings_remains_one_sample() -> None:
    evidence = _snapshot(
        _by_id(_cycles(33))["toronto_2014"],
        33,
    ).evidence

    assert isinstance(evidence, HistoricalMayoralEvidence)
    assert [
        sample.poll_sample_id
        for sample in evidence.poll_samples
        if sample.poll_sample_id == "nanos_city_2014_09_16_20_n1000"
    ] == [
        "nanos_city_2014_09_16_20_n1000"
    ]
    assert {
        reading.poll_reading_id
        for reading in evidence.poll_readings
        if reading.poll_sample_id == "nanos_city_2014_09_16_20_n1000"
    } == {
        "nanos_sep_all",
        "nanos_sep_decided",
    }
    assert {
        reading.poll_sample_id for reading in evidence.poll_readings
        if reading.poll_reading_id in {"nanos_sep_all", "nanos_sep_decided"}
    } == {"nanos_city_2014_09_16_20_n1000"}


def test_snapshot_exposes_the_cutoff_faithful_final_ballot_boundary() -> None:
    cycles = _by_id(_cycles(30))

    assert (
        cycles["toronto_2014"].snapshots[0]
        .evidence.final_ballot_evidence_available_at.isoformat()
        == "2014-09-16T00:00:00-04:00"
    )
    assert (
        cycles["toronto_2023"].snapshots[0]
        .evidence.final_ballot_evidence_available_at.isoformat()
        == "2023-05-13T00:00:00-04:00"
    )


def test_evidence_snapshots_admit_the_audited_2022_poll_at_its_cutoff() -> None:
    cycles = _by_id(_cycles(40, 10))

    early = _snapshot(cycles["toronto_2022"], 40)
    late = _snapshot(cycles["toronto_2022"], 10)
    assert isinstance(early.evidence, HistoricalMayoralEvidence)
    assert early.evidence.poll_samples == ()
    assert early.evidence.poll_readings == ()
    assert early.evidence.poll_responses == ()
    assert {sample.poll_sample_id for sample in late.evidence.poll_samples} == {
        "forum_city_2022_10_07_08_n1017"
    }
    assert {reading.poll_reading_id for reading in late.evidence.poll_readings} == {
        "forum_2022_oct08_decided_leaning"
    }
    assert early.evidence_revision.startswith("sha256:")
    assert early.evidence_revision != late.evidence_revision

    assert all(
        snapshot.evidence.poll_samples
        for snapshot in cycles["toronto_2018"].snapshots
    )


def test_responses_without_reported_option_order_remain_replayable() -> None:
    evidence = _snapshot(_by_id(_cycles(0))["toronto_2018"], 0).evidence

    dart_responses = tuple(
        response
        for response in evidence.poll_responses
        if response.poll_reading_id == "dart_2018_head_to_head"
    )
    assert {response.response_option_id for response in dart_responses} == {
        "candidate-keesmaat",
        "candidate-tory",
    }
    assert all(response.option_order is None for response in dart_responses)


def test_evidence_revisions_are_stable_and_change_only_with_visible_evidence() -> None:
    first = _by_id(_cycles(40, 3, 2))["toronto_2023"]
    second = _by_id(_cycles(40, 3, 2))["toronto_2023"]

    assert [row.evidence_revision for row in first.snapshots] == [
        row.evidence_revision for row in second.snapshots
    ]
    assert _snapshot(first, 40).evidence_revision != _snapshot(
        first, 3
    ).evidence_revision
    assert _snapshot(first, 3).evidence_revision != _snapshot(
        first, 2
    ).evidence_revision

    corpus = load_historical_mayoral_corpus(ROOT)
    reordered = replace(
        corpus,
        poll_samples=tuple(reversed(corpus.poll_samples)),
        poll_readings=tuple(reversed(corpus.poll_readings)),
        poll_responses=tuple(reversed(corpus.poll_responses)),
    )
    reordered_cycle = _by_id(
        build_historical_mayoral_evaluation_cycles(
            reordered,
            lead_times=(2,),
            analysis_time_local=time(12, 30),
        )
    )["toronto_2023"]
    assert reordered_cycle.snapshots[0].evidence_revision == _snapshot(
        first, 2
    ).evidence_revision


def test_pre_final_cutoff_fails_closed_at_next_midnight_boundary() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)

    # Forty-two days before the 2014 election is September 15. The source
    # records only that date, so the Final Ballot becomes usable next midnight.
    with pytest.raises(ValueError, match="precedes.*Final Ballot"):
        build_historical_mayoral_evaluation_cycles(
            corpus,
            lead_times=(42,),
            analysis_time_local=time(23, 59),
        )

    cycles = _by_id(
        build_historical_mayoral_evaluation_cycles(
            corpus,
            lead_times=(41,),
            analysis_time_local=time(0),
        )
    )
    assert (
        cycles["toronto_2014"].snapshots[0].analysis_cutoff.isoformat()
        == "2014-09-16T00:00:00-04:00"
    )


def test_outcomes_do_not_leak_into_snapshot_evidence_or_its_revision() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    original = _by_id(
        build_historical_mayoral_evaluation_cycles(
            corpus,
            lead_times=(30,),
            analysis_time_local=time(9),
        )
    )["toronto_2018"]
    changed_outcomes = tuple(
        replace(row, share=row.share + Decimal("0.001"))
        if row.election_cycle_id == "toronto_2018" and row.candidate_id == "tory"
        else replace(row, share=row.share - Decimal("0.001"))
        if row.election_cycle_id == "toronto_2018"
        and row.candidate_id == "keesmaat"
        else row
        for row in corpus.outcomes
    )
    changed = _by_id(
        build_historical_mayoral_evaluation_cycles(
            replace(corpus, outcomes=changed_outcomes),
            lead_times=(30,),
            analysis_time_local=time(9),
        )
    )["toronto_2018"]

    assert not hasattr(original.snapshots[0].evidence, "outcome")
    assert original.outcome.candidate_shares != changed.outcome.candidate_shares
    assert (
        original.snapshots[0].evidence_revision
        == changed.snapshots[0].evidence_revision
    )


def test_adapter_rejects_unknown_cycles_and_broken_poll_lineage() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    unknown_election = replace(
        corpus.elections[0],
        election_cycle_id="toronto_2099",
    )
    with pytest.raises(ValueError, match="unknown historical mayoral cycle"):
        build_historical_mayoral_evaluation_cycles(
            replace(corpus, elections=(unknown_election,) + corpus.elections[1:]),
            lead_times=(30,),
            analysis_time_local=time(12),
        )

    unknown_cycle_sample = replace(
        corpus.poll_samples[0],
        election_cycle_id="toronto_2099",
    )
    with pytest.raises(ValueError, match="references unknown cycle"):
        build_historical_mayoral_evaluation_cycles(
            replace(
                corpus,
                poll_samples=(unknown_cycle_sample,) + corpus.poll_samples[1:],
            ),
            lead_times=(30,),
            analysis_time_local=time(12),
        )

    orphan_reading = replace(
        corpus.poll_readings[0],
        poll_sample_id="missing-sample",
    )
    with pytest.raises(ValueError, match="references unknown sample"):
        build_historical_mayoral_evaluation_cycles(
            replace(
                corpus,
                poll_readings=(orphan_reading,) + corpus.poll_readings[1:],
            ),
            lead_times=(30,),
            analysis_time_local=time(12),
        )

    orphan_response = replace(
        corpus.poll_responses[0],
        poll_reading_id="missing-reading",
    )
    with pytest.raises(ValueError, match="references unknown reading"):
        build_historical_mayoral_evaluation_cycles(
            replace(
                corpus,
                poll_responses=(orphan_response,) + corpus.poll_responses[1:],
            ),
            lead_times=(30,),
            analysis_time_local=time(12),
        )


def test_adapter_validates_source_backed_incumbent_against_final_ballot() -> None:
    corpus = load_historical_mayoral_corpus(ROOT)
    outcomes = tuple(
        replace(row, candidate_id="renamed-tory")
        if row.election_cycle_id == "toronto_2018" and row.candidate_id == "tory"
        else row
        for row in corpus.outcomes
    )

    with pytest.raises(ValueError, match="source-backed incumbent.*absent"):
        build_historical_mayoral_evaluation_cycles(
            replace(corpus, outcomes=outcomes),
            lead_times=(30,),
            analysis_time_local=time(12),
        )
