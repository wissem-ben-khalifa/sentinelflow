"""
SentinelFlow - Schema Validator
Detects schema changes between expected and actual dataframes.
Useful for catching breaking changes in upstream data sources.
"""

import pandas as pd
from datetime import datetime
from config.logging_config import get_logger

logger = get_logger(__name__)

EXPECTED_SCHEMAS = {
    "users": {
        "user_id": "int64",
        "name": "object",
        "country": "object",
        "registration_date": "object",
        "age": "int64",
        "email": "object"
    },
    "products": {
        "product_id": "int64",
        "category": "object",
        "price": "float64",
        "brand": "object",
        "stock": "int64",
        "created_at": "object"
    },
    "orders": {
        "order_id": "int64",
        "user_id": "float64",
        "product_id": "int64",
        "quantity": "int64",
        "amount": "float64",
        "timestamp": "object",
        "status": "object"
    }
}


def validate_schema(
    df: pd.DataFrame,
    dataset_name: str
) -> dict:
    """
    Validate a dataframe against the expected schema.
    Returns a dict with change detection results.
    """
    if dataset_name not in EXPECTED_SCHEMAS:
        logger.warning(f"No expected schema found for dataset: {dataset_name}")
        return {"valid": True, "changes": []}

    expected = EXPECTED_SCHEMAS[dataset_name]
    actual = {col: str(dtype) for col, dtype in df.dtypes.items()}

    changes = []

    for col, expected_dtype in expected.items():
        if col not in actual:
            changes.append({
                "change_type": "missing_column",
                "column": col,
                "expected": expected_dtype,
                "actual": None,
                "severity": "critical"
            })
        elif expected_dtype not in actual[col]:
            changes.append({
                "change_type": "type_change",
                "column": col,
                "expected": expected_dtype,
                "actual": actual[col],
                "severity": "warning"
            })

    for col in actual:
        if col not in expected:
            changes.append({
                "change_type": "new_column",
                "column": col,
                "expected": None,
                "actual": actual[col],
                "severity": "info"
            })

    is_valid = not any(c["severity"] == "critical" for c in changes)

    if changes:
        logger.warning(
            f"Schema changes detected in {dataset_name}: "
            f"{len(changes)} changes found"
        )
        for change in changes:
            logger.warning(
                f"  {change['change_type']}: column '{change['column']}' "
                f"expected={change['expected']} actual={change['actual']}"
            )
    else:
        logger.info(f"Schema validation passed for {dataset_name}")

    return {
        "dataset_name": dataset_name,
        "valid": is_valid,
        "changes": changes,
        "checked_at": datetime.now().isoformat()
    }


def detect_schema_drift(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    dataset_name: str
) -> dict:
    """
    Compare schemas between two dataframes to detect drift.
    Useful when comparing last week's data to today's data.
    """
    baseline_schema = {col: str(dtype) for col, dtype in baseline_df.dtypes.items()}
    current_schema = {col: str(dtype) for col, dtype in current_df.dtypes.items()}

    changes = []

    for col in baseline_schema:
        if col not in current_schema:
            changes.append({
                "change_type": "column_dropped",
                "column": col,
                "baseline_type": baseline_schema[col],
                "current_type": None
            })
        elif baseline_schema[col] != current_schema[col]:
            changes.append({
                "change_type": "type_changed",
                "column": col,
                "baseline_type": baseline_schema[col],
                "current_type": current_schema[col]
            })

    for col in current_schema:
        if col not in baseline_schema:
            changes.append({
                "change_type": "column_added",
                "column": col,
                "baseline_type": None,
                "current_type": current_schema[col]
            })

    logger.info(
        f"Schema drift check for {dataset_name}: "
        f"{len(changes)} changes detected"
    )

    return {
        "dataset_name": dataset_name,
        "schema_drift_detected": len(changes) > 0,
        "changes": changes,
        "checked_at": datetime.now().isoformat()
    }