"""
Bluestock Fintech — Data Analyst Internship Cohort 2025
Capstone Project I — Mutual Fund Analytics
Fund Performance Analytics
Author: Surendhar
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats
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
nifty50 = pd.read_csv("data/nifty50.csv", parse_dates=["date"])
nifty100 = pd.read_csv("data/nifty100.csv", parse_dates=["date"])

nav = nav.sort_values(["amfi_code","date"]).reset_index(drop=True)
nav = nav.merge(perf[["amfi_code","scheme_name","fund_house","category","expense_ratio_pct"]], on="amfi_code", how="left")

print("Data loaded!")
print(f"NAV: {nav.shape} | Schemes: {perf.shape[0]} | Nifty50: {nifty50.shape}")

# ─────────────────────────────────────────────
# TASK 1 — Daily Returns
# ─────────────────────────────────────────────
print("\n[Task 1] Computing daily returns...")
nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
nav = nav.dropna(subset=["daily_return"])

# Validate distribution
ret_stats = nav.groupby("amfi_code")["daily_return"].describe()
print("Daily return stats (sample):")
print(ret_stats.head(3))
print("Distribution looks reasonable — mean near 0, std around 0.01")

# ─────────────────────────────────────────────
# TASK 2 — CAGR (1yr, 3yr, 5yr)
# ─────────────────────────────────────────────
print("\n[Task 2] Computing CAGR...")

def compute_cagr(group, years):
    end_date = group["date"].max()
    start_date = end_date - pd.DateOffset(years=years)
    subset = group[group["date"] >= start_date]
    if len(subset) < 2:
        return np.nan
    nav_start = subset.iloc[0]["nav"]
    nav_end = subset.iloc[-1]["nav"]
    n = years
    return (nav_end / nav_start) ** (1/n) - 1

cagr_results = []
for code, group in nav.groupby("amfi_code"):
    name = group["scheme_name"].iloc[0]
    cagr_1yr = compute_cagr(group, 1)
    cagr_3yr = compute_cagr(group, 3)
    cagr_5yr = compute_cagr(group, 5)
    cagr_results.append({
        "amfi_code": code,
        "scheme_name": name,
        "cagr_1yr_pct": round(cagr_1yr * 100, 2) if not np.isnan(cagr_1yr) else np.nan,
        "cagr_3yr_pct": round(cagr_3yr * 100, 2) if not np.isnan(cagr_3yr) else np.nan,
        "cagr_5yr_pct": round(cagr_5yr * 100, 2) if not np.isnan(cagr_5yr) else np.nan,
    })

cagr_df = pd.DataFrame(cagr_results)
print("CAGR Table (top 5 by 3yr):")
print(cagr_df.nlargest(5, "cagr_3yr_pct")[["scheme_name","cagr_1yr_pct","cagr_3yr_pct","cagr_5yr_pct"]].to_string(index=False))

# ─────────────────────────────────────────────
# TASK 3 — Sharpe Ratio
# ─────────────────────────────────────────────
print("\n[Task 3] Computing Sharpe Ratio...")

RF = 0.065 / 252  # Daily risk-free rate

sharpe_results = []
for code, group in nav.groupby("amfi_code"):
    name = group["scheme_name"].iloc[0]
    returns = group["daily_return"].dropna()
    excess = returns - RF
    sharpe = (excess.mean() / returns.std()) * np.sqrt(252)
    sharpe_results.append({
        "amfi_code": code,
        "scheme_name": name,
        "sharpe_ratio": round(sharpe, 4)
    })

sharpe_df = pd.DataFrame(sharpe_results).sort_values("sharpe_ratio", ascending=False)
sharpe_df["sharpe_rank"] = range(1, len(sharpe_df)+1)
print("Top 5 by Sharpe Ratio:")
print(sharpe_df.head(5)[["scheme_name","sharpe_ratio","sharpe_rank"]].to_string(index=False))

# ─────────────────────────────────────────────
# TASK 4 — Sortino Ratio
# ─────────────────────────────────────────────
print("\n[Task 4] Computing Sortino Ratio...")

sortino_results = []
for code, group in nav.groupby("amfi_code"):
    name = group["scheme_name"].iloc[0]
    returns = group["daily_return"].dropna()
    excess = returns - RF
    downside = returns[returns < 0]
    downside_std = downside.std()
    sortino = (excess.mean() / downside_std) * np.sqrt(252) if downside_std > 0 else np.nan
    sortino_results.append({
        "amfi_code": code,
        "scheme_name": name,
        "sortino_ratio": round(sortino, 4) if not np.isnan(sortino) else np.nan
    })

sortino_df = pd.DataFrame(sortino_results)
print("Top 5 by Sortino Ratio:")
print(sortino_df.nlargest(5,"sortino_ratio")[["scheme_name","sortino_ratio"]].to_string(index=False))

# ─────────────────────────────────────────────
# TASK 5 — Alpha and Beta (OLS Regression)
# ─────────────────────────────────────────────
print("\n[Task 5] Computing Alpha and Beta...")

# Prepare benchmark returns
nifty100["return"] = nifty100["close"].pct_change()
nifty100 = nifty100.dropna()

alpha_beta_results = []
for code, group in nav.groupby("amfi_code"):
    name = group["scheme_name"].iloc[0]
    fund_ret = group[["date","daily_return"]].dropna()
    merged = fund_ret.merge(nifty100[["date","return"]], on="date", how="inner")

    if len(merged) < 30:
        continue

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        merged["return"], merged["daily_return"]
    )
    beta = round(slope, 4)
    alpha = round(intercept * 252, 4)  # Annualised alpha

    alpha_beta_results.append({
        "amfi_code": code,
        "scheme_name": name,
        "alpha": alpha,
        "beta": beta,
        "r_squared": round(r_value**2, 4)
    })

alpha_beta_df = pd.DataFrame(alpha_beta_results)
print("Top 5 by Alpha:")
print(alpha_beta_df.nlargest(5,"alpha")[["scheme_name","alpha","beta","r_squared"]].to_string(index=False))

# Save alpha_beta.csv
alpha_beta_df.to_csv("alpha_beta.csv", index=False)
print("Saved: alpha_beta.csv")

# ─────────────────────────────────────────────
# TASK 6 — Maximum Drawdown
# ─────────────────────────────────────────────
print("\n[Task 6] Computing Maximum Drawdown...")

drawdown_results = []
for code, group in nav.groupby("amfi_code"):
    name = group["scheme_name"].iloc[0]
    group = group.sort_values("date")
    running_max = group["nav"].cummax()
    drawdown = group["nav"] / running_max - 1
    max_dd = drawdown.min()
    worst_idx = drawdown.idxmin()
    peak_idx = group["nav"][:worst_idx].idxmax()
    worst_date = group.loc[worst_idx, "date"]
    peak_date = group.loc[peak_idx, "date"]

    drawdown_results.append({
        "amfi_code": code,
        "scheme_name": name,
        "max_drawdown_pct": round(max_dd * 100, 2),
        "peak_date": peak_date.date(),
        "trough_date": worst_date.date()
    })

drawdown_df = pd.DataFrame(drawdown_results)
print("Top 5 Worst Drawdowns:")
print(drawdown_df.nsmallest(5,"max_drawdown_pct")[["scheme_name","max_drawdown_pct","peak_date","trough_date"]].to_string(index=False))

# ─────────────────────────────────────────────
# TASK 7 — Fund Scorecard (0-100)
# ─────────────────────────────────────────────
print("\n[Task 7] Computing Fund Scorecard...")

scorecard = cagr_df[["amfi_code","scheme_name","cagr_3yr_pct"]].copy()
scorecard = scorecard.merge(sharpe_df[["amfi_code","sharpe_ratio"]], on="amfi_code", how="left")
scorecard = scorecard.merge(alpha_beta_df[["amfi_code","alpha"]], on="amfi_code", how="left")
scorecard = scorecard.merge(perf[["amfi_code","expense_ratio_pct"]], on="amfi_code", how="left")
scorecard = scorecard.merge(drawdown_df[["amfi_code","max_drawdown_pct"]], on="amfi_code", how="left")

# Rank each metric
scorecard["return_rank"] = scorecard["cagr_3yr_pct"].rank(pct=True) * 100
scorecard["sharpe_rank_score"] = scorecard["sharpe_ratio"].rank(pct=True) * 100
scorecard["alpha_rank"] = scorecard["alpha"].rank(pct=True) * 100
scorecard["expense_rank"] = (1 - scorecard["expense_ratio_pct"].rank(pct=True)) * 100  # inverse
scorecard["dd_rank"] = (1 - scorecard["max_drawdown_pct"].rank(pct=True)) * 100  # inverse

# Composite scorecard
scorecard["fund_score"] = (
    0.30 * scorecard["return_rank"] +
    0.25 * scorecard["sharpe_rank_score"] +
    0.20 * scorecard["alpha_rank"] +
    0.15 * scorecard["expense_rank"] +
    0.10 * scorecard["dd_rank"]
).round(2)

scorecard = scorecard.sort_values("fund_score", ascending=False).reset_index(drop=True)
scorecard["overall_rank"] = range(1, len(scorecard)+1)

print("Top 10 Funds by Scorecard:")
print(scorecard.head(10)[["scheme_name","fund_score","overall_rank"]].to_string(index=False))

# Save fund_scorecard.csv
scorecard_out = scorecard[["amfi_code","scheme_name","cagr_3yr_pct","sharpe_ratio",
                            "alpha","expense_ratio_pct","max_drawdown_pct","fund_score","overall_rank"]]
scorecard_out.to_csv("fund_scorecard.csv", index=False)
print("Saved: fund_scorecard.csv")

# ─────────────────────────────────────────────
# TASK 8 — Benchmark Comparison Chart
# ─────────────────────────────────────────────
print("\n[Task 8] Benchmark Comparison Chart...")

# Get top 5 funds by scorecard
top5_codes = scorecard.head(5)["amfi_code"].tolist()
top5_names = scorecard.head(5)["scheme_name"].tolist()

# Prepare 3-year data
cutoff = nav["date"].max() - pd.DateOffset(years=3)
nav_3yr = nav[nav["date"] >= cutoff]
nifty50_3yr = nifty50[nifty50["date"] >= cutoff].copy()
nifty100_3yr = nifty100[nifty100["date"] >= cutoff].copy()

fig, axes = plt.subplots(2, 1, figsize=(16, 14))
fig.suptitle("Top 5 Funds vs Nifty 50 & Nifty 100 — 3 Year Benchmark Comparison",
             fontsize=14, fontweight="bold")

# Chart — Normalized performance
ax = axes[0]
colors = plt.cm.tab10(np.linspace(0, 0.5, 5))

for i, (code, name) in enumerate(zip(top5_codes, top5_names)):
    fund_data = nav_3yr[nav_3yr["amfi_code"] == code].sort_values("date")
    if len(fund_data) == 0:
        continue
    normalized = fund_data["nav"] / fund_data["nav"].iloc[0] * 100
    ax.plot(fund_data["date"], normalized, lw=2, color=colors[i], label=name[:30])

# Normalize benchmarks
n50_norm = nifty50_3yr["close"] / nifty50_3yr["close"].iloc[0] * 100
n100_norm = nifty100_3yr["close"] / nifty100_3yr["close"].iloc[0] * 100

ax.plot(nifty50_3yr["date"], n50_norm, lw=2.5, color="black", linestyle="--", label="Nifty 50")
ax.plot(nifty100_3yr["date"], n100_norm, lw=2.5, color="gray", linestyle="--", label="Nifty 100")

ax.set_title("Normalized Performance (Base = 100)", fontsize=12)
ax.set_ylabel("Indexed Return (Base 100)")
ax.set_xlabel("Date")
ax.legend(loc="upper left", fontsize=8)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=30)

# Chart — Tracking Error
ax2 = axes[1]
tracking_errors = []
for code, name in zip(top5_codes, top5_names):
    fund_data = nav_3yr[nav_3yr["amfi_code"] == code][["date","daily_return"]].dropna()
    merged = fund_data.merge(nifty50_3yr[["date"]].assign(
        n50_ret=nifty50_3yr["close"].pct_change().values[:len(nifty50_3yr)]
    ), on="date", how="inner")
    if len(merged) > 0 and "n50_ret" in merged.columns:
        te = (merged["daily_return"] - merged["n50_ret"]).std() * np.sqrt(252)
        tracking_errors.append({"Fund": name[:30], "Tracking Error": round(te * 100, 2)})

if tracking_errors:
    te_df = pd.DataFrame(tracking_errors)
    bars = ax2.bar(te_df["Fund"], te_df["Tracking Error"],
                   color=plt.cm.tab10(np.linspace(0, 0.5, len(te_df))), edgecolor="white")
    for bar, val in zip(bars, te_df["Tracking Error"]):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f"{val:.2f}%", ha="center", fontsize=9)
    ax2.set_title("Tracking Error vs Nifty 50 (annualised)", fontsize=12)
    ax2.set_ylabel("Tracking Error (%)")
    ax2.set_xticklabels(te_df["Fund"], rotation=20, ha="right", fontsize=9)

plt.tight_layout()
plt.savefig("charts/benchmark_comparison.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: charts/benchmark_comparison.png")

print("\n" + "="*60)
print("ALL TASKS COMPLETE!")
print("Deliverables: fund_scorecard.csv, alpha_beta.csv, charts/benchmark_comparison.png")
print("="*60)
