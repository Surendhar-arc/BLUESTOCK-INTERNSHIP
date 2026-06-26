"""
Bluestock Fintech — Data Analyst Internship Cohort 2025
Capstone Project I — Mutual Fund Analytics
EDA Analysis — Exactly 10 Charts as per task
Author: Surendhar
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
import os

warnings.filterwarnings("ignore")
os.makedirs("charts", exist_ok=True)

# Load Data
nav = pd.read_csv("data/nav_history.csv", parse_dates=["date"])
perf = pd.read_csv("data/scheme_performance.csv")
txn = pd.read_csv("data/investor_transactions.csv", parse_dates=["transaction_date"])
holdings = pd.read_csv("data/portfolio_holdings.csv")
nav = nav.merge(perf[["amfi_code","scheme_name","fund_house","category"]], on="amfi_code", how="left")
sip = txn[txn["transaction_type"]=="SIP"].copy()
txn_merged = txn.merge(perf[["amfi_code","category"]], on="amfi_code", how="left")

sns.set_theme(style="darkgrid")
print("Data loaded. Generating charts...")

# ─────────────────────────────────────────────
# CHART 1 — NAV Trend (Plotly style using Matplotlib)
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16,7))
colors = plt.cm.tab20(np.linspace(0,1,nav["amfi_code"].nunique()))
for i,code in enumerate(nav["amfi_code"].unique()):
    s = nav[nav["amfi_code"]==code].sort_values("date")
    ax.plot(s["date"],s["nav"],lw=0.8,alpha=0.5,color=colors[i])
ax.axvspan(pd.Timestamp("2023-01-01"),pd.Timestamp("2023-12-31"),alpha=0.15,color="green")
ax.axvspan(pd.Timestamp("2024-01-01"),pd.Timestamp("2024-12-31"),alpha=0.15,color="red")
ax.annotate("2023 Bull Run", xy=(pd.Timestamp("2023-06-01"), nav["nav"].quantile(0.92)),
            fontsize=12, color="green", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
ax.annotate("2024 Market Correction", xy=(pd.Timestamp("2024-06-01"), nav["nav"].quantile(0.80)),
            fontsize=12, color="red", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
ax.set_title("Daily NAV Trend — All 40 Mutual Fund Schemes (2022–2026)", fontsize=14, fontweight="bold")
ax.set_xlabel("Date"); ax.set_ylabel("NAV (INR)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("charts/chart1_nav_trend.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 1 done")

# ─────────────────────────────────────────────
# CHART 2 — AUM Grouped Bar by Fund House (Seaborn)
# ─────────────────────────────────────────────
aum_g = perf.groupby("fund_house")["aum_crore"].sum().sort_values(ascending=False).reset_index()
fig, ax = plt.subplots(figsize=(14,7))
palette = ["#e74c3c" if "SBI" in f else "#4a90d9" for f in aum_g["fund_house"]]
sns.barplot(data=aum_g, x="fund_house", y="aum_crore", palette=palette, ax=ax)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
ax.set_title("AUM by Fund House — SBI Dominance Highlighted", fontsize=14, fontweight="bold")
ax.set_xlabel("Fund House"); ax.set_ylabel("AUM (Crore INR)")
sbi_val = aum_g[aum_g["fund_house"].str.contains("SBI")]["aum_crore"].sum()
sbi_idx = aum_g[aum_g["fund_house"].str.contains("SBI")].index[0]
ax.annotate(f"SBI: ₹{sbi_val:.1f} Cr",
            xy=(sbi_idx, sbi_val),
            xytext=(sbi_idx+1.5, sbi_val*0.85),
            arrowprops=dict(arrowstyle="->", color="red"),
            fontsize=11, color="red", fontweight="bold")
red_p = mpatches.Patch(color="#e74c3c", label="SBI Fund House")
blue_p = mpatches.Patch(color="#4a90d9", label="Other Fund Houses")
ax.legend(handles=[red_p, blue_p])
plt.tight_layout()
plt.savefig("charts/chart2_aum_fundhouse.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 2 done")

# ─────────────────────────────────────────────
# CHART 3 — SIP Inflow Time-Series
# ─────────────────────────────────────────────
sip["month"] = sip["transaction_date"].dt.to_period("M")
ms = sip.groupby("month")["amount_inr"].sum().reset_index()
ms["cr"] = ms["amount_inr"] / 1e7
ms["mdt"] = ms["month"].dt.to_timestamp()
ms = ms.sort_values("mdt")
mi = ms["cr"].idxmax(); mv = ms.loc[mi,"cr"]; md = ms.loc[mi,"mdt"]

fig, ax = plt.subplots(figsize=(16,6))
ax.plot(ms["mdt"], ms["cr"], color="#2ecc71", lw=2.5, marker="o", ms=4)
ax.fill_between(ms["mdt"], ms["cr"], alpha=0.15, color="#2ecc71")
ax.annotate(f"All-Time High\n₹{mv:.0f} Cr (Dec 2025)",
            xy=(md, mv),
            xytext=(md - pd.DateOffset(months=10), mv * 0.82),
            arrowprops=dict(arrowstyle="->", color="red", lw=1.5),
            fontsize=12, color="red", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9))
ax.set_title("Monthly SIP Inflow Time-Series (Jan 2022 – Dec 2025)", fontsize=14, fontweight="bold")
ax.set_xlabel("Month"); ax.set_ylabel("SIP Inflow (Crore INR)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("charts/chart3_sip_timeseries.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 3 done")

# ─────────────────────────────────────────────
# CHART 4 — Category Inflow Heatmap (Seaborn)
# ─────────────────────────────────────────────
txn_merged["month_num"] = txn_merged["transaction_date"].dt.month
hd = txn_merged.groupby(["category","month_num"])["amount_inr"].sum().reset_index()
hp = hd.pivot(index="category", columns="month_num", values="amount_inr").fillna(0)
ml = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
hp.columns = [ml[i-1] for i in hp.columns]

fig, ax = plt.subplots(figsize=(14,6))
sns.heatmap(hp/1e7, annot=True, fmt=".0f", cmap="YlOrRd",
            linewidths=0.5, ax=ax,
            cbar_kws={"label":"Net Inflow (Crore INR)"})
ax.set_title("Category Inflow Heatmap — Months vs Fund Categories", fontsize=13, fontweight="bold")
ax.set_xlabel("Month"); ax.set_ylabel("Fund Category")
plt.tight_layout()
plt.savefig("charts/chart4_category_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 4 done")

# ─────────────────────────────────────────────
# CHART 5 — Investor Demographics
# ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18,6))
fig.suptitle("Investor Demographics Analysis", fontsize=15, fontweight="bold")

# Age group pie
ac = txn["age_group"].value_counts()
axes[0].pie(ac.values, labels=ac.index, autopct="%1.1f%%",
            colors=sns.color_palette("Set2", len(ac)), startangle=90)
axes[0].set_title("Age Group Distribution")

# SIP box plot by age group
sd = txn[txn["transaction_type"]=="SIP"]
ao = sorted(sd["age_group"].dropna().unique())
ag = [sd[sd["age_group"]==a]["amount_inr"].values for a in ao]
axes[1].boxplot(ag, labels=ao)
axes[1].set_title("SIP Amount Box Plot by Age Group")
axes[1].set_xlabel("Age Group"); axes[1].set_ylabel("Amount (INR)")
axes[1].tick_params(axis="x", rotation=30)

# Gender split
gc = txn["gender"].value_counts()
axes[2].pie(gc.values, labels=gc.index, autopct="%1.1f%%",
            colors=["#3498db","#e91e8c"], startangle=90)
axes[2].set_title("Gender Split")

plt.tight_layout()
plt.savefig("charts/chart5_demographics.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 5 done")

# ─────────────────────────────────────────────
# CHART 6 — Geographic Distribution
# ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(18,7))
fig.suptitle("Geographic Distribution of SIP Investments", fontsize=14, fontweight="bold")

ss = sip.groupby("state")["amount_inr"].sum().sort_values(ascending=True) / 1e7
ss.plot(kind="barh", ax=axes[0], color="#3498db", edgecolor="white")
axes[0].set_title("SIP Amount by State (Crore INR)")
axes[0].set_xlabel("Amount (Crore INR)"); axes[0].set_ylabel("State")

tc = txn["city_tier"].value_counts()
axes[1].pie(tc.values, labels=tc.index, autopct="%1.1f%%",
            colors=["#e74c3c","#2ecc71"], startangle=90,
            explode=[0.05]*len(tc))
axes[1].set_title("T30 vs B30 City Tier Distribution")

plt.tight_layout()
plt.savefig("charts/chart6_geographic.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 6 done")

# ─────────────────────────────────────────────
# CHART 7 — Folio Count Growth
# ─────────────────────────────────────────────
txn["mp"] = txn["transaction_date"].dt.to_period("M")
fm = txn.groupby("mp")["investor_id"].nunique().reset_index()
fm["mdt"] = fm["mp"].dt.to_timestamp()
fm = fm.sort_values("mdt")
fm["cum"] = fm["investor_id"].cumsum()

start_val = fm["cum"].iloc[0]; end_val = fm["cum"].iloc[-1]
start_date = fm["mdt"].iloc[0]; end_date = fm["mdt"].iloc[-1]

fig, ax = plt.subplots(figsize=(14,6))
ax.plot(fm["mdt"], fm["cum"], color="#9b59b6", lw=2.5, marker="o", ms=4)
ax.fill_between(fm["mdt"], fm["cum"], alpha=0.15, color="#9b59b6")
ax.annotate(f"Start: {start_val:,} folios",
            xy=(start_date, start_val),
            xytext=(start_date + pd.DateOffset(months=3), start_val * 1.3),
            arrowprops=dict(arrowstyle="->", color="green"),
            fontsize=10, color="green", fontweight="bold")
ax.annotate(f"End: {end_val:,} folios",
            xy=(end_date, end_val),
            xytext=(end_date - pd.DateOffset(months=10), end_val * 0.9),
            arrowprops=dict(arrowstyle="->", color="red"),
            fontsize=10, color="red", fontweight="bold")
ax.set_title("Folio Count Growth (Jan 2022 – Dec 2025)", fontsize=13, fontweight="bold")
ax.set_xlabel("Month"); ax.set_ylabel("Cumulative Unique Investors")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("charts/chart7_folio_growth.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 7 done")

# ─────────────────────────────────────────────
# CHART 8 — NAV Return Correlation Matrix (Seaborn)
# ─────────────────────────────────────────────
top10 = perf.nlargest(10, "aum_crore")["amfi_code"].tolist()
n10 = nav[nav["amfi_code"].isin(top10)].copy()
n10["dr"] = n10.groupby("amfi_code")["nav"].pct_change()
pr = n10.pivot_table(index="date", columns="amfi_code", values="dr")
lbls = [perf[perf["amfi_code"]==c]["scheme_name"].values[0][:18]
        if len(perf[perf["amfi_code"]==c])>0 else str(c) for c in pr.columns]
pr.columns = lbls
cm = pr.corr()
mask = np.triu(np.ones_like(cm, dtype=bool))

fig, ax = plt.subplots(figsize=(12,9))
sns.heatmap(cm, annot=True, fmt=".2f", cmap="coolwarm",
            mask=mask, linewidths=0.5, vmin=-1, vmax=1, ax=ax,
            cbar_kws={"label":"Correlation Coefficient"})
ax.set_title("Pairwise NAV Return Correlation — Top 10 Funds by AUM", fontsize=13, fontweight="bold")
plt.xticks(rotation=45, ha="right", fontsize=8)
plt.yticks(fontsize=8)
plt.tight_layout()
plt.savefig("charts/chart8_correlation.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 8 done")

# ─────────────────────────────────────────────
# CHART 9 — Sector Allocation Donut
# ─────────────────────────────────────────────
sw = holdings.groupby("sector")["weight_pct"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(12,8))
wedges, texts, autotexts = ax.pie(
    sw.values, labels=sw.index, autopct="%1.1f%%",
    colors=sns.color_palette("tab20", len(sw)),
    startangle=90, pctdistance=0.85,
    wedgeprops=dict(width=0.5, edgecolor="white", linewidth=2)
)
for t in texts: t.set_fontsize(8)
for at in autotexts: at.set_fontsize(7)
ax.set_title("Sector Allocation Donut — Aggregate Across All Equity Funds",
             fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/chart9_sector_donut.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 9 done")

print("\nAll 9 charts saved in charts/ folder")
print("Chart 10 = EDA Findings documented in Jupyter Notebook")
