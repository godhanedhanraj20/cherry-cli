from fastapi import HTTPException

from services.auth import get_authenticated_client
from utils.errors import TSGError


async def get_client():
    client = None
    try:
        client = await get_authenticated_client()
        yield client
    except TSGError as exc:
        raise HTTPException(status_code=401, detail={"error": str(exc)}) from exc
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
