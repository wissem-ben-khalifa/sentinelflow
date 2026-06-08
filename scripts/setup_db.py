"""
SentinelFlow - Database Setup
Creates all PostgreSQL tables needed by the platform.
Run this once before starting the pipeline.
"""

import psycopg2
from psycopg2 import sql
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
    """Create and return a PostgreSQL connection."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def create_tables(conn):
    """Create all SentinelFlow tables."""
    cursor = conn.cursor()


    # Profiling Results

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiling_results (
            id                  SERIAL PRIMARY KEY,
            dataset_name        VARCHAR(100) NOT NULL,
            column_name         VARCHAR(100) NOT NULL,
            run_date            TIMESTAMP NOT NULL DEFAULT NOW(),
            row_count           INTEGER,
            null_count          INTEGER,
            missing_percentage  FLOAT,
            duplicate_count     INTEGER,
            duplicate_ratio     FLOAT,
            mean                FLOAT,
            median              FLOAT,
            std                 FLOAT,
            min_value           FLOAT,
            max_value           FLOAT,
            skewness            FLOAT,
            kurtosis            FLOAT,
            q25                 FLOAT,
            q75                 FLOAT
        );
    """)
    logger.info("Created table: profiling_results")


    # Validation Results

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_results (
            id                  SERIAL PRIMARY KEY,
            dataset_name        VARCHAR(100) NOT NULL,
            run_date            TIMESTAMP NOT NULL DEFAULT NOW(),
            expectation_type    VARCHAR(200) NOT NULL,
            column_name         VARCHAR(100),
            success             BOOLEAN NOT NULL,
            observed_value      TEXT,
            expected_value      TEXT,
            severity            VARCHAR(20) DEFAULT 'warning'
        );
    """)
    logger.info("Created table: validation_results")


    # Anomaly Results

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_results (
            id                  SERIAL PRIMARY KEY,
            dataset_name        VARCHAR(100) NOT NULL,
            run_date            TIMESTAMP NOT NULL DEFAULT NOW(),
            detection_method    VARCHAR(50) NOT NULL,
            record_id           INTEGER,
            anomaly_score       FLOAT,
            is_anomaly          BOOLEAN NOT NULL,
            features_used       TEXT,
            explanation         TEXT
        );
    """)
    logger.info("Created table: anomaly_results")


    # Drift Results

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drift_results (
            id                  SERIAL PRIMARY KEY,
            dataset_name        VARCHAR(100) NOT NULL,
            column_name         VARCHAR(100) NOT NULL,
            run_date            TIMESTAMP NOT NULL DEFAULT NOW(),
            detection_method    VARCHAR(50) NOT NULL,
            drift_score         FLOAT,
            drift_detected      BOOLEAN NOT NULL,
            baseline_mean       FLOAT,
            current_mean        FLOAT,
            baseline_std        FLOAT,
            current_std         FLOAT
        );
    """)
    logger.info("Created table: drift_results")


    # Pipeline Metadata

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            id                  SERIAL PRIMARY KEY,
            pipeline_id         VARCHAR(100) NOT NULL,
            dataset_name        VARCHAR(100) NOT NULL,
            source              VARCHAR(200),
            owner               VARCHAR(100),
            run_date            TIMESTAMP NOT NULL DEFAULT NOW(),
            execution_time_sec  FLOAT,
            row_count           INTEGER,
            quality_score       FLOAT,
            anomaly_count       INTEGER,
            drift_detected      BOOLEAN DEFAULT FALSE,
            status              VARCHAR(20) DEFAULT 'success'
        );
    """)
    logger.info("Created table: pipeline_metadata")


    # Lineage Tracking

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lineage (
            id                  SERIAL PRIMARY KEY,
            pipeline_id         VARCHAR(100) NOT NULL,
            source_name         VARCHAR(200) NOT NULL,
            source_type         VARCHAR(50),
            transformation      VARCHAR(200),
            destination_name    VARCHAR(200) NOT NULL,
            destination_type    VARCHAR(50),
            run_date            TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    logger.info("Created table: lineage")


    # Alerts

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id                  SERIAL PRIMARY KEY,
            alert_type          VARCHAR(100) NOT NULL,
            dataset_name        VARCHAR(100),
            message             TEXT NOT NULL,
            severity            VARCHAR(20) DEFAULT 'warning',
            triggered_at        TIMESTAMP NOT NULL DEFAULT NOW(),
            resolved            BOOLEAN DEFAULT FALSE,
            resolved_at         TIMESTAMP
        );
    """)
    logger.info("Created table: alerts")

    conn.commit()
    cursor.close()
    logger.info("All tables created successfully")


def verify_tables(conn):
    """Print all created tables to confirm setup."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    cursor.close()

    logger.info(f"Tables in database ({len(tables)} total):")
    for table in tables:
        logger.info(f"  {table[0]}")


def main():
    logger.info("Connecting to PostgreSQL")
    conn = get_connection()
    logger.info("Connected successfully")

    create_tables(conn)
    verify_tables(conn)

    conn.close()
    logger.info("Database setup complete")


if __name__ == "__main__":
    main()