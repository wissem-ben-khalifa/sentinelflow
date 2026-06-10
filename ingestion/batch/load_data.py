"""
SentinelFlow - Batch Data Loader
Loads raw CSV files into PostgreSQL for warehouse storage.
Tracks load history and detects schema changes.
"""

import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from config.settings import DATABASE_URL, RAW_DATA_DIR
from config.logging_config import get_logger

logger = get_logger(__name__)


def get_engine():
    return create_engine(DATABASE_URL)


def create_raw_tables(engine) -> None:
    """Create raw data tables in PostgreSQL if they don't exist."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS raw_users (
                user_id INTEGER,
                name VARCHAR(200),
                country VARCHAR(100),
                registration_date TIMESTAMP,
                age INTEGER,
                email VARCHAR(200),
                loaded_at TIMESTAMP DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS raw_products (
                product_id INTEGER,
                category VARCHAR(100),
                price FLOAT,
                brand VARCHAR(100),
                stock INTEGER,
                created_at TIMESTAMP,
                loaded_at TIMESTAMP DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS raw_orders (
                order_id INTEGER,
                user_id FLOAT,
                product_id INTEGER,
                quantity INTEGER,
                amount FLOAT,
                timestamp TIMESTAMP,
                status VARCHAR(50),
                loaded_at TIMESTAMP DEFAULT NOW()
            )
        """))

        conn.commit()
    logger.info("Raw data tables created or verified")


def load_csv_to_postgres(
    filename: str,
    table_name: str,
    engine
) -> dict:
    """
    Load a CSV file into a PostgreSQL table.
    Returns a summary of the load operation.
    """
    filepath = RAW_DATA_DIR / filename
    logger.info(f"Loading {filepath} into {table_name}")

    df = pd.read_csv(filepath)
    df["loaded_at"] = datetime.now()

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )

    summary = {
        "table": table_name,
        "rows_loaded": len(df),
        "columns": list(df.columns),
        "loaded_at": datetime.now().isoformat()
    }

    logger.info(f"Loaded {len(df)} rows into {table_name}")
    return summary


def run_batch_load() -> list[dict]:
    """
    Load all raw datasets into PostgreSQL.
    Returns list of load summaries.
    """
    engine = get_engine()
    create_raw_tables(engine)

    datasets = [
        ("users.csv", "raw_users"),
        ("products.csv", "raw_products"),
        ("orders.csv", "raw_orders")
    ]

    summaries = []
    for filename, table_name in datasets:
        summary = load_csv_to_postgres(filename, table_name, engine)
        summaries.append(summary)

    return summaries


if __name__ == "__main__":
    summaries = run_batch_load()
    for s in summaries:
        print(f"{s['table']}: {s['rows_loaded']} rows loaded")