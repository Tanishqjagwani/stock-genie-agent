import logging
import resend

from config.settings import RESEND_API_KEY, EMAIL_FROM, EMAIL_TO

logger = logging.getLogger(__name__)


def send_report_email(subject: str, html: str) -> None:
    """Send the HTML report via Resend."""
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY not set, cannot send email")
        return
    if not EMAIL_TO:
        logger.error("EMAIL_TO not set, cannot send email")
        return

    resend.api_key = RESEND_API_KEY

    params = {
        "from": EMAIL_FROM,
        "to": [EMAIL_TO],
        "subject": subject,
        "html": html,
    }

    resp = resend.Emails.send(params)
    logger.info(f"Email sent: {resp}")
