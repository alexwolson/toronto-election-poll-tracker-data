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
from backend.model.polling_estimate import BallotCandidate
from backend.model.ward_polling import calculate_ward_polling


TORONTO = ZoneInfo("America/Toronto")
CUTOFF = datetime(2026, 8, 17, 12, tzinfo=TORONTO)
BALLOT_AB = (
    BallotCandidate("candidate-a", "Candidate A"),
    BallotCandidate("candidate-b", "Candidate B"),
)


def _bundle(*specs: dict[str, object]) -> PollSourceBundle:
    documents: dict[str, SourceDocument] = {}
    links: dict[str, PollSampleDocument] = {}
    samples: dict[str, PollSample] = {}
    readings = []
    responses = []
    for index, spec in enumerate(specs, 1):
        sample_id = str(spec["sample_id"])
        pollster = str(spec["pollster"])
        fieldwork_end = spec["fieldwork_end"]
        assert isinstance(fieldwork_end, date)
        document_id = f"document-{sample_id}"
        if sample_id not in samples:
            documents[document_id] = SourceDocument(
                source_document_id=document_id,
                document_role="tables",
                publisher_url=f"https://example.com/{document_id}",
                retrieval_url=None,
                retrieval_status="retrieved",
                retrieved_at=datetime(2026, 8, 1, tzinfo=TORONTO),
                media_type="application/pdf",
                sha256="0" * 64,
                local_path=PurePosixPath(
                    f"data/source_documents/{document_id}.pdf"
                ),
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
            links[sample_id] = PollSampleDocument(
                sample_id, document_id, None, None
            )
            samples[sample_id] = PollSample(
                poll_sample_id=sample_id,
                election_cycle_id="toronto-2026",
                pollster=pollster,
                sponsor=None,
                geography_type="ward",
                geography_id="toronto-ward-11",
                fieldwork_start=fieldwork_end,
                fieldwork_end=fieldwork_end,
                publication_date=fieldwork_end,
                publication_at=None,
                publication_time_precision="date_only",
                evidence_available_at=datetime.combine(
                    fieldwork_end, datetime.min.time(), TORONTO
                ),
                collection_mode="ivr",
                recruited_sample_size=400,
                extraction_status="extracted",
                notes=None,
            )

        reading_id = str(spec.get("reading_id", f"reading-{index}"))
        readings.append(
            PollReading(
                poll_reading_id=reading_id,
                poll_sample_id=sample_id,
                source_document_id=document_id,
                source_locator="p. 1",
                contest_type="council",
                contest_id="toronto-ward-11-2026",
                question_order_status="not_reported",
                question_order=None,
                document_display_order=index,
                question_text_status="reported",
                question_text=str(
                    spec.get(
                        "question_text",
                        "Who would you vote for? Who are you leaning toward?",
                    )
                ),
                scenario_label=str(spec.get("scenario_label", "published field")),
                population=str(spec.get("population", "Ward residents age 18+")),
                turnout_screen=str(spec.get("turnout_screen", "not_reported")),
                turnout_screen_text=None,
                denominator_type=str(spec.get("denominator_type", "custom")),
                denominator_text=(
                    None
                    if spec.get("denominator_text", "Decided and Leaning") is None
                    else str(spec.get("denominator_text", "Decided and Leaning"))
                ),
                unweighted_base_status="reported",
                unweighted_base=300,
                weighted_base_status="not_reported",
                weighted_base=None,
                reported_base_status="not_reported",
                reported_base=None,
                tested_choice_set_status="unknown",
                response_coverage=str(spec.get("response_coverage", "complete")),
                reported_share_unit="percent",
                reported_share_precision=0,
                notes=None,
                reading_purpose=str(
                    spec.get("reading_purpose", "general_vote_intention")
                ),
            )
        )
        shares = spec["shares"]
        assert isinstance(shares, dict)
        for option_order, (candidate_id, value) in enumerate(shares.items(), 1):
            is_residual = candidate_id == "other"
            responses.append(
                PollResponse(
                    poll_reading_id=reading_id,
                    response_option_id=(
                        "other" if is_residual else f"candidate-{candidate_id}"
                    ),
                    response_kind="other" if is_residual else "candidate",
                    candidate_id=None if is_residual else str(candidate_id),
                    candidate_name=(
                        None
                        if is_residual
                        else str(candidate_id).replace("-", " ").title()
                    ),
                    candidate_observation_status=(
                        None if is_residual else "individually_published"
                    ),
                    response_label="Other" if is_residual else None,
                    option_order=option_order,
                    reported_value=str(value),
                    share=Decimal(str(value)),
                    notes=None,
                )
            )

    return PollSourceBundle(
        tuple(documents.values()),
        tuple(links.values()),
        tuple(samples.values()),
        tuple(readings),
        tuple(responses),
    )


def _calculate(
    bundle: PollSourceBundle,
    *,
    ballot: tuple[BallotCandidate, ...] = BALLOT_AB,
    certified: bool = True,
):
    return calculate_ward_polling(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-ward-11-2026",
        analysis_cutoff=CUTOFF,
        final_ballot=ballot,
        ballot_certified=certified,
    )


def test_a_ward_without_polling_is_c0() -> None:
    result = _calculate(_bundle())

    assert result.evidence_tier == "C0"
    assert result.readings == ()
    assert result.estimate.status == "unavailable"


def test_context_only_reading_does_not_create_a_ward_evidence_tier() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "consideration",
                "pollster": "Example Pollster",
                "fieldwork_end": date(2026, 8, 12),
                "reading_purpose": "context_only",
                "shares": {"candidate-a": "0.6", "candidate-b": "0.4"},
            }
        )
    )

    assert result.evidence_tier == "C0"
    assert result.readings == ()


