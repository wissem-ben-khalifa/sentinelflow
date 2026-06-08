"""
SentinelFlow - Jensen-Shannon Divergence
Measures similarity between two probability distributions.
Symmetric version of KL divergence, always between 0 and 1.

JS = 0: identical distributions
JS < 0.1: very similar
JS 0.1-0.3: moderate difference
JS > 0.3: significant difference
"""

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from config.logging_config import get_logger

logger = get_logger(__name__)


def js_divergence_detect(
    baseline: pd.Series,
    current: pd.Series,
    bins: int = 10,
    threshold: float = 0.3
) -> dict:
    """
    Calculate Jensen-Shannon divergence between two distributions.

    Returns a dict with js_score and drift_detected.
    """
    baseline_clean = pd.to_numeric(baseline, errors="coerce").dropna()
    current_clean = pd.to_numeric(current, errors="coerce").dropna()

    if len(baseline_clean) == 0 or len(current_clean) == 0:
        logger.warning("Empty series passed to JS divergence")
        return {
            "js_score": None,
            "drift_detected": False,
            "interpretation": "insufficient data"
        }

    breakpoints = np.linspace(
        min(baseline_clean.min(), current_clean.min()),
        max(baseline_clean.max(), current_clean.max()),
        bins + 1
    )

    baseline_counts, _ = np.histogram(baseline_clean, bins=breakpoints)
    current_counts, _ = np.histogram(current_clean, bins=breakpoints)

    baseline_pct = baseline_counts / len(baseline_clean)
    current_pct = current_counts / len(current_clean)

    baseline_pct = np.where(baseline_pct == 0, 1e-6, baseline_pct)
    current_pct = np.where(current_pct == 0, 1e-6, current_pct)

    js_score = float(jensenshannon(baseline_pct, current_pct))
    drift_detected = js_score > threshold

    if js_score < 0.1:
        interpretation = "distributions are very similar"
    elif js_score < 0.3:
        interpretation = "moderate distributional difference"
    else:
        interpretation = "significant distributional shift detected"

    logger.info(f"JS divergence: {js_score:.4f} — {interpretation}")

    return {
        "js_score": round(js_score, 6),
        "drift_detected": drift_detected,
        "interpretation": interpretation,
        "baseline_mean": float(baseline_clean.mean()),
        "current_mean": float(current_clean.mean()),
        "baseline_std": float(baseline_clean.std()),
        "current_std": float(current_clean.std())
    }


def run_js_on_dataframe(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    columns: list,
    dataset_name: str
) -> list[dict]:
    """
    Run JS divergence on multiple columns between two dataframes.
    Returns a list of result dicts ready for database insertion.
    """
    results = []

    for col in columns:
        if col not in baseline_df.columns or col not in current_df.columns:
            logger.warning(f"Column {col} not found in one of the dataframes")
            continue

        js_result = js_divergence_detect(baseline_df[col], current_df[col])

        results.append({
            "dataset_name": dataset_name,
            "column_name": col,
            "detection_method": "js_divergence",
            "drift_score": js_result["js_score"],
            "drift_detected": js_result["drift_detected"],
            "baseline_mean": js_result["baseline_mean"],
            "current_mean": js_result["current_mean"],
            "baseline_std": js_result["baseline_std"],
            "current_std": js_result["current_std"]
        })

    return results