from decimal import Decimal

import pytest

from backend.model.publication import (
    PROBABILITY_BAND_GRID,
    ErrorInterval,
    SensitivityVariant,
    band_for,
    evaluate_band_stability,
    unavailable_variant,
)

D = Decimal


def test_grid_matches_adr_0006_verbatim() -> None:
    # 11 half-open bands, closed only at 100; the frequency statements are the
    # exact ADR 0006 wording.
    expected = [
        ("0", "0.05", False, "0–<5%", "less than 1 in 10"),
        ("0.05", "0.15", False, "5–<15%", "about 1 in 10"),
        ("0.15", "0.25", False, "15–<25%", "about 2 in 10"),
        ("0.25", "0.35", False, "25–<35%", "about 3 in 10"),
        ("0.35", "0.45", False, "35–<45%", "about 4 in 10"),
        ("0.45", "0.55", False, "45–<55%", "about 5 in 10"),
        ("0.55", "0.65", False, "55–<65%", "about 6 in 10"),
        ("0.65", "0.75", False, "65–<75%", "about 7 in 10"),
        ("0.75", "0.85", False, "75–<85%", "about 8 in 10"),
        ("0.85", "0.95", False, "85–<95%", "about 9 in 10"),
        ("0.95", "1", True, "95–100%", "more than 9 in 10"),
    ]
    assert len(PROBABILITY_BAND_GRID) == 11
    for band, (lo, hi, incl, label, freq) in zip(PROBABILITY_BAND_GRID, expected):
        assert band.lower == D(lo)
        assert band.upper == D(hi)
        assert band.upper_inclusive is incl
        assert band.label == label
        assert band.frequency_statement == freq


def test_band_for_is_half_open_and_closed_only_at_one() -> None:
    assert band_for(D("0")).label == "0–<5%"
    assert band_for(D("0.049")).label == "0–<5%"
    assert band_for(D("0.05")).label == "5–<15%"  # boundary lands in the upper band
    assert band_for(D("0.15")).label == "15–<25%"
    assert band_for(D("0.5")).label == "45–<55%"
    assert band_for(D("0.9499")).label == "85–<95%"
    assert band_for(D("0.95")).label == "95–100%"
    assert band_for(D("1")).label == "95–100%"  # closed at 100


def test_band_for_accepts_float_at_boundaries_without_drift() -> None:
    # 0.15 as a float must still land in [15,25), not [5,15) via binary drift.
    assert band_for(0.15).label == "15–<25%"
    assert band_for(0.95).label == "95–100%"


def test_band_for_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        band_for(D("-0.01"))
    with pytest.raises(ValueError):
        band_for(D("1.01"))


def _variant(label, p, lo, hi):
    return SensitivityVariant(
        label=label,
        probability=D(p),
        error_interval=ErrorInterval(lower=D(lo), upper=D(hi)),
    )


def test_publishes_when_variants_agree_and_intervals_strictly_inside() -> None:
    decision = evaluate_band_stability(
        [
            _variant("primary", "0.50", "0.47", "0.53"),
            _variant("regular-only", "0.51", "0.48", "0.54"),
            _variant("incumbency", "0.49", "0.46", "0.52"),
        ]
    )
    assert decision.is_published
    assert decision.band.label == "45–<55%"
    assert decision.band.frequency_statement == "about 5 in 10"
    assert decision.reason == ""


def test_unavailable_when_variants_disagree_on_band() -> None:
    decision = evaluate_band_stability(
        [
            _variant("primary", "0.53", "0.51", "0.54"),
            _variant("incumbency", "0.57", "0.56", "0.58"),  # different band
        ]
    )
    assert not decision.is_published
    assert "incumbency" in decision.reason


def test_unavailable_on_interband_boundary_touch() -> None:
    # error interval touches the 55% inter-band boundary from inside.
    decision = evaluate_band_stability([_variant("primary", "0.53", "0.50", "0.55")])
    assert not decision.is_published
    assert "boundary" in decision.reason.lower()


def test_touch_at_outer_probability_limits_is_allowed() -> None:
    top = evaluate_band_stability(
        [_variant("primary", "0.99", "0.97", "1")]  # touches 1.0, outer limit
    )
    assert top.is_published
    assert top.band.label == "95–100%"
    bottom = evaluate_band_stability(
        [_variant("primary", "0.02", "0", "0.04")]  # touches 0, outer limit
    )
    assert bottom.is_published
    assert bottom.band.label == "0–<5%"


def test_fails_closed_when_a_variant_cannot_run() -> None:
    decision = evaluate_band_stability(
        [
            _variant("primary", "0.50", "0.47", "0.53"),
            unavailable_variant("leave-one-pollster-out"),
        ]
    )
    assert not decision.is_published
    assert "leave-one-pollster-out" in decision.reason


def test_fails_closed_on_empty_variant_set() -> None:
    decision = evaluate_band_stability([])
    assert not decision.is_published
    assert decision.band is None


def test_error_interval_rejects_inverted_or_out_of_range_bounds() -> None:
    with pytest.raises(ValueError):
        ErrorInterval(lower=D("0.6"), upper=D("0.4"))
    with pytest.raises(ValueError):
        ErrorInterval(lower=D("-0.1"), upper=D("0.4"))


def test_runnable_variant_must_contain_its_point_and_carry_an_interval() -> None:
    with pytest.raises(ValueError):
        SensitivityVariant(
            label="p",
            probability=D("0.5"),
            error_interval=ErrorInterval(lower=D("0.6"), upper=D("0.7")),
        )
    with pytest.raises(ValueError):
        SensitivityVariant(label="p", probability=D("0.5"), error_interval=None)
