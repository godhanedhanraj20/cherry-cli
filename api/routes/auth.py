from fastapi import APIRouter

from api.schemas.auth import AuthStatusResponse, LoginRequest, LoginResponse
from api.services_adapter.adapters import auth_status_adapter, login_adapter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    return await login_adapter(
        api_id=payload.api_id,
        api_hash=payload.api_hash,
        phone_number=payload.phone_number,
        otp=payload.otp,
        password=payload.password,
    )


@router.get("/status", response_model=AuthStatusResponse)
async def status():
    return await auth_status_adapter()
