"""
SentinelFlow - Kafka Producer
Simulates real time e-commerce events by producing
messages to Kafka topics continuously.
Injects anomalous events at a configurable rate
to simulate real production issues.
"""

import json
import random
import time
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from config.logging_config import get_logger
from kafka_config.topics_config import BOOTSTRAP_SERVERS

logger = get_logger(__name__)

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

PAGES = [
    "home", "product_list", "product_detail",
    "cart", "checkout", "order_confirmation", "profile"
]

ELEMENTS = [
    "add_to_cart", "buy_now", "remove_item",
    "search", "filter", "sort", "pagination"
]

CART_ACTIONS = ["add", "remove", "update"]


def create_producer() -> KafkaProducer:
    """Create and return a Kafka producer."""
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
        retries=3
    )
    logger.info(f"Kafka producer connected to {BOOTSTRAP_SERVERS}")
    return producer


def generate_page_view(inject_anomaly: bool = False) -> dict:
    """Generate a page view event."""
    return {
        "user_id": random.randint(1, 1000),
        "page": random.choice(PAGES),
        "duration_sec": random.randint(1, 300) if not inject_anomaly else random.randint(9000, 99999),
        "timestamp": datetime.now().isoformat()
    }


def generate_purchase(inject_anomaly: bool = False) -> dict:
    """Generate a purchase event."""
    return {
        "user_id": random.randint(1, 1000),
        "product_id": random.randint(1, 200),
        "amount": round(random.uniform(20.0, 500.0), 2) if not inject_anomaly else round(random.uniform(9000.0, 50000.0), 2),
        "quantity": random.randint(1, 10) if not inject_anomaly else random.randint(500, 9999),
        "timestamp": datetime.now().isoformat()
    }


def generate_user_click() -> dict:
    """Generate a user click event."""
    return {
        "user_id": random.randint(1, 1000),
        "element": random.choice(ELEMENTS),
        "page": random.choice(PAGES),
        "timestamp": datetime.now().isoformat()
    }


def generate_cart_event() -> dict:
    """Generate a cart event."""
    return {
        "user_id": random.randint(1, 1000),
        "product_id": random.randint(1, 200),
        "action": random.choice(CART_ACTIONS),
        "quantity": random.randint(1, 10),
        "timestamp": datetime.now().isoformat()
    }


def produce_events(
    num_events: int = 100,
    delay_sec: float = 0.1,
    anomaly_rate: float = 0.05
) -> dict:
    """
    Produce events to all Kafka topics.
    num_events: total events to produce per topic
    delay_sec: delay between events to simulate real time
    anomaly_rate: proportion of events that are anomalous
    """
    producer = create_producer()

    counts = {
        "page_views": 0,
        "purchases": 0,
        "user_clicks": 0,
        "cart_events": 0,
        "anomalies_injected": 0
    }

    logger.info(
        f"Starting event production: {num_events} events per topic, "
        f"anomaly_rate={anomaly_rate}"
    )

    for i in range(num_events):
        inject_anomaly = random.random() < anomaly_rate

        # Page view event
        page_view = generate_page_view(inject_anomaly=inject_anomaly)
        producer.send(
            "page_views",
            key=str(page_view["user_id"]),
            value=page_view
        )
        counts["page_views"] += 1

        # Purchase event
        purchase = generate_purchase(inject_anomaly=inject_anomaly)
        producer.send(
            "purchases",
            key=str(purchase["user_id"]),
            value=purchase
        )
        counts["purchases"] += 1

        # Click event
        click = generate_user_click()
        producer.send(
            "user_clicks",
            key=str(click["user_id"]),
            value=click
        )
        counts["user_clicks"] += 1

        # Cart event
        cart = generate_cart_event()
        producer.send(
            "cart_events",
            key=str(cart["user_id"]),
            value=cart
        )
        counts["cart_events"] += 1

        if inject_anomaly:
            counts["anomalies_injected"] += 1

        if (i + 1) % 10 == 0:
            logger.info(f"Produced {i + 1}/{num_events} event batches")

        time.sleep(delay_sec)

    producer.flush()
    producer.close()

    logger.info(
        f"Production complete: {counts}"
    )

    return counts


if __name__ == "__main__":
    counts = produce_events(
        num_events=50,
        delay_sec=0.1,
        anomaly_rate=0.05
    )
    print(f"Events produced: {counts}")