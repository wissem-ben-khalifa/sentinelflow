"""
SentinelFlow - Full Pipeline Runner
Runs the complete batch pipeline end to end in one command.
Order of execution:
    1. Data generation
    2. Data profiling
    3. Data validation
    4. Anomaly detection (Isolation Forest + Autoencoder + Statistical)
    5. Drift detection
    6. Metadata recording
    7. Lineage recording
    8. Alert checks
"""

import time
import uuid
import pandas as pd
from datetime import datetime
from config.settings import RAW_DATA_DIR, SAMPLES_DIR
from config.logging_config import get_logger
from ingestion.batch.generate_data import generate_all
from profiling.profiler import run_profiler, get_quality_score
from validation.expectations import run_validation
from detection.isolation_forest.train import run_isolation_forest
from detection.autoencoder.train import run_autoencoder
from detection.statistical.runner import run_statistical_detection
from detection.drift.runner import run_drift_detection
from metadata.tracker import record_pipeline_run
from metadata.lineage import record_full_pipeline_lineage
from alerting.alert_manager import run_all_checks

logger = get_logger(__name__)

DATASETS = ["users", "products", "orders"]


def run_step(step_name: str, func, *args, **kwargs):
    """
    Run a single pipeline step with timing and error handling.
    Returns the result and elapsed time.
    """
    logger.info(f"Starting step: {step_name}")
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = round(time.time() - start, 2)
        logger.info(f"Completed step: {step_name} in {elapsed}s")
        return result, elapsed
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        logger.error(f"Failed step: {step_name} after {elapsed}s — {e}")
        raise


