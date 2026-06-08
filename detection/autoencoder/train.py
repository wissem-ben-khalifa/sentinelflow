"""
SentinelFlow - Autoencoder Training and Detection
Trains autoencoder on clean data, detects anomalies in raw data,
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
    SAMPLES_DIR
)
from config.logging_config import get_logger
from detection.autoencoder.model import AutoencoderDetector

logger = get_logger(__name__)

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
    """Insert autoencoder anomaly results into PostgreSQL."""
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
    logger.info(f"Saved {len(results)} autoencoder results to database")


def run_autoencoder(dataset_name: str, epochs: int = 50) -> dict:
    """
    Full autoencoder pipeline for one dataset.
    Trains on clean data, detects anomalies in raw data,
    saves results to PostgreSQL.
    """
    if dataset_name not in FEATURE_CONFIG:
        logger.warning(f"No feature config for dataset: {dataset_name}")
        return {}

    feature_columns = FEATURE_CONFIG[dataset_name]

    clean_path = SAMPLES_DIR / f"{dataset_name}_clean.csv"
    raw_path = RAW_DATA_DIR / f"{dataset_name}.csv"

    clean_df = pd.read_csv(clean_path)
    raw_df = pd.read_csv(raw_path)

    detector = AutoencoderDetector(threshold_percentile=95)
    detector.train(clean_df, feature_columns, epochs=epochs)
    detector.save(dataset_name)

    result_df = detector.predict(raw_df)

    id_columns = {
        "users": "user_id",
        "products": "product_id",
        "orders": "order_id"
    }
    id_column = id_columns[dataset_name]

    records = []
    for _, row in result_df.iterrows():
        record_id = int(row[id_column]) if pd.notna(row[id_column]) else None
        is_anomaly = bool(row["is_anomaly_ae"])
        explanation = (
            f"Reconstruction error {row['reconstruction_error']:.6f} "
            f"exceeds threshold"
        ) if is_anomaly else None

        records.append({
            "dataset_name": dataset_name,
            "run_date": datetime.now(),
            "detection_method": "autoencoder",
            "record_id": record_id,
            "anomaly_score": float(row["anomaly_score_ae"]),
            "is_anomaly": is_anomaly,
            "features_used": str(feature_columns),
            "explanation": explanation
        })

    conn = get_connection()
    save_anomaly_results(records, conn)
    conn.close()

    anomaly_count = int(result_df["is_anomaly_ae"].sum())
    summary = {
        "dataset": dataset_name,
        "total_records": len(result_df),
        "anomaly_count": anomaly_count,
        "anomaly_rate": round(anomaly_count / len(result_df) * 100, 2)
    }

    logger.info(
        f"{dataset_name}: {anomaly_count} anomalies detected "
        f"({summary['anomaly_rate']}% of records)"
    )

    return summary


if __name__ == "__main__":
    datasets = ["users", "products", "orders"]

    for dataset in datasets:
        summary = run_autoencoder(dataset, epochs=50)
        print(
            f"{summary['dataset']}: "
            f"{summary['anomaly_count']} anomalies / "
            f"{summary['total_records']} records "
            f"({summary['anomaly_rate']}%)"
        )