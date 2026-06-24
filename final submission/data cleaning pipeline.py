"""
Bluestock Fintech — Data Analyst Internship Cohort 2025
Day 2: Data Cleaning + SQLite Database Design
Author: Surendhar
"""

import pandas as pd
import numpy as np
import sqlite3
from sqlalchemy import create_engine
import os

# ─────────────────────────────────────────────
# SETUP FOLDERS
# ─────────────────────────────────────────────
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)

print("=" * 60)
print("BLUESTOCK FINTECH — DAY 2: DATA CLEANING + SQLITE DB")
print("=" * 60)


# ─────────────────────────────────────────────
# STEP 1: CLEAN nav_history.csv
# ─────────────────────────────────────────────
print("\n[STEP 1] Cleaning nav_history.csv ...")

nav = pd.read_csv("data/raw/nav_history.csv")

print(f"  Original shape: {nav.shape}")

# Parse dates to datetime
nav["date"] = pd.to_datetime(nav["date"], errors="coerce")

# Sort by amfi_code and date
nav = nav.sort_values(["amfi_code", "date"]).reset_index(drop=True)

# Forward-fill missing NAV for holidays/weekends
nav["nav"] = nav.groupby("amfi_code")["nav"].ffill()

# Remove duplicates
nav = nav.drop_duplicates(subset=["amfi_code", "date"])

# Validate NAV > 0
nav = nav[nav["nav"] > 0]

# Remove rows where date could not be parsed
nav = nav.dropna(subset=["date"])

print(f"  Cleaned shape:  {nav.shape}")
print(f"  Nulls remaining: {nav.isnull().sum().to_dict()}")

nav.to_csv("data/processed/nav_history_cleaned.csv", index=False)
print("  Saved: data/processed/nav_history_cleaned.csv")


# ─────────────────────────────────────────────
# STEP 2: CLEAN investor_transactions.csv
# ─────────────────────────────────────────────
print("\n[STEP 2] Cleaning investor_transactions.csv ...")

txn = pd.read_csv("data/raw/investor_transactions.csv")

print(f"  Original shape: {txn.shape}")

# Fix date format
txn["transaction_date"] = pd.to_datetime(txn["transaction_date"], errors="coerce")

# Standardise transaction_type values
txn["transaction_type"] = txn["transaction_type"].str.strip().str.title()
txn["transaction_type"] = txn["transaction_type"].replace({
    "Sip": "SIP",
    "sip": "SIP",
    "lumpsum": "Lumpsum",
    "redemption": "Redemption"
})

# Validate amount > 0
txn = txn[txn["amount_inr"] > 0]

# Check KYC status enum values — keep only valid ones
valid_kyc = ["Verified", "Pending"]
txn = txn[txn["kyc_status"].isin(valid_kyc)]

# Remove rows where date could not be parsed
txn = txn.dropna(subset=["transaction_date"])

print(f"  Cleaned shape:  {txn.shape}")
print(f"  Transaction types: {txn['transaction_type'].unique().tolist()}")
print(f"  KYC values: {txn['kyc_status'].unique().tolist()}")

txn.to_csv("data/processed/investor_transactions_cleaned.csv", index=False)
print("  Saved: data/processed/investor_transactions_cleaned.csv")


# ─────────────────────────────────────────────
# STEP 3: CLEAN scheme_performance.csv
# ─────────────────────────────────────────────
print("\n[STEP 3] Cleaning scheme_performance.csv ...")

perf = pd.read_csv("data/raw/scheme_performance.csv")

print(f"  Original shape: {perf.shape}")

# Validate all return values are numeric
return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct"]
for col in return_cols:
    perf[col] = pd.to_numeric(perf[col], errors="coerce")

# Flag anomalies — return > 100% or < -100%
for col in return_cols:
    anomaly_count = ((perf[col] > 100) | (perf[col] < -100)).sum()
    if anomaly_count > 0:
        print(f"  Anomalies in {col}: {anomaly_count} rows flagged")

perf["anomaly_flag"] = (
    (perf[return_cols] > 100).any(axis=1) |
    (perf[return_cols] < -100).any(axis=1)
)

# Check expense_ratio range (valid: 0.1% to 2.5%)
invalid_expense = perf[
    (perf["expense_ratio_pct"] < 0.1) | (perf["expense_ratio_pct"] > 2.5)
]
print(f"  Expense ratio out of range (0.1-2.5%): {len(invalid_expense)} rows")
print(f"  Expense ratio range in data: {perf['expense_ratio_pct'].min()} to {perf['expense_ratio_pct'].max()}")

perf.to_csv("data/processed/scheme_performance_cleaned.csv", index=False)
print(f"  Cleaned shape: {perf.shape}")
print("  Saved: data/processed/scheme_performance_cleaned.csv")


