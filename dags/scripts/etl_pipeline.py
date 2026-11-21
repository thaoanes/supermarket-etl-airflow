import os
import sys
import uuid
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Nạp biến môi trường từ .env (nếu có)
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "etl_db"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

if not DB_CONFIG["user"] or not DB_CONFIG["password"]:
    raise ValueError("Missing DB_USER or DB_PASSWORD in environment variables.")

RUN_ID = f"RUN_{uuid.uuid4().hex[:8].upper()}"


def write_log(cur, step_name, status, message):
    sql = "INSERT INTO etl_log (run_id, step_name, status, message) VALUES (%s, %s, %s, %s);"
    cur.execute(sql, (RUN_ID, step_name, status, message))


def main():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()

        write_log(cur, "PIPELINE", "START", "Begin Supermarket ETL pipeline")

        excel_path = os.path.join(
            os.path.dirname(__file__), "../data/Supermarket_sales.xlsx"
        )

        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path, sheet_name="supermarket_sales")
            cur.execute("TRUNCATE TABLE staging_sales;")

            for _, row in df.iterrows():
                insert_staging = """
                    INSERT INTO staging_sales (invoice_id, branch, city, customer_type, gender,
                    product_line, unit_price, quantity, tax_5, total, date, time, payment,
                    cogs, gross_margin_percentage, gross_income, rating)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                cur.execute(
                    insert_staging,
                    (
                        row["Invoice ID"],
                        row["Branch"],
                        row["City"],
                        row["Customer type"],
                        row["Gender"],
                        row["Product line"],
                        row["Unit price"],
                        row["Quantity"],
                        row["Tax 5%"],
                        row["Total"],
                        row["Date"],
                        row["Time"],
                        row["Payment"],
                        row["cogs"],
                        row["gross margin percentage"],
                        row["gross income"],
                        row["Rating"],
                    ),
                )
            write_log(
                cur,
                "EXTRACT_INGEST",
                "SUCCESS",
                f"Loaded {len(df)} rows into staging.",
            )
        else:
            raise FileNotFoundError(
                f"Không tìm thấy file Excel tại đường dẫn: {excel_path}"
            )

        # 2. Transform & Load
        sql_transform_load = """
            WITH cleaned AS (
                SELECT DISTINCT ON (invoice_id)
                    invoice_id, branch, city, customer_type, gender,
                    product_line, unit_price, quantity, total, date, payment, gross_income
                FROM staging_sales
                WHERE invoice_id IS NOT NULL
                  AND quantity > 0
                  AND total >= 0
                ORDER BY invoice_id, date DESC
            )
            INSERT INTO warehouse_sales (invoice_id, branch, city, customer_type, gender, product_line, unit_price, quantity, total, date, payment, gross_income)
            SELECT invoice_id, branch, city, customer_type, gender, product_line, unit_price, quantity, total, date, payment, gross_income
            FROM cleaned
            ON CONFLICT (invoice_id) DO UPDATE SET
                branch = EXCLUDED.branch,
                total = EXCLUDED.total,
                gross_income = EXCLUDED.gross_income,
                loaded_at = NOW();
        """
        cur.execute(sql_transform_load)
        write_log(
            cur,
            "TRANSFORM_LOAD",
            "SUCCESS",
            "Transferred and upserted data into warehouse_sales.",
        )

        # 3. Data Validation
        sql_validate = """
            WITH cleaned AS (
                SELECT DISTINCT invoice_id FROM staging_sales
                WHERE invoice_id IS NOT NULL AND quantity > 0 AND total >= 0
            )
            SELECT invoice_id FROM cleaned
            EXCEPT
            SELECT invoice_id FROM warehouse_sales;
        """
        cur.execute(sql_validate)
        missing_records = cur.fetchall()

        if len(missing_records) > 0:
            raise Exception(
                f"Validation Failed: Found {len(missing_records)} missing records!"
            )

        write_log(cur, "VALIDATION", "SUCCESS", "Data validation passed successfully.")
        write_log(cur, "PIPELINE", "SUCCESS", "ETL Pipeline completed successfully.")
        conn.commit()

        print("PIPELINE SUCCESS")
        sys.exit(0)

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"PIPELINE FAILED: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()