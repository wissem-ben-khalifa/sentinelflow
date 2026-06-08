"""
SentinelFlow - Data Generator
Generates realistic e-commerce data with intentional quality issues
to simulate real production data problems.
"""

import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from config.settings import SAMPLES_DIR, RAW_DATA_DIR
from config.logging_config import get_logger

logger = get_logger(__name__)


# Configuration

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

NUM_USERS = 1000
NUM_PRODUCTS = 200
NUM_ORDERS = 5000

COUNTRIES = [
    "Tunisia", "France", "Germany", "USA",
    "UK", "Italy", "Spain", "Canada", "Egypt", "Morocco"
]

CATEGORIES = [
    "Electronics", "Clothing", "Books",
    "Home", "Sports", "Beauty", "Food", "Toys"
]

BRANDS = [
    "AlphaTech", "BetaWear", "GammaBooks",
    "DeltaHome", "EpsilonSport", "ZetaBeauty"
]


# Users Table


def generate_users(n: int = NUM_USERS, inject_issues: bool = True) -> pd.DataFrame:
    """
    Generate users table.
    inject_issues adds realistic data quality problems.
    """
    logger.info(f"Generating {n} users (inject_issues={inject_issues})")

    users = pd.DataFrame({
        "user_id": range(1, n + 1),
        "name": [f"User_{i}" for i in range(1, n + 1)],
        "country": [random.choice(COUNTRIES) for _ in range(n)],
        "registration_date": [
            datetime(2022, 1, 1) + timedelta(days=random.randint(0, 730))
            for _ in range(n)
        ],
        "age": [random.randint(18, 70) for _ in range(n)],
        "email": [f"user_{i}@email.com" for i in range(1, n + 1)]
    })

    if inject_issues:
        # Inject missing values in name (2% of rows)
        missing_name_idx = random.sample(range(n), int(n * 0.02))
        users.loc[missing_name_idx, "name"] = None

        # Inject missing values in country (3% of rows)
        missing_country_idx = random.sample(range(n), int(n * 0.03))
        users.loc[missing_country_idx, "country"] = None

        # Inject invalid ages (out of range)
        invalid_age_idx = random.sample(range(n), int(n * 0.01))
        users.loc[invalid_age_idx, "age"] = random.choice([5, 150, -1, 200])

        # Inject duplicate rows (1% of rows)
        duplicate_rows = users.sample(int(n * 0.01))
        users = pd.concat([users, duplicate_rows], ignore_index=True)

        logger.info(f"Injected issues into users: missing names, invalid ages, duplicates")

    return users


# Products Table


def generate_products(n: int = NUM_PRODUCTS, inject_issues: bool = True) -> pd.DataFrame:
    """
    Generate products table.
    inject_issues adds realistic data quality problems.
    """
    logger.info(f"Generating {n} products (inject_issues={inject_issues})")

    products = pd.DataFrame({
        "product_id": range(1, n + 1),
        "category": [random.choice(CATEGORIES) for _ in range(n)],
        "price": [round(random.uniform(5.0, 500.0), 2) for _ in range(n)],
        "brand": [random.choice(BRANDS) for _ in range(n)],
        "stock": [random.randint(0, 1000) for _ in range(n)],
        "created_at": [
            datetime(2022, 1, 1) + timedelta(days=random.randint(0, 365))
            for _ in range(n)
        ]
    })

    if inject_issues:
        # Inject negative prices (invalid)
        invalid_price_idx = random.sample(range(n), int(n * 0.02))
        products.loc[invalid_price_idx, "price"] = random.choice([-10.0, -99.0, 0.0])

        # Inject missing category (2% of rows)
        missing_cat_idx = random.sample(range(n), int(n * 0.02))
        products.loc[missing_cat_idx, "category"] = None

        # Inject anomalous price spikes (0.5% of rows)
        spike_idx = random.sample(range(n), max(1, int(n * 0.005)))
        products.loc[spike_idx, "price"] = random.choice([9999.0, 15000.0, 50000.0])

        logger.info("Injected issues into products: negative prices, missing categories, spikes")

    return products

# Orders Table


