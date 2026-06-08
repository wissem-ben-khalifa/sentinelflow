"""
SentinelFlow - Z-Score Anomaly Detection
Detects anomalies based on how many standard deviations
a value is from the mean.
"""

import pandas as pd
import numpy as np
from config.logging_config import get_logger

logger = get_logger(__name__)


def zscore_detect(
    series: pd.Series,
    threshold: float = 3.0
) -> pd.DataFrame:
    """
    Detect anomalies in a numeric series using Z-Score.
    Values beyond threshold standard deviations from mean are anomalies.

    Returns a dataframe with columns:
        value: original value
        zscore: calculated z-score
        is_anomaly: boolean
        explanation: human readable reason
    """
    numeric = pd.to_numeric(series, errors="coerce")
    mean = numeric.mean()
    std = numeric.std()

    if std == 0:
        logger.warning(f"Standard deviation is 0 for series, skipping zscore detection")
        return pd.DataFrame({
            "value": series,
            "zscore": 0.0,
            "is_anomaly": False,
            "explanation": "std is 0, cannot compute zscore"
        })

    zscores = (numeric - mean) / std

    is_anomaly = zscores.abs() > threshold

    explanations = []
    for val, z, anomaly in zip(numeric, zscores, is_anomaly):
        if anomaly:
            direction = "above" if z > 0 else "below"
            explanations.append(
                f"Value {val:.2f} is {abs(z):.2f} std {direction} mean ({mean:.2f})"
            )
        else:
            explanations.append(None)

    result = pd.DataFrame({
        "value": series.values,
        "zscore": np.round(zscores.values, 4),
        "is_anomaly": is_anomaly.values,
        "explanation": explanations
    })

    anomaly_count = int(is_anomaly.sum())
    logger.info(
        f"Z-Score detection: {anomaly_count} anomalies "
        f"(threshold={threshold}, mean={mean:.2f}, std={std:.2f})"
    )

    return result


def zscore_detect_dataframe(
    df: pd.DataFrame,
    columns: list,
    threshold: float = 3.0
) -> dict:
    """
    Run Z-Score detection on multiple columns of a dataframe.
    Returns a dict of column_name: result_dataframe.
    """
    results = {}
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in dataframe")
            continue
        results[col] = zscore_detect(df[col], threshold)

    return results