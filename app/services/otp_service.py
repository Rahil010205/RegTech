"""In-memory OTP issuance and verification."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import threading
import time
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class _OtpRecord:
    digest: str
    expires_at: float
    last_sent_at: float
    attempts: int = 0


_lock = threading.Lock()
_otps: dict[str, _OtpRecord] = {}


def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if "@" not in value or "." not in value.split("@")[-1]:
        raise ValidationError("Enter a valid work email.")
    return value


def role_for_email(email: str) -> str:
    local = email.split("@", 1)[0]
    if "admin" in local:
        return "ADMIN"
    if "regulator" in local:
        return "REGULATOR"
    return "ORGANIZATION"


def display_name_for_role(role: str) -> str:
    if role == "ADMIN":
        return "Platform Admin"
    if role == "REGULATOR":
        return "Regulatory Officer"
    return "Org Compliance Lead"


def _digest(email: str, otp: str) -> str:
    settings = get_settings()
    payload = f"{email}:{otp}:{settings.secret_key}".encode()
    return hashlib.sha256(payload).hexdigest()


def issue_otp(email: str) -> str:
    settings = get_settings()
    now = time.time()
    with _lock:
        existing = _otps.get(email)
        if existing and now - existing.last_sent_at < settings.otp_resend_seconds:
            wait = int(settings.otp_resend_seconds - (now - existing.last_sent_at))
            raise ValidationError(f"Please wait {max(wait, 1)} seconds before requesting another code.")
        otp = f"{secrets.randbelow(1_000_000):06d}"
        _otps[email] = _OtpRecord(
            digest=_digest(email, otp),
            expires_at=now + settings.otp_ttl_seconds,
            last_sent_at=now,
        )
    logger.info("OTP issued for %s", email)
    return otp


def verify_otp(email: str, otp: str) -> None:
    now = time.time()
    with _lock:
        record = _otps.get(email)
        if record is None or now > record.expires_at:
            _otps.pop(email, None)
            raise UnauthorizedError("That code is invalid or has expired.")
        record.attempts += 1
        if record.attempts > 5:
            _otps.pop(email, None)
            raise UnauthorizedError("Too many attempts. Request a new code.")
        if not hmac.compare_digest(record.digest, _digest(email, otp)):
            raise UnauthorizedError("That code is invalid or has expired.")
        _otps.pop(email, None)
