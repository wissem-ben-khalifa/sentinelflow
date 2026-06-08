"""
SentinelFlow - Validation Engine
Runs business rule validations on datasets and stores results in PostgreSQL.
Uses pure pandas-based checks instead of Great Expectations API
to avoid version compatibility issues.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import psycopg2
from config.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD
)
from config.logging_config import get_logger

logger = get_logger(__name__)


def get_connection():
    """Create and return a PostgreSQL connection."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def save_validation_results(results: list[dict], conn) -> None:
    """Insert validation results into PostgreSQL."""
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO validation_results (
            dataset_name, run_date, expectation_type,
            column_name, success, observed_value,
            expected_value, severity
        ) VALUES (
            %(dataset_name)s, %(run_date)s, %(expectation_type)s,
            %(column_name)s, %(success)s, %(observed_value)s,
            %(expected_value)s, %(severity)s
        )
    """

    for result in results:
        cursor.execute(insert_query, result)

    conn.commit()
    cursor.close()
    logger.info(f"Saved {len(results)} validation results to database")


def build_result(
    dataset_name: str,
    expectation_type: str,
    column_name: str,
    success: bool,
    observed_value: str,
    expected_value: str,
    severity: str = "warning"
) -> dict:
    """Build a single validation result dict."""
    return {
        "dataset_name": dataset_name,
        "run_date": datetime.now(),
        "expectation_type": expectation_type,
        "column_name": column_name,
        "success": success,
        "observed_value": observed_value,
        "expected_value": expected_value,
        "severity": severity
    }


# Validation checks

def check_no_missing_values(
    df: pd.DataFrame,
    column: str,
    dataset_name: str,
    severity: str = "warning"
) -> dict:
    """Check that a column has no missing values."""
    null_count = int(df[column].isnull().sum())
    success = null_count == 0
    return build_result(
        dataset_name=dataset_name,
        expectation_type="expect_column_values_to_not_be_null",
        column_name=column,
        success=success,
        observed_value=f"{null_count} nulls",
        expected_value="0 nulls",
        severity=severity
    )


def check_values_in_range(
    df: pd.DataFrame,
    column: str,
    min_val: float,
    max_val: float,
    dataset_name: str,
    severity: str = "warning"
) -> dict:
    """Check that numeric values fall within an expected range."""
    numeric = pd.to_numeric(df[column], errors="coerce")
    out_of_range = int(((numeric < min_val) | (numeric > max_val)).sum())
    success = out_of_range == 0
    return build_result(
        dataset_name=dataset_name,
        expectation_type="expect_column_values_to_be_between",
        column_name=column,
        success=success,
        observed_value=f"{out_of_range} out of range values",
        expected_value=f"between {min_val} and {max_val}",
        severity=severity
    )


def check_values_greater_than(
    df: pd.DataFrame,
    column: str,
    min_val: float,
    dataset_name: str,
    severity: str = "critical"
) -> dict:
    """Check that all values are strictly greater than a minimum."""
    numeric = pd.to_numeric(df[column], errors="coerce")
    violations = int((numeric <= min_val).sum())
    success = violations == 0
    return build_result(
        dataset_name=dataset_name,
        expectation_type="expect_column_values_to_be_greater_than",
        column_name=column,
        success=success,
        observed_value=f"{violations} values <= {min_val}",
        expected_value=f"all values > {min_val}",
        severity=severity
    )


def check_no_duplicates(
    df: pd.DataFrame,
    column: str,
    dataset_name: str,
    severity: str = "warning"
) -> dict:
    """Check that a column has no duplicate values."""
    duplicate_count = int(df[column].duplicated().sum())
    success = duplicate_count == 0
    return build_result(
        dataset_name=dataset_name,
        expectation_type="expect_column_values_to_be_unique",
        column_name=column,
        success=success,
        observed_value=f"{duplicate_count} duplicates",
        expected_value="0 duplicates",
        severity=severity
    )


def check_values_in_set(
    df: pd.DataFrame,
    column: str,
    valid_set: list,
    dataset_name: str,
    severity: str = "warning"
) -> dict:
    """Check that all values belong to an allowed set."""
    invalid = df[column].dropna()
    invalid_count = int((~invalid.isin(valid_set)).sum())
    success = invalid_count == 0
    return build_result(
        dataset_name=dataset_name,
        expectation_type="expect_column_values_to_be_in_set",
        column_name=column,
        success=success,
        observed_value=f"{invalid_count} invalid values",
        expected_value=f"values in {valid_set}",
        severity=severity
    )


def check_schema(
    df: pd.DataFrame,
    expected_schema: dict,
    dataset_name: str
) -> list[dict]:
    """
    Check that the dataframe matches the expected schema.
    expected_schema is a dict of column_name: expected_dtype string.
    Detects missing columns, extra columns, and type mismatches.
    """
    results = []

    for col, expected_type in expected_schema.items():
        if col not in df.columns:
            results.append(build_result(
                dataset_name=dataset_name,
                expectation_type="expect_column_to_exist",
                column_name=col,
                success=False,
                observed_value="column missing",
                expected_value=f"column {col} of type {expected_type}",
                severity="critical"
            ))
        else:
            actual_type = str(df[col].dtype)
            type_match = expected_type in actual_type
            results.append(build_result(
                dataset_name=dataset_name,
                expectation_type="expect_column_type_to_match",
                column_name=col,
                success=type_match,
                observed_value=actual_type,
                expected_value=expected_type,
                severity="warning"
            ))

    extra_columns = set(df.columns) - set(expected_schema.keys())
    for col in extra_columns:
        results.append(build_result(
            dataset_name=dataset_name,
            expectation_type="expect_no_extra_columns",
            column_name=col,
            success=False,
            observed_value="unexpected column found",
            expected_value="column not in schema",
            severity="warning"
        ))

    return results


# Dataset-specific validation suites

def validate_users(df: pd.DataFrame) -> list[dict]:
    """Run all validation checks for the users dataset."""
    logger.info("Validating users dataset")
    results = []

    results.append(check_no_missing_values(df, "user_id", "users", "critical"))
    results.append(check_no_missing_values(df, "name", "users", "warning"))
    results.append(check_no_missing_values(df, "country", "users", "warning"))
    results.append(check_no_duplicates(df, "user_id", "users", "critical"))
    results.append(check_values_in_range(df, "age", 18, 100, "users", "warning"))

    expected_schema = {
        "user_id": "int",
        "name": "object",
        "country": "object",
        "registration_date": "object",
        "age": "int",
        "email": "object"
    }
    results.extend(check_schema(df, expected_schema, "users"))

    return results


def validate_products(df: pd.DataFrame) -> list[dict]:
    """Run all validation checks for the products dataset."""
    logger.info("Validating products dataset")
    results = []

    results.append(check_no_missing_values(df, "product_id", "products", "critical"))
    results.append(check_no_missing_values(df, "category", "products", "warning"))
    results.append(check_no_duplicates(df, "product_id", "products", "critical"))
    results.append(check_values_greater_than(df, "price", 0, "products", "critical"))

    valid_categories = [
        "Electronics", "Clothing", "Books",
        "Home", "Sports", "Beauty", "Food", "Toys"
    ]
    results.append(check_values_in_set(df, "category", valid_categories, "products", "warning"))

    expected_schema = {
        "product_id": "int",
        "category": "object",
        "price": "float",
        "brand": "object",
        "stock": "int",
        "created_at": "object"
    }
    results.extend(check_schema(df, expected_schema, "products"))

    return results


def validate_orders(df: pd.DataFrame) -> list[dict]:
    """Run all validation checks for the orders dataset."""
    logger.info("Validating orders dataset")
    results = []

    results.append(check_no_missing_values(df, "order_id", "orders", "critical"))
    results.append(check_no_missing_values(df, "user_id", "orders", "warning"))
    results.append(check_no_duplicates(df, "order_id", "orders", "critical"))
    results.append(check_values_greater_than(df, "amount", 0, "orders", "critical"))
    results.append(check_values_in_range(df, "quantity", 1, 100, "orders", "warning"))

    valid_statuses = ["completed", "pending", "cancelled", "refunded"]
    results.append(check_values_in_set(df, "status", valid_statuses, "orders", "warning"))

    expected_schema = {
        "order_id": "int",
        "user_id": "float",
        "product_id": "int",
        "quantity": "int",
        "amount": "float",
        "timestamp": "object",
        "status": "object"
    }
    results.extend(check_schema(df, expected_schema, "orders"))

    return results


def run_validation(df: pd.DataFrame, dataset_name: str) -> list[dict]:
    """
    Run the correct validation suite for a dataset
    and save results to PostgreSQL.
    """
    validators = {
        "users": validate_users,
        "products": validate_products,
        "orders": validate_orders
    }

    if dataset_name not in validators:
        logger.warning(f"No validation suite found for dataset: {dataset_name}")
        return []

    results = validators[dataset_name](df)

    passed = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])
    logger.info(f"{dataset_name} validation: {passed} passed, {failed} failed")

    conn = get_connection()
    save_validation_results(results, conn)
    conn.close()

    return results


if __name__ == "__main__":
    from config.settings import RAW_DATA_DIR

    datasets = {
        "users": RAW_DATA_DIR / "users.csv",
        "products": RAW_DATA_DIR / "products.csv",
        "orders": RAW_DATA_DIR / "orders.csv"
    }

    for name, path in datasets.items():
        df = pd.read_csv(path)
        results = run_validation(df, name)
        passed = sum(1 for r in results if r["success"])
        failed = sum(1 for r in results if not r["success"])
        critical = sum(1 for r in results if not r["success"] and r["severity"] == "critical")
        print(f"{name}: {passed} passed, {failed} failed, {critical} critical")