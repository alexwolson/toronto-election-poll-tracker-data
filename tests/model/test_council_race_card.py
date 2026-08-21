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
    load_ward_poll_readings,
    race_exposure_triggers,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/raw/canonical/election_results.csv"
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
    # An incumbent race passes its triggers through unchanged (ward 11 is now an
    # open seat after Saxe left, so ward 20's running incumbent Kandavel anchors this).
    assert race_exposure_triggers(races["20"]) == exposure_triggers(
        races["20"].incumbent
    )
    assert race_exposure_triggers(races["20"])  # non-empty
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


def test_prior_result_uses_the_latest_contest_including_by_elections() -> None:
    results, _ = _fixtures()
    prior = build_prior_results(results)
    # Ward 20 held a 2023 by-election (Kandavel), more recent than the 2022 general.
    assert prior["20"].year == 2023
    assert prior["20"].winner_name == "Parthi Kandavel"
    assert prior["20"].field_size == 23
    # Ward 25's 2025 by-election (Shan) and Ward 15's 2024 by-election.
    assert prior["25"].year == 2025
    assert prior["25"].winner_name == "Neethan Shan"
    assert prior["15"].year == 2024
    # A ward with no later contest still shows its 2022 general.
    assert prior["11"].year == 2022


def test_competitiveness_facts_count_prior_ward_winners() -> None:
    results, races = _fixtures()
    prior = build_prior_results(results)
    facts = derive_competitiveness_facts(races["11"], prior.get("11"))
    assert facts.field_size == len(races["11"].candidates)
    # Saxe (won 2022) re-registered in ward 14, leaving Layton (won 2018) as the
    # only prior winner of this seat still in the ward 11 field.
    assert facts.candidates_who_won_this_ward == 1
    assert facts.both_won_this_ward is False
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


WARD_POLLS = ROOT / "data/raw/polls/ward_poll_readings.csv"


def test_raw_ward_poll_is_surfaced_where_it_exists() -> None:
    # The lone 2026 ward poll (Ward 13, Forum) is shown as raw observed evidence
    # with its limitations, never averaged (ADR 0037).
    readings = load_ward_poll_readings(WARD_POLLS)
    reading = readings["13"][0]
    assert reading.firm == "Forum Research"
    assert reading.sample_size == 355
    assert reading.denominator == "decided voters"
    assert reading.ballot_status == "different_candidate_field"  # a limitation
    assert reading.undecided_share == 0.45
    moise = next(c for c in reading.candidates if c.candidate_id == "moise")
    assert moise.is_incumbent
    assert moise.share == 0.35


def test_wards_without_a_poll_have_no_readings() -> None:
    readings = load_ward_poll_readings(WARD_POLLS)
    assert readings.get("12", ()) == ()  # Matlow — no ward poll
    assert readings.get("14", ()) == ()  # Fletcher open seat — no ward poll


def test_ward_11_carries_both_forum_scenarios() -> None:
    # The Aug-12 Forum poll offered two council scenarios; both are ingested, and
    # the Layton-enters reading (its field matches the registered ballot) leads.
    readings = load_ward_poll_readings(WARD_POLLS)
    w11 = readings["11"]
    assert len(w11) == 2
    layton = next(r for r in w11 if r.poll_id.endswith("layton"))
    assert layton.candidates[0].candidate_id == "layton"
    assert layton.candidates[0].share == 0.44
    saxe = next(c for c in layton.candidates if c.candidate_id == "saxe")
    assert saxe.is_incumbent and saxe.share == 0.17


def test_ward_poll_names_the_candidates_first_and_residual_last() -> None:
    readings = load_ward_poll_readings(WARD_POLLS)
    order = [c.candidate_id for c in readings["13"][0].candidates]
    assert order[0] == "moise"  # top named by share
    assert order[-1] == "residual"  # residual shown last despite its 40% share
