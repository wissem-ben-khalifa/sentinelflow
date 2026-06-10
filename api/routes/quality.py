"""
SentinelFlow - Quality Routes
Endpoints for data profiling and validation results.
"""

from fastapi import APIRouter, HTTPException
import psycopg2
from config.settings import (
    POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
)

router = APIRouter()


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


@router.get("/profiling/{dataset_name}")
def get_profiling_results(dataset_name: str):
    """Get latest profiling results for a dataset."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT ON (column_name)
            column_name, run_date, row_count,
            null_count, missing_percentage,
            duplicate_count, duplicate_ratio,
            mean, median, std, min_value, max_value,
            skewness, kurtosis, q25, q75
        FROM profiling_results
        WHERE dataset_name = %s
        ORDER BY column_name, run_date DESC
    """, (dataset_name,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No profiling results for {dataset_name}")

    columns = [
        "column_name", "run_date", "row_count",
        "null_count", "missing_percentage",
        "duplicate_count", "duplicate_ratio",
        "mean", "median", "std", "min_value", "max_value",
        "skewness", "kurtosis", "q25", "q75"
    ]

    return [dict(zip(columns, row)) for row in rows]


@router.get("/validation/{dataset_name}")
def get_validation_results(dataset_name: str):
    """Get latest validation results for a dataset."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT ON (expectation_type, column_name)
            expectation_type, column_name, success,
            observed_value, expected_value, severity, run_date
        FROM validation_results
        WHERE dataset_name = %s
        ORDER BY expectation_type, column_name, run_date DESC
    """, (dataset_name,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No validation results for {dataset_name}")

    columns = [
        "expectation_type", "column_name", "success",
        "observed_value", "expected_value", "severity", "run_date"
    ]

    return [dict(zip(columns, row)) for row in rows]


@router.get("/summary")
def get_quality_summary():
    """Get quality summary across all datasets."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT ON (dataset_name)
            dataset_name, quality_score, anomaly_count,
            drift_detected, run_date, status
        FROM pipeline_metadata
        ORDER BY dataset_name, run_date DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    columns = [
        "dataset_name", "quality_score", "anomaly_count",
        "drift_detected", "run_date", "status"
    ]

    return [dict(zip(columns, row)) for row in rows]