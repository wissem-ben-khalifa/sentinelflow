"""
SentinelFlow - Kafka Consumer
Consumes events from Kafka topics in real time,
runs anomaly detection on each event,
and stores results in PostgreSQL.
"""

import json
import psycopg2
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from config.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD
)
from config.logging_config import get_logger
from kafka_config.topics_config import (
    BOOTSTRAP_SERVERS,
    ANOMALOUS_AMOUNT_THRESHOLD,
    ANOMALOUS_QUANTITY_THRESHOLD
)

logger = get_logger(__name__)


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def save_streaming_anomaly(
    topic: str,
    event: dict,
    is_anomaly: bool,
    anomaly_reason: str,
    anomaly_score: float
) -> None:
    """Save a streaming anomaly detection result to PostgreSQL."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO anomaly_results (
            dataset_name, run_date, detection_method,
            record_id, anomaly_score, is_anomaly,
            features_used, explanation
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        f"stream_{topic}",
        datetime.now(),
        "streaming_threshold",
        event.get("user_id"),
        anomaly_score,
        is_anomaly,
        "amount,quantity",
        anomaly_reason if is_anomaly else None
    ))

    conn.commit()
    cursor.close()
    conn.close()


def detect_purchase_anomaly(event: dict) -> tuple[bool, str, float]:
    """
    Real time anomaly detection for purchase events.
    Returns (is_anomaly, reason, score).
    """
    amount = event.get("amount", 0)
    quantity = event.get("quantity", 0)

    if amount > ANOMALOUS_AMOUNT_THRESHOLD:
        score = min(1.0, amount / ANOMALOUS_AMOUNT_THRESHOLD)
        return True, f"Anomalous amount detected: {amount}", score

    if quantity > ANOMALOUS_QUANTITY_THRESHOLD:
        score = min(1.0, quantity / ANOMALOUS_QUANTITY_THRESHOLD)
        return True, f"Anomalous quantity detected: {quantity}", score

    return False, None, 0.0


def detect_page_view_anomaly(event: dict) -> tuple[bool, str, float]:
    """
    Real time anomaly detection for page view events.
    Detects unusually long session durations.
    """
    duration = event.get("duration_sec", 0)
    threshold = 3600

    if duration > threshold:
        score = min(1.0, duration / threshold)
        return True, f"Anomalous session duration: {duration}s", score

    return False, None, 0.0


def consume_events(
    topics: list = None,
    max_messages: int = 200,
    timeout_ms: int = 5000
) -> dict:
    """
    Consume events from Kafka topics and run real time anomaly detection.
    Stops after max_messages or when timeout is reached.
    """
    if topics is None:
        topics = ["purchases", "page_views", "user_clicks", "cart_events"]

    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="sentinelflow-consumer",
        consumer_timeout_ms=timeout_ms
    )

    logger.info(f"Kafka consumer started on topics: {topics}")

    counts = {
        "total_consumed": 0,
        "anomalies_detected": 0,
        "by_topic": {}
    }

    for topic in topics:
        counts["by_topic"][topic] = {"consumed": 0, "anomalies": 0}

    for message in consumer:
        topic = message.topic
        event = message.value

        counts["total_consumed"] += 1
        counts["by_topic"][topic]["consumed"] += 1

        is_anomaly = False
        reason = None
        score = 0.0

        if topic == "purchases":
            is_anomaly, reason, score = detect_purchase_anomaly(event)
        elif topic == "page_views":
            is_anomaly, reason, score = detect_page_view_anomaly(event)

        if is_anomaly:
            counts["anomalies_detected"] += 1
            counts["by_topic"][topic]["anomalies"] += 1
            logger.warning(
                f"STREAMING ANOMALY | topic={topic} | "
                f"user_id={event.get('user_id')} | {reason}"
            )

        save_streaming_anomaly(topic, event, is_anomaly, reason, score)

        if counts["total_consumed"] >= max_messages:
            logger.info(f"Reached max_messages limit: {max_messages}")
            break

    consumer.close()

    logger.info(
        f"Consumer finished: {counts['total_consumed']} messages, "
        f"{counts['anomalies_detected']} anomalies detected"
    )

    return counts


if __name__ == "__main__":
    counts = consume_events(
        topics=["purchases", "page_views"],
        max_messages=200,
        timeout_ms=10000
    )
    print(f"Consumed: {counts}")