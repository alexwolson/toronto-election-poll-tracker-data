import json
from pathlib import Path

from backend.model.council_biography import load_council_results
from backend.model.council_hints import (
    load_officeholding_history,
    load_supported_hints,
)
from backend.model.council_race import load_registered_field, load_ward_incumbency
from backend.model.council_race_card import load_ward_poll_readings
from backend.model.council_snapshot import (
    COUNCIL_RACE_CARD_SCHEMA_VERSION,
    build_council_snapshot,
    load_ward_names,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/raw/canonical/election_results.csv"
INCUMBENCY = ROOT / "data/raw/defeatability/ward_defeatability.csv"
FIELD = ROOT / "data/raw/candidates/councillor_registered.csv"
WARD_POLLS = ROOT / "data/raw/polls/ward_poll_readings.csv"
WARD_NAMES = ROOT / "data/raw/defeatability/data-qT4Kx.csv"
HINTS = ROOT / "data/raw/hints/supported_historical_hints.csv"


def _snapshot():
    return build_council_snapshot(
        load_ward_incumbency(INCUMBENCY),
        load_registered_field(FIELD),
        load_council_results(RESULTS),
        load_ward_poll_readings(WARD_POLLS),
        ward_names=load_ward_names(WARD_NAMES),
        officeholding=load_officeholding_history(RESULTS),
        supported_hints=load_supported_hints(HINTS),
    )


def test_snapshot_covers_all_wards_and_serializes_cleanly() -> None:
    snap = _snapshot()
    assert snap["schema_version"] == COUNCIL_RACE_CARD_SCHEMA_VERSION
    assert "6%" in snap["base_rate_note"]
    assert len(snap["wards"]) == 25
    json.dumps(snap, allow_nan=False)  # no Decimal / NaN leaks


def test_schema_bumped_to_v5_for_candidate_history_contract_2_1() -> None:
    assert COUNCIL_RACE_CARD_SCHEMA_VERSION == 5


def test_ward_23_han_dong_surfaces_prior_mp_and_mpp_offices() -> None:
    # Han Dong has no council history, so the council-only biography match stays
    # empty — but his all-offices past elections must still surface (ADR 0050).
    dong = next(
        c
        for c in _snapshot()["wards"]["23"]["candidates"]
        if c["display_name"] == "Han Dong"
    )
    assert dong["is_matched"] is False
    assert dong["candidate_id"] is None
    results = {(e["office_type"], e["result"]) for e in dong["past_elections"]}
    assert ("mp", "won") in results
    assert ("mpp", "won") in results
    mp = next(e for e in dong["past_elections"] if e["office_type"] == "mp")
    assert mp["party_name"]  # partisan office carries a party
    assert mp["district_name"]  # e.g. Don Valley North
    years = [e["year"] for e in dong["past_elections"]]
    assert years == sorted(years, reverse=True)  # most recent first
    # a loss states where they placed and out of how many
    lost = next(e for e in dong["past_elections"] if e["result"] == "lost")
    assert lost["rank"] is not None
    assert lost["field_size"] is not None


def test_ward_11_card_carries_the_full_picture() -> None:
    w = _snapshot()["wards"]["11"]
    assert w["ward_name"] == "University-Rosedale"
    assert w["is_open_seat"] is True  # Saxe re-registered in ward 14 -> open seat
    # The CDI file still records Saxe as the ward's sitting incumbent (historical),
    # but the card gates her exposure triggers off now that the seat is open.
    assert w["incumbent"]["name"] == "Dianne Saxe"
    assert w["incumbent"]["council_wins"] == 1
    assert w["incumbent"]["exposure_triggers"] == []  # gated off for an open seat
    assert w["competitiveness"]["both_won_this_ward"] is False  # only Layton remains
    assert w["prior_result"]["margin_votes"] == 123
    # both ward-poll scenarios present; Layton leads the operative one
    assert len(w["ward_polls"]) == 2
    layton = next(p for p in w["ward_polls"] if p["poll_id"].endswith("layton"))
    assert layton["candidates"][0]["candidate_name"] == "Mike Layton"
    assert layton["candidates"][0]["share"] == 0.44
    # Layton appears in the field as a former councillor
    assert any(
        c["display_name"] == "Mike Layton" and c["is_former_councillor"]
        for c in w["candidates"]
    )


def test_ward_11_saxe_history_orders_same_year_by_full_date() -> None:
    # Saxe re-registered in ward 14; her all-offices history is unchanged.
    saxe = next(
        c
        for c in _snapshot()["wards"]["14"]["candidates"]
        if c["display_name"] == "Dianne Saxe"
    )
    dates = [e["election_date"] for e in saxe["past_elections"]]
    assert dates == sorted(dates, reverse=True)  # full-date descending
    council_22 = next(
        i
        for i, e in enumerate(saxe["past_elections"])
        if e["office_type"] == "councillor" and e["year"] == 2022
    )
    mpp_22 = next(
        i
        for i, e in enumerate(saxe["past_elections"])
        if e["office_type"] == "mpp" and e["year"] == 2022
    )
    assert council_22 < mpp_22  # Oct 24 council win before June 2 provincial race


def test_ward_20_last_election_is_the_2023_by_election_and_matches_incumbent() -> None:
    w = _snapshot()["wards"]["20"]
    # "Last election" is the 2023 by-election Kandavel won, not the 2022 general.
    assert w["prior_result"]["year"] == 2023
    assert w["prior_result"]["winner_name"] == "Parthi Kandavel"
    # ...and it agrees with the incumbent's most recent win.
    assert w["incumbent"]["most_recent_win"]["year"] == 2023


def test_candidate_history_contract_2_1_named_ward_cases() -> None:
    snap = _snapshot()
    public_ids = {
        "own_returning_councillor__open_contest",
        "opponent_returning_councillor__open_contest",
        "own_prior_win_type__trustee",
        "own_any_all_past_race_victory__non_incumbent_non_returning",
        "own_any_all_past_race__non_incumbent_non_returning",
        "own_multiple_all_past_races__non_incumbent_non_returning",
        "own_prior_council_run_without_victory_vs_no_history__non_incumbent_non_returning",
        "own_prior_council_run_without_victory_vs_other_history__non_incumbent_non_returning",
        "own_most_recent_all_past_race_margin__non_incumbent_non_returning",
        "own_most_recent_all_past_race_was_victory__non_incumbent_non_returning",
        "own_prior_mpp_race__non_incumbent_non_returning",
        "opponent_strongest_most_recent_all_past_race_margin__incumbent",
    }
    fired_ids = {
        hint["hint_id"]
        for ward in snap["wards"].values()
        for candidate in ward["candidates"]
        for hint in candidate["historical_hints"]
    }
    assert fired_ids <= public_ids

    ward_20 = snap["wards"]["20"]
    for name in ("Naser Kaid", "Kevin Rupasinghe"):
        candidate = next(c for c in ward_20["candidates"] if c["display_name"] == name)
        ids = {hint["hint_id"] for hint in candidate["historical_hints"]}
        assert "own_any_all_past_race__non_incumbent_non_returning" in ids
        assert "own_multiple_all_past_races__non_incumbent_non_returning" in ids
        assert (
            "own_most_recent_all_past_race_margin__non_incumbent_non_returning" in ids
        )
        assert {
            "own_prior_council_run_without_victory_vs_no_history__non_incumbent_non_returning",
            "own_prior_council_run_without_victory_vs_other_history__non_incumbent_non_returning",
        } <= ids

    huy = next(
        c for c in snap["wards"]["11"]["candidates"] if c["display_name"] == "Huy Lieu"
    )
    assert len(huy["past_elections"]) == 2
    assert {race["office_type"] for race in huy["past_elections"]} == {
        "councillor",
        "trustee",
    }
    assert all(race["result"] == "lost" for race in huy["past_elections"])
    huy_ids = {hint["hint_id"] for hint in huy["historical_hints"]}
    assert "own_multiple_all_past_races__non_incumbent_non_returning" in huy_ids
    assert (
        "own_most_recent_all_past_race_margin__non_incumbent_non_returning" in huy_ids
    )

    zakir = next(
        c
        for c in snap["wards"]["25"]["candidates"]
        if c["display_name"] == "Zakir Patel"
    )
    hints = {hint["hint_id"]: hint for hint in zakir["historical_hints"]}
    assert {
        "own_prior_win_type__trustee",
        "own_any_all_past_race_victory__non_incumbent_non_returning",
        "own_any_all_past_race__non_incumbent_non_returning",
        "own_multiple_all_past_races__non_incumbent_non_returning",
        "own_prior_council_run_without_victory_vs_no_history__non_incumbent_non_returning",
        "own_prior_council_run_without_victory_vs_other_history__non_incumbent_non_returning",
        "own_most_recent_all_past_race_margin__non_incumbent_non_returning",
    } == set(hints)
    prior_win = hints["own_any_all_past_race_victory__non_incumbent_non_returning"]
    assert prior_win["direction"] == "positive"
    assert prior_win["source"]["victory_count"] == 2
    assert prior_win["source"]["qualifying_candidacy_count"] == 3


def test_open_seat_card_gates_triggers_and_surfaces_disagreement() -> None:
    w = _snapshot()["wards"]["14"]  # Fletcher — withdrew, field-derived open
    assert w["is_open_seat"] is True
    assert w["incumbent"]["exposure_triggers"] == []  # gated off for open seats
    assert w["incumbency_flag_disagrees"] is True
    assert w["ward_polls"] == []  # no ward poll here


def test_open_seat_with_a_ward_poll_still_lists_it() -> None:
    w = _snapshot()["wards"]["19"]  # Bradford open seat, but two Forum polls
    assert w["is_open_seat"] is True
    assert len(w["ward_polls"]) == 2
    assert all(
        p["candidates"][0]["candidate_name"] == "Nate Erskine-Smith"
        for p in w["ward_polls"]
    )
