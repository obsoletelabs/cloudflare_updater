"""Email Notification Library"""

import logging
import time
from os import environ
from smtplib import SMTP, SMTP_SSL

logger = logging.getLogger(__name__)

# Environment configuration
smtp_enabled = environ.get("NOTIFIER_SMTP_ENABLED", "false").lower() == "true"
smtp_username = environ.get("NOTIFIER_SMTP_USERNAME", "")
smtp_password = environ.get("NOTIFIER_SMTP_PASSWORD", "")
smtp_server = environ.get("NOTIFIER_SMTP_SERVER", "")

smtp_security = environ.get("NOTIFIER_SMTP_SECURITY", "starttls").lower()  # starttls, tls, none
smtp_port = int( environ.get("NOTIFIER_SMTP_PORT", "0") )
# Determine default port based on security setting
if smtp_port == 0:
    if smtp_security == "tls":
        smtp_port = 465
    elif smtp_security == "starttls":
        smtp_port = 587
    else:
        smtp_port = 25


email_from = environ.get("NOTIFIER_EMAIL_FROM_ADDRESS", smtp_username)
email_to = environ.get("NOTIFIER_EMAIL_TO_ADDRESSES", "")

# Retry configuration
smtp_retries = int(environ.get("NOTIFIER_SMTP_RETRIES", "3"))
smtp_retry_delay = float(environ.get("NOTIFIER_SMTP_RETRY_DELAY", "1.5"))

# Disable SMTP if required fields are missing
if smtp_username == "" or smtp_password == "" or smtp_server == "" or email_to == "":
    smtp_enabled = False
    logger.warning("SMTP is not properly configured; email notifications are disabled.")
else:
    logger.info("SMTP email notifications are enabled.")


def _normalize_recipients(sendto):
    """Convert sendto into a list of email addresses."""
    if not sendto:
        sendto = email_to

    if isinstance(sendto, str):
        sendto = [addr.strip() for addr in sendto.split(",") if addr.strip()]

    if not isinstance(sendto, (list, tuple)):
        sendto = [str(sendto)]

    return sendto


def _open_smtp_connection():
    """Open an SMTP connection using the configured security mode."""
    if smtp_security == "tls":
        # Implicit TLS (SMTPS, usually port 465)
        logger.debug("Opening SMTP_SSL connection to %s:%s", smtp_server, smtp_port)
        return SMTP_SSL(smtp_server, smtp_port, timeout=5)

    # Normal SMTP (optionally upgraded with STARTTLS)
    logger.debug("Opening SMTP connection to %s:%s", smtp_server, smtp_port)
    server = SMTP(smtp_server, smtp_port, timeout=5)

    if smtp_security == "starttls":
        logger.debug("Starting TLS upgrade via STARTTLS")
        server.starttls()

    return server


def send_email_notification(subject: str, body: str, sendto=None) -> bool:
    """Send an email using SMTP with TLS, login, retry logic, and fallback recipients."""
    if not smtp_enabled:
        logger.warning("SMTP is disabled; email not sent.")
        return False

    recipients = _normalize_recipients(sendto)
    message = f"Subject: {subject}\n\n{body}"

    for attempt in range(1, smtp_retries + 1):
        try:
            with _open_smtp_connection() as server:
                server.login(smtp_username, smtp_password)
                server.sendmail(email_from, recipients, message)

            logger.info("Email sent successfully to %s", recipients)
            return True

        except Exception as e:
            logger.error(
                "SMTP attempt %d/%d failed: %s",
                attempt, smtp_retries, e
            )

            if attempt < smtp_retries:
                time.sleep(smtp_retry_delay)
            else:
                logger.critical("All SMTP retry attempts failed.")

    return False
