"""
SentinelFlow - Seed Data Script
Generates and loads initial data into the platform.
Run this once after setup_db.py to populate the system.
"""

from config.logging_config import get_logger
from ingestion.batch.generate_data import generate_all
from ingestion.batch.load_data import run_batch_load
from profiling.profiler import run_profiler, get_quality_score
from validation.expectations import run_validation
from metadata.lineage import record_full_pipeline_lineage
from metadata.tracker import record_pipeline_run
import pandas as pd
import time
import uuid
from datetime import datetime
from config.settings import RAW_DATA_DIR

logger = get_logger(__name__)


def seed(inject_issues: bool = True) -> None:
    """
    Full seed pipeline:
    1. Generate data
    2. Load to PostgreSQL
    3. Run profiling
    4. Run validation
    5. Record metadata
    """
    pipeline_id = f"seed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    start = time.time()

    logger.info(f"Starting data seed: {pipeline_id}")

    logger.info("Generating data")
    generate_all(inject_issues=inject_issues)

    logger.info("Loading data to PostgreSQL")
    run_batch_load()

    datasets = ["users", "products", "orders"]
    for dataset_name in datasets:
        df = pd.read_csv(RAW_DATA_DIR / f"{dataset_name}.csv")

        profiling_results = run_profiler(df, dataset_name)
        quality_score = get_quality_score(profiling_results)

        run_validation(df, dataset_name)

        record_pipeline_run(
            pipeline_id=pipeline_id,
            dataset_name=dataset_name,
            source=f"data/raw/{dataset_name}.csv",
            owner="seed_script",
            execution_time_sec=round(time.time() - start, 2),
            row_count=len(df),
            quality_score=quality_score,
            anomaly_count=0,
            drift_detected=False,
            status="seeded"
        )

        record_full_pipeline_lineage(
            pipeline_id=pipeline_id,
            dataset_name=dataset_name,
            source_file=f"data/raw/{dataset_name}.csv"
        )

    logger.info(f"Seed complete in {round(time.time() - start, 2)}s")


if __name__ == "__main__":
    seed(inject_issues=True)
    print("Seed complete")