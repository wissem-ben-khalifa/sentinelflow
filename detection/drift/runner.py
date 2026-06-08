"""
SentinelFlow - Drift Detection Runner
Runs PSI, KS-Test, and JS Divergence on all datasets
and saves results to PostgreSQL.
Uses clean data as baseline and drifted data as current.
"""

import pandas as pd
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
from detection.drift.psi import run_psi_on_dataframe
from detection.drift.ks_test import run_ks_on_dataframe
from detection.drift.js_divergence import run_js_on_dataframe

logger = get_logger(__name__)

DRIFT_COLUMNS = {
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


def save_drift_results(results: list[dict], conn) -> None:
    cursor = conn.cursor()
    insert_query = """
        INSERT INTO drift_results (
            dataset_name, column_name, run_date,
            detection_method, drift_score, drift_detected,
            baseline_mean, current_mean,
            baseline_std, current_std
        ) VALUES (
            %(dataset_name)s, %(column_name)s, %(run_date)s,
            %(detection_method)s, %(drift_score)s, %(drift_detected)s,
            %(baseline_mean)s, %(current_mean)s,
            %(baseline_std)s, %(current_std)s
        )
    """
    for result in results:
        result["run_date"] = datetime.now()
        result["drift_detected"] = bool(result["drift_detected"])
        result["drift_score"] = float(result["drift_score"]) if result["drift_score"] is not None else None
        cursor.execute(insert_query, result)
    conn.commit()
    cursor.close()
    logger.info(f"Saved {len(results)} drift results to database")


def run_drift_detection(dataset_name: str) -> dict:
    """
    Run all three drift detection methods for a dataset.
    Uses clean samples as baseline and raw data as current.
    For orders, uses the drifted dataset to simulate real drift.
    """
    if dataset_name not in DRIFT_COLUMNS:
        logger.warning(f"No column config for dataset: {dataset_name}")
        return {}

    columns = DRIFT_COLUMNS[dataset_name]

    baseline_df = pd.read_csv(SAMPLES_DIR / f"{dataset_name}_clean.csv")

    if dataset_name == "orders":
        current_df = pd.read_csv(RAW_DATA_DIR / "orders_drifted.csv")
        logger.info("Using drifted orders dataset to simulate distribution shift")
    else:
        current_df = pd.read_csv(RAW_DATA_DIR / f"{dataset_name}.csv")

    all_results = []
    all_results.extend(run_psi_on_dataframe(baseline_df, current_df, columns, dataset_name))
    all_results.extend(run_ks_on_dataframe(baseline_df, current_df, columns, dataset_name))
    all_results.extend(run_js_on_dataframe(baseline_df, current_df, columns, dataset_name))

    conn = get_connection()
    save_drift_results(all_results, conn)
    conn.close()

    drift_detected_count = sum(1 for r in all_results if r["drift_detected"])

    summary = {
        "dataset": dataset_name,
        "total_checks": len(all_results),
        "drift_detected_count": drift_detected_count
    }

    logger.info(
        f"{dataset_name}: {drift_detected_count}/{len(all_results)} "
        f"drift checks triggered"
    )

    return summary


if __name__ == "__main__":
    datasets = ["users", "products", "orders"]

    for dataset in datasets:
        summary = run_drift_detection(dataset)
        print(
            f"{summary['dataset']}: "
            f"{summary['drift_detected_count']}/{summary['total_checks']} "
            f"drift checks triggered"
        )