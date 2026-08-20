import json
from pathlib import Path

from backend.model.council_biography import load_council_results
from backend.model.council_race import load_registered_field, load_ward_incumbency
from backend.model.council_race_card import load_ward_poll_readings
from backend.model.council_snapshot import (
    COUNCIL_RACE_CARD_SCHEMA_VERSION,
    build_council_snapshot,
    load_ward_names,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/raw/elections/historical_council_results.csv"
INCUMBENCY = ROOT / "data/raw/defeatability/ward_defeatability.csv"
FIELD = ROOT / "data/raw/candidates/councillor_registered.csv"
WARD_POLLS = ROOT / "data/raw/polls/ward_poll_readings.csv"
WARD_NAMES = ROOT / "data/raw/defeatability/data-qT4Kx.csv"


def _snapshot():
    return build_council_snapshot(
        load_ward_incumbency(INCUMBENCY),
        load_registered_field(FIELD),
        load_council_results(RESULTS),
        load_ward_poll_readings(WARD_POLLS),
        ward_names=load_ward_names(WARD_NAMES),
    )


def test_snapshot_covers_all_wards_and_serializes_cleanly() -> None:
    snap = _snapshot()
    assert snap["schema_version"] == COUNCIL_RACE_CARD_SCHEMA_VERSION
    assert "6%" in snap["base_rate_note"]
    assert len(snap["wards"]) == 25
    json.dumps(snap, allow_nan=False)  # no Decimal / NaN leaks


def test_ward_11_card_carries_the_full_picture() -> None:
    w = _snapshot()["wards"]["11"]
    assert w["ward_name"] == "University-Rosedale"
    assert w["is_open_seat"] is False
    assert w["incumbent"]["name"] == "Dianne Saxe"
    assert w["incumbent"]["council_wins"] == 1
    assert w["incumbent"]["exposure_triggers"]  # Saxe fires exposure triggers
    assert w["competitiveness"]["both_won_this_ward"] is True
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