# ─────────────────────────────────────────────
# STEP 4: DESIGN SQLite STAR SCHEMA
# ─────────────────────────────────────────────
print("\n[STEP 4] Designing SQLite Star Schema ...")

schema_sql = """
-- Bluestock Fintech — Mutual Fund Analytics
-- Star Schema Design

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code       INTEGER PRIMARY KEY,
    scheme_name     TEXT NOT NULL,
    fund_house      TEXT NOT NULL,
    category        TEXT,
    plan            TEXT,
    risk_grade      TEXT,
    morningstar_rating INTEGER
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    full_date       DATE NOT NULL UNIQUE,
    year            INTEGER,
    month           INTEGER,
    quarter         INTEGER,
    day_of_week     TEXT,
    is_weekend      INTEGER
);

CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL,
    date            DATE NOT NULL,
    nav             REAL NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id     TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    amfi_code       INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    amount_inr      REAL NOT NULL,
    state           TEXT,
    city            TEXT,
    city_tier       TEXT,
    age_group       TEXT,
    gender          TEXT,
    annual_income_lakh REAL,
    payment_mode    TEXT,
    kyc_status      TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL,
    return_1yr_pct  REAL,
    return_3yr_pct  REAL,
    return_5yr_pct  REAL,
    benchmark_3yr_pct REAL,
    alpha           REAL,
    beta            REAL,
    sharpe_ratio    REAL,
    sortino_ratio   REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    expense_ratio_pct REAL,
    anomaly_flag    INTEGER DEFAULT 0,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL,
    aum_crore       REAL NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
"""

with open("schema.sql", "w") as f:
    f.write(schema_sql)

print("  Saved: schema.sql")


# ─────────────────────────────────────────────
# STEP 5: LOAD DATA INTO SQLITE
# ─────────────────────────────────────────────
print("\n[STEP 5] Loading data into SQLite database ...")

engine = create_engine("sqlite:///bluestock_mf.db")
conn = sqlite3.connect("bluestock_mf.db")
cursor = conn.cursor()

# Create tables from schema
cursor.executescript(schema_sql)
conn.commit()

# Load dim_fund
dim_fund = perf[["amfi_code", "scheme_name", "fund_house", "category", "plan", "risk_grade", "morningstar_rating"]].copy()
dim_fund.to_sql("dim_fund", engine, if_exists="replace", index=False)
print(f"  dim_fund loaded: {len(dim_fund)} rows")

# Load dim_date from nav dates
all_dates = pd.DataFrame(nav["date"].unique(), columns=["full_date"])
all_dates["full_date"] = pd.to_datetime(all_dates["full_date"])
all_dates["year"] = all_dates["full_date"].dt.year
all_dates["month"] = all_dates["full_date"].dt.month
all_dates["quarter"] = all_dates["full_date"].dt.quarter
all_dates["day_of_week"] = all_dates["full_date"].dt.day_name()
all_dates["is_weekend"] = all_dates["full_date"].dt.dayofweek.isin([5, 6]).astype(int)
all_dates.to_sql("dim_date", engine, if_exists="replace", index=False)
print(f"  dim_date loaded: {len(all_dates)} rows")

# Load fact_nav
nav.to_sql("fact_nav", engine, if_exists="replace", index=False)
print(f"  fact_nav loaded: {len(nav)} rows")

# Load fact_transactions
txn.to_sql("fact_transactions", engine, if_exists="replace", index=False)
print(f"  fact_transactions loaded: {len(txn)} rows")

# Load fact_performance
fact_perf = perf[["amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
                   "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio",
                   "std_dev_ann_pct", "max_drawdown_pct", "expense_ratio_pct", "anomaly_flag"]].copy()
fact_perf.to_sql("fact_performance", engine, if_exists="replace", index=False)
print(f"  fact_performance loaded: {len(fact_perf)} rows")

# Load fact_aum
fact_aum = perf[["amfi_code", "aum_crore"]].copy()
fact_aum.to_sql("fact_aum", engine, if_exists="replace", index=False)
print(f"  fact_aum loaded: {len(fact_aum)} rows")

# Verify row counts
print("\n  Row count verification:")
for table in ["dim_fund", "dim_date", "fact_nav", "fact_transactions", "fact_performance", "fact_aum"]:
    count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"    {table}: {count} rows")


# ─────────────────────────────────────────────
# STEP 6: 10 ANALYTICAL SQL QUERIES
# ─────────────────────────────────────────────
print("\n[STEP 6] Running 10 Analytical SQL Queries ...")

