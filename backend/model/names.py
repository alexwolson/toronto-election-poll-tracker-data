"""Canonical candidate name registry.

All candidate name variations map to a short lowercase key used
consistently across all processed data.
"""

_REGISTRY: dict[str, str] = {
    # Olivia Chow
    "olivia chow": "chow",
    "chow olivia": "chow",
    "o. chow": "chow",
    "chow": "chow",
    # Brad Bradford
    "brad bradford": "bradford",
    "bradford brad": "bradford",
    "bradford": "bradford",
    # Ana Bailao
    "ana bailão": "bailao",
    "bailão ana": "bailao",
    "ana bailao": "bailao",
    "bailao ana": "bailao",
    "ana bailo": "bailao",
    "bailao": "bailao",
    # Josh Matlow
    "josh matlow": "matlow",
    "matlow josh": "matlow",
    "matlow": "matlow",
    # Anthony Furey
    "anthony furey": "furey",
    "furey anthony": "furey",
    "furey": "furey",
    # Marco Mendicino
    "marco mendicino": "mendicino",
    "mendicino marco": "mendicino",
    "mendicino": "mendicino",
    # John Tory
    "john tory": "tory",
    "tory john": "tory",
    "j. tory": "tory",
    "tory": "tory",
}

# Used by the ingestion pipeline to validate candidate columns in poll data.
KNOWN_CANDIDATES = sorted(set(_REGISTRY.values()))


class CanonicalNameError(ValueError):
    pass


def canonical_name(name: str) -> str:
    """Return the canonical key for a candidate name.

    Raises CanonicalNameError if the name is not recognised.
    """
    key = name.strip().lower()
    if key not in _REGISTRY:
        raise CanonicalNameError(
            f"Unrecognised candidate name: {name!r}. "
            f"Add it to backend/model/names.py if it is a valid variation."
        )
    return _REGISTRY[key]
