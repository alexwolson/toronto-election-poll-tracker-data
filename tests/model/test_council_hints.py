from pathlib import Path

from backend.model.council_hints import (
    CandidacyRecord,
    CandidateFeatures,
    candidate_features,
    fire_candidate_hints,
    load_supported_hints,
    resolve_person_id,
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
