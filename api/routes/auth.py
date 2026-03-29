from fastapi import APIRouter

from api.schemas.auth import AuthResponse, AuthStatusResponse, SendOtpRequest, TwoFARequest, VerifyOtpRequest
from api.services_adapter.adapters import auth_status_adapter, send_otp_adapter, two_fa_adapter, verify_otp_adapter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-otp", response_model=AuthResponse)
async def send_otp(payload: SendOtpRequest):
    return await send_otp_adapter(
        api_id=payload.api_id,
        api_hash=payload.api_hash,
        phone_number=payload.phone_number,
    )


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(payload: VerifyOtpRequest):
    return await verify_otp_adapter(phone_number=payload.phone_number, otp=payload.otp)


@router.post("/2fa", response_model=AuthResponse)
async def two_fa(payload: TwoFARequest):
    return await two_fa_adapter(password=payload.password)


@router.get("/status", response_model=AuthStatusResponse)
async def status():
    return await auth_status_adapter()