queries = {
    "Q1 — Top 5 Funds by AUM": """
        SELECT f.scheme_name, f.fund_house, a.aum_crore
        FROM fact_aum a
        JOIN dim_fund f ON a.amfi_code = f.amfi_code
        ORDER BY a.aum_crore DESC
        LIMIT 5;
    """,

    "Q2 — Average NAV Per Month": """
        SELECT
            strftime('%Y', date) AS year,
            strftime('%m', date) AS month,
            ROUND(AVG(nav), 4) AS avg_nav
        FROM fact_nav
        GROUP BY year, month
        ORDER BY year, month;
    """,

    "Q3 — SIP Transaction Count Year on Year": """
        SELECT
            strftime('%Y', transaction_date) AS year,
            COUNT(*) AS sip_count,
            ROUND(SUM(amount_inr), 2) AS total_sip_amount
        FROM fact_transactions
        WHERE transaction_type = 'SIP'
        GROUP BY year
        ORDER BY year;
    """,

    "Q4 — Transactions by State": """
        SELECT
            state,
            COUNT(*) AS total_transactions,
            ROUND(SUM(amount_inr), 2) AS total_amount
        FROM fact_transactions
        GROUP BY state
        ORDER BY total_transactions DESC;
    """,

    "Q5 — Funds with Expense Ratio Below 1%": """
        SELECT f.scheme_name, f.fund_house, f.category, p.expense_ratio_pct
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        WHERE p.expense_ratio_pct < 1.0
        ORDER BY p.expense_ratio_pct ASC;
    """,

    "Q6 — Top 5 Funds by 3 Year Returns": """
        SELECT f.scheme_name, f.category, p.return_3yr_pct
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        ORDER BY p.return_3yr_pct DESC
        LIMIT 5;
    """,

    "Q7 — Total Redemption Amount by Age Group": """
        SELECT
            age_group,
            COUNT(*) AS redemption_count,
            ROUND(SUM(amount_inr), 2) AS total_redeemed
        FROM fact_transactions
        WHERE transaction_type = 'Redemption'
        GROUP BY age_group
        ORDER BY total_redeemed DESC;
    """,

    "Q8 — Funds with Highest Sharpe Ratio (Risk Adjusted Returns)": """
        SELECT f.scheme_name, f.category, p.sharpe_ratio, p.return_3yr_pct
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        ORDER BY p.sharpe_ratio DESC
        LIMIT 5;
    """,

    "Q9 — KYC Status Distribution": """
        SELECT
            kyc_status,
            COUNT(*) AS count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_transactions), 2) AS percentage
        FROM fact_transactions
        GROUP BY kyc_status;
    """,

    "Q10 — Most Popular Payment Mode by Transaction Volume": """
        SELECT
            payment_mode,
            COUNT(*) AS transaction_count,
            ROUND(SUM(amount_inr), 2) AS total_amount
        FROM fact_transactions
        GROUP BY payment_mode
        ORDER BY transaction_count DESC;
    """
}

queries_sql_content = "-- Bluestock Fintech — 10 Analytical SQL Queries\n\n"

for title, query in queries.items():
    print(f"\n  {title}")
    result = pd.read_sql_query(query, conn)
    print(result.to_string(index=False))
    queries_sql_content += f"-- {title}\n{query.strip()}\n\n"

with open("queries.sql", "w") as f:
    f.write(queries_sql_content)

print("\n  Saved: queries.sql")


# ─────────────────────────────────────────────
# STEP 7: DATA DICTIONARY
# ─────────────────────────────────────────────
print("\n[STEP 7] Creating Data Dictionary ...")

