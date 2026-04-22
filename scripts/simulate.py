#!/usr/bin/env python3
"""Run the projection simulation using processed data.

Run: uv run scripts/simulate.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from src.simulation import WardSimulation

PROCESSED = Path("data/processed")


def main() -> None:
    # 1. Load Data
    ward_data = pd.read_csv(PROCESSED / "ward_defeatability.csv")
    mayoral_averages = pd.read_csv(PROCESSED / "mayoral_polling_average.csv")
    coattails = pd.read_csv(PROCESSED / "coattail_adjustments.csv")
    challengers = pd.read_csv(PROCESSED / "challengers.csv")
    leans = pd.read_csv(PROCESSED / "ward_mayoral_lean.csv")
    
    # 2. Run Simulation
    print(f"Running simulation with {mayoral_averages.shape[0]} candidates...")
    sim = WardSimulation(
        ward_data, 
        mayoral_averages, 
        coattails, 
        challengers, 
        leans,
        n_draws=10000
    )
    results = sim.run()
    
    # 3. Print Report
    print("\n--- Ward Projections ---")
    win_probs = results["win_probabilities"]
    winner_matrix = results["winner_matrix"]
    factors = results["factors"]
    
    report_df = ward_data[["ward", "councillor_name", "is_running"]].copy()
    report_df["win_prob"] = report_df["ward"].map(win_probs)
    
    # Identify most likely winner per ward
    likely_winners = []
    for ward_idx in range(25):
        winners = winner_matrix[:, ward_idx]
        unique, counts = np.unique(winners, return_counts=True)
        winner = unique[np.argmax(counts)]
        winner_prob = counts.max() / len(winners)
        likely_winners.append((winner, winner_prob))
    
    report_df["likely_winner"] = [w[0] for w in likely_winners]
    report_df["likely_winner_prob"] = [w[1] for w in likely_winners]
    
    # Add factors
    report_df["f_vuln"] = report_df["ward"].apply(lambda w: factors[w]["vuln"])
    report_df["f_coat"] = report_df["ward"].apply(lambda w: factors[w]["coat"])
    report_df["f_chal"] = report_df["ward"].apply(lambda w: factors[w]["chal"])
    
    # Classification logic as per Part 5
    def classify(row: pd.Series) -> str:
        if not row["is_running"]: return "Open Seat"
        prob = row["win_prob"]
        if prob > 0.90: return "Safe Incumbent"
        if prob > 0.70: return "Leaning Incumbent"
        if prob > 0.30: return "Competitive / Toss-up"
        if prob > 0.10: return "Leaning Challenger"
        return "Likely Loss"
    
    report_df["classification"] = report_df.apply(classify, axis=1)
    report_df = report_df.sort_values("win_prob")
    
    header = (
        f"{'Ward':<4} | {'Incumbent':<20} | {'Inc. %':<7} | "
        f"{'Vuln':>5} | {'Coat':>5} | {'Chal':>5} | "
        f"{'Likely Winner':<22} | {'Classification'}"
    )
    print(header)
    print("-" * len(header))
    for _, row in report_df.iterrows():
        # Format factors: + or - to show direction
        f_v = f"{row['f_vuln']:+4.1f}"
        f_co = f"{row['f_coat']:+4.1f}"
        f_ch = f"{row['f_chal']:+4.1f}"
        
        print(
            f"{row['ward']:<4} | {row['councillor_name']:<20} | "
            f"{row['win_prob']:>6.1%} | "
            f"{f_v:>5} | {f_co:>5} | {f_ch:>5} | "
            f"{row['likely_winner']:<22} | "
            f"{row['classification']}"
        )
        
    print("\n--- Citywide Council Composition ---")
    print(f"Mean Incumbents Returning: {results['composition_mean']:.1f} / 25")
    print(f"Standard Deviation:        {results['composition_std']:.1f}")
    
    ci_low = int(pd.Series(results["composition_dist"]).quantile(0.025))
    ci_high = int(pd.Series(results["composition_dist"]).quantile(0.975))
    print(f"95% Confidence Interval:  [{ci_low}, {ci_high}]")


if __name__ == "__main__":
    main()
