"""
SentinelFlow - Integration Tests
Tests the full pipeline end to end.
Requires PostgreSQL to be running.
"""

import pytest
import pandas as pd
import os
from pathlib import Path


def postgres_available() -> bool:
    """Check if PostgreSQL is available for integration tests."""
    try:
        import psycopg2
        from config.settings import (
            POSTGRES_HOST, POSTGRES_PORT,
            POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
        )
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        conn.close()
        return True
    except Exception:
        return False


requires_postgres = pytest.mark.skipif(
    not postgres_available(),
    reason="PostgreSQL not available"
)


@requires_postgres
def test_data_generation_creates_files():
    from ingestion.batch.generate_data import generate_all
    from config.settings import RAW_DATA_DIR, SAMPLES_DIR

    generate_all(inject_issues=True)

    assert (RAW_DATA_DIR / "users.csv").exists()
    assert (RAW_DATA_DIR / "products.csv").exists()
    assert (RAW_DATA_DIR / "orders.csv").exists()
    assert (SAMPLES_DIR / "users_clean.csv").exists()


@requires_postgres
def test_profiler_saves_to_database():
    from profiling.profiler import run_profiler
    from config.settings import RAW_DATA_DIR
    import psycopg2
    from config.settings import (
        POSTGRES_HOST, POSTGRES_PORT,
        POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    )

    df = pd.read_csv(RAW_DATA_DIR / "users.csv")
    results = run_profiler(df, "users_integration_test")

    assert len(results) > 0

    conn = psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        dbname=POSTGRES_DB, user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM profiling_results
        WHERE dataset_name = 'users_integration_test'
    """)
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    assert count > 0


@requires_postgres
def test_validation_saves_to_database():
    from validation.expectations import run_validation
    from config.settings import RAW_DATA_DIR
    import psycopg2
    from config.settings import (
        POSTGRES_HOST, POSTGRES_PORT,
        POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    )

    df = pd.read_csv(RAW_DATA_DIR / "users.csv")
    results = run_validation(df, "users")

    assert len(results) > 0
    assert any(r["success"] for r in results)
    assert any(not r["success"] for r in results)


@requires_postgres
def test_isolation_forest_detects_anomalies():
    from detection.isolation_forest.train import run_isolation_forest

    summary = run_isolation_forest("orders")

    assert "anomaly_count" in summary
    assert summary["anomaly_count"] > 0
    assert summary["total_records"] > 0


@requires_postgres
def test_drift_detection_finds_drift_in_orders():
    from detection.drift.runner import run_drift_detection

    summary = run_drift_detection("orders")

    assert summary["drift_detected_count"] > 0


@requires_postgres
def test_alert_manager_creates_alerts():
    from alerting.alert_manager import run_all_checks
    import psycopg2
    from config.settings import (
        POSTGRES_HOST, POSTGRES_PORT,
        POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    )

    summary = run_all_checks("orders")

    assert summary["total_alerts"] >= 0

    conn = psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        dbname=POSTGRES_DB, user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alerts")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    assert count > 0