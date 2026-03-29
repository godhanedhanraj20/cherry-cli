import asyncio
import pytest
import warnings

# Suppress Pyrogram sync deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pyrogram.sync")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
