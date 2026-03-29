from utils.metadata_manager import (
    add_tag,
    get_tags,
    remove_custom_name,
    remove_tag,
    set_custom_name,
)
from utils.errors import TSGError


def manage_tags(file_ids: list[str], action: str, tag_name: str | None = None):
    if action not in ["add", "remove", "list"]:
        raise TSGError("Invalid action. Use: add, remove, list")

    results = []
    for fid in file_ids:
        if action == "add":
            if not tag_name:
                raise TSGError("Tag name is required for adding a tag.")
            add_tag(fid, tag_name)
            results.append({"file_id": fid, "action": "add", "tag": tag_name})
        elif action == "remove":
            if not tag_name:
                raise TSGError("Tag name is required for removing a tag.")
            remove_tag(fid, tag_name)
            results.append({"file_id": fid, "action": "remove", "tag": tag_name})
        else:
            tags = get_tags(fid)
            results.append({"file_id": fid, "action": "list", "tags": tags})

    return results


def rename_file(file_id: str, name: str | None):
    if name is not None and not name.strip():
        raise TSGError("Name cannot be empty")

    if name:
        set_custom_name(file_id, name)
        return {"file_id": file_id, "custom_name": name, "removed": False}

    remove_custom_name(file_id)
    return {"file_id": file_id, "custom_name": None, "removed": True}
