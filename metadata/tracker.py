"""
SentinelFlow - Metadata Tracker
Records pipeline execution metadata after every run.
Provides traceability and audit history for every dataset processed.
"""

import psycopg2
from datetime import datetime
from config.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD
)
from config.logging_config import get_logger

logger = get_logger(__name__)


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def record_pipeline_run(
    pipeline_id: str,
    dataset_name: str,
    source: str,
    owner: str,
    execution_time_sec: float,
    row_count: int,
    quality_score: float,
    anomaly_count: int,
    drift_detected: bool,
    status: str = "success"
) -> int:
    """
    Record a pipeline execution in the metadata table.
    Returns the inserted row id.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pipeline_metadata (
            pipeline_id, dataset_name, source, owner,
            run_date, execution_time_sec, row_count,
            quality_score, anomaly_count, drift_detected, status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
    """, (
        pipeline_id,
        dataset_name,
        source,
        owner,
        datetime.now(),
        execution_time_sec,
        row_count,
        quality_score,
        anomaly_count,
        drift_detected,
        status
    ))

    row_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    logger.info(
        f"Recorded pipeline run: {pipeline_id} | "
        f"{dataset_name} | quality={quality_score} | "
        f"anomalies={anomaly_count} | drift={drift_detected}"
    )

    return row_id


def get_pipeline_history(dataset_name: str, limit: int = 10) -> list[dict]:
    """
    Get recent pipeline run history for a dataset.
    Returns a list of metadata dicts ordered by most recent first.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, pipeline_id, dataset_name, source, owner,
            run_date, execution_time_sec, row_count,
            quality_score, anomaly_count, drift_detected, status
        FROM pipeline_metadata
        WHERE dataset_name = %s
        ORDER BY run_date DESC
        LIMIT %s
    """, (dataset_name, limit))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    columns = [
        "id", "pipeline_id", "dataset_name", "source", "owner",
        "run_date", "execution_time_sec", "row_count",
        "quality_score", "anomaly_count", "drift_detected", "status"
    ]

    return [dict(zip(columns, row)) for row in rows]


def get_latest_quality_scores() -> list[dict]:
    """
    Get the most recent quality score for each dataset.
    Used by the dashboard overview page.
    """
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


def get_pipeline_health_score() -> float:
    """
    Calculate an overall platform health score (0 to 100)
    based on recent quality scores across all datasets.
    """
    scores = get_latest_quality_scores()

    if not scores:
        return 0.0

    quality_avg = sum(s["quality_score"] for s in scores if s["quality_score"]) / len(scores)
    drift_penalty = sum(10 for s in scores if s["drift_detected"])
    health = max(0.0, quality_avg - drift_penalty)

    return round(health, 2)