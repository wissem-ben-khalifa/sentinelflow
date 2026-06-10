"""
SentinelFlow - Airflow Quality Check DAG
Runs lightweight quality checks every hour
without full anomaly detection.
"""
import sys
import os
sys.path.insert(0, "/opt/airflow/project")
os.environ.setdefault("POSTGRES_HOST", "postgres")
os.environ.setdefault("POSTGRES_PORT", "5432")
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "sentinelflow",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2)
}

dag = DAG(
    "sentinelflow_quality_check",
    default_args=default_args,
    description="Hourly lightweight data quality checks",
    schedule_interval="0 * * * *",
    catchup=False,
    tags=["sentinelflow", "quality", "hourly"]
)


def run_quick_profiling():
    import pandas as pd
    from profiling.profiler import run_profiler, get_quality_score
    from config.settings import RAW_DATA_DIR
    from config.logging_config import get_logger

    logger = get_logger(__name__)

    for dataset in ["users", "products", "orders"]:
        df = pd.read_csv(RAW_DATA_DIR / f"{dataset}.csv")
        results = run_profiler(df, dataset)
        score = get_quality_score(results)
        logger.info(f"Quality check: {dataset} score={score}")


def run_quick_validation():
    import pandas as pd
    from validation.expectations import run_validation
    from config.settings import RAW_DATA_DIR

    for dataset in ["users", "products", "orders"]:
        df = pd.read_csv(RAW_DATA_DIR / f"{dataset}.csv")
        run_validation(df, dataset)


def run_quick_alerts():
    from alerting.alert_manager import run_all_checks

    for dataset in ["users", "products", "orders"]:
        run_all_checks(dataset)


profiling_task = PythonOperator(
    task_id="quick_profiling",
    python_callable=run_quick_profiling,
    dag=dag
)

validation_task = PythonOperator(
    task_id="quick_validation",
    python_callable=run_quick_validation,
    dag=dag
)

alert_task = PythonOperator(
    task_id="quick_alerts",
    python_callable=run_quick_alerts,
    dag=dag
)

profiling_task >> validation_task >> alert_task