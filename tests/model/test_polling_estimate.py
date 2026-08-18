from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from pathlib import PurePosixPath
from zoneinfo import ZoneInfo

from backend.model.poll_sources import (
    PollReading,
    PollResponse,
    PollSample,
    PollSampleDocument,
    PollSourceBundle,
    SourceDocument,
)
from backend.model.polling_estimate import (
    BallotCandidate,
    calculate_mayoral_polling_estimate,
)


TORONTO = ZoneInfo("America/Toronto")


def _bundle(*polls: tuple[str, str, date, dict[str, str]]) -> PollSourceBundle:
    documents = []
    links = []
    samples = []
    readings = []
    responses = []
    for index, (sample_id, pollster, fieldwork_end, shares) in enumerate(polls, 1):
        document_id = f"document-{index}"
        reading_id = f"reading-{index}"
        documents.append(
            SourceDocument(
                source_document_id=document_id,
                document_role="tables",
                publisher_url=f"https://example.com/{document_id}",
                retrieval_url=None,
                retrieval_status="retrieved",
                retrieved_at=datetime(2026, 8, 1, tzinfo=TORONTO),
                media_type="application/pdf",
                sha256="0" * 64,
                local_path=PurePosixPath(f"data/source_documents/{document_id}.pdf"),
                byte_size=1,
                page_count=1,
                sheet_count=None,
                text_layer_status="present",
                visual_qa_status="passed",
                access_class="public",
                redistribution_status="unknown",
                reuse_terms_url=None,
                notes=None,
            )
        )
        links.append(PollSampleDocument(sample_id, document_id, None, None))
        samples.append(
            PollSample(
                poll_sample_id=sample_id,
                election_cycle_id="toronto-2026",
                pollster=pollster,
                sponsor=None,
                geography_type="citywide",
                geography_id="toronto",
                fieldwork_start=fieldwork_end,
                fieldwork_end=fieldwork_end,
                publication_date=fieldwork_end,
                publication_at=None,
                publication_time_precision="date_only",
                evidence_available_at=datetime.combine(
                    fieldwork_end, datetime.min.time(), TORONTO
                ),
                collection_mode="ivr",
                recruited_sample_size=1000,
                extraction_status="extracted",
                notes=None,
            )
        )
        readings.append(
            PollReading(
                poll_reading_id=reading_id,
                poll_sample_id=sample_id,
                source_document_id=document_id,
                source_locator="p. 1",
                contest_type="mayoral",
                contest_id="toronto-mayor-2026",
                question_order_status="not_reported",
                question_order=None,
                document_display_order=1,
                question_text_status="reported",
                question_text=(
                    "If the mayoral election were held today, who would you "
                    "vote for? Who are you leaning toward?"
                ),
                scenario_label="published field",
                population="Toronto residents",
                turnout_screen="not_reported",
                turnout_screen_text=None,
                denominator_type="custom",
                denominator_text="Decided and Leaning voters",
                unweighted_base_status="not_reported",
                unweighted_base=None,
                weighted_base_status="not_reported",
                weighted_base=None,
                reported_base_status="not_reported",
                reported_base=None,
                tested_choice_set_status="unknown",
                response_coverage="complete",
                reported_share_unit="percent",
                reported_share_precision=0,
                notes=None,
            )
        )
        for option_order, (candidate_id, share) in enumerate(shares.items(), 1):
            is_residual = candidate_id == "other"
            responses.append(
                PollResponse(
                    poll_reading_id=reading_id,
                    response_option_id=(
                        "other" if is_residual else f"candidate-{candidate_id}"
                    ),
                    response_kind="other" if is_residual else "candidate",
                    candidate_id=None if is_residual else candidate_id,
                    candidate_name=(
                        None if is_residual else candidate_id.replace("-", " ").title()
                    ),
                    candidate_observation_status=(
                        None if is_residual else "individually_published"
                    ),
                    response_label="Other" if is_residual else None,
                    option_order=option_order,
                    reported_value=f"{share}%",
                    share=Decimal(share) / 100,
                    notes=None,
                )
            )
    return PollSourceBundle(
        tuple(documents), tuple(links), tuple(samples), tuple(readings), tuple(responses)
    )


def test_two_pollsters_produce_an_equal_firm_polling_estimate() -> None:
    bundle = _bundle(
        (
            "forum-2026-07-29",
            "Forum Research",
            date(2026, 7, 29),
            {"chow": "47", "bradford": "32", "alexander": "11", "other": "10"},
        ),
        (
            "liaison-2026-08-05",
            "Liaison Strategies",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "alexander": "10", "other": "3"},
        ),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
            BallotCandidate("alexander", "Chris Alexander"),
        ),
        ballot_certified=True,
    )

    assert result.status == "available"
    assert [(row.candidate_id, row.share) for row in result.candidates] == [
        ("chow", Decimal("0.47")),
        ("bradford", Decimal("0.36")),
        ("alexander", Decimal("0.105")),
    ]
    assert result.poll_residual_share == Decimal("0.065")
    assert result.selected_poll_sample_ids == (
        "forum-2026-07-29",
        "liaison-2026-08-05",
    )


def test_a_politically_sponsored_poll_does_not_supply_replication() -> None:
    bundle = _bundle(
        (
            "independent",
            "Independent Pollster",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "campaign",
            "Campaign Pollster",
            date(2026, 8, 6),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
    )
    campaign_sample = replace(
        bundle.poll_samples[1], sponsor="Brad Bradford Campaign"
    )
    bundle = replace(
        bundle,
        poll_samples=(bundle.poll_samples[0], campaign_sample),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
        ),
        ballot_certified=True,
    )

    assert result.status == "unavailable"
    assert result.reason == "insufficient_replication"


