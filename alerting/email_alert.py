"""
SentinelFlow - Email Alerting
Sends email notifications when critical issues are detected.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config.settings import (
    ALERT_EMAIL_SENDER,
    ALERT_EMAIL_PASSWORD,
    ALERT_EMAIL_RECEIVER,
    SMTP_HOST,
    SMTP_PORT
)
from config.logging_config import get_logger

logger = get_logger(__name__)


def send_email_alert(
    subject: str,
    body: str,
    severity: str = "warning"
) -> bool:
    """
    Send an email alert.
    Returns True if sent successfully, False otherwise.
    """
    if not ALERT_EMAIL_SENDER or not ALERT_EMAIL_PASSWORD:
        logger.warning("Email credentials not configured, skipping email alert")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[SentinelFlow {severity.upper()}] {subject}"
        msg["From"] = ALERT_EMAIL_SENDER
        msg["To"] = ALERT_EMAIL_RECEIVER

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="background-color: white; padding: 20px; border-radius: 8px;">
                <h2 style="color: {'#ff4444' if severity == 'critical' else '#ffaa00'};">
                    SentinelFlow Alert
                </h2>
                <p><strong>Severity:</strong> {severity.upper()}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>{body}</p>
                <hr>
                <p style="color: #888; font-size: 12px;">
                    This alert was generated automatically by SentinelFlow.
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(ALERT_EMAIL_SENDER, ALERT_EMAIL_PASSWORD)
            server.sendmail(
                ALERT_EMAIL_SENDER,
                ALERT_EMAIL_RECEIVER,
                msg.as_string()
            )

        logger.info(f"Email alert sent: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False


def send_pipeline_failure_alert(pipeline_id: str, error: str) -> bool:
    """Send an alert when a pipeline run fails."""
    return send_email_alert(
        subject=f"Pipeline failure: {pipeline_id}",
        body=f"Pipeline {pipeline_id} failed with error: {error}",
        severity="critical"
    )


def send_drift_alert(dataset_name: str, column: str, score: float) -> bool:
    """Send an alert when data drift is detected."""
    return send_email_alert(
        subject=f"Data drift detected in {dataset_name}",
        body=(
            f"Significant data drift detected in dataset '{dataset_name}', "
            f"column '{column}' with score {score:.4f}. "
            f"This may indicate a change in your data distribution."
        ),
        severity="warning"
    )


def send_anomaly_alert(dataset_name: str, anomaly_count: int, total: int) -> bool:
    """Send an alert when anomaly rate is high."""
    rate = round(anomaly_count / total * 100, 2) if total > 0 else 0
    return send_email_alert(
        subject=f"High anomaly rate in {dataset_name}",
        body=(
            f"High anomaly rate detected in dataset '{dataset_name}': "
            f"{anomaly_count}/{total} records ({rate}%) flagged as anomalies."
        ),
        severity="critical"
    )