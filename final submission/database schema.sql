
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
