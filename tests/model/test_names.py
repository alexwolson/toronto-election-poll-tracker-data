"""Tests for the canonical candidate name registry."""

from __future__ import annotations

import pytest

from backend.model.names import KNOWN_CANDIDATES, CanonicalNameError, canonical_name


@pytest.mark.parametrize(
    "variation",
    [
        "Chris Alexander",
        "chris alexander",
        "Alexander Chris",
        "Alexander",
        "  alexander ",
    ],
)
def test_canonical_name_resolves_alexander_variations(variation):
    assert canonical_name(variation) == "alexander"


def test_alexander_in_known_candidates():
    assert "alexander" in KNOWN_CANDIDATES


def test_canonical_name_rejects_unknown():
    with pytest.raises(CanonicalNameError):
        canonical_name("Nobody At All")
