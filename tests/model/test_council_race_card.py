from pathlib import Path

from backend.model.council_biography import build_all_biographies, load_council_results
from backend.model.council_race import (
    CouncilRace,
    WardIncumbent,
    build_council_races,
    load_registered_field,
    load_ward_incumbency,
)
from backend.model.council_race_card import (
    COUNCIL_INCUMBENT_BASE_RATE_COPY,
    build_prior_results,
    derive_competitiveness_facts,
    exposure_triggers,
    race_exposure_triggers,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/raw/elections/historical_council_results.csv"
INCUMBENCY = ROOT / "data/raw/defeatability/ward_defeatability.csv"
FIELD = ROOT / "data/raw/candidates/councillor_registered.csv"


def _fixtures():
    results = load_council_results(RESULTS)
    bios = build_all_biographies(results)
    races = build_council_races(
        load_ward_incumbency(INCUMBENCY), load_registered_field(FIELD), bios
    )
    return results, races


def test_exposure_triggers_decompose_the_cdi_for_an_incumbent() -> None:
    _, races = _fixtures()
    # Saxe (ward 11): 35.4% (not <35), score 68 (>=65), New Voter Margin +8746 (>0).
    saxe = {t.key for t in exposure_triggers(races["11"].incumbent)}
    assert saxe == {"high_structural_exposure", "ward_growth_exceeds_cushion"}
    # Kandavel (ward 20): 27.3% (<35), score 66, NVM +2187 -> all three.
    kandavel = {t.key for t in exposure_triggers(races["20"].incumbent)}
    assert kandavel == {
        "narrow_prior_win",
        "high_structural_exposure",
        "ward_growth_exceeds_cushion",
    }


def test_a_safe_incumbent_fires_no_triggers() -> None:
    _, races = _fixtures()
    # Matlow (ward 12): 84.7%, score 3, NVM -12863.
    assert exposure_triggers(races["12"].incumbent) == ()


def test_triggers_are_gated_off_for_open_seats() -> None:
    _, races = _fixtures()
    # An incumbent race passes its triggers through unchanged.
    assert race_exposure_triggers(races["11"]) == exposure_triggers(
        races["11"].incumbent
    )
    assert race_exposure_triggers(races["11"])  # non-empty
    # An open seat suppresses triggers even when the incumbent's numbers fire.
    firing = WardIncumbent(
        ward="99",
        name="Test Incumbent",
        is_running=False,
        is_byelection_incumbent=False,
        defeatability_score=70,
        vote_share=0.30,
        notes="New Voter Margin: +5000",
        biography=None,
    )
    assert exposure_triggers(firing)  # would fire on the raw numbers
    open_race = CouncilRace(
        ward="99",
        incumbent=firing,
        is_open_seat=True,
        incumbent_in_field=False,
        incumbency_flag_disagrees=False,
        candidates=(),
    )
    assert race_exposure_triggers(open_race) == ()
    assert races["14"].is_open_seat and race_exposure_triggers(races["14"]) == ()


def test_trigger_copy_is_house_voice_reader_facing() -> None:
    _, races = _fixtures()
    copy = {t.key: t.copy for t in exposure_triggers(races["20"].incumbent)}
    assert "under 35%" in copy["narrow_prior_win"]
    assert "more electors" in copy["ward_growth_exceeds_cushion"]


def test_prior_result_gives_the_last_winning_margin() -> None:
    results, _ = _fixtures()
    prior = build_prior_results(results)
    w11 = prior["11"]
    # 2022: Saxe 8614 beat Di Pasquale 8491 -> 123 votes.
    assert w11.winner_votes == 8614
    assert w11.margin_votes == 123
    assert w11.margin_share < 0.01


def test_competitiveness_facts_flag_two_prior_winners() -> None:
    results, races = _fixtures()
    prior = build_prior_results(results)
    facts = derive_competitiveness_facts(races["11"], prior.get("11"))
    assert facts.field_size == len(races["11"].candidates)
    # Saxe (won 2022) and Layton (won 2018) both won this 25-ward seat.
    assert facts.candidates_who_won_this_ward == 2
    assert facts.both_won_this_ward is True
    assert facts.prior_margin_votes == 123


def test_open_seat_of_newcomers_flags_no_prior_winners() -> None:
    results, races = _fixtures()
    prior = build_prior_results(results)
    facts = derive_competitiveness_facts(races["14"], prior.get("14"))  # Fletcher open
    assert facts.candidates_who_won_this_ward == 0
    assert facts.both_won_this_ward is False


def test_base_rate_copy_is_honest_and_present() -> None:
    assert "6%" in COUNCIL_INCUMBENT_BASE_RATE_COPY
    assert "rarely" in COUNCIL_INCUMBENT_BASE_RATE_COPY.lower()
