"""
SentinelFlow - Airflow Batch Pipeline DAG
Schedules the full batch pipeline to run daily at midnight.
"""
import sys
import os
sys.path.insert(0, "/opt/airflow/project")
os.environ.setdefault("POSTGRES_HOST", "postgres")
os.environ.setdefault("POSTGRES_PORT", "5432")
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "sentinelflow",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

dag = DAG(
    "sentinelflow_batch_pipeline",
    default_args=default_args,
    description="Daily batch pipeline for data quality and anomaly detection",
    schedule_interval="0 0 * * *",
    catchup=False,
    tags=["sentinelflow", "batch", "quality"]
)


def run_data_generation():
    from ingestion.batch.generate_data import generate_all
    generate_all(inject_issues=True)


def run_profiling():
    import pandas as pd
    from profiling.profiler import run_profiler
    from config.settings import RAW_DATA_DIR

    for dataset in ["users", "products", "orders"]:
        df = pd.read_csv(RAW_DATA_DIR / f"{dataset}.csv")
        run_profiler(df, dataset)


def run_validation():
    import pandas as pd
    from validation.expectations import run_validation
    from config.settings import RAW_DATA_DIR

    for dataset in ["users", "products", "orders"]:
        df = pd.read_csv(RAW_DATA_DIR / f"{dataset}.csv")
        run_validation(df, dataset)


def run_anomaly_detection():
    from detection.isolation_forest.train import run_isolation_forest
    from detection.statistical.runner import run_statistical_detection

    for dataset in ["users", "products", "orders"]:
        run_isolation_forest(dataset)
        run_statistical_detection(dataset)


def run_drift_detection():
    from detection.drift.runner import run_drift_detection

    for dataset in ["users", "products", "orders"]:
        run_drift_detection(dataset)


def run_alerts():
    from alerting.alert_manager import run_all_checks

    for dataset in ["users", "products", "orders"]:
        run_all_checks(dataset)


generate_task = PythonOperator(
    task_id="generate_data",
    python_callable=run_data_generation,
    dag=dag
)

profiling_task = PythonOperator(
    task_id="run_profiling",
    python_callable=run_profiling,
    dag=dag
)

validation_task = PythonOperator(
    task_id="run_validation",
    python_callable=run_validation,
    dag=dag
)

anomaly_task = PythonOperator(
    task_id="run_anomaly_detection",
    python_callable=run_anomaly_detection,
    dag=dag
)

drift_task = PythonOperator(
    task_id="run_drift_detection",
    python_callable=run_drift_detection,
    dag=dag
)

alert_task = PythonOperator(
    task_id="run_alerts",
    python_callable=run_alerts,
    dag=dag
)

generate_task >> profiling_task >> validation_task >> anomaly_task >> drift_task >> alert_task