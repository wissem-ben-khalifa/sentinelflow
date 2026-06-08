"""
SentinelFlow - Isolation Forest Training and Detection
Trains on clean data, detects anomalies in raw data,
and saves results to PostgreSQL.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import psycopg2
from config.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    RAW_DATA_DIR,
    SAMPLES_DIR,
    ANOMALY_SCORE_THRESHOLD
)
from config.logging_config import get_logger
from detection.isolation_forest.model import IsolationForestDetector

logger = get_logger(__name__)

# Features to use for each dataset
FEATURE_CONFIG = {
    "orders": ["amount", "quantity"],
    "products": ["price", "stock"],
    "users": ["age"]
}


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def save_anomaly_results(results: list[dict], conn) -> None:
    """Insert anomaly detection results into PostgreSQL."""
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO anomaly_results (
            dataset_name, run_date, detection_method,
            record_id, anomaly_score, is_anomaly,
            features_used, explanation
        ) VALUES (
            %(dataset_name)s, %(run_date)s, %(detection_method)s,
            %(record_id)s, %(anomaly_score)s, %(is_anomaly)s,
            %(features_used)s, %(explanation)s
        )
    """

    for result in results:
        cursor.execute(insert_query, result)

    conn.commit()
    cursor.close()
    logger.info(f"Saved {len(results)} anomaly results to database")


def build_explanation(row: pd.Series, feature_columns: list) -> str:
    """Build a human readable explanation for an anomaly."""
    parts = []
    for col in feature_columns:
        parts.append(f"{col}={row[col]}")
    return "Unusual combination detected: " + ", ".join(parts)


def run_isolation_forest(dataset_name: str) -> dict:
    """
    Full pipeline for one dataset:
    1. Load clean data and train the model
    2. Load raw data and detect anomalies
    3. Save results to PostgreSQL
    """
    if dataset_name not in FEATURE_CONFIG:
        logger.warning(f"No feature config for dataset: {dataset_name}")
        return {}

    feature_columns = FEATURE_CONFIG[dataset_name]

    # Load clean training data
    clean_path = SAMPLES_DIR / f"{dataset_name}_clean.csv"
    raw_path = RAW_DATA_DIR / f"{dataset_name}.csv"

    clean_df = pd.read_csv(clean_path)
    raw_df = pd.read_csv(raw_path)

    # Train on clean data
    detector = IsolationForestDetector(contamination=0.05)
    detector.train(clean_df, feature_columns)
    detector.save(dataset_name)

    # Detect anomalies in raw data
    result_df = detector.predict(raw_df)

    # Build records for database
    id_column = f"{dataset_name[:-1]}_id" if dataset_name != "orders" else "order_id"
    if dataset_name == "users":
        id_column = "user_id"
    elif dataset_name == "products":
        id_column = "product_id"
    elif dataset_name == "orders":
        id_column = "order_id"

    records = []
    for _, row in result_df.iterrows():
        record_id = int(row[id_column]) if pd.notna(row[id_column]) else None
        records.append({
            "dataset_name": dataset_name,
            "run_date": datetime.now(),
            "detection_method": "isolation_forest",
            "record_id": record_id,
            "anomaly_score": float(row["anomaly_score"]),
            "is_anomaly": bool(row["is_anomaly"]),
            "features_used": str(feature_columns),
            "explanation": build_explanation(row, feature_columns) if row["is_anomaly"] else None
        })

    conn = get_connection()
    save_anomaly_results(records, conn)
    conn.close()

    anomaly_count = int(result_df["is_anomaly"].sum())
    high_score_count = int((result_df["anomaly_score"] > ANOMALY_SCORE_THRESHOLD).sum())

    summary = {
        "dataset": dataset_name,
        "total_records": len(result_df),
        "anomaly_count": anomaly_count,
        "anomaly_rate": round(anomaly_count / len(result_df) * 100, 2),
        "high_score_count": high_score_count
    }

    logger.info(
        f"{dataset_name}: {anomaly_count} anomalies detected "
        f"({summary['anomaly_rate']}% of records)"
    )

    return summary


if __name__ == "__main__":
    datasets = ["users", "products", "orders"]

    for dataset in datasets:
        summary = run_isolation_forest(dataset)
        print(
            f"{summary['dataset']}: "
            f"{summary['anomaly_count']} anomalies / "
            f"{summary['total_records']} records "
            f"({summary['anomaly_rate']}%)"
        )