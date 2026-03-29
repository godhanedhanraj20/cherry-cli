from typing import Optional

from pydantic import BaseModel


class SendOtpRequest(BaseModel):
    api_id: int
    api_hash: str
    phone_number: str


class VerifyOtpRequest(BaseModel):
    session_id: str
    otp: str


class TwoFARequest(BaseModel):
    session_id: str
    password: str


class AuthStatusResponse(BaseModel):
    logged_in: bool
    is_premium: bool = False


class SendOtpResponse(BaseModel):
    status: str
    session_id: str


class AuthResponse(BaseModel):
    status: str
    is_premium: bool = False
    requires_2fa: bool = False
    session_id: Optional[str] = None
