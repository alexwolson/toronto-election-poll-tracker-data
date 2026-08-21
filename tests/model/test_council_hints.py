from pathlib import Path

from backend.model.council_hints import (
    CandidacyRecord,
    candidate_features,
    fire_candidate_hints,
    load_hint_contract,
    load_supported_hints,
    past_election_history,
    resolve_person_id,
    signal_direction,
)

ROOT = Path(__file__).resolve().parents[2]
HINTS = load_supported_hints(ROOT / "data/raw/hints/supported_historical_hints.csv")
CONTRACT = load_hint_contract(ROOT / "data/raw/hints/historical_hint_contract.json")


def _rec(office, date, win, share, margin):
    return CandidacyRecord("p1", office, date, win, share, margin)


def _fire(features, opponents=(), *, open_contest):
    return {
        h.hint_id: h
        for h in fire_candidate_hints(
            features, list(opponents), is_open_contest=open_contest, hints=HINTS
        )
    }


# --- the catalog loads the schema-2.1 public hints ---------------------------


def test_catalog_loads_all_schema_2_1_public_hints() -> None:
    assert CONTRACT["schema_version"] == "2.1.0"
    ids = {h.hint_id for h in HINTS}
    assert ids == {
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
    assert len(HINTS) == 12
    trustee = next(h for h in HINTS if h.hint_id == "own_prior_win_type__trustee")
    assert trustee.evidence_tier == "consistent_across_elections"
    assert "school-board trustee" in trustee.frontend_copy


# --- feature derivation follows the contract --------------------------------


def test_former_trustee_win_is_prior_elected_office() -> None:
    f = candidate_features(
        [_rec("trustee", "2018-10-22", True, 0.50, 0.20)], is_sitting_incumbent=False
    )
    assert f.has_all_prior_victory
    assert "trustee" in f.prior_office_types_won
    assert f.all_prior_candidacy_count == 1
    assert f.all_prior_victory_count == 1


def test_returning_councillor_counts_prior_council_win() -> None:
    rec = [_rec("councillor", "2018-10-22", True, 0.55, 0.10)]
    returning = candidate_features(rec, is_sitting_incumbent=False)
    assert returning.returning_councillor
    assert returning.has_all_prior_victory
    assert returning.all_prior_candidacy_count == 1
    assert returning.all_prior_victory_count == 1


def test_sitting_incumbents_prior_council_record_is_in_complete_history() -> None:
    rec = [_rec("councillor", "2018-10-22", True, 0.55, 0.10)]
    incumbent = candidate_features(rec, is_sitting_incumbent=True)
    assert incumbent.is_sitting_incumbent
    assert not incumbent.returning_councillor
    assert incumbent.has_all_prior_victory
    assert incumbent.all_prior_candidacy_count == 1
    assert incumbent.all_prior_victory_count == 1


def test_ran_but_never_won_has_zero_victories_and_a_negative_margin() -> None:
    f = candidate_features(
        [_rec("mpp", "2022-06-02", False, 0.15, -0.30)], is_sitting_incumbent=False
    )
    assert not f.has_all_prior_victory
    assert f.all_prior_candidacy_count == 1
    assert f.all_prior_victory_count == 0
    assert f.most_recent_all_prior_margin == -0.30
    assert f.most_recent_all_prior_was_victory is False
    assert "mpp" in f.prior_office_types_contested


# --- hint firing ------------------------------------------------------------


def _trustee_winner():
    return candidate_features(
        [_rec("trustee", "2018-10-22", True, 0.50, 0.20)],
        is_sitting_incumbent=False,
    )


def test_trustee_winner_in_open_seat_fires_own_hints() -> None:
    fired = _fire(_trustee_winner(), open_contest=True)
    assert set(fired) == {
        "own_prior_win_type__trustee",
        "own_any_all_past_race_victory__non_incumbent_non_returning",
        "own_any_all_past_race__non_incumbent_non_returning",
        "own_most_recent_all_past_race_margin__non_incumbent_non_returning",
        "own_most_recent_all_past_race_was_victory__non_incumbent_non_returning",
    }


def test_binary_prior_win_hint_fires_for_non_incumbent_facing_incumbent() -> None:
    fired = _fire(_trustee_winner(), open_contest=False)
    assert "own_any_all_past_race_victory__non_incumbent_non_returning" in fired
    assert "own_prior_win_type__trustee" in fired


def test_returning_councillor_in_open_contest_fires_small_sample_hint_only() -> None:
    returning = candidate_features(
        [_rec("councillor", "2018-10-22", True, 0.50, 0.20)],
        is_sitting_incumbent=False,
    )
    assert set(_fire(returning, open_contest=True)) == {
        "own_returning_councillor__open_contest"
    }


def test_binary_prior_win_hint_is_gated_off_for_sitting_incumbent() -> None:
    incumbent = candidate_features(
        [_rec("councillor", "2022-10-24", True, 0.50, 0.20)],
        is_sitting_incumbent=True,
    )
    assert _fire(incumbent, open_contest=False) == {}


def test_single_prior_loss_fires_history_and_margin_hints() -> None:
    f = candidate_features(
        [_rec("trustee", "2022-10-24", False, 0.10, -0.30)],
        is_sitting_incumbent=False,
    )
    fired = _fire(f, open_contest=True)
    assert set(fired) == {
        "own_any_all_past_race__non_incumbent_non_returning",
        "own_most_recent_all_past_race_margin__non_incumbent_non_returning",
    }
    assert (
        fired[
            "own_most_recent_all_past_race_margin__non_incumbent_non_returning"
        ].direction
        == ""
    )


def test_newcomer_with_no_history_fires_nothing() -> None:
    f = candidate_features([], is_sitting_incumbent=False)
    assert _fire(f, open_contest=True) == {}


def test_multiple_unsuccessful_council_runs_fire_both_paired_comparisons() -> None:
    f = candidate_features(
        [
            _rec("councillor", "2022-10-24", False, 0.20, -0.25),
            _rec("councillor", "2018-10-22", False, 0.15, -0.40),
        ],
        is_sitting_incumbent=False,
    )
    fired = _fire(f, open_contest=False)
    positive = "own_prior_council_run_without_victory_vs_no_history__non_incumbent_non_returning"
    negative = "own_prior_council_run_without_victory_vs_other_history__non_incumbent_non_returning"
    assert positive in fired and negative in fired
    assert fired[positive].direction == "positive"
    assert fired[negative].direction == "negative"
    assert "own_multiple_all_past_races__non_incumbent_non_returning" in fired


def test_prior_mpp_race_uses_named_office_scope() -> None:
    f = candidate_features(
        [_rec("mpp", "2022-06-02", False, 0.15, -0.30)],
        is_sitting_incumbent=False,
    )
    fired = _fire(f, open_contest=False)
    assert "own_prior_mpp_race__non_incumbent_non_returning" in fired


def test_open_candidate_faces_returning_councillor_even_when_own_history_unknown() -> (
    None
):
    unknown = candidate_features(
        [], is_sitting_incumbent=False, history_confirmed=False, name="Newcomer"
    )
    returning = candidate_features(
        [_rec("councillor", "2018-10-22", True, 0.50, 0.20)],
        is_sitting_incumbent=False,
        name="Former Councillor",
    )
    fired = _fire(unknown, [returning], open_contest=True)
    hint = fired["opponent_returning_councillor__open_contest"]
    assert hint.direction == "negative"
    assert hint.source is not None
    assert hint.source.opponent_name == "Former Councillor"


def test_incumbent_opponent_margin_requires_complete_opponent_history() -> None:
    incumbent = candidate_features([], is_sitting_incumbent=True, name="Incumbent")
    challenger = candidate_features(
        [_rec("mpp", "2022-06-02", True, 0.40, 0.10)],
        is_sitting_incumbent=False,
        name="Challenger",
    )
    hint_id = "opponent_strongest_most_recent_all_past_race_margin__incumbent"
    fired = _fire(incumbent, [challenger], open_contest=False)
    assert fired[hint_id].direction == ""
    assert fired[hint_id].source is not None
    assert fired[hint_id].source.opponent_name == "Challenger"

    unknown = candidate_features(
        [], is_sitting_incumbent=False, history_confirmed=False, name="Unknown"
    )
    assert hint_id not in _fire(incumbent, [challenger, unknown], open_contest=False)


# --- signed historical direction (ticket 02) --------------------------------


def test_signal_direction_withholds_a_verdict_for_continuous_hints() -> None:
    assert signal_direction("own_prior_win_type__trustee", None) == "positive"
    assert (
        signal_direction(
            "own_any_all_past_race_victory__non_incumbent_non_returning", None
        )
        == "positive"
    )
    for hint_id in (
        "own_most_recent_all_past_race_margin__non_incumbent_non_returning",
        "opponent_strongest_most_recent_all_past_race_margin__incumbent",
    ):
        assert signal_direction(hint_id, -0.2) == ""
        assert signal_direction(hint_id, 0.2) == ""


def test_binary_prior_win_provenance_uses_complete_visible_history() -> None:
    subject = candidate_features(
        [
            _cand("c1", "councillor", "2025-09-29", False, 0.10, rank=5, field_size=20),
            _cand("c2", "trustee", "2022-10-24", True, 0.42, rank=1, field_size=6),
            _cand("c3", "trustee", "2018-10-22", True, 0.35, rank=1, field_size=9),
        ],
        name="Subject",
        is_sitting_incumbent=False,
    )
    fired = _fire(subject, open_contest=False)
    prior_win = fired["own_any_all_past_race_victory__non_incumbent_non_returning"]
    assert prior_win.direction == "positive"
    assert prior_win.source is not None
    assert prior_win.source.victory_count == 2
    assert prior_win.source.qualifying_candidacy_count == 3
    assert prior_win.source.year == 2022


# --- generous single-person_id resolution -----------------------------------

_VARIANTS = {
    "pA": {frozenset({"mike", "layton"})},
    "pB": {frozenset({"jane", "doe"})},
    "pC1": {frozenset({"john", "smith"})},
    "pC2": {frozenset({"john", "smith"})},
}


def test_resolver_matches_across_middle_names() -> None:
    assert resolve_person_id("Mike", "Layton", _VARIANTS) == "pA"
    assert resolve_person_id("Mike Robert", "Layton", _VARIANTS) == "pA"  # superset


def test_resolver_returns_none_when_ambiguous_or_absent() -> None:
    assert resolve_person_id("John", "Smith", _VARIANTS) is None  # two person_ids
    assert resolve_person_id("Nobody", "Here", _VARIANTS) is None


# --- past election history (all offices, won and lost) ----------------------


def _cand(
    contest,
    office,
    date,
    win,
    share,
    *,
    district="",
    party="",
    body="",
    rank=None,
    field_size=None,
):
    return CandidacyRecord(
        "p1",
        office,
        date,
        win,
        share,
        None,
        contest_id=contest,
        district_name=district,
        party_name=party,
        represented_body=body,
        vote_rank=rank,
        field_size=field_size,
    )


def test_past_election_history_lists_all_candidacies_recent_first() -> None:
    records = [
        _cand(
            "c_mpp14",
            "mpp",
            "2014-06-12",
            True,
            0.40,
            district="Trinity-Spadina",
            party="Liberal",
            body="ontario_legislative_assembly",
        ),
        _cand(
            "c_mp21",
            "mp",
            "2021-09-20",
            True,
            0.45,
            district="Don Valley North",
            party="Liberal",
            body="canada_house_of_commons",
        ),
        _cand(
            "c_coun18",
            "councillor",
            "2018-10-22",
            False,
            0.20,
            district="Ward 5",
            body="toronto_city_council",
        ),
    ]
    history = past_election_history(records)
    assert [e.year for e in history] == [2021, 2018, 2014]  # most recent first
    mp = history[0]
    assert mp.office_type == "mp"
    assert mp.district_name == "Don Valley North"
    assert mp.party_name == "Liberal"
    assert mp.result == "won"
    council = next(e for e in history if e.office_type == "councillor")
    assert council.result == "lost"
    assert council.party_name is None  # municipal races are non-partisan


def test_past_election_history_collapses_ranked_ballot_rounds() -> None:
    # A single contest split across rounds (composite ballot) is one race.
    records = [
        _cand("c1", "mayor", "2018-10-22", False, 0.30, body="x"),
        _cand("c1", "mayor", "2018-10-22", True, 0.52, body="x"),
    ]
    history = past_election_history(records)
    assert len(history) == 1
    assert history[0].result == "won"
    assert history[0].vote_share == 0.52


def test_past_election_history_empty_for_no_records() -> None:
    assert past_election_history([]) == ()


def test_past_election_history_carries_rank_and_field_size() -> None:
    # A loss should say where they placed (2nd vs 11th) and out of how many.
    records = [
        _cand("c1", "councillor", "2018-10-22", False, 0.20, rank=2, field_size=11),
    ]
    history = past_election_history(records)
    assert history[0].result == "lost"
    assert history[0].rank == 2
    assert history[0].field_size == 11


def test_past_election_history_orders_same_year_by_full_date() -> None:
    # Supplied provincial-first, but the October council race is more recent than
    # the June provincial one — order must follow the full date, not the year.
    records = [
        _cand("c_mpp", "mpp", "2022-06-02", False, 0.30, rank=3, field_size=6),
        _cand("c_coun", "councillor", "2022-10-24", True, 0.52),
    ]
    history = past_election_history(records)
    assert [e.office_type for e in history] == ["councillor", "mpp"]
    assert history[0].election_date == "2022-10-24"
