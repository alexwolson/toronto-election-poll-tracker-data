from pathlib import Path

from backend.model.council_hints import (
    CandidacyRecord,
    CandidateFeatures,
    candidate_features,
    fire_candidate_hints,
    load_supported_hints,
    past_election_history,
    resolve_person_id,
    signal_direction,
)

ROOT = Path(__file__).resolve().parents[2]
HINTS = load_supported_hints(ROOT / "data/raw/hints/supported_historical_hints.csv")


def _rec(office, date, win, share, margin):
    return CandidacyRecord("p1", office, date, win, share, margin)


def _fire(features, opponents=(), *, open_contest):
    return {
        h.hint_id: h
        for h in fire_candidate_hints(
            features, list(opponents), is_open_contest=open_contest, hints=HINTS
        )
    }


# --- the catalog loads the six supported hints ------------------------------


def test_catalog_loads_the_six_supported_hints() -> None:
    ids = {h.hint_id for h in HINTS}
    assert ids == {
        "own_any_prior_elected_office__open_contest",
        "opponent_any_prior_elected_office__open_contest",
        "own_prior_win_type__trustee",
        "own_most_recent_prior_elected_margin",
        "opponent_strongest_prior_elected_margin",
        "own_prior_elected_victory_count",
    }
    trustee = next(h for h in HINTS if h.hint_id == "own_prior_win_type__trustee")
    assert trustee.evidence_tier == "consistent_across_elections"
    assert "school-board trustee" in trustee.frontend_copy


# --- feature derivation follows the contract --------------------------------


def test_former_trustee_win_is_prior_elected_office() -> None:
    f = candidate_features(
        [_rec("trustee", "2018-10-22", True, 0.50, 0.20)], is_sitting_incumbent=False
    )
    assert f.has_prior_elected_office
    assert "trustee" in f.prior_office_types_won
    assert f.prior_elected_victory_count == 1
    assert f.most_recent_prior_elected_margin == 0.20


def test_returning_councillor_counts_prior_council_win() -> None:
    rec = [_rec("councillor", "2018-10-22", True, 0.55, 0.10)]
    returning = candidate_features(rec, is_sitting_incumbent=False)
    assert returning.has_prior_elected_office
    assert returning.prior_elected_victory_count == 1
    assert returning.most_recent_prior_elected_margin == 0.10


def test_sitting_incumbents_prior_council_record_is_excluded() -> None:
    rec = [_rec("councillor", "2018-10-22", True, 0.55, 0.10)]
    incumbent = candidate_features(rec, is_sitting_incumbent=True)
    assert not incumbent.has_prior_elected_office
    assert incumbent.prior_elected_candidacy_count == 0
    assert incumbent.most_recent_prior_elected_margin is None


def test_ran_but_never_won_has_zero_victories_and_a_negative_margin() -> None:
    f = candidate_features(
        [_rec("mpp", "2022-06-02", False, 0.15, -0.30)], is_sitting_incumbent=False
    )
    assert not f.has_prior_elected_office
    assert f.prior_elected_candidacy_count == 1
    assert f.prior_elected_victory_count == 0
    assert f.most_recent_prior_elected_margin == -0.30


# --- hint firing ------------------------------------------------------------


def _trustee_winner():
    return CandidateFeatures(
        has_prior_elected_office=True,
        prior_office_types_won=frozenset({"trustee"}),
        prior_elected_candidacy_count=1,
        prior_elected_victory_count=1,
        most_recent_prior_elected_margin=0.20,
    )


def test_trustee_winner_in_open_seat_fires_own_hints() -> None:
    fired = _fire(_trustee_winner(), open_contest=True)
    assert fired["own_prior_win_type__trustee"]
    assert fired["own_any_prior_elected_office__open_contest"]
    assert fired["own_most_recent_prior_elected_margin"].value == 0.20
    assert fired["own_prior_elected_victory_count"].value == 1
    assert "opponent_any_prior_elected_office__open_contest" not in fired


