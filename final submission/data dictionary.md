# Bluestock Fintech — Data Dictionary
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
