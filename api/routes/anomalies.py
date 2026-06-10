"""
SentinelFlow - Anomaly Routes
Endpoints for anomaly detection results.
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
def get_anomalies(dataset_name: str, method: str = None, limit: int = 100):
    """
    Get anomaly detection results for a dataset.
    Optionally filter by detection method.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if method:
        cursor.execute("""
            SELECT
                id, detection_method, record_id,
                anomaly_score, is_anomaly, explanation, run_date
            FROM anomaly_results
            WHERE dataset_name = %s
            AND detection_method = %s
            AND is_anomaly = TRUE
            ORDER BY anomaly_score DESC
            LIMIT %s
        """, (dataset_name, method, limit))
    else:
        cursor.execute("""
            SELECT
                id, detection_method, record_id,
                anomaly_score, is_anomaly, explanation, run_date
            FROM anomaly_results
            WHERE dataset_name = %s
            AND is_anomaly = TRUE
            ORDER BY anomaly_score DESC
            LIMIT %s
        """, (dataset_name, limit))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    columns = [
        "id", "detection_method", "record_id",
        "anomaly_score", "is_anomaly", "explanation", "run_date"
    ]

    return [dict(zip(columns, row)) for row in rows]


@router.get("/summary/all")
def get_anomaly_summary():
    """Get anomaly counts grouped by dataset and detection method."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            dataset_name,
            detection_method,
            COUNT(*) as total_records,
            SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomaly_count,
            ROUND(AVG(anomaly_score)::numeric, 4) as avg_score
        FROM anomaly_results
        GROUP BY dataset_name, detection_method
        ORDER BY dataset_name, detection_method
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    columns = [
        "dataset_name", "detection_method",
        "total_records", "anomaly_count", "avg_score"
    ]

    return [dict(zip(columns, row)) for row in rows]