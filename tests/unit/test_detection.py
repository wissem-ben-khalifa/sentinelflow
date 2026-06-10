"""
SentinelFlow - Detection Engine Tests
"""

import pytest
import pandas as pd
import numpy as np
from detection.statistical.zscore import zscore_detect, zscore_detect_dataframe
from detection.statistical.iqr import iqr_detect, iqr_detect_dataframe


@pytest.fixture
def normal_series():
    np.random.seed(42)
    return pd.Series(np.random.normal(100, 10, 100))


@pytest.fixture
def series_with_spike():
    np.random.seed(42)
    data = np.random.normal(100, 10, 100).tolist()
    data[50] = 9999.0
    data[75] = -9999.0
    return pd.Series(data)


@pytest.fixture
def sample_dataframe(series_with_spike):
    return pd.DataFrame({
        "amount": series_with_spike,
        "quantity": pd.Series(np.random.randint(1, 10, 100))
    })


def test_zscore_no_anomalies_in_normal_data(normal_series):
    result = zscore_detect(normal_series, threshold=3.0)
    anomaly_count = result["is_anomaly"].sum()
    assert anomaly_count == 0


def test_zscore_detects_spike(series_with_spike):
    result = zscore_detect(series_with_spike, threshold=3.0)
    assert result["is_anomaly"].sum() >= 1


def test_zscore_result_columns(normal_series):
    result = zscore_detect(normal_series)
    assert "value" in result.columns
    assert "zscore" in result.columns
    assert "is_anomaly" in result.columns
    assert "explanation" in result.columns


def test_zscore_explanation_for_anomaly(series_with_spike):
    result = zscore_detect(series_with_spike, threshold=3.0)
    anomalies = result[result["is_anomaly"] == True]
    assert len(anomalies) > 0
    for explanation in anomalies["explanation"]:
        assert explanation is not None
        assert len(explanation) > 0


def test_zscore_dataframe(sample_dataframe):
    results = zscore_detect_dataframe(sample_dataframe, ["amount", "quantity"])
    assert "amount" in results
    assert "quantity" in results
    assert results["amount"]["is_anomaly"].sum() >= 1


def test_iqr_no_anomalies_in_normal_data(normal_series):
    result = iqr_detect(normal_series, factor=3.0)
    assert result["is_anomaly"].sum() == 0


def test_iqr_detects_spike(series_with_spike):
    result = iqr_detect(series_with_spike, factor=1.5)
    assert result["is_anomaly"].sum() >= 1


def test_iqr_result_columns(normal_series):
    result = iqr_detect(normal_series)
    assert "value" in result.columns
    assert "is_anomaly" in result.columns
    assert "lower_bound" in result.columns
    assert "upper_bound" in result.columns
    assert "explanation" in result.columns


def test_iqr_bounds_are_correct(normal_series):
    result = iqr_detect(normal_series, factor=1.5)
    q1 = normal_series.quantile(0.25)
    q3 = normal_series.quantile(0.75)
    iqr = q3 - q1
    expected_lower = q1 - 1.5 * iqr
    expected_upper = q3 + 1.5 * iqr
    assert abs(result["lower_bound"].iloc[0] - expected_lower) < 0.001
    assert abs(result["upper_bound"].iloc[0] - expected_upper) < 0.001


def test_iqr_dataframe(sample_dataframe):
    results = iqr_detect_dataframe(sample_dataframe, ["amount"])
    assert "amount" in results
    assert results["amount"]["is_anomaly"].sum() >= 1