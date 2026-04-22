"""Part 7: Simulation Engine.

Runs thousands of Monte Carlo draws to produce win probabilities and
council composition distributions.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd


def inv_logit(x: float) -> float:
    """The sigmoid function: 1 / (1 + exp(-x))."""
    return 1.0 / (1.0 + np.exp(-x))


# Vote-splitting penalty: applied to the strongest challenger when 2+ challengers
# share the same mayoral alignment. Editorial parameter per spec v0.2.
SPLIT_PENALTY = -0.5

# Defeatability threshold below which an incumbent with no viable challengers is "safe"
SAFE_DEFEATABILITY_THRESHOLD = 30

# Win probability assigned directly to safe incumbents (no simulation run)
SAFE_INCUMBENT_WIN_PROB = 0.97

# Endorsement boost for the candidate backed by the departing councillor (open seats)
ENDORSEMENT_BOOST = 1.0

# Additional Gaussian noise applied to each candidate's strength in open seat races
OPEN_SEAT_NOISE_SIGMA = 0.4

# Additional logit noise for by-election incumbents (higher baseline uncertainty per spec Part 2)
BYELECTION_NOISE_SIGMA = 0.4

POLL_HALF_LIFE_DAYS = 12.0
DECAY_LAMBDA = math.log(2) / POLL_HALF_LIFE_DAYS
SAMPLE_SCALE = 400.0
INCUMBENT_CANDIDATE = "chow"

# Coattail strength parameter (gamma), must match coattails.py
from .coattails import COATTAIL_STRENGTH as GAMMA


class WardSimulation:
    def __init__(
        self,
        ward_data: pd.DataFrame,
        mayoral_averages: pd.DataFrame,
        coattails: pd.DataFrame,
        challengers: pd.DataFrame,
        leans: pd.DataFrame,
        n_draws: int = 5000,
        seed: int = 42,
        ward_polls: pd.DataFrame | None = None,
    ):
        """
        ward_data: [ward, councillor_name, is_running, defeatability_score, ...]
        mayoral_averages: [candidate, share]
        coattails: [ward, coattail_adjustment]
        challengers: [ward, candidate_name, name_recognition_tier, mayoral_alignment, ...]
        leans: [ward, candidate, lean]
        ward_polls: Optional ward-level poll data for override (Part 6)
        """
        self.ward_data = ward_data
        self.mayoral_averages = mayoral_averages
        self.coattails = coattails
        self.challengers = challengers
        self.leans = leans
        self.n_draws = n_draws
        self.rng = np.random.default_rng(seed)
        if ward_polls is None:
            self.ward_polls = pd.DataFrame(
                columns=[
                    "ward",
                    "poll_id",
                    "date_published",
                    "sample_size",
                    "inc_win_share",
                    "notes",
                ]
            )
        else:
            self.ward_polls = ward_polls.copy()
            if "date_published" in self.ward_polls.columns:
                self.ward_polls["_parsed_date_published"] = pd.to_datetime(
                    self.ward_polls["date_published"], errors="coerce", utc=True
                )

    def _compute_candidate_strength(
        self, cand: pd.Series, mayoral_mood: dict[str, float], ward_num: int
    ) -> float:
        """Compute mu_j (Stage 2 strength)."""
        tier_baselines = {"well-known": 2.0, "known": 1.0, "unknown": 0.0}
        mu_tier = tier_baselines.get(cand["name_recognition_tier"], 0.0)

        fundraising_bonuses = {
            "high": 0.5,
            "medium": 0.0,
            "low": -0.5,
        }
        mu_tier += fundraising_bonuses.get(cand.get("fundraising_tier", "medium"), 0.0)

        w_a = 2.0
        alignment = cand["mayoral_alignment"]
        boost = 0.0
        if alignment != "unaligned":
            lean_row = self.leans[
                (self.leans["ward"] == ward_num)
                & (self.leans["candidate"] == alignment)
            ]
            if not lean_row.empty:
                lean = lean_row.iloc[0]["lean"]
                mood = mayoral_mood.get(alignment, 0.0)
                boost = w_a * (lean + (mood - 0.20))

        return mu_tier + boost

    def _apply_split_penalties(
        self,
        candidate_strengths: dict[str, float],
        ward_challengers: pd.DataFrame,
    ) -> dict[str, float]:
        """Apply SPLIT_PENALTY to the strongest challenger in each alignment group
        that has 2 or more challengers."""
        adjusted = dict(candidate_strengths)

        # Group challengers by alignment (exclude unaligned)
        alignment_groups: dict[str, list[str]] = {}
        for _, row in ward_challengers.iterrows():
            align = str(row.get("mayoral_alignment", "unaligned"))
            if align == "unaligned":
                continue
            name = row["candidate_name"]
            if name not in candidate_strengths:
                continue
            alignment_groups.setdefault(align, []).append(name)

        for align, names in alignment_groups.items():
            if len(names) < 2:
                continue
            strongest = max(names, key=lambda n: candidate_strengths[n])
            adjusted[strongest] = adjusted[strongest] + SPLIT_PENALTY

        return adjusted

    def _compute_ward_poll_weight(self, ward_num: int) -> tuple[float, float]:
        """Return (alpha_w, poll_inc_win_share) for the most recent ward poll, if any.

        alpha_w decays with poll age (same lambda as mayoral aggregator).
        Returns (0.0, 0.0) if no polls exist for this ward.
        """
        ward_p = self.ward_polls[self.ward_polls["ward"] == ward_num]
        if ward_p.empty:
            return 0.0, 0.0

        if "_parsed_date_published" in ward_p.columns:
            ward_p = ward_p[ward_p["_parsed_date_published"].notna()]
            if ward_p.empty:
                return 0.0, 0.0
            latest = ward_p.loc[ward_p["_parsed_date_published"].idxmax()]
            pub = latest["_parsed_date_published"].to_pydatetime()
        else:
            ward_p = ward_p.copy()
            ward_p["_date"] = pd.to_datetime(ward_p["date_published"], errors="coerce")
            ward_p = ward_p[ward_p["_date"].notna()]
            if ward_p.empty:
                return 0.0, 0.0
            latest = ward_p.sort_values("_date").iloc[-1]
            pub = latest["_date"].to_pydatetime()

        ref = datetime.now(timezone.utc)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        age_days = max(0.0, (ref - pub).total_seconds() / 86400)

        recency_weight = math.exp(-DECAY_LAMBDA * age_days)
        sample_weight = min(1.0, float(latest["sample_size"]) / SAMPLE_SCALE)
        alpha_w = recency_weight * sample_weight

        return alpha_w, float(latest["inc_win_share"])

    def _get_candidate_poll_support(self, ward_num: int) -> dict[str, float]:
        required_columns = {
            "ward",
            "candidate_name",
            "candidate_support",
            "date_published",
            "sample_size",
        }
        if not required_columns.issubset(self.ward_polls.columns):
            return {}

        ward_p = self.ward_polls[self.ward_polls["ward"] == ward_num]
        if ward_p.empty:
            return {}

        ref = datetime.now(timezone.utc)
        weighted_sum: dict[str, float] = {}
        total_weight: dict[str, float] = {}

        for _, r in ward_p.iterrows():
            name = str(r.get("candidate_name", "")).strip()
            if not name:
                continue

            support = r.get("candidate_support")
            if pd.isna(support):
                continue

            pub = r.get("_parsed_date_published")
            if pd.isna(pub):
                pub = pd.to_datetime(r.get("date_published"), errors="coerce", utc=True)
            if pd.isna(pub):
                continue
            pub_dt = pub.to_pydatetime()
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)

            sample_size = r.get("sample_size")
            if pd.isna(sample_size):
                continue

            age_days = max(0.0, (ref - pub_dt).total_seconds() / 86400)
            row_weight = math.exp(-DECAY_LAMBDA * age_days) * min(
                1.0, float(sample_size) / SAMPLE_SCALE
            )
            if row_weight <= 0.0:
                continue

            weighted_sum[name] = (
                weighted_sum.get(name, 0.0) + float(support) * row_weight
            )
            total_weight[name] = total_weight.get(name, 0.0) + row_weight

        out: dict[str, float] = {}
        for name, weight in total_weight.items():
            if weight > 0.0:
                out[name] = weighted_sum[name] / weight

        return out

    def _is_safe_incumbent(
        self, row: pd.Series, ward_challengers: pd.DataFrame
    ) -> bool:
        """Return True if this ward qualifies for the safe incumbent shortcut.

        Conditions (per spec Part 5):
        - Incumbent is running for re-election
        - Defeatability score < SAFE_DEFEATABILITY_THRESHOLD
        - No challengers classified as well-known or known
        """
        if not row["is_running"]:
            return False
        if row["defeatability_score"] >= SAFE_DEFEATABILITY_THRESHOLD:
            return False
        viable_tiers = {"well-known", "known"}
        return not any(
            str(c.get("name_recognition_tier", "unknown")) in viable_tiers
            for _, c in ward_challengers.iterrows()
        )

    def _softmax(self, strengths: list[float]) -> np.ndarray:
        arr = np.array(strengths, dtype=float)
        max_v = float(arr.max()) if arr.size else 0.0
        exp_s = np.exp(arr - max_v)
        total = float(exp_s.sum())
        if total <= 0.0:
            return np.ones(len(strengths), dtype=float) / max(len(strengths), 1)
        return exp_s / total

    def _blend_candidate_probabilities(
        self,
        ward_num: int,
        names: list[str],
        strengths: list[float],
    ) -> np.ndarray:
        structural_probs = self._softmax(strengths)
        candidate_support = self._get_candidate_poll_support(ward_num)
        poll_weights = np.array(
            [max(0.0, candidate_support.get(name, 0.0)) for name in names],
            dtype=float,
        )
        poll_total = float(poll_weights.sum())
        if poll_total <= 0.0:
            return structural_probs

        poll_probs = poll_weights / poll_total
        alpha_w, _ = self._compute_ward_poll_weight(ward_num)
        alpha = min(1.0, max(0.0, float(alpha_w)))
        blended = alpha * poll_probs + (1.0 - alpha) * structural_probs
        total = float(blended.sum())
        if total <= 0.0:
            return structural_probs
        return blended / total

    def _compute_incumbent_polling(self, mayoral_mood: dict[str, float]) -> tuple[float, float]:
        """Return (incumbent_draw, incumbent_avg) for the current simulation draw.

        Used to compute P_w per-draw per the spec:
          P_w = lean * (draw / avg) + avg
        Returns (0.0, 0.0) when incumbent is absent from the polling averages;
        the caller's guard `if inc_avg > 0` handles this by defaulting mood_factor to 1.0.
        """
        avg_series = self.mayoral_averages.loc[
            self.mayoral_averages["candidate"] == INCUMBENT_CANDIDATE, "share"
        ]
        if avg_series.empty:
            return 0.0, 0.0
        avg = float(avg_series.iloc[0])
        draw = float(mayoral_mood.get(INCUMBENT_CANDIDATE, avg))
        return draw, avg

    def run(self) -> dict[str, Any]:
        """Run the Monte Carlo simulation."""

        # 1. Prepare Mayoral Dirichlet
        eff_n = 2000
        candidates = self.mayoral_averages["candidate"].tolist()
        shares = self.mayoral_averages["share"].to_numpy()
        shares = shares / shares.sum()
        alpha = shares * eff_n

        # 2. Results storage
        ward_nums = sorted(self.ward_data["ward"].unique().tolist())
        n_wards = len(ward_nums)
        winner_names = np.empty((self.n_draws, n_wards), dtype=object)
        incumbent_wins_count = np.zeros(self.n_draws)
        mayor_winner_by_draw = np.empty(self.n_draws, dtype=object)

        # Decomposed effects for explanatory factors
        # shape: (n_draws, n_wards)
        vuln_effects = np.zeros((self.n_draws, n_wards))
        coat_effects = np.zeros((self.n_draws, n_wards))
        chal_effects = np.zeros((self.n_draws, n_wards))

        # 3. Main Loop
        for i in range(self.n_draws):
            mayoral_draw = self.rng.dirichlet(alpha)
            mayoral_mood = dict(zip(candidates, mayoral_draw))
            mayor_winner_by_draw[i] = candidates[int(np.argmax(mayoral_draw))]
            inc_draw, inc_avg = self._compute_incumbent_polling(mayoral_mood)

            for ward_idx, ward_num in enumerate(ward_nums):
                row = self.ward_data[self.ward_data["ward"] == ward_num].iloc[0]
                ward_challengers = self.challengers[
                    self.challengers["ward"] == ward_num
                ]

                # Safe incumbent shortcut (spec Part 5): skip simulation for uncontested wards
                if self._is_safe_incumbent(row, ward_challengers):
                    if self.rng.random() < SAFE_INCUMBENT_WIN_PROB:
                        winner_names[i, ward_idx] = row["councillor_name"]
                        incumbent_wins_count[i] += 1
                    else:
                        # Rare 3% upset. Safe wards have only unknown-tier challengers;
                        # we use Generic Challenger rather than computing strength scores
                        # for a ~1-in-33 event that won't materially affect projections.
                        winner_names[i, ward_idx] = "Generic Challenger"
                    continue

                raw_strengths = {
                    c_row["candidate_name"]: self._compute_candidate_strength(
                        c_row, mayoral_mood, ward_num
                    )
                    for _, c_row in ward_challengers.iterrows()
                }
                adjusted_strengths = self._apply_split_penalties(
                    raw_strengths, ward_challengers
                )
                c_strengths_list = list(adjusted_strengths.values())
                f_star = max(c_strengths_list) if c_strengths_list else 0.0

                if not row["is_running"]:
                    # Open seat sub-model (spec Part 5): endorsement boost + wider noise
                    open_strengths: dict[str, float] = {}
                    for _, c_row in ward_challengers.iterrows():
                        base = self._compute_candidate_strength(
                            c_row, mayoral_mood, ward_num
                        )
                        endorsed = bool(c_row.get("is_endorsed_by_departing", False))
                        boost = ENDORSEMENT_BOOST if endorsed else 0.0
                        noise = self.rng.normal(0.0, OPEN_SEAT_NOISE_SIGMA)
                        open_strengths[c_row["candidate_name"]] = base + boost + noise

                    open_strengths = self._apply_split_penalties(
                        open_strengths, ward_challengers
                    )

                    if not open_strengths:
                        winner_names[i, ward_idx] = "Generic Challenger"
                    else:
                        names = list(open_strengths.keys())
                        probs = self._blend_candidate_probabilities(
                            ward_num, names, list(open_strengths.values())
                        )
                        winner_names[i, ward_idx] = self.rng.choice(names, p=probs)
                    continue  # skip incumbent win/loss logic below
                else:
                    # Incumbent ward: fetch coat_row only when needed
                    coat_row = self.coattails[self.coattails["ward"] == ward_num].iloc[0]
                    d_w = row["defeatability_score"]
                    # Per spec Part 3: P_w(draw) = lean * (draw/avg) + avg
                    # This scales the lean component by the incumbent's polling
                    # draw relative to their average, while keeping the base
                    # city-wide term fixed.
                    lean = coat_row["lean"] if "lean" in coat_row.index else 0.0
                    mood_factor = (inc_draw / inc_avg) if inc_avg > 0 else 1.0
                    p_w = lean * mood_factor + inc_avg
                    c_w = coat_row["alignment_delta"] * p_w * GAMMA

                    beta_0 = 4.0
                    beta_1 = -0.05
                    beta_2 = 3.0
                    beta_3 = -0.5

                    # Log components for explanatory factors
                    vuln_effects[i, ward_idx] = beta_1 * d_w
                    coat_effects[i, ward_idx] = beta_2 * c_w
                    chal_effects[i, ward_idx] = beta_3 * f_star

                    z = (
                        beta_0
                        + vuln_effects[i, ward_idx]
                        + coat_effects[i, ward_idx]
                        + chal_effects[i, ward_idx]
                    )
                    if row.get("is_byelection_incumbent", False):
                        z += self.rng.normal(0.0, BYELECTION_NOISE_SIGMA)
                    prob = inv_logit(z)

                    # Part 6: Ward-level polling override
                    alpha_w, poll_p = self._compute_ward_poll_weight(ward_num)
                    if alpha_w > 0.0:
                        prob = alpha_w * poll_p + (1.0 - alpha_w) * prob

                if self.rng.random() < prob:
                    winner_names[i, ward_idx] = row["councillor_name"]
                    incumbent_wins_count[i] += 1
                else:
                    if not c_strengths_list:
                        winner_names[i, ward_idx] = "Generic Challenger"
                    else:
                        names = list(adjusted_strengths.keys())
                        probs = self._blend_candidate_probabilities(
                            ward_num, names, c_strengths_list
                        )
                        winner = self.rng.choice(names, p=probs)
                        winner_names[i, ward_idx] = winner

        # 4. Aggregate Results
        win_probs = {}
        factors = {}
        candidate_win_probs: dict[int, dict[str, float]] = {}
        incumbent_probability_interval: dict[int, dict[str, float]] = {}
        for ward_idx, ward_num in enumerate(ward_nums):
            row = self.ward_data[self.ward_data["ward"] == ward_num].iloc[0]
            counts = pd.Series(winner_names[:, ward_idx]).value_counts(normalize=True)
            candidate_win_probs[ward_num] = {
                str(k): float(v) for k, v in counts.items()
            }

            if not row["is_running"]:
                incumbent_probability_interval[ward_num] = {"low": 0.0, "high": 0.0}
            else:
                draw_vals = (
                    winner_names[:, ward_idx] == row["councillor_name"]
                ).astype(float)
                p_hat = float(draw_vals.mean())
                n = len(draw_vals)
                z = 1.2815515655446004
                se = float(np.sqrt(max(p_hat * (1.0 - p_hat), 0.0) / n))
                low = max(0.0, p_hat - z * se)
                high = min(1.0, p_hat + z * se)
                incumbent_probability_interval[ward_num] = {
                    "low": low,
                    "high": high,
                }

            if not row["is_running"]:
                win_probs[ward_num] = 0.0
                factors[ward_num] = {"vuln": 0.0, "coat": 0.0, "chal": 0.0}
            else:
                win_probs[ward_num] = np.mean(
                    winner_names[:, ward_idx] == row["councillor_name"]
                )
                factors[ward_num] = {
                    "vuln": np.mean(vuln_effects[:, ward_idx]),
                    "coat": np.mean(coat_effects[:, ward_idx]),
                    "chal": np.mean(chal_effects[:, ward_idx]),
                }

        composition_by_mayor: dict[str, dict[str, float | int]] = {}
        for candidate in candidates:
            mask = mayor_winner_by_draw == candidate
            draws = incumbent_wins_count[mask]
            n_draws = int(draws.size)
            if n_draws == 0:
                composition_by_mayor[candidate] = {
                    "mean": 0.0,
                    "std": 0.0,
                    "n_draws": 0,
                }
            else:
                composition_by_mayor[candidate] = {
                    "mean": float(draws.mean()),
                    "std": float(draws.std()),
                    "n_draws": n_draws,
                }

        return {
            "win_probabilities": win_probs,
            "incumbent_probability_interval": incumbent_probability_interval,
            "candidate_win_probabilities": candidate_win_probs,
            "factors": factors,
            "composition_mean": incumbent_wins_count.mean(),
            "composition_std": incumbent_wins_count.std(),
            "composition_by_mayor": composition_by_mayor,
            "composition_dist": incumbent_wins_count,
            "winner_matrix": winner_names,
        }