def test_a_stale_single_poll_remains_visible_as_c1() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "june",
                "pollster": "Forum Research",
                "fieldwork_end": date(2026, 6, 23),
                "shares": {
                    "candidate-a": "0.41",
                    "candidate-b": "0.22",
                    "other": "0.37",
                },
            }
        )
    )

    assert result.evidence_tier == "C1"
    assert len(result.readings) == 1
    assert result.readings[0].is_stale is True
    assert result.estimate.status == "unavailable"


def test_same_firm_waves_remain_c1_and_are_not_averaged() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "first",
                "pollster": "Forum Research",
                "fieldwork_end": date(2026, 8, 10),
                "shares": {"candidate-a": "0.50", "candidate-b": "0.50"},
            },
            {
                "sample_id": "second",
                "pollster": "Forum Research",
                "fieldwork_end": date(2026, 8, 12),
                "shares": {"candidate-a": "0.45", "candidate-b": "0.55"},
            },
        )
    )

    assert result.evidence_tier == "C1"
    assert [reading.sample.poll_sample_id for reading in result.readings] == [
        "first",
        "second",
    ]
    assert [reading.is_latest_for_pollster for reading in result.readings] == [
        False,
        True,
    ]
    assert result.estimate.status == "unavailable"


def test_two_pollsters_use_latest_equal_firm_shares_and_optional_residual() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "first-old",
                "pollster": "First Pollster",
                "fieldwork_end": date(2026, 8, 1),
                "shares": {
                    "candidate-a": "0.40",
                    "candidate-b": "0.30",
                    "other": "0.30",
                },
            },
            {
                "sample_id": "first-new",
                "pollster": "First Pollster",
                "fieldwork_end": date(2026, 8, 10),
                "shares": {
                    "candidate-a": "0.50",
                    "candidate-b": "0.30",
                    "other": "0.20",
                },
            },
            {
                "sample_id": "second",
                "pollster": "Second Pollster",
                "fieldwork_end": date(2026, 8, 11),
                "shares": {"candidate-a": "0.40", "candidate-b": "0.35"},
                "turnout_screen": "likely_voters",
                "denominator_type": "decided_respondents",
                "denominator_text": "Decided voters",
            },
        ),
        ballot=(*BALLOT_AB, BallotCandidate("candidate-c", "Candidate C")),
    )

    assert result.evidence_tier == "C2"
    assert result.estimate.status == "available"
    assert [(row.candidate_id, row.share) for row in result.estimate.candidates] == [
        ("candidate-a", Decimal("0.45")),
        ("candidate-b", Decimal("0.325")),
    ]
    assert result.estimate.poll_residual_share is None
    assert result.estimate.selected_poll_sample_ids == ("first-new", "second")
    assert result.estimate.unmeasured_final_candidates == (
        BallotCandidate("candidate-c", "Candidate C"),
    )


def test_c2_can_have_no_estimate_when_fields_differ() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "narrow",
                "pollster": "First Pollster",
                "fieldwork_end": date(2026, 8, 10),
                "shares": {"candidate-a": "0.55", "candidate-b": "0.45"},
            },
            {
                "sample_id": "expanded",
                "pollster": "Second Pollster",
                "fieldwork_end": date(2026, 8, 11),
                "shares": {
                    "candidate-a": "0.45",
                    "candidate-b": "0.35",
                    "candidate-c": "0.20",
                },
            },
        ),
        ballot=(*BALLOT_AB, BallotCandidate("candidate-c", "Candidate C")),
    )

    assert result.evidence_tier == "C2"
    assert result.estimate.status == "unavailable"


def test_fresh_unreplicated_expansion_withdraws_a_narrower_estimate() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "narrow-one",
                "pollster": "First Pollster",
                "fieldwork_end": date(2026, 8, 9),
                "shares": {"candidate-a": "0.55", "candidate-b": "0.45"},
            },
            {
                "sample_id": "narrow-two",
                "pollster": "Second Pollster",
                "fieldwork_end": date(2026, 8, 10),
                "shares": {"candidate-a": "0.50", "candidate-b": "0.50"},
            },
            {
                "sample_id": "expanded",
                "pollster": "Third Pollster",
                "fieldwork_end": date(2026, 8, 11),
                "shares": {
                    "candidate-a": "0.45",
                    "candidate-b": "0.35",
                    "candidate-c": "0.20",
                },
            },
        ),
        ballot=(*BALLOT_AB, BallotCandidate("candidate-c", "Candidate C")),
    )

    assert result.estimate.status == "unavailable"
    assert result.estimate.reason == "expanded_field_awaiting_replication"


def test_a_non_ballot_scenario_is_context_until_the_candidate_qualifies() -> None:
    bundle = _bundle(
        {
            "sample_id": "hypothetical",
            "pollster": "Forum Research",
            "fieldwork_end": date(2026, 8, 12),
            "scenario_label": "hypothetical field",
            "shares": {
                "candidate-a": "0.45",
                "candidate-b": "0.35",
                "candidate-c": "0.20",
            },
        }
    )

    before = _calculate(bundle)
    after = _calculate(
        bundle,
        ballot=(*BALLOT_AB, BallotCandidate("candidate-c", "Candidate C")),
    )

    assert len(before.readings) == 1
    assert before.readings[0].matches_ballot is False
    assert before.evidence_tier == "C1"
    assert after.readings[0].matches_ballot is True
    assert after.evidence_tier == "C1"


def test_unreported_denominator_with_a_leaning_follow_up_can_be_averaged() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "unlabelled",
                "pollster": "First Pollster",
                "fieldwork_end": date(2026, 8, 11),
                "shares": {"candidate-a": "0.44", "candidate-b": "0.17"},
                "denominator_type": "not_reported",
                "denominator_text": None,
            },
            {
                "sample_id": "labelled",
                "pollster": "Second Pollster",
                "fieldwork_end": date(2026, 8, 12),
                "shares": {"candidate-a": "0.40", "candidate-b": "0.20"},
            },
        )
    )

    assert result.estimate.status == "available"


