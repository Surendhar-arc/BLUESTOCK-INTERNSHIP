"""
Bluestock Fintech — Simple Fund Recommender
Capstone Project I — Mutual Fund Analytics
Author: Surendhar
Usage: python recommender.py
"""

import pandas as pd

perf = pd.read_csv("data/scheme_performance.csv")

def recommend_funds(risk_appetite):
    """
    Simple fund recommender based on risk appetite.
    Input: risk_appetite — 'Low', 'Moderate', or 'High'
    Output: Top 3 funds by Sharpe ratio within matching risk_grade
    """
    risk_map = {
        "Low": ["Low"],
        "Moderate": ["Moderate"],
        "High": ["High", "Very High"]
    }

    if risk_appetite not in risk_map:
        print("Invalid input. Please enter Low, Moderate, or High.")
        return None

    matching_grades = risk_map[risk_appetite]
    filtered = perf[perf["risk_grade"].isin(matching_grades)]
    top3 = filtered.nlargest(3, "sharpe_ratio")[
        ["scheme_name","fund_house","category",
         "sharpe_ratio","risk_grade","expense_ratio_pct"]
    ].reset_index(drop=True)
    top3.index += 1
    return top3

if __name__ == "__main__":
    print("=" * 60)
    print("BLUESTOCK FINTECH — MUTUAL FUND RECOMMENDER")
    print("=" * 60)
    risk = input("\nEnter your risk appetite (Low / Moderate / High): ").strip().title()
    result = recommend_funds(risk)
    if result is not None:
        print(f"\nTop 3 Recommended Funds for {risk} Risk Appetite:")
        print(result.to_string())
