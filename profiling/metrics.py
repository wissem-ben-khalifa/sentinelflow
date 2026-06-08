"""
SentinelFlow - Profiling Metrics
Pure functions that calculate metrics for a single pandas Series.
"""

import pandas as pd
import numpy as np
from typing import Optional


def calculate_missing(series: pd.Series) -> dict:
    """Calculate missing value metrics for a column."""
    null_count = int(series.isnull().sum())
    total = len(series)
    return {
        "null_count": null_count,
        "missing_percentage": round(null_count / total * 100, 4) if total > 0 else 0.0
    }


def calculate_uniqueness(series: pd.Series) -> dict:
    """Calculate duplicate metrics for a column."""
    total = len(series)
    duplicate_count = int(series.duplicated().sum())
    return {
        "duplicate_count": duplicate_count,
        "duplicate_ratio": round(duplicate_count / total, 4) if total > 0 else 0.0
    }


def calculate_statistics(series: pd.Series) -> dict:
    """Calculate descriptive statistics for numeric columns."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()

    if len(numeric) == 0:
        return {
            "mean": None,
            "median": None,
            "std": None,
            "min_value": None,
            "max_value": None,
            "skewness": None,
            "kurtosis": None,
            "q25": None,
            "q75": None
        }

    return {
        "mean": round(float(numeric.mean()), 4),
        "median": round(float(numeric.median()), 4),
        "std": round(float(numeric.std()), 4),
        "min_value": round(float(numeric.min()), 4),
        "max_value": round(float(numeric.max()), 4),
        "skewness": round(float(numeric.skew()), 4),
        "kurtosis": round(float(numeric.kurt()), 4),
        "q25": round(float(numeric.quantile(0.25)), 4),
        "q75": round(float(numeric.quantile(0.75)), 4)
    }


def profile_column(series: pd.Series) -> dict:
    """Run all metrics on a single column and return combined result."""
    result = {}
    result.update(calculate_missing(series))
    result.update(calculate_uniqueness(series))
    result.update(calculate_statistics(series))
    return result