def test_an_open_self_selected_poll_does_not_supply_replication() -> None:
    bundle = _bundle(
        (
            "probability-sample",
            "First Pollster",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "open-web-poll",
            "Second Pollster",
            date(2026, 8, 6),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
    )
    open_sample = replace(
        bundle.poll_samples[1], collection_mode="open self-selected web poll"
    )
    bundle = replace(
        bundle,
        poll_samples=(bundle.poll_samples[0], open_sample),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
        ),
        ballot_certified=True,
    )

    assert result.status == "unavailable"


def test_an_explicit_likely_voter_screen_is_not_mixed_with_unscreened_polling() -> None:
    bundle = _bundle(
        (
            "all-residents",
            "First Pollster",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "likely-voters",
            "Second Pollster",
            date(2026, 8, 6),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
    )
    likely_voter_reading = replace(
        bundle.poll_readings[1],
        turnout_screen="likely_voters",
        turnout_screen_text="Likely voters",
    )
    bundle = replace(
        bundle,
        poll_readings=(bundle.poll_readings[0], likely_voter_reading),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
        ),
        ballot_certified=True,
    )

    assert result.status == "unavailable"


def test_an_unchecked_source_document_does_not_supply_replication() -> None:
    bundle = _bundle(
        (
            "checked",
            "First Pollster",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "unchecked",
            "Second Pollster",
            date(2026, 8, 6),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
    )
    unchecked_document = replace(
        bundle.source_documents[1], visual_qa_status="pending"
    )
    bundle = replace(
        bundle,
        source_documents=(bundle.source_documents[0], unchecked_document),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
        ),
        ballot_certified=True,
    )

    assert result.status == "unavailable"


def test_a_poll_without_basic_sample_methodology_does_not_supply_replication() -> None:
    bundle = _bundle(
        (
            "documented",
            "First Pollster",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "undocumented",
            "Second Pollster",
            date(2026, 8, 6),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
    )
    undocumented = replace(
        bundle.poll_samples[1],
        recruited_sample_size=None,
        collection_mode="not-reported",
        notes=None,
    )
    bundle = replace(
        bundle,
        poll_samples=(bundle.poll_samples[0], undocumented),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
        ),
        ballot_certified=True,
    )

    assert result.status == "unavailable"


def test_a_consideration_question_is_not_vote_intention() -> None:
    bundle = _bundle(
        (
            "vote-intention",
            "First Pollster",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "consideration",
            "Second Pollster",
            date(2026, 8, 6),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
    )
    consideration_reading = replace(
        bundle.poll_readings[1],
        question_text="Which candidate would you most likely consider supporting?",
        reading_purpose="context_only",
    )
    bundle = replace(
        bundle,
        poll_readings=(bundle.poll_readings[0], consideration_reading),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
        ),
        ballot_certified=True,
    )

    assert result.status == "unavailable"


def test_two_samples_from_one_pollster_do_not_count_as_replication() -> None:
    bundle = _bundle(
        (
            "first",
            "Same Pollster",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "second",
            "Same Pollster",
            date(2026, 8, 6),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
        ),
        ballot_certified=True,
    )

    assert result.status == "unavailable"


def test_one_firm_expanded_field_withdraws_the_replicated_narrower_field() -> None:
    bundle = _bundle(
        (
            "narrow-one",
            "First Pollster",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "narrow-two",
            "Second Pollster",
            date(2026, 8, 6),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
        (
            "expanded",
            "Third Pollster",
            date(2026, 8, 7),
            {"chow": "43", "bradford": "38", "alexander": "9", "other": "10"},
        ),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
            BallotCandidate("alexander", "Chris Alexander"),
        ),
        ballot_certified=True,
    )

    assert result.status == "unavailable"
    assert result.reason == "expanded_field_awaiting_replication"


def test_twenty_one_day_old_evidence_qualifies_but_twenty_two_does_not() -> None:
    polls = (
        (
            "boundary",
            "Boundary Pollster",
            date(2026, 7, 27),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "recent",
            "Recent Pollster",
            date(2026, 8, 5),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
    )
    ballot = (
        BallotCandidate("chow", "Olivia Chow"),
        BallotCandidate("bradford", "Brad Bradford"),
    )

    at_boundary = calculate_mayoral_polling_estimate(
        _bundle(*polls),
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=ballot,
        ballot_certified=False,
    )
    after_boundary = calculate_mayoral_polling_estimate(
        _bundle(*polls),
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 18, 12, tzinfo=TORONTO),
        final_ballot=ballot,
        ballot_certified=False,
    )

    assert at_boundary.status == "preview"
    assert after_boundary.status == "unavailable"


def test_unmeasured_final_candidates_are_returned_without_a_zero_share() -> None:
    bundle = _bundle(
        (
            "first",
            "First Pollster",
            date(2026, 8, 5),
            {"chow": "47", "bradford": "40", "other": "13"},
        ),
        (
            "second",
            "Second Pollster",
            date(2026, 8, 6),
            {"chow": "45", "bradford": "42", "other": "13"},
        ),
    )

    result = calculate_mayoral_polling_estimate(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-mayor-2026",
        analysis_cutoff=datetime(2026, 8, 17, 12, tzinfo=TORONTO),
        final_ballot=(
            BallotCandidate("chow", "Olivia Chow"),
            BallotCandidate("bradford", "Brad Bradford"),
            BallotCandidate("alexander", "Chris Alexander"),
        ),
        ballot_certified=False,
    )

    assert [row.candidate_id for row in result.candidates] == ["chow", "bradford"]
    assert result.unmeasured_final_candidates == (
        BallotCandidate("alexander", "Chris Alexander"),
    )
