"""
SentinelFlow - Drift Routes
Endpoints for drift detection results.
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


@router.get("/{dataset_name}")
def get_drift_results(dataset_name: str):
    """Get latest drift detection results for a dataset."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT ON (column_name, detection_method)
            column_name, detection_method, drift_score,
            drift_detected, baseline_mean, current_mean,
            baseline_std, current_std, run_date
        FROM drift_results
        WHERE dataset_name = %s
        ORDER BY column_name, detection_method, run_date DESC
    """, (dataset_name,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No drift results for {dataset_name}")

    columns = [
        "column_name", "detection_method", "drift_score",
        "drift_detected", "baseline_mean", "current_mean",
        "baseline_std", "current_std", "run_date"
    ]

    return [dict(zip(columns, row)) for row in rows]


@router.get("/summary/all")
def get_drift_summary():
    """Get drift summary across all datasets."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT ON (dataset_name, column_name, detection_method)
            dataset_name, column_name, detection_method,
            drift_score, drift_detected, run_date
        FROM drift_results
        ORDER BY dataset_name, column_name, detection_method, run_date DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    columns = [
        "dataset_name", "column_name", "detection_method",
        "drift_score", "drift_detected", "run_date"
    ]

    return [dict(zip(columns, row)) for row in rows]