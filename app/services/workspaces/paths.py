import uuid
from pathlib import Path

from app.exceptions import InvalidRequestError
from app.settings import WORKSPACE_STORAGE_DIR


def is_valid_uuid(workspace_id: str) -> bool:
    try:
        return str(uuid.UUID(workspace_id)) == workspace_id
    except ValueError:
        return False


def validate_uuid(workspace_id: str) -> None:
    if not is_valid_uuid(workspace_id):
        raise InvalidRequestError("Invalid workspace ID format.")


def check_path(path: Path, parent_path: Path) -> None:
    if not path.resolve().is_relative_to(parent_path.resolve()):
        raise InvalidRequestError("Invalid path.")


def get_workspace_dir(workspace_id: str) -> Path:
    validate_uuid(workspace_id)

    workspace_dir = WORKSPACE_STORAGE_DIR / workspace_id

    check_path(workspace_dir, WORKSPACE_STORAGE_DIR)
    return workspace_dir


def get_workspace_file_path(workspace_id: str, filename: str) -> Path:
    workspace_dir = get_workspace_dir(workspace_id)
    file_path = workspace_dir / filename
    check_path(file_path, workspace_dir)
    return file_path
