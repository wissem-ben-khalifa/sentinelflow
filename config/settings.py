"""
SentinelFlow - Central Configuration
Loads all settings from environment variables with safe defaults.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

# Load .env file
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLES_DIR = DATA_DIR / "samples"


# PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "sentinelflow")
POSTGRES_USER = os.getenv("POSTGRES_USER", "sentinelflow_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


# MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "sentinelflow-data")

# Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPICS = {
    "page_views": os.getenv("KAFKA_TOPIC_PAGE_VIEWS", "page_views"),
    "purchases": os.getenv("KAFKA_TOPIC_PURCHASES", "purchases"),
    "clicks": os.getenv("KAFKA_TOPIC_CLICKS", "user_clicks"),
    "cart": os.getenv("KAFKA_TOPIC_CART", "cart_events"),
}

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_DEBUG = os.getenv("API_DEBUG", "True") == "True"

# Alerting
ALERT_EMAIL_SENDER = os.getenv("ALERT_EMAIL_SENDER", "")
ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD", "")
ALERT_EMAIL_RECEIVER = os.getenv("ALERT_EMAIL_RECEIVER", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# Thresholds
ANOMALY_SCORE_THRESHOLD = float(os.getenv("ANOMALY_SCORE_THRESHOLD", 0.6))
MISSING_VALUES_THRESHOLD = float(os.getenv("MISSING_VALUES_THRESHOLD", 0.10))
PSI_THRESHOLD = float(os.getenv("PSI_THRESHOLD", 0.25))
ZSCORE_THRESHOLD = float(os.getenv("ZSCORE_THRESHOLD", 3.0))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)