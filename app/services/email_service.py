"""Send one-time passcodes by SMTP."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_otp_email(to_email: str, code: str) -> bool:
    """Deliver a 6-digit OTP. Returns False when SMTP is not configured."""
    settings = get_settings()
    host = (settings.smtp_host or "").strip()
    from_addr = (settings.smtp_from or settings.smtp_username or "").strip()
    if not host or not from_addr:
        logger.warning("OTP email skipped: SMTP is not configured")
        return False

    message = EmailMessage()
    message["Subject"] = "Your RegTech AI sign-in code"
    message["From"] = from_addr
    message["To"] = to_email
    message.set_content(
        f"Your RegTech AI one-time password is {code}.\n\n"
        f"It expires in {settings.otp_ttl_seconds // 60} minutes. "
        "If you did not request this, you can ignore this email.\n"
    )
    message.add_alternative(
        f"""
        <div style="font-family:Segoe UI,Arial,sans-serif;background:#09090b;color:#fafafa;padding:32px">
          <h1 style="font-size:18px;margin:0 0 12px">RegTech AI</h1>
          <p style="color:#a1a1aa;margin:0 0 20px">Use this one-time password to sign in.</p>
          <p style="letter-spacing:8px;font-size:28px;font-weight:600;margin:0 0 20px">{code}</p>
          <p style="color:#71717a;font-size:12px;margin:0">Expires in {settings.otp_ttl_seconds // 60} minutes.</p>
        </div>
        """,
        subtype="html",
    )

    try:
        with smtplib.SMTP(host, settings.smtp_port, timeout=20) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)
        logger.info("OTP email sent to %s", to_email)
        return True
    except OSError:
        logger.exception("Failed to send OTP email to %s", to_email)
        return False
