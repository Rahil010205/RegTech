"""OTP request / verify schemas."""

from pydantic import BaseModel, Field

from app.api.schemas.common import MessageResponse


class OtpRequestPayload(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)


class OtpVerifyPayload(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class OtpRequestResponse(MessageResponse):
    email_sent: bool
    dev_otp: str | None = None


class AuthUserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str


class OtpVerifyResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse
