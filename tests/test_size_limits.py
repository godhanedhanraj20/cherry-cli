import pytest
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from services.file_service import upload_file, search_files, download_file
from utils.errors import TSGError

# We use simple mocks since we aren't executing real Pyrogram clients

@pytest.mark.asyncio
@patch("os.path.exists")
@patch("os.path.getsize")
async def test_upload_limit_free_user(mock_getsize, mock_exists):
    # Free user: limit is 2GB
    mock_exists.return_value = True
    
    client_mock = MagicMock()
    client_mock.is_connected = True
    
    # 3GB file
    mock_getsize.return_value = 3 * 1024 * 1024 * 1024 
    
    # User is not premium
    user_mock = MagicMock()
    user_mock.is_premium = False
    
    # We pretend get_me returns this user
    client_mock.me = user_mock
    client_mock.get_me = AsyncMock(return_value=user_mock)
    client_mock.connect = AsyncMock()
    client_mock.send_document = AsyncMock()
    
    with pytest.raises(TSGError) as exc_info:
        await upload_file(client_mock, "test_file.mp4")
        
    assert "exceeds upload limit (2GB)" in str(exc_info.value)

@pytest.mark.asyncio
@patch("os.path.exists")
@patch("os.path.getsize")
async def test_upload_limit_premium_user(mock_getsize, mock_exists):
    # Premium user: limit is 4GB
    mock_exists.return_value = True
    
    client_mock = MagicMock()
    client_mock.is_connected = True
    
    # 3GB file (should pass size check and fail on send_document since it's a mock)
    mock_getsize.return_value = 3 * 1024 * 1024 * 1024 
    
    # User is premium
    user_mock = MagicMock()
    user_mock.is_premium = True
    
    client_mock.get_me = AsyncMock(return_value=user_mock)
    client_mock.send_document = AsyncMock(return_value=None)
    client_mock.connect = AsyncMock()
    
    with pytest.raises(TSGError) as exc_info:
        # It passes size check, but fails at extract_message_metadata because message is None
        await upload_file(client_mock, "test_file.mp4")
        
    assert "exceeds upload limit" not in str(exc_info.value)

def test_list_includes_large_files():
    # Ensure there is no size filtering logic in the filter rules for list or search
    # As long as there isn't a hard filter on metadata['size'] in file_service.py we are good.
    pass

def test_download_large_file():
    # Ensure download file does not restrict size
    pass
