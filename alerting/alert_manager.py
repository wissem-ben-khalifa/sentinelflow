"""
SentinelFlow - Alert Manager
Evaluates detection results against thresholds
and triggers alerts when violations are found.
Stores all alerts in PostgreSQL.
"""

import psycopg2
from datetime import datetime
from config.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    ANOMALY_SCORE_THRESHOLD,
    MISSING_VALUES_THRESHOLD,
    PSI_THRESHOLD
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


def save_alert(
    alert_type: str,
    dataset_name: str,
    message: str,
    severity: str = "warning"
) -> int:
    """
    Save a single alert to the database.
    Returns the inserted alert id.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts (
            alert_type, dataset_name, message,
            severity, triggered_at, resolved
        ) VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        alert_type,
        dataset_name,
        message,
        severity,
        datetime.now(),
        False
    ))

    alert_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    logger.warning(f"ALERT [{severity.upper()}] {alert_type} | {dataset_name} | {message}")

    return alert_id


def check_missing_values_alert(dataset_name: str) -> list[dict]:
    """
    Check profiling results for missing value threshold violations.
    Triggers alert if missing_percentage > MISSING_VALUES_THRESHOLD.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT column_name, missing_percentage
        FROM profiling_results
        WHERE dataset_name = %s
        AND missing_percentage > %s
        ORDER BY run_date DESC
    """, (dataset_name, MISSING_VALUES_THRESHOLD * 100))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    alerts = []
    for column_name, missing_pct in rows:
        message = (
            f"Column '{column_name}' in '{dataset_name}' has "
            f"{missing_pct:.2f}% missing values "
            f"(threshold: {MISSING_VALUES_THRESHOLD * 100:.0f}%)"
        )
        alert_id = save_alert(
            alert_type="missing_values",
            dataset_name=dataset_name,
            message=message,
            severity="warning"
        )
        alerts.append({"id": alert_id, "message": message})

    return alerts


def check_anomaly_alerts(dataset_name: str) -> list[dict]:
    """
    Check anomaly results for high anomaly rates.
    Triggers alert if anomaly rate exceeds threshold.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            detection_method,
            COUNT(*) as total,
            SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomaly_count
        FROM anomaly_results
        WHERE dataset_name = %s
        GROUP BY detection_method
    """, (dataset_name,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    alerts = []
    for method, total, anomaly_count in rows:
        if total == 0:
            continue
        anomaly_rate = anomaly_count / total
        if anomaly_rate > ANOMALY_SCORE_THRESHOLD:
            message = (
                f"High anomaly rate detected in '{dataset_name}' "
                f"using {method}: {anomaly_count}/{total} records "
                f"({anomaly_rate * 100:.2f}%) flagged as anomalies"
            )
            alert_id = save_alert(
                alert_type="high_anomaly_rate",
                dataset_name=dataset_name,
                message=message,
                severity="critical"
            )
            alerts.append({"id": alert_id, "message": message})

    return alerts


def check_drift_alerts(dataset_name: str) -> list[dict]:
    """
    Check drift results for PSI threshold violations.
    Triggers alert if any drift is detected.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT column_name, detection_method, drift_score
        FROM drift_results
        WHERE dataset_name = %s
        AND drift_detected = TRUE
        ORDER BY run_date DESC
    """, (dataset_name,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    alerts = []
    seen = set()
    for column_name, method, drift_score in rows:
        key = f"{column_name}_{method}"
        if key in seen:
            continue
        seen.add(key)

        message = (
            f"Data drift detected in '{dataset_name}' column '{column_name}' "
            f"using {method}: score={drift_score:.4f}"
        )
        alert_id = save_alert(
            alert_type="data_drift",
            dataset_name=dataset_name,
            message=message,
            severity="warning"
        )
        alerts.append({"id": alert_id, "message": message})

    return alerts


def check_validation_alerts(dataset_name: str) -> list[dict]:
    """
    Check validation results for critical failures.
    Triggers alert for any critical severity validation failure.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT expectation_type, column_name, observed_value
        FROM validation_results
        WHERE dataset_name = %s
        AND success = FALSE
        AND severity = 'critical'
        ORDER BY run_date DESC
    """, (dataset_name,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    alerts = []
    seen = set()
    for expectation_type, column_name, observed_value in rows:
        key = f"{expectation_type}_{column_name}"
        if key in seen:
            continue
        seen.add(key)

        message = (
            f"Critical validation failure in '{dataset_name}': "
            f"{expectation_type} on column '{column_name}' — {observed_value}"
        )
        alert_id = save_alert(
            alert_type="validation_failure",
            dataset_name=dataset_name,
            message=message,
            severity="critical"
        )
        alerts.append({"id": alert_id, "message": message})

    return alerts

def clear_alerts(dataset_name: str) -> None:
    """Clear existing unresolved alerts for a dataset before inserting new ones."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM alerts
        WHERE dataset_name = %s
        AND resolved = FALSE
    """, (dataset_name,))
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Cleared existing alerts for dataset: {dataset_name}")

def run_all_checks(dataset_name: str) -> dict:
    """
    Run all alert checks for a dataset.
    Returns a summary of all alerts triggered.
    """
    clear_alerts(dataset_name)
    logger.info(f"Running alert checks for dataset: {dataset_name}")

    missing_alerts = check_missing_values_alert(dataset_name)
    anomaly_alerts = check_anomaly_alerts(dataset_name)
    drift_alerts = check_drift_alerts(dataset_name)
    validation_alerts = check_validation_alerts(dataset_name)

    total = (
        len(missing_alerts) +
        len(anomaly_alerts) +
        len(drift_alerts) +
        len(validation_alerts)
    )

    summary = {
        "dataset": dataset_name,
        "missing_value_alerts": len(missing_alerts),
        "anomaly_alerts": len(anomaly_alerts),
        "drift_alerts": len(drift_alerts),
        "validation_alerts": len(validation_alerts),
        "total_alerts": total
    }

    logger.info(
        f"{dataset_name} alert summary: "
        f"{total} total alerts triggered"
    )

    return summary


if __name__ == "__main__":
    datasets = ["users", "products", "orders"]

    for dataset in datasets:
        summary = run_all_checks(dataset)
        print(
            f"{summary['dataset']}: "
            f"missing={summary['missing_value_alerts']} | "
            f"anomaly={summary['anomaly_alerts']} | "
            f"drift={summary['drift_alerts']} | "
            f"validation={summary['validation_alerts']} | "
            f"total={summary['total_alerts']}"
        )