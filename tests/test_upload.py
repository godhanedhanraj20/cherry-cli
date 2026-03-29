import pytest
import os
import shutil
import tempfile
from typer.testing import CliRunner
from cli.commands import app
from unittest.mock import AsyncMock, MagicMock

runner = CliRunner()

@pytest.fixture
def mock_upload_file(monkeypatch):
    mock = AsyncMock(return_value={"id": 1, "name": "test.txt", "size": "1B"})
    monkeypatch.setattr("cli.commands.upload_file", mock)
    return mock

@pytest.fixture
def mock_auth(monkeypatch):
    mock_client = MagicMock()
    mock_client.is_connected = True
    mock_client.disconnect = AsyncMock() # We need to mock disconnect as async too!
    mock = AsyncMock(return_value=mock_client)
    monkeypatch.setattr("cli.commands.get_authenticated_client", mock)
    return mock

@pytest.fixture
def test_dir():
    dir_path = tempfile.mkdtemp()
    
    # Create some files
    with open(os.path.join(dir_path, "file1.txt"), "w") as f:
        f.write("1")
    with open(os.path.join(dir_path, "file2.txt"), "w") as f:
        f.write("2")
        
    # Create a nested dir
    nested = os.path.join(dir_path, "nested")
    os.makedirs(nested)
    with open(os.path.join(nested, "file3.txt"), "w") as f:
        f.write("3")
        
    yield dir_path
    
    shutil.rmtree(dir_path)

def test_upload_single_file(mock_upload_file, mock_auth, test_dir):
    file_path = os.path.join(test_dir, "file1.txt")
    result = runner.invoke(app, ["upload", file_path])
    if result.exit_code != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"EXCEPTION: {result.exception}")
    assert result.exit_code == 0
    assert "Uploading:" in result.stdout
    assert "Success: 1" in result.stdout

def test_upload_folder(mock_upload_file, mock_auth, test_dir):
    result = runner.invoke(app, ["upload", test_dir], input="y\n") # Confirm prompt for >3 files (3 files in test_dir)
    if result.exit_code != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"EXCEPTION: {result.exception}")
    assert result.exit_code == 0
    assert "Found 3 files" in result.stdout
    assert "Success: 3" in result.stdout

def test_upload_missing_file(mock_upload_file, mock_auth):
    result = runner.invoke(app, ["upload", "does_not_exist.txt"])
    assert result.exit_code == 1 # Now raises Exit(1) because path doesn't exist up front
    assert "Error: Path 'does_not_exist.txt' does not exist" in result.stdout
