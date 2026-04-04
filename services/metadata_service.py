from utils.errors import TSGError
from utils.metadata_manager import add_tag, get_tags, remove_custom_name, remove_tag, set_custom_name



def manage_tags(file_ids: list[str], action: str, tag_name: str | None = None):
    if action not in ["add", "remove", "list"]:
        raise TSGError("Invalid action. Use: add, remove, list")

    results = []
    for fid in file_ids:
        if not fid:
            raise TSGError("Invalid file_id")
        if action == "add":
            if not tag_name:
                raise TSGError("Tag name is required for adding a tag.")
            if len(tag_name.strip()) > 50:
                raise TSGError("Tag too long")
            add_tag(fid, tag_name)
            results.append({"file_id": fid, "action": "add", "tag": tag_name.strip().lower()})
        elif action == "remove":
            if not tag_name:
                raise TSGError("Tag name is required for removing a tag.")
            if len(tag_name.strip()) > 50:
                raise TSGError("Tag too long")
            remove_tag(fid, tag_name)
            results.append({"file_id": fid, "action": "remove", "tag": tag_name.strip().lower()})
        else:
            tags = get_tags(fid)
            results.append({"file_id": fid, "action": "list", "tags": tags})

    return results



def rename_file(file_id: str, name: str | None):
    if not file_id:
        raise TSGError("Invalid file_id")
    if name is not None and not name.strip():
        raise TSGError("Invalid filename")

    if name:
        set_custom_name(file_id, name)
        return {"file_id": file_id, "custom_name": name.strip(), "removed": False}

    remove_custom_name(file_id)
    return {"file_id": file_id, "custom_name": None, "removed": True}
