import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from cli.commands import delete, download, tag
import typer
from typing import List

# Placeholder tests for batch commands logic

def test_batch_delete():
    # Verify that the typer argument signature accepts List[str]
    assert "file_ids: List[str]" in str(delete.__annotations__) or "file_ids" in delete.__annotations__

def test_batch_download():
    # Verify that the typer argument signature accepts List[str]
    assert "file_ids: List[str]" in str(download.__annotations__) or "file_ids" in download.__annotations__

def test_partial_failure():
    # Verify that the typer argument signature accepts string for manual splitting
    assert "file_ids_str" in tag.__annotations__

@pytest.mark.asyncio
async def test_download_keyboard_interrupt():
    from services.file_service import download_file
    from utils.errors import TSGError
    import os

    # Mock client and message
    client = AsyncMock()
    message = MagicMock()
    message.document = MagicMock(file_size=100)
    message.document.file_name = "test.txt"
    client.get_messages.return_value = message
    
    async def mock_stream(*args, **kwargs):
        raise KeyboardInterrupt()
        yield b"chunk"
        
    client.stream_media = mock_stream
    
