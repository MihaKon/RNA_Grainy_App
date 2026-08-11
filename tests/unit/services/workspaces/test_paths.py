import uuid
from pathlib import Path

import pytest
from app.exceptions import InvalidRequestError
from app.services.workspaces.paths import (
    is_valid_uuid,
    get_workspace_dir,
    get_workspace_file_path,
)


def test_is_valid_uuid_with_valid_uuid() -> None:
    workspace_id = str(uuid.uuid4())
    result = is_valid_uuid(workspace_id)

    assert result is True


def test_is_valid_uuid_rejects_invalid_uuid() -> None:
    workspace_id = str(uuid.uuid4())[:-1]
    result = is_valid_uuid(workspace_id)

    assert result is False


def test_get_workspace_dir_returns_correct_path(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = str(uuid.uuid4())
    result = get_workspace_dir(workspace_id)

    assert result == isolated_workspace_storage / workspace_id


def test_get_workspace_file_path_returns_correct_path(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = str(uuid.uuid4())
    filename = "test_file.pdb"
    result = get_workspace_file_path(workspace_id, filename)

    assert result == isolated_workspace_storage / workspace_id / filename


def test_get_workspace_file_path_rejects_invalid_filename(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = str(uuid.uuid4())
    filename = "../test_file.pdb"

    with pytest.raises(InvalidRequestError):
        get_workspace_file_path(workspace_id, filename)


def test_get_workspace_dir_rejects_invalid_uuid(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = str(uuid.uuid4())[:-1]

    with pytest.raises(InvalidRequestError):
        get_workspace_dir(workspace_id)
