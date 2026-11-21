-- Tạo database etl_db nếu chưa tồn tại (chạy trong ngữ cảnh DB mặc định)
SELECT 'CREATE DATABASE etl_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'etl_db')\gexec

\connect etl_db

-- Bảng raw lưu dữ liệu thô dạng TEXT khi ingest
CREATE TABLE IF NOT EXISTS raw_sales (
    raw_id                  SERIAL PRIMARY KEY,
    invoice_id              TEXT,
    branch                  TEXT,
    city                    TEXT,
    customer_type           TEXT,
    gender                  TEXT,
    product_line            TEXT,
    unit_price              TEXT,
    quantity                TEXT,
    tax_5pct                TEXT,
    total                   TEXT,
    date                    TEXT,
    time                    TEXT,
    payment                 TEXT,
    cogs                    TEXT,
    gross_margin_percentage TEXT,
    gross_income            TEXT,
    rating                  TEXT,
    loaded_at               TIMESTAMP DEFAULT NOW()
);

-- Bảng staging dữ liệu đã ép kiểu
CREATE TABLE IF NOT EXISTS staging_sales (
    invoice_id   TEXT NOT NULL,
    branch       TEXT,
    city         TEXT,
    customer_type TEXT,
    gender       TEXT,
    product_line TEXT,
    unit_price   NUMERIC(12, 2),
    quantity     INT,
    total        NUMERIC(12, 2),
    date         DATE,
    payment      TEXT,
    gross_income NUMERIC(12, 2),
    loaded_at    TIMESTAMP DEFAULT NOW()
);

-- Bảng Data Warehouse chính (idempotent theo invoice_id)
CREATE TABLE IF NOT EXISTS warehouse_sales (
    invoice_id   TEXT PRIMARY KEY,
    branch       TEXT,
    city         TEXT,
    customer_type TEXT,
    gender       TEXT,
    product_line TEXT,
    unit_price   NUMERIC(12, 2),
    quantity     INT,
    total        NUMERIC(12, 2),
    date         DATE,
    payment      TEXT,
    gross_income NUMERIC(12, 2),
    updated_at   TIMESTAMP DEFAULT NOW()
);

-- Bảng ghi log từng bước ETL
CREATE TABLE IF NOT EXISTS etl_log (
    id          SERIAL PRIMARY KEY,
    run_id      TEXT NOT NULL,
    step_name   TEXT NOT NULL,
    status      TEXT NOT NULL,
    message     TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);