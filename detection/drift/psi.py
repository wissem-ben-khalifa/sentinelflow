"""
SentinelFlow - Population Stability Index (PSI)
Measures how much a distribution has shifted between
a baseline period and a current period.

PSI < 0.1:  No significant change
PSI 0.1-0.25: Moderate change, monitor closely
PSI > 0.25: Significant change, action required
"""

import numpy as np
import pandas as pd
from config.logging_config import get_logger

logger = get_logger(__name__)


def calculate_psi(
    baseline: pd.Series,
    current: pd.Series,
    bins: int = 10
) -> dict:
    """
    Calculate PSI between baseline and current distributions.

    baseline: historical data series (what we expect)
    current: new incoming data series (what we have now)
    bins: number of buckets to use for binning

    Returns a dict with psi_score and interpretation.
    """
    baseline_clean = pd.to_numeric(baseline, errors="coerce").dropna()
    current_clean = pd.to_numeric(current, errors="coerce").dropna()

    if len(baseline_clean) == 0 or len(current_clean) == 0:
        logger.warning("Empty series passed to PSI calculation")
        return {
            "psi_score": None,
            "drift_detected": False,
            "interpretation": "insufficient data"
        }

    # Create bins based on baseline distribution
    breakpoints = np.linspace(
        min(baseline_clean.min(), current_clean.min()),
        max(baseline_clean.max(), current_clean.max()),
        bins + 1
    )

    # Calculate proportions in each bin
    baseline_counts, _ = np.histogram(baseline_clean, bins=breakpoints)
    current_counts, _ = np.histogram(current_clean, bins=breakpoints)

    baseline_pct = baseline_counts / len(baseline_clean)
    current_pct = current_counts / len(current_clean)

    # Avoid division by zero and log of zero
    baseline_pct = np.where(baseline_pct == 0, 1e-6, baseline_pct)
    current_pct = np.where(current_pct == 0, 1e-6, current_pct)

    # PSI formula
    psi_values = (current_pct - baseline_pct) * np.log(current_pct / baseline_pct)
    psi_score = float(np.sum(psi_values))

    drift_detected = psi_score > 0.25

    if psi_score < 0.1:
        interpretation = "no significant change"
    elif psi_score < 0.25:
        interpretation = "moderate change, monitor closely"
    else:
        interpretation = "significant change, action required"

    logger.info(f"PSI score: {psi_score:.4f} — {interpretation}")

    return {
        "psi_score": round(psi_score, 6),
        "drift_detected": drift_detected,
        "interpretation": interpretation,
        "baseline_mean": float(baseline_clean.mean()),
        "current_mean": float(current_clean.mean()),
        "baseline_std": float(baseline_clean.std()),
        "current_std": float(current_clean.std())
    }


def run_psi_on_dataframe(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    columns: list,
    dataset_name: str
) -> list[dict]:
    """
    Run PSI on multiple columns between two dataframes.
    Returns a list of result dicts ready for database insertion.
    """
    results = []

    for col in columns:
        if col not in baseline_df.columns or col not in current_df.columns:
            logger.warning(f"Column {col} not found in one of the dataframes")
            continue

        psi_result = calculate_psi(baseline_df[col], current_df[col])

        results.append({
            "dataset_name": dataset_name,
            "column_name": col,
            "detection_method": "psi",
            "drift_score": psi_result["psi_score"],
            "drift_detected": psi_result["drift_detected"],
            "baseline_mean": psi_result["baseline_mean"],
            "current_mean": psi_result["current_mean"],
            "baseline_std": psi_result["baseline_std"],
            "current_std": psi_result["current_std"]
        })

    return results