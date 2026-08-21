from pathlib import Path

from backend.model.publication_manifest import (
    build_publication_manifest,
    load_live_cycle,
)

ROOT = Path(__file__).resolve().parents[2]
LIVE_CYCLE = load_live_cycle(ROOT / "data/raw/elections/live_cycle.json")


def _manifest(live_cycle, summary=None):
    return build_publication_manifest(
        as_of="2026-08-20",
        live_cycle=live_cycle,
        feed_versions={"mayoral_polling": 1, "council_race_cards": 2},
        mayoral_publication_summary=summary,
    )


def test_final_ballot_certification_follows_the_explicit_flag_not_the_clock() -> None:
    # The committed config withholds certification until the maintainer confirms.
    assert LIVE_CYCLE["field_certified"] is False
    assert _manifest(LIVE_CYCLE)["election"]["final_ballot_certified"] is False
    certified = {**LIVE_CYCLE, "field_certified": True}
    assert _manifest(certified)["election"]["final_ballot_certified"] is True


def test_manifest_indexes_all_four_feeds() -> None:
    m = _manifest(LIVE_CYCLE)
    assert set(m["feeds"]) == {
        "mayoral_forecast",
        "mayoral_polling",
        "council_race_cards",
        "manifest",
    }
    assert m["generated_at"] == "2026-08-20"
    assert m["election"]["nomination_close_date"] == "2026-08-21"
    assert m["feed_versions"]["council_race_cards"] == 2
