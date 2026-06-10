"""
SentinelFlow - Metadata Routes
Endpoints for pipeline metadata, lineage and alerts.
"""

from fastapi import APIRouter, HTTPException
import psycopg2
from config.settings import (
    POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
)
from metadata.tracker import get_pipeline_health_score

router = APIRouter()


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


@router.get("/health")
def get_health():
    """Get overall platform health score."""
    score = get_pipeline_health_score()
    return {
        "health_score": score,
        "status": "healthy" if score >= 80 else "degraded" if score >= 60 else "critical"
    }


@router.get("/pipelines")
def get_pipeline_history(limit: int = 20):
    """Get recent pipeline run history."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pipeline_id, dataset_name, source, owner,
            run_date, execution_time_sec, row_count,
            quality_score, anomaly_count, drift_detected, status
        FROM pipeline_metadata
        ORDER BY run_date DESC
        LIMIT %s
    """, (limit,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    columns = [
        "pipeline_id", "dataset_name", "source", "owner",
        "run_date", "execution_time_sec", "row_count",
        "quality_score", "anomaly_count", "drift_detected", "status"
    ]

    return [dict(zip(columns, row)) for row in rows]


@router.get("/lineage/{pipeline_id}")
def get_lineage(pipeline_id: str):
    """Get full lineage chain for a pipeline run."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            source_name, source_type, transformation,
            destination_name, destination_type, run_date
        FROM lineage
        WHERE pipeline_id = %s
        ORDER BY run_date ASC
    """, (pipeline_id,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No lineage found for {pipeline_id}")

    columns = [
        "source_name", "source_type", "transformation",
        "destination_name", "destination_type", "run_date"
    ]

    return [dict(zip(columns, row)) for row in rows]


@router.get("/alerts")
def get_alerts(resolved: bool = False, limit: int = 50):
    """Get recent alerts."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, alert_type, dataset_name, message,
            severity, triggered_at, resolved
        FROM alerts
        WHERE resolved = %s
        ORDER BY triggered_at DESC
        LIMIT %s
    """, (resolved, limit))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    columns = [
        "id", "alert_type", "dataset_name", "message",
        "severity", "triggered_at", "resolved"
    ]

    return [dict(zip(columns, row)) for row in rows]