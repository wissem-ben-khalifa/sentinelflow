"""
SentinelFlow - Statistical Detection Runner
Runs both Z-Score and IQR detection and saves results to PostgreSQL.
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
    ZSCORE_THRESHOLD
)
from config.logging_config import get_logger
from detection.statistical.zscore import zscore_detect_dataframe
from detection.statistical.iqr import iqr_detect_dataframe

logger = get_logger(__name__)

NUMERIC_COLUMNS = {
    "users": ["age"],
    "products": ["price", "stock"],
    "orders": ["amount", "quantity"]
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
    logger.info(f"Saved {len(results)} statistical detection results to database")


def run_statistical_detection(dataset_name: str) -> dict:
    """
    Run Z-Score and IQR detection on a dataset
    and save results to PostgreSQL.
    """
    if dataset_name not in NUMERIC_COLUMNS:
        logger.warning(f"No column config for dataset: {dataset_name}")
        return {}

    columns = NUMERIC_COLUMNS[dataset_name]
    raw_path = RAW_DATA_DIR / f"{dataset_name}.csv"
    df = pd.read_csv(raw_path)

    zscore_results = zscore_detect_dataframe(df, columns, threshold=ZSCORE_THRESHOLD)
    iqr_results = iqr_detect_dataframe(df, columns, factor=1.5)

    id_columns = {
        "users": "user_id",
        "products": "product_id",
        "orders": "order_id"
    }
    id_column = id_columns[dataset_name]

    records = []
    total_zscore_anomalies = 0
    total_iqr_anomalies = 0

    for col in columns:
        if col in zscore_results:
            zdf = zscore_results[col]
            for idx, row in zdf.iterrows():
                record_id = int(df.loc[idx, id_column]) if pd.notna(df.loc[idx, id_column]) else None
                is_anomaly = bool(row["is_anomaly"])
                if is_anomaly:
                    total_zscore_anomalies += 1
                records.append({
                    "dataset_name": dataset_name,
                    "run_date": datetime.now(),
                    "detection_method": "zscore",
                    "record_id": record_id,
                    "anomaly_score": float(abs(row["zscore"])) if pd.notna(row["zscore"]) else 0.0,
                    "is_anomaly": is_anomaly,
                    "features_used": col,
                    "explanation": row["explanation"] if is_anomaly else None
                })

        if col in iqr_results:
            idf = iqr_results[col]
            for idx, row in idf.iterrows():
                record_id = int(df.loc[idx, id_column]) if pd.notna(df.loc[idx, id_column]) else None
                is_anomaly = bool(row["is_anomaly"])
                if is_anomaly:
                    total_iqr_anomalies += 1
                records.append({
                    "dataset_name": dataset_name,
                    "run_date": datetime.now(),
                    "detection_method": "iqr",
                    "record_id": record_id,
                    "anomaly_score": 1.0 if is_anomaly else 0.0,
                    "is_anomaly": is_anomaly,
                    "features_used": col,
                    "explanation": row["explanation"] if is_anomaly else None
                })

    conn = get_connection()
    save_anomaly_results(records, conn)
    conn.close()

    summary = {
        "dataset": dataset_name,
        "total_records": len(df),
        "zscore_anomalies": total_zscore_anomalies,
        "iqr_anomalies": total_iqr_anomalies
    }

    logger.info(
        f"{dataset_name}: zscore={total_zscore_anomalies} anomalies, "
        f"iqr={total_iqr_anomalies} anomalies"
    )

    return summary


if __name__ == "__main__":
    datasets = ["users", "products", "orders"]

    for dataset in datasets:
        summary = run_statistical_detection(dataset)
        print(
            f"{summary['dataset']}: "
            f"zscore={summary['zscore_anomalies']} | "
            f"iqr={summary['iqr_anomalies']}"
        )