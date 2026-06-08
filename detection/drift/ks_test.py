"""
SentinelFlow - Kolmogorov-Smirnov Test
Compares two distributions to detect if they are
statistically significantly different.

p-value < 0.05: distributions are significantly different (drift detected)
p-value >= 0.05: no significant difference detected
"""

import numpy as np
import pandas as pd
from scipy import stats
from config.logging_config import get_logger

logger = get_logger(__name__)


def ks_test_detect(
    baseline: pd.Series,
    current: pd.Series,
    significance_level: float = 0.05
) -> dict:
    """
    Run KS test between baseline and current distributions.

    Returns a dict with ks_statistic, p_value, and drift_detected.
    """
    baseline_clean = pd.to_numeric(baseline, errors="coerce").dropna()
    current_clean = pd.to_numeric(current, errors="coerce").dropna()

    if len(baseline_clean) == 0 or len(current_clean) == 0:
        logger.warning("Empty series passed to KS test")
        return {
            "ks_statistic": None,
            "p_value": None,
            "drift_detected": False,
            "interpretation": "insufficient data"
        }

    ks_statistic, p_value = stats.ks_2samp(baseline_clean, current_clean)

    drift_detected = p_value < significance_level

    if drift_detected:
        interpretation = (
            f"distributions are significantly different "
            f"(p={p_value:.4f} < {significance_level})"
        )
    else:
        interpretation = (
            f"no significant difference detected "
            f"(p={p_value:.4f} >= {significance_level})"
        )

    logger.info(f"KS test: statistic={ks_statistic:.4f}, p={p_value:.4f} — {interpretation}")

    return {
        "ks_statistic": round(float(ks_statistic), 6),
        "p_value": round(float(p_value), 6),
        "drift_detected": drift_detected,
        "interpretation": interpretation,
        "baseline_mean": float(baseline_clean.mean()),
        "current_mean": float(current_clean.mean()),
        "baseline_std": float(baseline_clean.std()),
        "current_std": float(current_clean.std())
    }


def run_ks_on_dataframe(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    columns: list,
    dataset_name: str
) -> list[dict]:
    """
    Run KS test on multiple columns between two dataframes.
    Returns a list of result dicts ready for database insertion.
    """
    results = []

    for col in columns:
        if col not in baseline_df.columns or col not in current_df.columns:
            logger.warning(f"Column {col} not found in one of the dataframes")
            continue

        ks_result = ks_test_detect(baseline_df[col], current_df[col])

        results.append({
            "dataset_name": dataset_name,
            "column_name": col,
            "detection_method": "ks_test",
            "drift_score": ks_result["ks_statistic"],
            "drift_detected": ks_result["drift_detected"],
            "baseline_mean": ks_result["baseline_mean"],
            "current_mean": ks_result["current_mean"],
            "baseline_std": ks_result["baseline_std"],
            "current_std": ks_result["current_std"]
        })

    return results