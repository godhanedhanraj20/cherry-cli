import pytest
from services.file_service import _matches_type

# We'll create a dummy function that mimics the exact filtering logic 
# of search_files so we can unit test the logic isolated from Pyrogram

def search_files_logic(files, query=None, tag=None, file_type=None):
    query = query.strip().lower() if query else None
    tag = tag.strip().lower() if tag else None
    file_type = file_type.strip().lower() if file_type else None

    results = []
    for file in files:
        file_name = file.get("name", "").lower()
        
        # Hide internal files
        if file_name == "metadata_backup.json":
            continue
            
        # AND logic: Name-based filtering
        if query and query not in file_name:
            continue
            
        # AND logic: Tag-based filtering
        if tag:
            raw_tags = file.get("tags") or []
            if isinstance(raw_tags, str):
                raw_tags = [t.strip() for t in raw_tags.split(",")] if raw_tags != "-" else []
            tags_list = [t.lower() for t in raw_tags if t.strip()]
            
            if tag not in tags_list:
                continue
                
        # AND logic: Type-based filtering
        if file_type:
            # Mimic fallback to extension since we don't have pyrogram native attributes here
            if not _matches_type(file_name, file_type):
                continue
                
        results.append(file)
        
    return results

def test_combined_filters():
    files = [
        {"name": "Pokemon.mp4", "tags": "anime, childhood"},
        {"name": "Naruto.mp4", "tags": "anime, ninja"},
        {"name": "Pokemon_Game.zip", "tags": "games"},
        {"name": "metadata_backup.json", "tags": ""}
    ]

    # Query only
    results = search_files_logic(files, query="pokemon")
    assert len(results) == 2

    # Tag only
    results = search_files_logic(files, tag="anime")
    assert len(results) == 2

    # File type only
    results = search_files_logic(files, file_type="video")
    assert len(results) == 2
    
    # Combined (query + tag + type)
    results = search_files_logic(files, query="pokemon", tag="anime", file_type="video")
    assert len(results) == 1
    assert results[0]["name"] == "Pokemon.mp4"
    
    # Internal file should never be returned
    results = search_files_logic(files, query="metadata")
    assert len(results) == 0

    # Case insensitive
    results = search_files_logic(files, query="PoKeMon", tag="AniMe")
    assert len(results) == 1

def test_matches_type():
    assert _matches_type("video.mp4", "video") is True
    assert _matches_type("image.jpg", "image") is True
    assert _matches_type("doc.pdf", "document") is True
    assert _matches_type("song.mp3", "audio") is True
    # ZIP was removed from the target list as per final instructions
    assert _matches_type("archive.zip", "document") is False
    assert _matches_type("unknown.exe", "video") is False

def test_combined_filters_query_tag_type():
    files = [
        {"name": "Pokemon.mp4", "tags": "anime, childhood"},
        {"name": "Naruto.mkv", "tags": "anime, ninja"},
        {"name": "Bleach.mkv", "tags": "anime"},
        {"name": "Pokemon_Game.exe", "tags": "anime"},
    ]
    # Match query pokemon + tag anime + type video
    results = search_files_logic(files, query="pokemon", tag="anime", file_type="video")
    assert len(results) == 1
    assert results[0]["name"] == "Pokemon.mp4"

def test_case_insensitive_search():
    files = [{"name": "PoKeMoN.MP4", "tags": ["AnImE"]}]
    results = search_files_logic(files, query="pOkEmOn", tag="aNiMe", file_type="video")
    assert len(results) == 1

def test_empty_result():
    files = [{"name": "Pokemon.mp4", "tags": ["anime"]}]
    results = search_files_logic(files, query="Naruto")
    assert len(results) == 0

def test_invalid_type():
    files = [{"name": "Pokemon.mp4", "tags": ["anime"]}]
    results = search_files_logic(files, file_type="document")
    assert len(results) == 0

def test_multiple_tags():
    files = [
        {"name": "Pokemon.mp4", "tags": ["anime", "childhood", "games"]},
        {"name": "Naruto.mp4", "tags": "anime, ninja"},
    ]
    results = search_files_logic(files, tag="games")
    assert len(results) == 1
    assert results[0]["name"] == "Pokemon.mp4"

def test_no_tag_field():
    files = [
        {"name": "Pokemon.mp4"}, # No tag field
        {"name": "Naruto.mp4", "tags": ["anime"]},
    ]
    results = search_files_logic(files, tag="anime")
    assert len(results) == 1
    assert results[0]["name"] == "Naruto.mp4"