def generate_orders(
    n: int = NUM_ORDERS,
    num_users: int = NUM_USERS,
    num_products: int = NUM_PRODUCTS,
    inject_issues: bool = True
) -> pd.DataFrame:
    """
    Generate orders table.
    inject_issues adds realistic data quality problems.
    """
    logger.info(f"Generating {n} orders (inject_issues={inject_issues})")

    orders = pd.DataFrame({
        "order_id": range(1, n + 1),
        "user_id": [random.randint(1, num_users) for _ in range(n)],
        "product_id": [random.randint(1, num_products) for _ in range(n)],
        "quantity": [random.randint(1, 10) for _ in range(n)],
        "amount": [round(random.uniform(20.0, 500.0), 2) for _ in range(n)],
        "timestamp": [
            datetime(2024, 1, 1) + timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            for _ in range(n)
        ],
        "status": [
            random.choice(["completed", "pending", "cancelled", "refunded"])
            for _ in range(n)
        ]
    })

    if inject_issues:
        # Inject missing user_id (1% of rows)
        missing_user_idx = random.sample(range(n), int(n * 0.01))
        orders.loc[missing_user_idx, "user_id"] = None

        # Inject anomalous amounts (order amount way too high)
        anomaly_idx = random.sample(range(n), int(n * 0.01))
        orders.loc[anomaly_idx, "amount"] = random.choice([9999.0, 15000.0, 50000.0])

        # Inject zero or negative amounts
        invalid_amount_idx = random.sample(range(n), int(n * 0.005))
        orders.loc[invalid_amount_idx, "amount"] = random.choice([0.0, -50.0, -100.0])

        # Inject duplicate orders
        duplicate_rows = orders.sample(int(n * 0.01))
        orders = pd.concat([orders, duplicate_rows], ignore_index=True)

        logger.info("Injected issues into orders: missing users, anomalous amounts, duplicates")

    return orders



# Drifted Data (for drift detection testing)


def generate_drifted_orders(
    n: int = NUM_ORDERS,
    num_users: int = NUM_USERS,
    num_products: int = NUM_PRODUCTS
) -> pd.DataFrame:
    """
    Generate orders with distribution drift.
    Simulates a scenario where order amounts suddenly increase
    (e.g. a flash sale or pricing bug).
    """
    logger.info(f"Generating {n} drifted orders to simulate distribution shift")

    orders = pd.DataFrame({
        "order_id": range(NUM_ORDERS + 1, NUM_ORDERS + n + 1),
        "user_id": [random.randint(1, num_users) for _ in range(n)],
        "product_id": [random.randint(1, num_products) for _ in range(n)],
        "quantity": [random.randint(1, 10) for _ in range(n)],

        # Drifted: average amount shifted from ~260 to ~800
        "amount": [round(random.uniform(400.0, 1200.0), 2) for _ in range(n)],

        "timestamp": [
            datetime(2025, 1, 1) + timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            for _ in range(n)
        ],
        "status": [
            random.choice(["completed", "pending", "cancelled", "refunded"])
            for _ in range(n)
        ]
    })

    return orders


# Save to disk


def save_dataset(df: pd.DataFrame, filename: str, folder: Path) -> Path:
    """Save a dataframe as CSV to the given folder."""
    folder.mkdir(parents=True, exist_ok=True)
    filepath = folder / filename
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(df)} rows to {filepath}")
    return filepath



# Main


def generate_all(inject_issues: bool = True) -> dict:
    """
    Generate all datasets and save to data/raw and data/samples.
    Returns a dict with dataframes for immediate use.
    """
    logger.info("Starting full data generation")

    users = generate_users(inject_issues=inject_issues)
    products = generate_products(inject_issues=inject_issues)
    orders = generate_orders(inject_issues=inject_issues)
    drifted_orders = generate_drifted_orders()

    # Save raw data
    save_dataset(users, "users.csv", RAW_DATA_DIR)
    save_dataset(products, "products.csv", RAW_DATA_DIR)
    save_dataset(orders, "orders.csv", RAW_DATA_DIR)
    save_dataset(drifted_orders, "orders_drifted.csv", RAW_DATA_DIR)

    # Save clean samples (no issues injected) for model training
    users_clean = generate_users(inject_issues=False)
    products_clean = generate_products(inject_issues=False)
    orders_clean = generate_orders(inject_issues=False)

    save_dataset(users_clean, "users_clean.csv", SAMPLES_DIR)
    save_dataset(products_clean, "products_clean.csv", SAMPLES_DIR)
    save_dataset(orders_clean, "orders_clean.csv", SAMPLES_DIR)

    logger.info("Data generation complete")

    return {
        "users": users,
        "products": products,
        "orders": orders,
        "drifted_orders": drifted_orders,
        "users_clean": users_clean,
        "products_clean": products_clean,
        "orders_clean": orders_clean
    }


if __name__ == "__main__":
    datasets = generate_all(inject_issues=True)
    for name, df in datasets.items():
        print(f"{name}: {df.shape[0]} rows, {df.shape[1]} columns")