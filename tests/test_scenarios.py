import pytest
from tests.test_filters import search_files_logic

def test_full_flow():
    files = [
        {"name": "Pokemon.mp4", "tags": ["anime"]}
    ]
    results = search_files_logic(files, query="pokemon", tag="anime", file_type="video")
    assert len(results) == 1

def test_weird_filenames():
    files = [{"name": "file.mp4.mkv", "tags": []}]
    results = search_files_logic(files, file_type="video")
    assert len(results) == 1

def test_empty_metadata():
    files = [{}]
    results = search_files_logic(files)
    assert isinstance(results, list)
    assert len(results) == 1 # Empty metadata dict name="" doesn't get filtered unless query/tag requires it

def test_no_crash_on_invalid_tags():
    files = [{"name": "file.mp4", "tags": None}]
    results = search_files_logic(files, tag="anime")
    assert isinstance(results, list)
    assert len(results) == 0

def test_multiple_operations():
    files = []
    for i in range(10):
        files.append({"name": f"file_{i}.mp4", "tags": ["test"]})

    results = search_files_logic(files, tag="test")
    assert len(results) == 10
