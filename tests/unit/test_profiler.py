"""
SentinelFlow - Profiling Engine Tests
"""

import pytest
import pandas as pd
import numpy as np
from profiling.metrics import (
    calculate_missing,
    calculate_uniqueness,
    calculate_statistics,
    profile_column
)


@pytest.fixture
def clean_series():
    return pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])


@pytest.fixture
def series_with_nulls():
    return pd.Series([1.0, None, 3.0, None, 5.0])


@pytest.fixture
def series_with_duplicates():
    return pd.Series([1.0, 1.0, 2.0, 3.0, 3.0])


def test_calculate_missing_no_nulls(clean_series):
    result = calculate_missing(clean_series)
    assert result["null_count"] == 0
    assert result["missing_percentage"] == 0.0


def test_calculate_missing_with_nulls(series_with_nulls):
    result = calculate_missing(series_with_nulls)
    assert result["null_count"] == 2
    assert result["missing_percentage"] == 40.0


def test_calculate_uniqueness_no_duplicates(clean_series):
    result = calculate_uniqueness(clean_series)
    assert result["duplicate_count"] == 0
    assert result["duplicate_ratio"] == 0.0


def test_calculate_uniqueness_with_duplicates(series_with_duplicates):
    result = calculate_uniqueness(series_with_duplicates)
    assert result["duplicate_count"] == 2
    assert result["duplicate_ratio"] == 0.4


def test_calculate_statistics_basic(clean_series):
    result = calculate_statistics(clean_series)
    assert result["mean"] == 3.0
    assert result["median"] == 3.0
    assert result["min_value"] == 1.0
    assert result["max_value"] == 5.0


def test_calculate_statistics_empty_series():
    result = calculate_statistics(pd.Series([], dtype=float))
    assert result["mean"] is None
    assert result["std"] is None


def test_calculate_statistics_non_numeric():
    result = calculate_statistics(pd.Series(["a", "b", "c"]))
    assert result["mean"] is None


def test_profile_column_returns_all_keys(clean_series):
    result = profile_column(clean_series)
    expected_keys = [
        "null_count", "missing_percentage",
        "duplicate_count", "duplicate_ratio",
        "mean", "median", "std",
        "min_value", "max_value",
        "skewness", "kurtosis", "q25", "q75"
    ]
    for key in expected_keys:
        assert key in result


def test_profile_column_mixed_data():
    series = pd.Series([1.0, 2.0, None, 2.0, 5.0])
    result = profile_column(series)
    assert result["null_count"] == 1
    assert result["duplicate_count"] == 1