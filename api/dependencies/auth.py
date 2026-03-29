from fastapi import HTTPException

from services.auth import get_authenticated_client
from utils.errors import TSGError


async def get_client():
    try:
        client = await get_authenticated_client()
        return client
    except TSGError as exc:
        raise HTTPException(status_code=401, detail={"error": str(exc)}) from exc
