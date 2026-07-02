import logging

import resend

from app.config import settings

logger = logging.getLogger("email_service")

resend.api_key = settings.RESEND_API_KEY


def _send(to_email: str, subject: str, html: str) -> bool:
    """
    Wrapped in try/except so an email provider outage never breaks the
    actual request (interest creation / accept / decline must still
    succeed even if Resend is down or misconfigured).
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set - skipping email to %s", to_email)
        return False
    try:
        resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as exc:
        logger.warning("Failed to send email to %s: %s", to_email, exc)
        return False


def send_high_match_email(owner_email: str, owner_name: str, tenant_name: str,
                           listing_location: str, score: int, explanation: str) -> bool:
    subject = f"Strong match ({score}/100) for your listing in {listing_location}"
    html = f"""
    <p>Hi {owner_name},</p>
    <p><strong>{tenant_name}</strong> has expressed interest in your listing in
    <strong>{listing_location}</strong> with a compatibility score of
    <strong>{score}/100</strong>.</p>
    <p><em>{explanation}</em></p>
    <p>Log in to your dashboard to accept or decline this request.</p>
    """
    return _send(owner_email, subject, html)


def send_interest_decision_email(tenant_email: str, tenant_name: str,
                                  listing_location: str, status: str) -> bool:
    verb = "accepted" if status == "accepted" else "declined"
    subject = f"Your interest request was {verb}"
    html = f"""
    <p>Hi {tenant_name},</p>
    <p>The owner of the listing in <strong>{listing_location}</strong> has
    <strong>{verb}</strong> your interest request.</p>
    {"<p>You can now chat with the owner directly from your dashboard.</p>" if status == "accepted" else ""}
    """
    return _send(tenant_email, subject, html)