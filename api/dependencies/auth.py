from services.auth import get_authenticated_client


async def get_client():
    client = await get_authenticated_client()
    try:
        yield client
    finally:
        await client.disconnect()
