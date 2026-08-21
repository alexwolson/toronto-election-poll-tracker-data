"""Shared publication core: Probability Bands, Frequency Statements, and the
Band Stability Gate.

Track-agnostic and pure. It consumes exact internal probabilities and decides
what may be shown; it computes no forecast, assigns no evidence tier, touches no
snapshot, and publishes nothing (ADR 0002 keeps every quantity dark until the
Final Ballot). The Mayoral Forecast and Council Forecast both feed their
Mandatory Sensitivity Variants through it.

Frozen decisions implemented here:
- The Probability Band grid and Frequency Statement wording are ADR 0006 verbatim.
- The Band Stability Gate is ADR 0018: a quantity publishes only when every
  Mandatory Sensitivity Variant lands in the same half-open band and each
  variant's two-sided 95% error interval lies wholly inside it; a variant that
  cannot run fails the gate, and any inter-band boundary touch is Forecast
  Unavailable. Fail-closed (ADR 0032); each quantity is gated independently
  (ADR 0003).

Bands are a presentation rule, not a claim of measured per-band calibration
(ADR 0006); exact probabilities stay internal.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

_ZERO: Final = Decimal(0)
_ONE: Final = Decimal(1)


def _as_decimal(value: Decimal | float | str) -> Decimal:
    # Convert floats through their shortest decimal string so grid boundaries
    # (0.05, 0.15, ...) stay exact instead of drifting via binary float.
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value)


def _as_probability(value: Decimal | float | str) -> Decimal:
    probability = _as_decimal(value)
    if probability < _ZERO or probability > _ONE:
        raise ValueError(f"probability {probability} is outside [0, 1]")
    return probability


@dataclass(frozen=True, slots=True)
class ProbabilityBand:
    """One fixed, pre-declared band of the ADR 0006 grid (fractions of 1)."""

    lower: Decimal
    upper: Decimal
    upper_inclusive: bool
    label: str
    frequency_statement: str

    def contains(self, probability: Decimal) -> bool:
        if probability < self.lower:
            return False
        if self.upper_inclusive:
            return probability <= self.upper
        return probability < self.upper


def _band(lower: str, upper: str, upper_inclusive: bool, label: str, freq: str):
    return ProbabilityBand(Decimal(lower), Decimal(upper), upper_inclusive, label, freq)


# ADR 0006 grid, verbatim: 0–<5% "less than 1 in 10", 5–<15% "about 1 in 10",
# successive centred ten-point bands through 85–<95% "about 9 in 10", and
# 95–100% "more than 9 in 10". Frozen (ADR 0005).
PROBABILITY_BAND_GRID: Final[tuple[ProbabilityBand, ...]] = (
    _band("0", "0.05", False, "0–<5%", "less than 1 in 10"),
    _band("0.05", "0.15", False, "5–<15%", "about 1 in 10"),
    _band("0.15", "0.25", False, "15–<25%", "about 2 in 10"),
    _band("0.25", "0.35", False, "25–<35%", "about 3 in 10"),
    _band("0.35", "0.45", False, "35–<45%", "about 4 in 10"),
    _band("0.45", "0.55", False, "45–<55%", "about 5 in 10"),
    _band("0.55", "0.65", False, "55–<65%", "about 6 in 10"),
    _band("0.65", "0.75", False, "65–<75%", "about 7 in 10"),
    _band("0.75", "0.85", False, "75–<85%", "about 8 in 10"),
    _band("0.85", "0.95", False, "85–<95%", "about 9 in 10"),
    _band("0.95", "1", True, "95–100%", "more than 9 in 10"),
)


# Coarse out-of-five grid (ADR 0049): the same shape at half the resolution, with
# "N in 5" frequency wording. The finest-stable-band rule publishes an out-of-ten
# band when every variant agrees at that resolution and falls back to this coarser
# grid when they agree only here — a true, robust statement at the resolution the
# evidence supports, rather than nothing. Frozen (ADR 0005).
PROBABILITY_BAND_GRID_FIVE: Final[tuple[ProbabilityBand, ...]] = (
    _band("0", "0.10", False, "0–<10%", "less than 1 in 5"),
    _band("0.10", "0.30", False, "10–<30%", "about 1 in 5"),
    _band("0.30", "0.50", False, "30–<50%", "about 2 in 5"),
    _band("0.50", "0.70", False, "50–<70%", "about 3 in 5"),
    _band("0.70", "0.90", False, "70–<90%", "about 4 in 5"),
    _band("0.90", "1", True, "90–100%", "more than 4 in 5"),
)

# Finest first: the gate returns the first grid on which every variant agrees.
_BAND_GRIDS: Final[tuple[tuple[ProbabilityBand, ...], ...]] = (
    PROBABILITY_BAND_GRID,
    PROBABILITY_BAND_GRID_FIVE,
)


def band_for(
    probability: Decimal | float | str,
    grid: tuple[ProbabilityBand, ...] = PROBABILITY_BAND_GRID,
) -> ProbabilityBand:
    """Map an exact probability in [0, 1] to its half-open Probability Band."""
    p = _as_probability(probability)
    for band in grid:
        if band.contains(p):
            return band
    raise AssertionError(  # pragma: no cover - grid covers [0, 1] exhaustively
        f"no band contains probability {p}"
    )


@dataclass(frozen=True, slots=True)
class ErrorInterval:
    """A two-sided numerical / Monte Carlo error interval on a probability."""

    lower: Decimal
    upper: Decimal

    def __post_init__(self) -> None:
        for bound in (self.lower, self.upper):
            if bound < _ZERO or bound > _ONE:
                raise ValueError(f"error-interval bound {bound} is outside [0, 1]")
        if self.lower > self.upper:
            raise ValueError("error-interval lower bound exceeds its upper bound")


@dataclass(frozen=True, slots=True)
class SensitivityVariant:
    """A Mandatory Sensitivity Variant's contribution to the stability gate.

    ``probability`` is None exactly when the variant could not be computed; such
    a variant fails the gate and is never silently omitted (ADR 0018).
    """

    label: str
    probability: Decimal | None
    error_interval: ErrorInterval | None

    def __post_init__(self) -> None:
        if self.probability is None:
            return
        if self.probability < _ZERO or self.probability > _ONE:
            raise ValueError(f"probability {self.probability} is outside [0, 1]")
        if self.error_interval is None:
            raise ValueError("a runnable variant must carry an error interval")
        if not (
            self.error_interval.lower <= self.probability <= self.error_interval.upper
        ):
            raise ValueError("variant probability lies outside its own error interval")

    def can_run(self) -> bool:
        return self.probability is not None


def unavailable_variant(label: str) -> SensitivityVariant:
    """A variant that could not be computed — fails the gate by construction."""
    return SensitivityVariant(label=label, probability=None, error_interval=None)


@dataclass(frozen=True, slots=True)
class PublicationDecision:
    """The gate outcome: a published band, or Forecast Unavailable with a reason."""

    band: ProbabilityBand | None
    reason: str

    @property
    def is_published(self) -> bool:
        return self.band is not None


def _unavailable(reason: str) -> PublicationDecision:
    return PublicationDecision(band=None, reason=reason)


def _interval_within_band(interval: ErrorInterval, band: ProbabilityBand) -> bool:
    # Strict interior on inter-band boundaries; the outer probability limits
    # (0 and 1) are exempt because no adjacent band makes the assignment
    # ambiguous there (ADR 0018 "boundary touch").
    lower_ok = (
        interval.lower >= band.lower
        if band.lower == _ZERO
        else interval.lower > band.lower
    )
    upper_ok = (
        interval.upper <= band.upper
        if band.upper_inclusive
        else interval.upper < band.upper
    )
    return lower_ok and upper_ok


def _consensus_on_grid(
    variants: tuple[SensitivityVariant, ...],
    grid: tuple[ProbabilityBand, ...],
) -> tuple[ProbabilityBand | None, str]:
    """The consensus band on one grid if every variant lands in it with its 95%
    interval inside; otherwise (None, the first disagreement's reason)."""
    consensus = band_for(variants[0].probability, grid)
    for variant in variants:
        band = band_for(variant.probability, grid)
        if band != consensus:
            return None, (
                f"variant {variant.label!r} lands in {band.label}, not "
                f"{consensus.label}"
            )
    for variant in variants:
        assert variant.error_interval is not None  # runnable => interval present
        if not _interval_within_band(variant.error_interval, consensus):
            return None, (
                f"variant {variant.label!r} 95% error interval touches a band boundary"
            )
    return consensus, ""


def evaluate_band_stability(
    variants: Iterable[SensitivityVariant],
) -> PublicationDecision:
    """Apply the ADR 0018 Band Stability Gate at the finest resolution that holds:
    the out-of-ten grid, then the coarser out-of-five grid (ADR 0049). A quantity
    publishes the finest band on which every variant agrees (with its 95% interval
    inside); if even the coarse grid is straddled, it is Forecast Unavailable."""
    variants = tuple(variants)
    if not variants:
        return _unavailable("no sensitivity variants supplied")

    for variant in variants:
        if not variant.can_run():
            return _unavailable(f"variant {variant.label!r} could not be computed")

    reason = ""
    for grid in _BAND_GRIDS:
        band, reason = _consensus_on_grid(variants, grid)
        if band is not None:
            return PublicationDecision(band=band, reason="")
    return _unavailable(reason)
