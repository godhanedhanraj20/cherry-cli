from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    api_id: int
    api_hash: str
    phone_number: str
    otp: str
    password: Optional[str] = None


class LoginResponse(BaseModel):
    status: str
    is_premium: bool


class AuthStatusResponse(BaseModel):
    logged_in: bool
    is_premium: bool = False
