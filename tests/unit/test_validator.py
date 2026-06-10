"""
SentinelFlow - Validation Engine Tests
"""

import pytest
import pandas as pd
from validation.expectations import (
    check_no_missing_values,
    check_values_in_range,
    check_values_greater_than,
    check_no_duplicates,
    check_values_in_set,
    check_schema
)


@pytest.fixture
def clean_df():
    return pd.DataFrame({
        "user_id": [1, 2, 3, 4, 5],
        "age": [25, 30, 35, 40, 45],
        "country": ["Tunisia", "France", "USA", "UK", "Germany"],
        "price": [10.0, 20.0, 30.0, 40.0, 50.0]
    })


@pytest.fixture
def dirty_df():
    return pd.DataFrame({
        "user_id": [1, 1, 3, 4, 5],
        "age": [25, 150, -1, 40, 45],
        "country": ["Tunisia", None, "USA", None, "Germany"],
        "price": [-10.0, 20.0, 0.0, 40.0, 50.0]
    })


def test_no_missing_values_passes_on_clean(clean_df):
    result = check_no_missing_values(clean_df, "user_id", "test")
    assert result["success"] is True


def test_no_missing_values_fails_on_dirty(dirty_df):
    result = check_no_missing_values(dirty_df, "country", "test")
    assert result["success"] is False


def test_values_in_range_passes(clean_df):
    result = check_values_in_range(clean_df, "age", 18, 100, "test")
    assert result["success"] is True


def test_values_in_range_fails(dirty_df):
    result = check_values_in_range(dirty_df, "age", 18, 100, "test")
    assert result["success"] is False


def test_values_greater_than_passes(clean_df):
    result = check_values_greater_than(clean_df, "price", 0, "test")
    assert result["success"] is True


def test_values_greater_than_fails(dirty_df):
    result = check_values_greater_than(dirty_df, "price", 0, "test")
    assert result["success"] is False


def test_no_duplicates_passes(clean_df):
    result = check_no_duplicates(clean_df, "user_id", "test")
    assert result["success"] is True


def test_no_duplicates_fails(dirty_df):
    result = check_no_duplicates(dirty_df, "user_id", "test")
    assert result["success"] is False


def test_values_in_set_passes(clean_df):
    valid = ["Tunisia", "France", "USA", "UK", "Germany"]
    result = check_values_in_set(clean_df, "country", valid, "test")
    assert result["success"] is True


def test_values_in_set_fails(clean_df):
    valid = ["Tunisia", "France"]
    result = check_values_in_set(clean_df, "country", valid, "test")
    assert result["success"] is False


def test_schema_passes_on_correct_schema(clean_df):
    schema = {
        "user_id": "int",
        "age": "int",
        "country": "object",
        "price": "float"
    }
    results = check_schema(clean_df, schema, "test")
    failures = [r for r in results if not r["success"]]
    assert len(failures) == 0


def test_schema_detects_missing_column(clean_df):
    schema = {
        "user_id": "int",
        "email": "object"
    }
    results = check_schema(clean_df, schema, "test")
    failures = [r for r in results if not r["success"]]
    assert any(r["expectation_type"] == "expect_column_to_exist" for r in failures)


def test_result_has_required_fields(clean_df):
    result = check_no_missing_values(clean_df, "user_id", "test")
    required_fields = [
        "dataset_name", "expectation_type", "column_name",
        "success", "observed_value", "expected_value", "severity"
    ]
    for field in required_fields:
        assert field in result