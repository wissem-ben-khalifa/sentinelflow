"""
SentinelFlow - Kafka Topics Configuration
Central definition of all Kafka topics and their schemas.
"""

TOPICS = {
    "page_views": {
        "name": "page_views",
        "description": "User page view events",
        "fields": ["user_id", "page", "duration_sec", "timestamp"]
    },
    "purchases": {
        "name": "purchases",
        "description": "Purchase transaction events",
        "fields": ["user_id", "product_id", "amount", "quantity", "timestamp"]
    },
    "user_clicks": {
        "name": "user_clicks",
        "description": "User click interaction events",
        "fields": ["user_id", "element", "page", "timestamp"]
    },
    "cart_events": {
        "name": "cart_events",
        "description": "Shopping cart add/remove events",
        "fields": ["user_id", "product_id", "action", "quantity", "timestamp"]
    }
}

BOOTSTRAP_SERVERS = "localhost:9092"

ANOMALOUS_AMOUNT_THRESHOLD = 5000.0
ANOMALOUS_QUANTITY_THRESHOLD = 100