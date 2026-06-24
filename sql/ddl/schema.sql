CREATE TABLE IF NOT EXISTS dim_country (
    country_id  SERIAL PRIMARY KEY,
    country_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS dim_product (
    stock_code           VARCHAR(30) PRIMARY KEY,
    description          VARCHAR(255),
    unit_price_reference NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id        SERIAL PRIMARY KEY,
    invoice_number VARCHAR(20),
    stock_code     VARCHAR(30) REFERENCES dim_product(stock_code),
    customer_id    BIGINT REFERENCES dim_customer(customer_id),
    country_id     INT REFERENCES dim_country(country_id),
    quantity       INT,
    invoice_date   TIMESTAMP,
    unit_price     NUMERIC(10, 2),
    is_return      BOOLEAN
);

ALTER TABLE fact_sales
ADD COLUMN IF NOT EXISTS is_return BOOLEAN;
