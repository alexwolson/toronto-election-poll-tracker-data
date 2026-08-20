from datetime import UTC, date, datetime
from decimal import Decimal

from backend.model.mayoral_evidence_tier import (
    MayoralEvidenceTier,
    MayoralPollSampleEvidence,
    classify_mayoral_evidence_tier,
)
from backend.model.mayoral_publication import (
    Availability,
    compose_mayoral_quantity_publication,
)
from backend.model.mayoral_publication_gates import (
    CHALLENGER_WIN,
    CLOSE_RESULT,
    INCUMBENT_DEFEAT,
)
from backend.model.publication import (
    ErrorInterval,
    SensitivityVariant,
    unavailable_variant,
)

NOM = datetime(2026, 8, 21, 18, 0, tzinfo=UTC)
D = Decimal


def _tier(samples):
    return classify_mayoral_evidence_tier(samples, nomination_close=NOM)


def _s(sid, pollster, end, measured=("chow", "bradford")):
    return MayoralPollSampleEvidence(sid, pollster, end, frozenset(measured))


def _variant(label, p, lo, hi):
    return SensitivityVariant(
        label=label,
        probability=D(p),
        error_interval=ErrorInterval(lower=D(lo), upper=D(hi)),
    )


def _agreeing():
    return [
        _variant("base", "0.50", "0.47", "0.53"),
        _variant("tail-high", "0.51", "0.48", "0.54"),
    ]


def test_pre_final_close_result_is_unavailable_and_shows_m1() -> None:
    # The live 2026 case: everything pre-Final, so no predictive quantity publishes.
    tier = _tier([_s("a", "Forum", date(2026, 8, 5))])
    pub = compose_mayoral_quantity_publication(
        CLOSE_RESULT, tier, race_has_incumbent=True, variants=_agreeing()
    )
    assert pub.availability is Availability.UNAVAILABLE
    assert pub.tier is MayoralEvidenceTier.M1_PRE_FINAL  # tier shown regardless
    assert pub.band is None


def test_open_seat_incumbent_defeat_is_not_applicable() -> None:
    tier = _tier([_s("a", "Forum", date(2026, 9, 20))])  # M2
    pub = compose_mayoral_quantity_publication(
        INCUMBENT_DEFEAT, tier, race_has_incumbent=False, variants=_agreeing()
    )
    assert pub.availability is Availability.NOT_APPLICABLE
    assert pub.band is None


def test_m2_close_result_publishes_a_band_when_variants_agree() -> None:
    tier = _tier([_s("a", "Forum", date(2026, 9, 20))])  # M2
    pub = compose_mayoral_quantity_publication(
        CLOSE_RESULT, tier, race_has_incumbent=True, variants=_agreeing()
    )
    assert pub.availability is Availability.AVAILABLE
    assert pub.tier is MayoralEvidenceTier.M2_POST_FINAL
    assert pub.band is not None
    assert pub.band.label == "45–<55%"


def test_m2_unavailable_when_variants_disagree_on_band() -> None:
    tier = _tier([_s("a", "Forum", date(2026, 9, 20))])  # M2
    pub = compose_mayoral_quantity_publication(
        CLOSE_RESULT,
        tier,
        race_has_incumbent=True,
        variants=[
            _variant("base", "0.53", "0.51", "0.54"),
            _variant("tail-high", "0.62", "0.60", "0.64"),  # different band
        ],
    )
    assert pub.availability is Availability.UNAVAILABLE
    assert pub.band is None


def test_unlocked_but_no_variants_fails_closed() -> None:
    # ADR 0032: an unlocked quantity with no computable variants is unavailable.
    tier = _tier([_s("a", "Forum", date(2026, 9, 20))])  # M2
    pub = compose_mayoral_quantity_publication(
        CLOSE_RESULT, tier, race_has_incumbent=True, variants=[]
    )
    assert pub.availability is Availability.UNAVAILABLE


def test_unlocked_but_a_variant_cannot_run_fails_closed() -> None:
    tier = _tier([_s("a", "Forum", date(2026, 9, 20))])  # M2
    pub = compose_mayoral_quantity_publication(
        CLOSE_RESULT,
        tier,
        race_has_incumbent=True,
        variants=[
            _variant("base", "0.50", "0.47", "0.53"),
            unavailable_variant("leave-one-out"),
        ],
    )
    assert pub.availability is Availability.UNAVAILABLE
    assert "leave-one-out" in pub.reason


def test_m3_challenger_win_publishes_for_a_measured_challenger() -> None:
    samples = [
        _s("a", "Forum", date(2026, 9, 15), ("chow", "bradford")),
        _s("b", "Liaison", date(2026, 9, 20), ("chow", "bradford")),
        _s("c", "Mainstreet", date(2026, 9, 22), ("chow", "bradford")),
    ]
    tier = _tier(samples)
    pub = compose_mayoral_quantity_publication(
        CHALLENGER_WIN,
        tier,
        race_has_incumbent=True,
        candidate_id="bradford",
        variants=_agreeing(),
    )
    assert pub.availability is Availability.AVAILABLE
    assert pub.tier is MayoralEvidenceTier.M3_REPLICATED_POST_FINAL
    assert pub.candidate_id == "bradford"


def test_m3_challenger_win_unavailable_for_an_unmeasured_challenger() -> None:
    samples = [
        _s("a", "Forum", date(2026, 9, 15), ("chow", "bradford")),
        _s("b", "Liaison", date(2026, 9, 20), ("chow", "bradford")),
        _s("c", "Mainstreet", date(2026, 9, 22), ("chow", "bradford")),
    ]
    tier = _tier(samples)  # field-level M3, but alexander measured in none
    pub = compose_mayoral_quantity_publication(
        CHALLENGER_WIN,
        tier,
        race_has_incumbent=True,
        candidate_id="alexander",
        variants=_agreeing(),
    )
    assert pub.availability is Availability.UNAVAILABLE
    assert pub.tier is MayoralEvidenceTier.M3_REPLICATED_POST_FINAL
