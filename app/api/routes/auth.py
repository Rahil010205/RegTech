"""Email OTP authentication."""

from uuid import uuid4

from fastapi import APIRouter, status

from app.api.schemas.auth import (
    OtpRequestPayload,
    OtpRequestResponse,
    OtpVerifyPayload,
    OtpVerifyResponse,
    AuthUserResponse,
)
from app.api.schemas.common import MessageResponse
from app.core.security import create_access_token
from app.services.email_service import send_otp_email
from app.services.otp_service import (
    display_name_for_role,
    issue_otp,
    normalize_email,
    role_for_email,
    verify_otp,
)

router = APIRouter()


@router.post("/otp/request", response_model=OtpRequestResponse)
async def request_otp(payload: OtpRequestPayload) -> OtpRequestResponse:
    """Generate a 6-digit OTP and email it when SMTP is configured."""
    email = normalize_email(payload.email)
    code = issue_otp(email)
    sent = send_otp_email(email, code)
    if sent:
        return OtpRequestResponse(
            message="A one-time password was sent to your email.",
            email_sent=True,
            dev_otp=None,
        )
    return OtpRequestResponse(
        message=(
            "A sign-in code was generated, but email is not configured. "
            "Set REGTECH_SMTP_* in .env to deliver codes to your inbox."
        ),
        email_sent=False,
        dev_otp=code,
    )


@router.post("/otp/verify", response_model=OtpVerifyResponse)
async def verify_otp_endpoint(payload: OtpVerifyPayload) -> OtpVerifyResponse:
    """Validate the emailed OTP and return a session JWT."""
    email = normalize_email(payload.email)
    verify_otp(email, payload.otp)
    role = role_for_email(email)
    user = AuthUserResponse(
        id=str(uuid4()),
        email=email,
        name=display_name_for_role(role),
        role=role,
    )
    token = create_access_token({"sub": email, "role": role, "user_id": user.id})
    return OtpVerifyResponse(access_token=token, user=user)


@router.post("/login", response_model=MessageResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def login() -> MessageResponse:
    """Password login is not used — use POST /auth/otp/request."""
    return MessageResponse(message="Use email OTP at /auth/otp/request")


@router.post("/refresh", response_model=MessageResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def refresh_token() -> MessageResponse:
    """Refresh an expired access token. Not yet implemented."""
    return MessageResponse(message="Auth not yet implemented")
