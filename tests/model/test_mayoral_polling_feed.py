from pathlib import Path

from backend.model.mayoral_polling_feed import (
    build_mayoral_polling_feed,
    load_mayoral_polls,
)

ROOT = Path(__file__).resolve().parents[2]
POLLS = ROOT / "data/raw/polls/polls.csv"


def test_polls_load_newest_published_first() -> None:
    polls = load_mayoral_polls(POLLS)
    assert polls[0].poll_id == "canadapulse-2026-09-24"
    published = [p.date_published for p in polls]
    assert published == sorted(published, reverse=True)


def test_shares_carry_only_populated_candidates() -> None:
    polls = load_mayoral_polls(POLLS)
    latest = polls[0]
    # Canada Pulse (published 2026-09-29): the selected decided-and-leaning
    # reading excludes non-voters and dont-know responses from the all-voter view.
    assert set(latest.shares) == {"alexander", "bradford", "chow", "other"}
    assert latest.shares == {
        "alexander": 0.09,
        "bradford": 0.34,
        "chow": 0.51,
        "other": 0.06,
    }
    assert set(latest.field_tested) == set(latest.shares)
    assert latest.denominator == "Decided and leaning voters"
    assert "denominator" not in latest.shares


def test_feed_exposes_latest_and_a_raw_per_candidate_trend() -> None:
    feed = build_mayoral_polling_feed(POLLS)
    assert feed["schema_version"] == 1
    assert feed["latest"]["poll_id"] == "canadapulse-2026-09-24"
    assert feed["latest"]["denominator"] == "Decided and leaning voters"
    assert "denominator" not in feed["candidates"]
    assert {"chow", "bradford", "alexander"} <= set(feed["candidates"])
    chow = feed["trend"]["chow"]
    assert [pt["date_conducted"] for pt in chow] == sorted(
        pt["date_conducted"] for pt in chow
    )  # chronological
    assert chow[-1]["share"] == 0.51  # most recent conducted (Canada Pulse 2026-09-24)
