from pathlib import Path

from backend.model.mayoral_polling_feed import (
    build_mayoral_polling_feed,
    load_mayoral_polls,
)

ROOT = Path(__file__).resolve().parents[2]
POLLS = ROOT / "data/raw/polls/polls.csv"


def test_polls_load_newest_published_first() -> None:
    polls = load_mayoral_polls(POLLS)
    assert polls[0].poll_id == "nanos-2026-10-04"
    published = [p.date_published for p in polls]
    assert published == sorted(published, reverse=True)


def test_shares_carry_only_populated_candidates() -> None:
    polls = load_mayoral_polls(POLLS)
    latest = polls[0]
    # Nanos (published 2026-10-06): three named candidates and someone else.
    # McVie and Parker were not published separately; neither is recorded at zero.
    assert set(latest.shares) == {
        "alexander",
        "bradford",
        "chow",
        "other",
    }
    assert latest.shares == {
        "alexander": 0.04,
        "bradford": 0.426,
        "chow": 0.524,
        "other": 0.01,
    }
    assert set(latest.field_tested) == set(latest.shares)
    assert latest.denominator == "Decided and leaning voters"
    assert "denominator" not in latest.shares


def test_feed_exposes_latest_and_a_raw_per_candidate_trend() -> None:
    feed = build_mayoral_polling_feed(POLLS)
    assert feed["schema_version"] == 1
    assert feed["latest"]["poll_id"] == "nanos-2026-10-04"
    assert feed["latest"]["denominator"] == "Decided and leaning voters"
    assert "denominator" not in feed["candidates"]
    assert {"chow", "bradford", "alexander"} <= set(feed["candidates"])
    chow = feed["trend"]["chow"]
    assert [pt["date_conducted"] for pt in chow] == sorted(
        pt["date_conducted"] for pt in chow
    )  # chronological
    assert chow[-1]["share"] == 0.524  # Nanos fieldwork ended 2026-10-04
