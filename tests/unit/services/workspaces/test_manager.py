from pathlib import Path

import pytest
from app.exceptions import InvalidRequestError, FileProcessingError
from app.settings import MIN_FREE_DISK_SIZE
from app.services.workspaces.manager import WorkspaceManager


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
        FileProcessingError,
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
