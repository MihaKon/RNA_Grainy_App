from pathlib import Path

import pytest

import app.services.workspaces.manager as manager_module
from app.exceptions import (
    FileProcessingError,
    InvalidRequestError,
    ResultNotFoundError,
)
from app.services.workspaces.manager import WorkspaceManager
from app.settings import MIN_FREE_DISK_SIZE


def test_setup_workspace_dir_creates_directory(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    assert workspace_dir == isolated_workspace_storage / workspace_id
    assert workspace_dir.is_dir()


def test_setup_workspace_dir_rejects_invalid_uuid(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()[:-1]

    with pytest.raises(InvalidRequestError):
        WorkspaceManager.setup_workspace_dir(workspace_id)


@pytest.mark.anyio
async def test_create_file_writes_content(
    isolated_workspace_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)
    content = "ACGUACGAAUUAUAUAAAAACCCG"
    filename = "coarse.cif"

    monkeypatch.setattr(
        WorkspaceManager,
        "_get_free_disk_size",
        lambda: 10**12,
    )

    result = await WorkspaceManager.create_file(workspace_id, content, filename)

    assert result == workspace_dir / filename
    assert result.is_file()
    assert result.read_text(encoding="utf-8") == content


@pytest.mark.anyio
async def test_create_file_rejects_insufficient_disk_space(
    isolated_workspace_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)
    content = "example content"
    filename = "coarse.cif"
    required_size = len(content.encode("utf-8"))

    monkeypatch.setattr(
        WorkspaceManager,
        "_get_free_disk_size",
        lambda: MIN_FREE_DISK_SIZE + required_size - 1,
    )

    with pytest.raises(
        FileProcessingError,
        match="enough disk space",
    ):
        await WorkspaceManager.create_file(
            workspace_id,
            content,
            filename,
        )

    assert not (workspace_dir / filename).exists()


def test_get_file_path_returns_correct_path(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)
    filename = "coarse.cif"
    file_path = workspace_dir / filename
    file_path.write_text("example content", encoding="utf-8")

    result = WorkspaceManager.get_file_path(workspace_id, filename)

    assert result == file_path


def test_get_file_path_rejects_missing_file(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()
    WorkspaceManager.setup_workspace_dir(workspace_id)

    with pytest.raises(
        ResultNotFoundError,
        match="does not exist",
    ):
        WorkspaceManager.get_file_path(
            workspace_id,
            "missing.cif",
        )


def test_cleanup_workspace_removes_directory(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)
    workspace_file = workspace_dir / "coarse.cif"
    workspace_file.write_text("example content", encoding="utf-8")

    WorkspaceManager.cleanup_workspace(workspace_id)

    assert not workspace_dir.exists()


def test_cleanup_workspace_ignores_missing_directory(
    isolated_workspace_storage: Path,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    WorkspaceManager.cleanup_workspace(workspace_id)
    WorkspaceManager.cleanup_workspace(workspace_id)

    assert not workspace_dir.exists()


@pytest.mark.anyio
@pytest.mark.parametrize(("limit", "succeeds"), [(104, False), (105, True)])
async def test_storage_limit_rejects_new_files_without_removing_existing_results(
    isolated_workspace_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit: int,
    succeeds: bool,
) -> None:
    existing = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )
    existing_file = existing / "coarse.mmcif"
    existing_file.write_bytes(b"A" * 100)
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace = WorkspaceManager.setup_workspace_dir(workspace_id)
    monkeypatch.setattr(manager_module, "WORKSPACE_STORAGE_MAX_SIZE", limit)
    monkeypatch.setattr(WorkspaceManager, "_get_free_disk_size", lambda: 10**12)

    if succeeds:
        result = await WorkspaceManager.create_file(
            workspace_id, "ąRNA", "coarse.mmcif"
        )
        assert result.read_text(encoding="utf-8") == "ąRNA"
    else:
        with pytest.raises(FileProcessingError, match="storage is full"):
            await WorkspaceManager.create_file(workspace_id, "ąRNA", "coarse.mmcif")
        assert not (workspace / "coarse.mmcif").exists()

    assert existing_file.read_bytes() == b"A" * 100
