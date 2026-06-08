"""
SentinelFlow - Lineage Tracker
Records data lineage: where data came from, what happened to it,
and where it went. Allows engineers to trace downstream impact.
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


def record_lineage(
    pipeline_id: str,
    source_name: str,
    source_type: str,
    transformation: str,
    destination_name: str,
    destination_type: str
) -> None:
    """
    Record a single lineage step.

    Example:
        source_name: users.csv
        source_type: csv_file
        transformation: profiling + validation
        destination_name: profiling_results
        destination_type: postgres_table
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO lineage (
            pipeline_id, source_name, source_type,
            transformation, destination_name,
            destination_type, run_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        pipeline_id,
        source_name,
        source_type,
        transformation,
        destination_name,
        destination_type,
        datetime.now()
    ))

    conn.commit()
    cursor.close()
    conn.close()

    logger.info(
        f"Lineage recorded: {source_name} -> "
        f"{transformation} -> {destination_name}"
    )


def record_full_pipeline_lineage(
    pipeline_id: str,
    dataset_name: str,
    source_file: str
) -> None:
    """
    Record the complete lineage chain for a standard pipeline run.
    Captures every transformation from raw file to final results.
    """
    steps = [
        {
            "source_name": source_file,
            "source_type": "csv_file",
            "transformation": "data_ingestion",
            "destination_name": f"data/raw/{dataset_name}.csv",
            "destination_type": "csv_file"
        },
        {
            "source_name": f"data/raw/{dataset_name}.csv",
            "source_type": "csv_file",
            "transformation": "data_profiling",
            "destination_name": "profiling_results",
            "destination_type": "postgres_table"
        },
        {
            "source_name": f"data/raw/{dataset_name}.csv",
            "source_type": "csv_file",
            "transformation": "data_validation",
            "destination_name": "validation_results",
            "destination_type": "postgres_table"
        },
        {
            "source_name": f"data/raw/{dataset_name}.csv",
            "source_type": "csv_file",
            "transformation": "anomaly_detection",
            "destination_name": "anomaly_results",
            "destination_type": "postgres_table"
        },
        {
            "source_name": f"data/raw/{dataset_name}.csv",
            "source_type": "csv_file",
            "transformation": "drift_detection",
            "destination_name": "drift_results",
            "destination_type": "postgres_table"
        },
        {
            "source_name": "anomaly_results",
            "source_type": "postgres_table",
            "transformation": "alerting",
            "destination_name": "alerts",
            "destination_type": "postgres_table"
        },
        {
            "source_name": "profiling_results",
            "source_type": "postgres_table",
            "transformation": "dashboard_rendering",
            "destination_name": "streamlit_dashboard",
            "destination_type": "dashboard"
        }
    ]

    for step in steps:
        record_lineage(
            pipeline_id=pipeline_id,
            **step
        )

    logger.info(f"Full lineage recorded for pipeline {pipeline_id} on dataset {dataset_name}")


def get_lineage(pipeline_id: str) -> list[dict]:
    """
    Get the full lineage chain for a pipeline run.
    """
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

    columns = [
        "source_name", "source_type", "transformation",
        "destination_name", "destination_type", "run_date"
    ]

    return [dict(zip(columns, row)) for row in rows]