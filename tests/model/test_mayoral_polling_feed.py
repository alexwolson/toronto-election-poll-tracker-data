from pathlib import Path

from backend.model.mayoral_polling_feed import (
    build_mayoral_polling_feed,
    load_mayoral_polls,
)

ROOT = Path(__file__).resolve().parents[2]
POLLS = ROOT / "data/raw/polls/polls.csv"


def test_polls_load_newest_published_first() -> None:
    polls = load_mayoral_polls(POLLS)
    assert polls[0].poll_id == "mainstreet-2026-10-07"
    published = [p.date_published for p in polls]
    assert published == sorted(published, reverse=True)


def test_shares_carry_only_populated_candidates() -> None:
    polls = load_mayoral_polls(POLLS)
    latest = polls[0]
    # Mainstreet (published 2026-10-09): decided and leaning, Alexander not offered.
    assert latest.shares == {
        "bradford": 0.443,
        "chow": 0.472,
        "odessa-paloma-parker": 0.028,
        "other": 0.032,
        "sarah-mcvie": 0.025,
    }
    assert set(latest.field_tested) == set(latest.shares)
    assert latest.denominator == "Decided and leaning voters"
    assert "denominator" not in latest.shares


def test_feed_exposes_latest_and_a_raw_per_candidate_trend() -> None:
    feed = build_mayoral_polling_feed(POLLS)
    assert feed["schema_version"] == 1
    assert feed["latest"]["poll_id"] == "mainstreet-2026-10-07"
    assert feed["latest"]["denominator"] == "Decided and leaning voters"
    assert "denominator" not in feed["candidates"]
    assert {"chow", "bradford", "alexander"} <= set(feed["candidates"])
    chow = feed["trend"]["chow"]
    assert [pt["date_conducted"] for pt in chow] == sorted(
        pt["date_conducted"] for pt in chow
    )  # chronological
    assert chow[-1]["share"] == 0.472  # Mainstreet fieldwork ended 2026-10-07
