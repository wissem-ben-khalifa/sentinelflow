"""
SentinelFlow - IQR Anomaly Detection
Detects anomalies using the Interquartile Range method.
More robust than Z-Score for skewed distributions.
"""

import pandas as pd
import numpy as np
from config.logging_config import get_logger

logger = get_logger(__name__)


def iqr_detect(
    series: pd.Series,
    factor: float = 1.5
) -> pd.DataFrame:
    """
    Detect anomalies using IQR method.
    Values below Q1 - factor*IQR or above Q3 + factor*IQR are anomalies.
    factor=1.5 is standard, factor=3.0 catches only extreme outliers.

    Returns a dataframe with columns:
        value: original value
        is_anomaly: boolean
        lower_bound: calculated lower fence
        upper_bound: calculated upper fence
        explanation: human readable reason
    """
    numeric = pd.to_numeric(series, errors="coerce")

    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - factor * iqr
    upper_bound = q3 + factor * iqr

    is_anomaly = (numeric < lower_bound) | (numeric > upper_bound)

    explanations = []
    for val, anomaly in zip(numeric, is_anomaly):
        if anomaly:
            if val < lower_bound:
                explanations.append(
                    f"Value {val:.2f} is below lower fence ({lower_bound:.2f})"
                )
            else:
                explanations.append(
                    f"Value {val:.2f} is above upper fence ({upper_bound:.2f})"
                )
        else:
            explanations.append(None)

    result = pd.DataFrame({
        "value": series.values,
        "is_anomaly": is_anomaly.values,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "explanation": explanations
    })

    anomaly_count = int(is_anomaly.sum())
    logger.info(
        f"IQR detection: {anomaly_count} anomalies "
        f"(Q1={q1:.2f}, Q3={q3:.2f}, IQR={iqr:.2f}, "
        f"bounds=[{lower_bound:.2f}, {upper_bound:.2f}])"
    )

    return result


def iqr_detect_dataframe(
    df: pd.DataFrame,
    columns: list,
    factor: float = 1.5
) -> dict:
    """
    Run IQR detection on multiple columns of a dataframe.
    Returns a dict of column_name: result_dataframe.
    """
    results = {}
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in dataframe")
            continue
        results[col] = iqr_detect(df[col], factor)

    return results