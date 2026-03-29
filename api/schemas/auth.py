from pydantic import BaseModel


class SendOtpRequest(BaseModel):
    api_id: int
    api_hash: str
    phone_number: str


class VerifyOtpRequest(BaseModel):
    phone_number: str
    otp: str


class TwoFARequest(BaseModel):
    password: str


class AuthStatusResponse(BaseModel):
    logged_in: bool
    is_premium: bool = False


class AuthResponse(BaseModel):
    status: str
    is_premium: bool = False
    requires_2fa: bool = False
