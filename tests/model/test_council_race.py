from pathlib import Path

from backend.model.council_biography import build_all_biographies, load_council_results
from backend.model.council_race import (
    build_council_races,
    load_registered_field,
    load_ward_incumbency,
    match_biography,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/raw/canonical/toronto_election_results.csv"
INCUMBENCY = ROOT / "data/raw/defeatability/ward_defeatability.csv"
FIELD = ROOT / "data/raw/candidates/councillor_registered.csv"


def _races():
    biographies = build_all_biographies(load_council_results(RESULTS))
    return build_council_races(
        load_ward_incumbency(INCUMBENCY),
        load_registered_field(FIELD),
        biographies,
    )


def test_every_ward_has_a_race_with_an_incumbent() -> None:
    races = _races()
    assert len(races) == 25
    assert all(race.incumbent is not None for race in races.values())


def test_open_seats_are_derived_from_the_fresh_field() -> None:
    races = _races()
    open_wards = {ward for ward, race in races.items() if race.is_open_seat}
    # Field-derived: Perks (4), Fletcher (14), Bradford (19) are all absent from
    # the current registered field. Fletcher is the one the is_running flag misses.
    assert open_wards == {"4", "14", "19"}
    assert races["11"].is_open_seat is False  # Saxe is in the field


def test_stale_incumbency_flag_is_surfaced_as_a_disagreement() -> None:
    races = _races()
    # Ward 14: the field says open (Fletcher absent) but the is_running flag still
    # says running -> derived correctly as open, and flagged for editorial review.
    assert races["14"].is_open_seat is True
    assert races["14"].incumbent_in_field is False
    assert races["14"].incumbency_flag_disagrees is True
    # Where field and flag agree, no disagreement is raised.
    assert races["4"].incumbency_flag_disagrees is False  # both say open
    assert races["19"].incumbency_flag_disagrees is False  # both say open
    assert races["11"].incumbency_flag_disagrees is False  # both say running


def test_incumbent_record_is_matched_to_a_biography() -> None:
    races = _races()
    # Ward 4: Gord Perks, a five-term councillor, retiring.
    perks = races["4"].incumbent
    assert perks.biography is not None
    assert perks.biography.council_wins == 5
    assert not perks.is_running
    # Ward 11: Dianne Saxe, one narrow term.
    saxe = races["11"].incumbent
    assert saxe.biography is not None
    assert saxe.biography.council_wins == 1
    assert saxe.defeatability_score == 68


def test_registered_candidate_is_matched_to_its_history() -> None:
    races = _races()
    saxe = next(c for c in races["11"].candidates if "saxe" in c.display_name.lower())
    assert saxe.candidate_id == "c00665"
    assert saxe.biography is not None
    assert saxe.biography.most_recent_win.year == 2022


def test_newcomers_carry_no_biography() -> None:
    races = _races()
    # Across the whole field, unmatched candidates are newcomers with no history.
    newcomers = [
        c for race in races.values() for c in race.candidates if not c.is_matched
    ]
    assert newcomers  # there are always newcomers
    assert all(c.biography is None and c.candidate_id is None for c in newcomers)


def test_fuzzy_match_is_order_insensitive() -> None:
    # The registration gives "First Last"; candidate_id lookups need it
    # (e.g. last-first "c01140"). A token-set match bridges both.
    biographies = build_all_biographies(load_council_results(RESULTS))
    bio = match_biography("Mike", "Layton", biographies)
    assert bio is not None
    assert bio.candidate_id == "c01140"
    assert bio.council_wins == 3
    # a genuine non-candidate returns nothing
    assert match_biography("Nobody", "Atall", biographies) is None
