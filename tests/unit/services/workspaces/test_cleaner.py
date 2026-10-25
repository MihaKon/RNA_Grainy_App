import os
from pathlib import Path

import pytest

import app.services.workspaces.cleaner as cleaner_module
from app.services.workspaces import WorkspaceCleaner, WorkspaceManager


def test_get_directory_size_returns_total_file_size(
    isolated_workspace_storage: Path,
) -> None:
    first_content = "A" * 10
    second_content = "U" * 20

    first_file = isolated_workspace_storage / "file1.pdb"
    second_file = isolated_workspace_storage / "file2.pdb"

    first_file.write_text(first_content, encoding="utf-8")
    second_file.write_text(second_content, encoding="utf-8")

    dir_size = WorkspaceCleaner.get_directory_size(isolated_workspace_storage)

    assert dir_size == 30


def test_scan_workspaces_returns_only_valid_workspace_directories(
    isolated_workspace_storage: Path,
) -> None:
    valid_workspace_id = WorkspaceManager.create_workspace_id()
    valid_workspace_dir = WorkspaceManager.setup_workspace_dir(valid_workspace_id)

    invalid_workspace_dir = isolated_workspace_storage / "invalid_dir"
    invalid_workspace_dir.mkdir()

    uuid_name_file = isolated_workspace_storage / WorkspaceManager.create_workspace_id()
    uuid_name_file.write_text(
        "not a workspace directory",
        encoding="utf-8",
    )

    result = WorkspaceCleaner._scan_workspaces()
    assert len(result) == 1
    assert result[0].path == valid_workspace_dir
    assert result[0].size == 0


def test_remove_expired_workspaces_removes_expired_workspace(
    isolated_workspace_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_time = 100.0
    workspace_lifetime = 60

    monkeypatch.setattr(cleaner_module, "WORKSPACE_MAX_LIFETIME", workspace_lifetime)

    monkeypatch.setattr(cleaner_module.time, "time", lambda: current_time)

    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    workspace = cleaner_module.WorkspaceSnapshot(
        path=workspace_dir,
        modified_at=current_time - workspace_lifetime - 1,
        size=0,
    )

    removed_count = WorkspaceCleaner._remove_expired_workspaces([workspace])

    assert not workspace_dir.exists()
    assert removed_count == 1


def test_remove_expired_workspaces_keeps_fresh_workspace(
    isolated_workspace_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_time = 30.0
    workspace_lifetime = 60

    monkeypatch.setattr(cleaner_module, "WORKSPACE_MAX_LIFETIME", workspace_lifetime)

    monkeypatch.setattr(cleaner_module.time, "time", lambda: current_time)

    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    workspace = cleaner_module.WorkspaceSnapshot(
        path=workspace_dir,
        modified_at=current_time,
        size=0,
    )

    removed_count = WorkspaceCleaner._remove_expired_workspaces([workspace])

    assert workspace_dir.exists()
    assert removed_count == 0


def test_remove_expired_workspaces_removes_workspace_at_lifetime_limit(
    isolated_workspace_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_time = 60
    workspace_lifetime = 60

    monkeypatch.setattr(cleaner_module, "WORKSPACE_MAX_LIFETIME", workspace_lifetime)

    monkeypatch.setattr(cleaner_module.time, "time", lambda: current_time)

    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    workspace = cleaner_module.WorkspaceSnapshot(
        path=workspace_dir, modified_at=current_time - workspace_lifetime, size=0
    )

    removed_count = WorkspaceCleaner._remove_expired_workspaces([workspace])

    assert not workspace_dir.exists()
    assert removed_count == 1


def test_cleanup_workspaces_returns_removed_workspace_count(
    isolated_workspace_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace_lifetime = 60

    first_workspace_dir = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )

    second_workspace_dir = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )

    current_time = cleaner_module.time.time()
    monkeypatch.setattr(cleaner_module, "WORKSPACE_MAX_LIFETIME", workspace_lifetime)
    monkeypatch.setattr(
        cleaner_module.time, "time", lambda: current_time + workspace_lifetime + 1
    )

    removed_count = WorkspaceCleaner.cleanup_workspaces()

    assert removed_count == 2
    assert not first_workspace_dir.exists()
    assert not second_workspace_dir.exists()


def test_old_activity_markers_do_not_shorten_or_extend_retention(
    isolated_workspace_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )
    metadata = workspace / "result.json"
    metadata.write_text("{}")
    os.utime(metadata, (100.0, 100.0))
    (workspace / ".consumed").touch()
    monkeypatch.setattr(cleaner_module.time, "time", lambda: 100.0 + 2 * 3600)

    assert WorkspaceCleaner.cleanup_workspaces() == 0
    assert workspace.exists()
    assert WorkspaceCleaner._scan_workspaces()[0].modified_at == 100.0

    monkeypatch.setattr(cleaner_module.time, "time", lambda: 100.0 + 24 * 3600)
    assert WorkspaceCleaner.cleanup_workspaces() == 1
    assert not workspace.exists()


def test_storage_size_counts_existing_files_without_evicting_fresh_results(
    isolated_workspace_storage: Path,
) -> None:
    workspace = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )
    (workspace / "coarse.mmcif").write_bytes(b"A" * 100)

    assert WorkspaceCleaner.get_storage_size() == 100
    assert WorkspaceCleaner.cleanup_workspaces() == 0
    assert workspace.exists()