def test_open_contest_own_hint_is_gated_off_in_an_incumbent_contest() -> None:
    fired = _fire(_trustee_winner(), open_contest=False)
    assert "own_any_prior_elected_office__open_contest" not in fired
    # office-specific and continuous hints still fire (all_primary_regimes)
    assert fired["own_prior_win_type__trustee"]
    assert fired["own_most_recent_prior_elected_margin"].value == 0.20


def test_opponent_hints_fire_from_the_ward_field() -> None:
    plain = CandidateFeatures(False, frozenset(), 0, 0, None)
    strong_opp = CandidateFeatures(True, frozenset({"mpp"}), 1, 1, 0.35)
    weak_opp = CandidateFeatures(True, frozenset({"trustee"}), 1, 1, 0.05)
    fired = _fire(plain, [strong_opp, weak_opp], open_contest=True)
    assert fired["opponent_any_prior_elected_office__open_contest"]
    assert fired["opponent_strongest_prior_elected_margin"].value == 0.35  # the max
    assert "own_any_prior_elected_office__open_contest" not in fired


def test_ran_but_never_won_fires_victory_count_of_zero() -> None:
    f = CandidateFeatures(False, frozenset(), 1, 0, -0.30)
    fired = _fire(f, open_contest=True)
    assert fired["own_prior_elected_victory_count"].value == 0
    assert fired["own_most_recent_prior_elected_margin"].value == -0.30
    assert "own_any_prior_elected_office__open_contest" not in fired


def test_newcomer_with_no_history_fires_nothing() -> None:
    f = CandidateFeatures(False, frozenset(), 0, 0, None)
    assert _fire(f, open_contest=True) == {}


# --- signed historical direction (ticket 02) --------------------------------


def test_signal_direction_for_all_six_hints() -> None:
    # own presence-of-a-positive-factor hints read positive
    assert (
        signal_direction("own_any_prior_elected_office__open_contest", None)
        == "positive"
    )
    assert signal_direction("own_prior_win_type__trustee", None) == "positive"
    # opponent hints are negative for the subject whose card they'd appear on
    assert (
        signal_direction("opponent_any_prior_elected_office__open_contest", None)
        == "negative"
    )
    assert (
        signal_direction("opponent_strongest_prior_elected_margin", 0.35) == "negative"
    )
    # own margin: the candidate's actual value decides, not the coefficient
    assert signal_direction("own_most_recent_prior_elected_margin", 0.24) == "positive"
    assert signal_direction("own_most_recent_prior_elected_margin", -0.26) == "negative"
    # own victory count: a measured zero is negative, one or more is positive
    assert signal_direction("own_prior_elected_victory_count", 0) == "negative"
    assert signal_direction("own_prior_elected_victory_count", 3) == "positive"
    # a missing value falls to the conservative (negative) reading
    assert signal_direction("own_most_recent_prior_elected_margin", None) == "negative"


def test_fire_attaches_measured_zero_and_opponent_provenance() -> None:
    subject = candidate_features(
        [
            _cand("c1", "trustee", "2022-10-24", False, 0.10, rank=7, field_size=8),
            _cand("c2", "trustee", "2018-10-22", False, 0.12, rank=5, field_size=9),
        ],
        name="Subject",
        is_sitting_incumbent=False,
    )
    opponent = candidate_features(
        [_cand("c3", "trustee", "2018-10-22", True, 0.40, rank=1, field_size=10)],
        name="Opp",
        is_sitting_incumbent=False,
    )
    fired = {
        h.hint_id: h
        for h in fire_candidate_hints(
            subject, [opponent], is_open_contest=True, hints=HINTS
        )
    }
    # measured zero (0 of 2 qualifying candidacies), negative
    vc = fired["own_prior_elected_victory_count"]
    assert vc.direction == "negative"
    assert vc.source is not None
    assert vc.source.coverage == "measured_zero"
    assert vc.source.victory_count == 0
    assert vc.source.qualifying_candidacy_count == 2
    assert vc.source.year == 2022  # most-recent qualifying race for context
    # opponent signal names the opponent it rests on
    opp_hint = fired["opponent_any_prior_elected_office__open_contest"]
    assert opp_hint.direction == "negative"
    assert opp_hint.source is not None
    assert opp_hint.source.opponent_name == "Opp"


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
