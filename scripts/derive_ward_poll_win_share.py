#!/usr/bin/env python3
"""Derive inc_win_share for a ward-level poll (spec Part 6).

The simulation's ward-poll override blends a poll-implied incumbent win
probability with the structural estimate. A raw vote share is not a win
probability, so this script converts a poll's topline into P(incumbent wins)
by Monte Carlo, accounting for:

  1. Sampling error on the decided-voter shares (Dirichlet with effective
     n = decided respondents).
  2. The undecided bloc, allocated with high uncertainty (low-concentration
     Dirichlet centred on the decided shares).
  3. The "other" bloc, split across the remaining candidates, none of whom
     individually exceeds the lowest named candidate (else the release would
     have named them).

Recency and sample-size discounting are NOT applied here — the simulation's
alpha_w handles those at run time.

Run: uv run scripts/derive_ward_poll_win_share.py
"""

from __future__ import annotations

import numpy as np

# --- Forum Research, Toronto Centre (Ward 13), June 22-23 2026, n=355, IVR ---
SAMPLE_SIZE = 355
UNDECIDED = 0.45
# Decided-voter shares as published
NAMED = {"moise": 0.35, "tate": 0.19, "stikuts": 0.06}
OTHER = 0.40
# "Other" is split across the remaining field; release names everyone above 6%,
# so no single other candidate exceeds the lowest named share. 5 registered
# challengers remain unnamed; use that many buckets.
N_OTHER_BUCKETS = 5
INCUMBENT = "moise"

# Undecideds are genuinely uncertain four months out: a Dirichlet with this
# concentration centred on the decided shares allows heavy swings (e.g. the
# whole bloc breaking 2:1 against the incumbent is well within its support).
UNDECIDED_CONCENTRATION = 10.0

N_DRAWS = 100_000
SEED = 13


def main() -> None:
    rng = np.random.default_rng(SEED)
    n_decided = SAMPLE_SIZE * (1.0 - UNDECIDED)

    names = list(NAMED.keys()) + [f"other_{i}" for i in range(N_OTHER_BUCKETS)]
    shares = np.array(
        list(NAMED.values()) + [OTHER / N_OTHER_BUCKETS] * N_OTHER_BUCKETS
    )
    inc_idx = names.index(INCUMBENT)

    wins = 0
    for _ in range(N_DRAWS):
        # 1. Sampling error on decided shares
        decided_draw = rng.dirichlet(shares * n_decided)
        # 2. Undecided allocation: centred on the decided draw, very diffuse
        undecided_draw = rng.dirichlet(
            np.maximum(decided_draw, 1e-6) * UNDECIDED_CONCENTRATION
        )
        final = (1.0 - UNDECIDED) * decided_draw + UNDECIDED * undecided_draw
        if final.argmax() == inc_idx:
            wins += 1

    p = wins / N_DRAWS
    print(f"P(incumbent wins | poll) = {p:.3f}  ({N_DRAWS} draws)")
    print(f"Suggested inc_win_share: {round(p, 2)}")


if __name__ == "__main__":
    main()
