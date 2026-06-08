"""
SentinelFlow - Profiling Engine
Profiles entire datasets column by column and stores results in PostgreSQL.
"""

import pandas as pd
from datetime import datetime
import psycopg2
from config.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD
)
from config.logging_config import get_logger
from profiling.metrics import profile_column

logger = get_logger(__name__)


def get_connection():
    """Create and return a PostgreSQL connection."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def profile_dataframe(df: pd.DataFrame, dataset_name: str) -> list[dict]:
    """
    Profile every column in a dataframe.
    Returns a list of metric dicts, one per column.
    """
    logger.info(f"Profiling dataset: {dataset_name} ({len(df)} rows, {len(df.columns)} columns)")

    results = []
    for column in df.columns:
        metrics = profile_column(df[column])
        metrics["dataset_name"] = dataset_name
        metrics["column_name"] = column
        metrics["row_count"] = len(df)
        metrics["run_date"] = datetime.now()
        results.append(metrics)
        logger.info(f"  {column}: {metrics['missing_percentage']}% missing, {metrics['duplicate_count']} duplicates")

    return results


def save_profiling_results(results: list[dict], conn) -> None:
    """Insert profiling results into PostgreSQL."""
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO profiling_results (
            dataset_name, column_name, run_date, row_count,
            null_count, missing_percentage,
            duplicate_count, duplicate_ratio,
            mean, median, std, min_value, max_value,
            skewness, kurtosis, q25, q75
        ) VALUES (
            %(dataset_name)s, %(column_name)s, %(run_date)s, %(row_count)s,
            %(null_count)s, %(missing_percentage)s,
            %(duplicate_count)s, %(duplicate_ratio)s,
            %(mean)s, %(median)s, %(std)s, %(min_value)s, %(max_value)s,
            %(skewness)s, %(kurtosis)s, %(q25)s, %(q75)s
        )
    """

    for result in results:
        cursor.execute(insert_query, result)

    conn.commit()
    cursor.close()
    logger.info(f"Saved {len(results)} profiling results to database")


def run_profiler(df: pd.DataFrame, dataset_name: str) -> list[dict]:
    """
    Full profiling pipeline.
    Profiles the dataframe and saves results to PostgreSQL.
    Returns the list of results for immediate use.
    """
    results = profile_dataframe(df, dataset_name)

    conn = get_connection()
    save_profiling_results(results, conn)
    conn.close()

    return results


def get_quality_score(results: list[dict]) -> float:
    """
    Calculate an overall quality score (0 to 100) for a dataset
    based on missing values and duplicates.
    Higher is better.
    """
    if not results:
        return 0.0

    total_missing = sum(r["missing_percentage"] for r in results)
    avg_missing = total_missing / len(results)

    total_duplicate = sum(r["duplicate_ratio"] for r in results)
    avg_duplicate = total_duplicate / len(results)

    score = 100.0 - (avg_missing * 0.7) - (avg_duplicate * 100 * 0.3)
    return round(max(0.0, min(100.0, score)), 2)


if __name__ == "__main__":
    from config.settings import RAW_DATA_DIR

    datasets = {
        "users": RAW_DATA_DIR / "users.csv",
        "products": RAW_DATA_DIR / "products.csv",
        "orders": RAW_DATA_DIR / "orders.csv"
    }

    for name, path in datasets.items():
        df = pd.read_csv(path)
        results = run_profiler(df, name)
        score = get_quality_score(results)
        print(f"{name} quality score: {score}/100")