data_dictionary = """# Bluestock Fintech — Data Dictionary
**Project:** Mutual Fund Analytics — Capstone Project I  
**Author:** Surendhar  
**Cohort:** 2025  
**Last Updated:** 2026-06-24

---

## 1. nav_history_cleaned.csv

| Column | Data Type | Description | Source |
|--------|-----------|-------------|--------|
| amfi_code | INTEGER | Unique AMFI identifier for each mutual fund scheme | AMFI India |
| date | DATE | Date of NAV record (datetime format YYYY-MM-DD) | AMFI India |
| nav | FLOAT | Net Asset Value of the fund on that date (in INR) | AMFI India |

**Cleaning Applied:**
- Parsed date column to datetime format
- Sorted by amfi_code and date
- Forward-filled missing NAV values for holidays and weekends
- Removed duplicate records
- Removed rows where NAV <= 0

---

## 2. investor_transactions_cleaned.csv

| Column | Data Type | Description | Source |
|--------|-----------|-------------|--------|
| investor_id | TEXT | Unique identifier for each investor | Internal CRM |
| transaction_date | DATE | Date of the transaction (YYYY-MM-DD) | Internal CRM |
| amfi_code | INTEGER | AMFI code of the fund invested in | AMFI India |
| transaction_type | TEXT | Type of transaction: SIP, Lumpsum, or Redemption | Internal CRM |
| amount_inr | FLOAT | Transaction amount in Indian Rupees | Internal CRM |
| state | TEXT | Indian state of the investor | KYC Records |
| city | TEXT | City of the investor | KYC Records |
| city_tier | TEXT | City classification: T30 (Top 30) or B30 (Beyond Top 30) | SEBI Classification |
| age_group | TEXT | Age group of investor: 18-25, 26-35, 36-45, 46-55, 56+ | KYC Records |
| gender | TEXT | Gender of the investor: Male or Female | KYC Records |
| annual_income_lakh | FLOAT | Annual income of investor in lakhs (INR) | KYC Records |
| payment_mode | TEXT | Payment method: UPI, Cheque, Mandate, etc. | Payment Gateway |
| kyc_status | TEXT | KYC verification status: Verified or Pending | SEBI/KYC Agency |

**Cleaning Applied:**
- Standardised transaction_type to SIP / Lumpsum / Redemption
- Fixed date format to datetime
- Removed records where amount_inr <= 0
- Kept only valid KYC status values (Verified, Pending)

---

## 3. scheme_performance_cleaned.csv

| Column | Data Type | Description | Source |
|--------|-----------|-------------|--------|
| amfi_code | INTEGER | Unique AMFI fund identifier | AMFI India |
| scheme_name | TEXT | Full name of the mutual fund scheme | AMFI India |
| fund_house | TEXT | Name of the Asset Management Company (AMC) | AMFI India |
| category | TEXT | Fund category: Large Cap, Small Cap, etc. | SEBI Classification |
| plan | TEXT | Plan type: Regular or Direct | AMFI India |
| return_1yr_pct | FLOAT | 1-year absolute return percentage | Morningstar / ValueResearch |
| return_3yr_pct | FLOAT | 3-year CAGR return percentage | Morningstar / ValueResearch |
| return_5yr_pct | FLOAT | 5-year CAGR return percentage | Morningstar / ValueResearch |
| benchmark_3yr_pct | FLOAT | Benchmark index 3-year return percentage | NSE / BSE |
| alpha | FLOAT | Excess return over benchmark (risk-adjusted) | Morningstar |
| beta | FLOAT | Fund sensitivity relative to market movements | Morningstar |
| sharpe_ratio | FLOAT | Risk-adjusted return per unit of risk | Morningstar |
| sortino_ratio | FLOAT | Return per unit of downside risk | Morningstar |
| std_dev_ann_pct | FLOAT | Annualised standard deviation of returns (volatility) | Morningstar |
| max_drawdown_pct | FLOAT | Maximum peak-to-trough decline in value | Morningstar |
| aum_crore | FLOAT | Assets Under Management in Indian Crores | AMFI India |
| expense_ratio_pct | FLOAT | Annual fund management fee percentage (valid range: 0.1% to 2.5%) | AMFI India |
| morningstar_rating | INTEGER | Star rating from 1 to 5 by Morningstar | Morningstar |
| risk_grade | TEXT | Risk classification: Low, Moderate, High, Very High | SEBI / Morningstar |
| anomaly_flag | INTEGER | 1 if return values are outside expected range, 0 otherwise | Derived |

**Cleaning Applied:**
- Validated all return columns are numeric
- Flagged anomalies where returns exceed +/-100%
- Checked expense ratio is within valid SEBI range (0.1% to 2.5%)

---

## 4. SQLite Database — bluestock_mf.db

### dim_fund
Dimension table storing fund master data.

### dim_date
Dimension table storing all unique dates with year, month, quarter, day attributes.

### fact_nav
Fact table storing daily NAV values per fund.

### fact_transactions
Fact table storing all investor transactions.

### fact_performance
Fact table storing fund performance metrics and risk ratios.

### fact_aum
Fact table storing Assets Under Management per fund.

---

*Document generated as part of Bluestock Fintech Data Analyst Internship — Cohort 2025*
"""

with open("data_dictionary.md", "w") as f:
    f.write(data_dictionary)

print("  Saved: data_dictionary.md")

conn.close()

print("\n" + "=" * 60)
print("ALL TASKS COMPLETE!")
print("=" * 60)
print("\nDeliverables ready:")
print("  data/processed/nav_history_cleaned.csv")
print("  data/processed/investor_transactions_cleaned.csv")
print("  data/processed/scheme_performance_cleaned.csv")
print("  bluestock_mf.db")
print("  schema.sql")
print("  queries.sql")
print("  data_dictionary.md")
print("\nNext step: Git commit with message 'Day 2: Cleaned data + SQLite DB loaded'")
