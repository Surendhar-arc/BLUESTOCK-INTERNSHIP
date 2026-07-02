"""
Bluestock Fintech — Data Analyst Internship Cohort 2025
Capstone Project I — Mutual Fund Analytics
Advanced Analytics + Risk Metrics
Author: Surendhar
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import warnings
import os

warnings.filterwarnings("ignore")
os.makedirs("charts", exist_ok=True)
sns.set_theme(style="darkgrid")

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
nav = pd.read_csv("data/nav_history.csv", parse_dates=["date"])
perf = pd.read_csv("data/scheme_performance.csv")
txn = pd.read_csv("data/investor_transactions.csv", parse_dates=["transaction_date"])
holdings = pd.read_csv("data/portfolio_holdings.csv")

nav = nav.sort_values(["amfi_code","date"]).reset_index(drop=True)
nav = nav.merge(perf[["amfi_code","scheme_name","risk_grade","sharpe_ratio","category"]], on="amfi_code", how="left")
nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
nav = nav.dropna(subset=["daily_return"])

print("Data loaded!")
print(f"NAV: {nav.shape} | Txn: {txn.shape} | Perf: {perf.shape} | Holdings: {holdings.shape}")

# ─────────────────────────────────────────────
# TASK 1 — Historical VaR (95%) and CVaR
# ─────────────────────────────────────────────
print("\n[Task 1] Computing Historical VaR and CVaR...")

var_results = []
for code, group in nav.groupby("amfi_code"):
    returns = group["daily_return"].dropna()
    name = group["scheme_name"].iloc[0]
    var_95 = np.percentile(returns, 5)
    cvar_95 = returns[returns <= var_95].mean()
    var_results.append({
        "amfi_code": code,
        "scheme_name": name,
        "var_95_pct": round(var_95 * 100, 4),
        "cvar_95_pct": round(cvar_95 * 100, 4),
        "risk_grade": group["risk_grade"].iloc[0]
    })

var_df = pd.DataFrame(var_results).sort_values("var_95_pct")
var_df.to_csv("var_cvar_report.csv", index=False)
print("Top 5 Highest VaR Funds:")
print(var_df.head(5)[["scheme_name","var_95_pct","cvar_95_pct"]].to_string(index=False))
print("Saved: var_cvar_report.csv")

# ─────────────────────────────────────────────
# TASK 2 — Rolling 90-day Sharpe Ratio
# ─────────────────────────────────────────────
print("\n[Task 2] Computing Rolling 90-day Sharpe...")

RF_daily = 0.065 / 252
top5_codes = perf.nlargest(5, "sharpe_ratio")["amfi_code"].tolist()
top5_names = perf.nlargest(5, "sharpe_ratio")["scheme_name"].tolist()

fig, ax = plt.subplots(figsize=(16, 7))
colors = plt.cm.tab10(np.linspace(0, 0.5, 5))

for i, (code, name) in enumerate(zip(top5_codes, top5_names)):
    fund_data = nav[nav["amfi_code"] == code].sort_values("date")
    returns = fund_data.set_index("date")["daily_return"]
    rolling_sharpe = (
        returns.rolling(90).mean() - RF_daily
    ) / returns.rolling(90).std() * np.sqrt(252)
    ax.plot(rolling_sharpe.index, rolling_sharpe.values,
            lw=1.8, color=colors[i], label=name[:30])

ax.axhline(y=0, color="black", linestyle="--", lw=1, alpha=0.5)
ax.set_title("Rolling 90-Day Sharpe Ratio — Top 5 Funds", fontsize=14, fontweight="bold")
ax.set_xlabel("Date")
ax.set_ylabel("Rolling Sharpe Ratio")
ax.legend(loc="upper left", fontsize=8)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("charts/rolling_sharpe_chart.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: charts/rolling_sharpe_chart.png")

# ─────────────────────────────────────────────
# TASK 3 — Investor Cohort Analysis
# ─────────────────────────────────────────────
print("\n[Task 3] Investor Cohort Analysis...")

sip = txn[txn["transaction_type"] == "SIP"].copy()
txn["first_year"] = txn.groupby("investor_id")["transaction_date"].transform("min").dt.year

cohort = txn.groupby(["investor_id","first_year"]).agg(
    total_invested=("amount_inr","sum"),
    sip_count=("transaction_type","count")
).reset_index()

sip_cohort = sip.groupby("investor_id").agg(
    avg_sip=("amount_inr","mean")
).reset_index()

cohort = cohort.merge(sip_cohort, on="investor_id", how="left")

top_fund_per_investor = txn.groupby(["investor_id","amfi_code"])["amount_inr"].sum().reset_index()
top_fund_per_investor = top_fund_per_investor.sort_values("amount_inr", ascending=False)
top_fund_per_investor = top_fund_per_investor.drop_duplicates(subset="investor_id")
top_fund_per_investor = top_fund_per_investor.merge(perf[["amfi_code","scheme_name"]], on="amfi_code", how="left")

cohort = cohort.merge(top_fund_per_investor[["investor_id","scheme_name"]], on="investor_id", how="left")
cohort = cohort.rename(columns={"scheme_name":"top_fund_preference"})

cohort_summary = cohort.groupby("first_year").agg(
    total_investors=("investor_id","count"),
    avg_sip_amount=("avg_sip","mean"),
    avg_total_invested=("total_invested","mean"),
    top_fund=("top_fund_preference", lambda x: x.mode()[0] if len(x) > 0 else "N/A")
).reset_index()

print("Investor Cohort Summary:")
print(cohort_summary.to_string(index=False))

# ─────────────────────────────────────────────
# TASK 4 — SIP Continuity Analysis
# ─────────────────────────────────────────────
print("\n[Task 4] SIP Continuity Analysis...")

sip_sorted = sip.sort_values(["investor_id","transaction_date"])
sip_sorted["prev_date"] = sip_sorted.groupby("investor_id")["transaction_date"].shift(1)
sip_sorted["gap_days"] = (sip_sorted["transaction_date"] - sip_sorted["prev_date"]).dt.days

sip_count = sip.groupby("investor_id").size().reset_index(name="sip_count")
frequent_sip = sip_count[sip_count["sip_count"] >= 6]["investor_id"].tolist()

sip_gaps = sip_sorted[sip_sorted["investor_id"].isin(frequent_sip)].groupby("investor_id")["gap_days"].mean().reset_index()
sip_gaps.columns = ["investor_id","avg_gap_days"]
sip_gaps["at_risk"] = sip_gaps["avg_gap_days"] > 35
sip_gaps["avg_gap_days"] = sip_gaps["avg_gap_days"].round(1)

at_risk_count = sip_gaps["at_risk"].sum()
total_frequent = len(sip_gaps)
continuity_rate = round((1 - at_risk_count/total_frequent) * 100, 2)

print(f"Total investors with 6+ SIP transactions: {total_frequent}")
print(f"At-risk investors (gap > 35 days): {at_risk_count}")
print(f"SIP Continuity Rate: {continuity_rate}%")
print(sip_gaps.head(10).to_string(index=False))

# ─────────────────────────────────────────────
# TASK 5 — Simple Fund Recommender
# ─────────────────────────────────────────────
print("\n[Task 5] Building Fund Recommender...")

def recommend_funds(risk_appetite):
    """
    Simple fund recommender based on risk appetite.
    Input: risk_appetite — 'Low', 'Moderate', or 'High'
    Output: Top 3 funds by Sharpe ratio within matching risk_grade
    """
    risk_map = {
        "Low": ["Low", "Moderate"],
        "Moderate": ["Moderate"],
        "High": ["High", "Very High"]
    }

    if risk_appetite not in risk_map:
        return "Invalid input. Please enter Low, Moderate, or High."

    matching_grades = risk_map[risk_appetite]
    filtered = perf[perf["risk_grade"].isin(matching_grades)]
    top3 = filtered.nlargest(3, "sharpe_ratio")[
        ["scheme_name","fund_house","category","sharpe_ratio","risk_grade","expense_ratio_pct"]
    ].reset_index(drop=True)
    top3.index += 1
    return top3

# Test all 3 risk appetites
print("\nRecommendations for LOW risk:")
print(recommend_funds("Low").to_string())
print("\nRecommendations for MODERATE risk:")
print(recommend_funds("Moderate").to_string())
print("\nRecommendations for HIGH risk:")
print(recommend_funds("High").to_string())

# ─────────────────────────────────────────────
# TASK 6 — Sector HHI Concentration
# ─────────────────────────────────────────────
print("\n[Task 6] Sector HHI Concentration...")

holdings["weight_sq"] = (holdings["weight_pct"] / 100) ** 2
hhi_df = holdings.groupby("amfi_code")["weight_sq"].sum().reset_index()
hhi_df.columns = ["amfi_code","hhi_score"]
hhi_df["hhi_score"] = hhi_df["hhi_score"].round(4)
hhi_df = hhi_df.merge(perf[["amfi_code","scheme_name","category"]], on="amfi_code", how="left")
hhi_df["concentration_level"] = hhi_df["hhi_score"].apply(
    lambda x: "High" if x > 0.15 else ("Moderate" if x > 0.08 else "Low")
)
hhi_df = hhi_df.sort_values("hhi_score", ascending=False)

print("Top 10 Funds by HHI Concentration:")
print(hhi_df.head(10)[["scheme_name","hhi_score","concentration_level"]].to_string(index=False))

print("\n" + "="*60)
print("ALL TASKS COMPLETE!")
print("="*60)
print("\nDeliverables:")
print("  var_cvar_report.csv")
print("  charts/rolling_sharpe_chart.png")
print("  recommender.py (saved separately)")