def run_full_pipeline(
    regenerate_data: bool = True,
    run_autoencoder_detection: bool = True
) -> dict:
    """
    Run the complete SentinelFlow batch pipeline.

    regenerate_data: if True generates fresh data with injected issues
    run_autoencoder_detection: if False skips autoencoder to save time
    """
    pipeline_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    pipeline_start = time.time()

    logger.info(f"Starting SentinelFlow pipeline: {pipeline_id}")
    logger.info(f"Datasets: {DATASETS}")

    report = {
        "pipeline_id": pipeline_id,
        "started_at": datetime.now().isoformat(),
        "steps": {},
        "datasets": {}
    }

    # Step 1 - Data Generation
    if regenerate_data:
        datasets, elapsed = run_step("data_generation", generate_all, inject_issues=True)
        report["steps"]["data_generation"] = {"status": "success", "elapsed": elapsed}
    else:
        logger.info("Skipping data generation, using existing data")
        datasets = {
            name: pd.read_csv(RAW_DATA_DIR / f"{name}.csv")
            for name in DATASETS
        }

    # Steps per dataset
    for dataset_name in DATASETS:
        logger.info(f"Processing dataset: {dataset_name}")
        dataset_report = {}
        df = pd.read_csv(RAW_DATA_DIR / f"{dataset_name}.csv")

        # Step 2 - Profiling
        profiling_results, elapsed = run_step(
            f"profiling_{dataset_name}",
            run_profiler,
            df,
            dataset_name
        )
        quality_score = get_quality_score(profiling_results)
        dataset_report["profiling"] = {
            "status": "success",
            "elapsed": elapsed,
            "quality_score": quality_score
        }

        # Step 3 - Validation
        validation_results, elapsed = run_step(
            f"validation_{dataset_name}",
            run_validation,
            df,
            dataset_name
        )
        passed = sum(1 for r in validation_results if r["success"])
        failed = sum(1 for r in validation_results if not r["success"])
        dataset_report["validation"] = {
            "status": "success",
            "elapsed": elapsed,
            "passed": passed,
            "failed": failed
        }

        # Step 4a - Isolation Forest
        if_summary, elapsed = run_step(
            f"isolation_forest_{dataset_name}",
            run_isolation_forest,
            dataset_name
        )
        dataset_report["isolation_forest"] = {
            "status": "success",
            "elapsed": elapsed,
            "anomaly_count": if_summary.get("anomaly_count", 0)
        }

        # Step 4b - Autoencoder
        if run_autoencoder_detection:
            ae_summary, elapsed = run_step(
                f"autoencoder_{dataset_name}",
                run_autoencoder,
                dataset_name,
                50
            )
            dataset_report["autoencoder"] = {
                "status": "success",
                "elapsed": elapsed,
                "anomaly_count": ae_summary.get("anomaly_count", 0)
            }

        # Step 4c - Statistical Detection
        stat_summary, elapsed = run_step(
            f"statistical_{dataset_name}",
            run_statistical_detection,
            dataset_name
        )
        dataset_report["statistical"] = {
            "status": "success",
            "elapsed": elapsed,
            "zscore_anomalies": stat_summary.get("zscore_anomalies", 0),
            "iqr_anomalies": stat_summary.get("iqr_anomalies", 0)
        }

        # Step 5 - Drift Detection
        drift_summary, elapsed = run_step(
            f"drift_{dataset_name}",
            run_drift_detection,
            dataset_name
        )
        drift_detected = drift_summary.get("drift_detected_count", 0) > 0
        dataset_report["drift"] = {
            "status": "success",
            "elapsed": elapsed,
            "drift_detected": drift_detected
        }

        # Step 6 - Metadata Recording
        total_anomalies = if_summary.get("anomaly_count", 0)
        record_pipeline_run(
            pipeline_id=pipeline_id,
            dataset_name=dataset_name,
            source=f"data/raw/{dataset_name}.csv",
            owner="sentinelflow",
            execution_time_sec=round(time.time() - pipeline_start, 2),
            row_count=len(df),
            quality_score=quality_score,
            anomaly_count=total_anomalies,
            drift_detected=drift_detected,
            status="success"
        )

        # Step 7 - Lineage Recording
        record_full_pipeline_lineage(
            pipeline_id=pipeline_id,
            dataset_name=dataset_name,
            source_file=f"data/raw/{dataset_name}.csv"
        )

        report["datasets"][dataset_name] = dataset_report
        logger.info(f"Dataset {dataset_name} complete — quality={quality_score}")

    # Step 8 - Alert Checks
    logger.info("Running alert checks across all datasets")
    alert_totals = {}
    for dataset_name in DATASETS:
        alert_summary, elapsed = run_step(
            f"alerts_{dataset_name}",
            run_all_checks,
            dataset_name
        )
        alert_totals[dataset_name] = alert_summary.get("total_alerts", 0)

    report["alerts"] = alert_totals
    report["total_elapsed"] = round(time.time() - pipeline_start, 2)
    report["completed_at"] = datetime.now().isoformat()
    report["status"] = "success"

    logger.info(f"Pipeline {pipeline_id} completed in {report['total_elapsed']}s")

    return report


def print_report(report: dict) -> None:
    """Print a clean summary of the pipeline run."""
    print(f"\npipeline id    : {report['pipeline_id']}")
    print(f"started at     : {report['started_at']}")
    print(f"completed at   : {report['completed_at']}")
    print(f"total elapsed  : {report['total_elapsed']}s")
    print(f"status         : {report['status']}")
    print(f"\ndataset results:")

    for dataset, steps in report["datasets"].items():
        quality = steps.get("profiling", {}).get("quality_score", "n/a")
        anomalies = steps.get("isolation_forest", {}).get("anomaly_count", "n/a")
        drift = steps.get("drift", {}).get("drift_detected", False)
        validation_failed = steps.get("validation", {}).get("failed", "n/a")
        print(
            f"  {dataset:12} "
            f"quality={quality:6} | "
            f"anomalies={anomalies:5} | "
            f"drift={str(drift):5} | "
            f"validation_failed={validation_failed}"
        )

    print(f"\nalerts triggered:")
    for dataset, count in report.get("alerts", {}).items():
        print(f"  {dataset:12} {count} alerts")


if __name__ == "__main__":
    report = run_full_pipeline(
        regenerate_data=True,
        run_autoencoder_detection=True
    )
    print_report(report)