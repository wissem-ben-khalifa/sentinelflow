"""
SentinelFlow - Slack Alerting
Sends Slack notifications via webhook when issues are detected.
"""

import json
import urllib.request
from datetime import datetime
from config.settings import SLACK_WEBHOOK_URL
from config.logging_config import get_logger

logger = get_logger(__name__)


def send_slack_alert(
    message: str,
    severity: str = "warning",
    dataset_name: str = None
) -> bool:
    """
    Send a Slack alert via webhook.
    Returns True if sent successfully, False otherwise.
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook not configured, skipping Slack alert")
        return False

    color = "#ff4444" if severity == "critical" else "#ffaa00"
    icon = ":rotating_light:" if severity == "critical" else ":warning:"

    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{icon} SentinelFlow Alert"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Severity:*\n{severity.upper()}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Dataset:*\n{dataset_name or 'N/A'}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Message:*\n{message}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                logger.info(f"Slack alert sent: {message[:50]}")
                return True
            else:
                logger.error(f"Slack alert failed with status: {response.status}")
                return False

    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False


def send_drift_slack_alert(dataset_name: str, column: str, score: float) -> bool:
    """Send a Slack alert for data drift."""
    return send_slack_alert(
        message=(
            f"Data drift detected in column `{column}` "
            f"with score `{score:.4f}`. "
            f"Check the SentinelFlow dashboard for details."
        ),
        severity="warning",
        dataset_name=dataset_name
    )


def send_anomaly_slack_alert(
    dataset_name: str,
    anomaly_count: int,
    total: int
) -> bool:
    """Send a Slack alert for high anomaly rate."""
    rate = round(anomaly_count / total * 100, 2) if total > 0 else 0
    return send_slack_alert(
        message=(
            f"{anomaly_count}/{total} records ({rate}%) "
            f"flagged as anomalies. Immediate review recommended."
        ),
        severity="critical",
        dataset_name=dataset_name
    )