from pathlib import Path

from backend.model.council_biography import (
    build_all_biographies,
    build_candidate_biography,
    load_council_results,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/raw/canonical/toronto_election_results.csv"


def _results():
    return load_council_results(RESULTS)


def test_multi_term_councillor_record_spans_the_boundary_change() -> None:
    # John Filion: won 2003/2006/2010/2014 in ward 23 (44-ward) and 2018 in ward
    # 18 (25-ward) — one identity across the redraw.
    bio = build_candidate_biography("c00755", _results())
    assert bio.council_wins == 5
    assert bio.is_former_councillor
    assert len(bio.appearances) == 5
    assert bio.most_recent_win.year == 2018
    assert bio.most_recent_win.ward == "18"
    assert [a.year for a in bio.appearances] == sorted(a.year for a in bio.appearances)


def test_returning_former_councillor_record() -> None:
    # Mike Layton: 2010/2014 ward 19 (44-ward), 2018 ward 11 (25-ward); best 2014.
    bio = build_candidate_biography("c01140", _results())
    assert bio.council_wins == 3
    assert bio.most_recent_win.year == 2018
    assert bio.most_recent_win.ward == "11"
    assert bio.best_result.year == 2014
    assert 0.83 <= bio.best_result.vote_share <= 0.84


def test_identity_is_exact_key_and_does_not_conflate_by_surname() -> None:
    # 'clayton jones' is a different person (canonical candidate_id c00487);
    # candidate_id identity must never pull that 2014 ward-39 row into Layton.
    bio = build_candidate_biography("c01140", _results())
    assert all(a.ward in {"19", "11"} for a in bio.appearances)
    assert not any(a.year == 2014 and a.ward == "39" for a in bio.appearances)


def test_single_term_incumbent_record() -> None:
    bio = build_candidate_biography("c00665", _results())
    assert bio.council_wins == 1
    assert len(bio.appearances) == 1
    assert bio.most_recent_win.year == 2022
    assert bio.most_recent_win.ward == "11"


def test_unknown_candidate_has_an_empty_biography() -> None:
    bio = build_candidate_biography("nobody atall", _results())
    assert bio.appearances == ()
    assert bio.council_wins == 0
    assert not bio.is_former_councillor
    assert bio.most_recent_win is None
    assert bio.best_result is None


def test_build_all_biographies_covers_every_distinct_candidate() -> None:
    results = _results()
    bios = build_all_biographies(results)
    assert "c00755" in bios
    assert "c01140" in bios
    assert len(bios) == len({r.candidate_id for r in results})
    # a built biography contains exactly that key's appearances
    assert bios["c00755"].council_wins == 5


def test_appearance_fields_are_typed_and_faithful() -> None:
    bio = build_candidate_biography("c00665", _results())
    a = bio.appearances[0]
    assert isinstance(a.year, int) and isinstance(a.votes, int)
    assert isinstance(a.is_winner, bool)
    assert a.boundary_era == "25-ward"
    assert a.votes == 8614
    assert 0.35 <= a.vote_share <= 0.36
