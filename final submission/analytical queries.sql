-- Bluestock Fintech — 10 Analytical SQL Queries

-- Q1 — Top 5 Funds by AUM
SELECT f.scheme_name, f.fund_house, a.aum_crore
        FROM fact_aum a
        JOIN dim_fund f ON a.amfi_code = f.amfi_code
        ORDER BY a.aum_crore DESC
        LIMIT 5;

-- Q2 — Average NAV Per Month
SELECT
            strftime('%Y', date) AS year,
            strftime('%m', date) AS month,
            ROUND(AVG(nav), 4) AS avg_nav
        FROM fact_nav
        GROUP BY year, month
        ORDER BY year, month;

-- Q3 — SIP Transaction Count Year on Year
SELECT
            strftime('%Y', transaction_date) AS year,
            COUNT(*) AS sip_count,
            ROUND(SUM(amount_inr), 2) AS total_sip_amount
        FROM fact_transactions
        WHERE transaction_type = 'SIP'
        GROUP BY year
        ORDER BY year;

-- Q4 — Transactions by State
SELECT
            state,
            COUNT(*) AS total_transactions,
            ROUND(SUM(amount_inr), 2) AS total_amount
        FROM fact_transactions
        GROUP BY state
        ORDER BY total_transactions DESC;

-- Q5 — Funds with Expense Ratio Below 1%
SELECT f.scheme_name, f.fund_house, f.category, p.expense_ratio_pct
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        WHERE p.expense_ratio_pct < 1.0
        ORDER BY p.expense_ratio_pct ASC;

-- Q6 — Top 5 Funds by 3 Year Returns
SELECT f.scheme_name, f.category, p.return_3yr_pct
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        ORDER BY p.return_3yr_pct DESC
        LIMIT 5;

-- Q7 — Total Redemption Amount by Age Group
SELECT
            age_group,
            COUNT(*) AS redemption_count,
            ROUND(SUM(amount_inr), 2) AS total_redeemed
        FROM fact_transactions
        WHERE transaction_type = 'Redemption'
        GROUP BY age_group
        ORDER BY total_redeemed DESC;

-- Q8 — Funds with Highest Sharpe Ratio (Risk Adjusted Returns)
SELECT f.scheme_name, f.category, p.sharpe_ratio, p.return_3yr_pct
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        ORDER BY p.sharpe_ratio DESC
        LIMIT 5;

-- Q9 — KYC Status Distribution
SELECT
            kyc_status,
            COUNT(*) AS count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_transactions), 2) AS percentage
        FROM fact_transactions
        GROUP BY kyc_status;

-- Q10 — Most Popular Payment Mode by Transaction Volume
SELECT
            payment_mode,
            COUNT(*) AS transaction_count,
            ROUND(SUM(amount_inr), 2) AS total_amount
        FROM fact_transactions
        GROUP BY payment_mode
        ORDER BY transaction_count DESC;