def test_all_respondent_reading_is_visible_but_not_averaged() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "expressed",
                "pollster": "First Pollster",
                "fieldwork_end": date(2026, 8, 11),
                "shares": {"candidate-a": "0.44", "candidate-b": "0.36"},
            },
            {
                "sample_id": "all-respondents",
                "pollster": "Second Pollster",
                "fieldwork_end": date(2026, 8, 12),
                "shares": {"candidate-a": "0.35", "candidate-b": "0.25"},
                "denominator_type": "all_respondents",
                "denominator_text": "All respondents",
            },
        )
    )

    assert result.evidence_tier == "C2"
    assert len(result.readings) == 2
    assert result.estimate.status == "unavailable"


def test_partial_field_is_visible_but_cannot_establish_an_exact_field() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "complete",
                "pollster": "First Pollster",
                "fieldwork_end": date(2026, 8, 11),
                "shares": {"candidate-a": "0.44", "candidate-b": "0.36"},
            },
            {
                "sample_id": "partial",
                "pollster": "Second Pollster",
                "fieldwork_end": date(2026, 8, 12),
                "shares": {"candidate-a": "0.40", "candidate-b": "0.35"},
                "response_coverage": "partial",
            },
        )
    )

    assert result.evidence_tier == "C2"
    assert len(result.readings) == 2
    assert result.estimate.status == "unavailable"


def test_dependent_scenarios_are_visible_but_count_as_one_sample() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "one-sample",
                "reading_id": "narrow",
                "pollster": "Forum Research",
                "fieldwork_end": date(2026, 8, 12),
                "shares": {"candidate-a": "0.55", "candidate-b": "0.45"},
            },
            {
                "sample_id": "one-sample",
                "reading_id": "expanded",
                "pollster": "Forum Research",
                "fieldwork_end": date(2026, 8, 12),
                "shares": {
                    "candidate-a": "0.45",
                    "candidate-b": "0.35",
                    "candidate-c": "0.20",
                },
            },
        ),
        ballot=(*BALLOT_AB, BallotCandidate("candidate-c", "Candidate C")),
    )

    assert [reading.reading.poll_reading_id for reading in result.readings] == [
        "narrow",
        "expanded",
    ]
    assert result.evidence_tier == "C1"
    assert result.estimate.status == "unavailable"


def test_a_qualifying_uncertified_estimate_is_preview_only() -> None:
    result = _calculate(
        _bundle(
            {
                "sample_id": "first",
                "pollster": "First Pollster",
                "fieldwork_end": date(2026, 8, 11),
                "shares": {"candidate-a": "0.55", "candidate-b": "0.45"},
            },
            {
                "sample_id": "second",
                "pollster": "Second Pollster",
                "fieldwork_end": date(2026, 8, 12),
                "shares": {"candidate-a": "0.50", "candidate-b": "0.50"},
            },
        ),
        certified=False,
    )

    assert result.estimate.status == "preview"


def test_staleness_removes_an_estimate_without_changing_c2() -> None:
    bundle = _bundle(
        {
            "sample_id": "boundary",
            "pollster": "First Pollster",
            "fieldwork_end": date(2026, 7, 27),
            "shares": {"candidate-a": "0.55", "candidate-b": "0.45"},
        },
        {
            "sample_id": "recent",
            "pollster": "Second Pollster",
            "fieldwork_end": date(2026, 8, 12),
            "shares": {"candidate-a": "0.50", "candidate-b": "0.50"},
        },
    )
    at_boundary = calculate_ward_polling(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-ward-11-2026",
        analysis_cutoff=CUTOFF,
        final_ballot=BALLOT_AB,
        ballot_certified=True,
    )
    after_boundary = calculate_ward_polling(
        bundle,
        election_cycle_id="toronto-2026",
        contest_id="toronto-ward-11-2026",
        analysis_cutoff=datetime(2026, 8, 18, 12, tzinfo=TORONTO),
        final_ballot=BALLOT_AB,
        ballot_certified=True,
    )

    assert at_boundary.evidence_tier == "C2"
    assert at_boundary.estimate.status == "available"
    assert after_boundary.evidence_tier == "C2"
    assert after_boundary.readings[0].is_stale is True
    assert after_boundary.estimate.status == "unavailable"
