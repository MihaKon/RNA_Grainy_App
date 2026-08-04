import logging
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

    remaining_workspaces, removed_count = WorkspaceCleaner._remove_expired_workspaces(
        [workspace]
    )

    assert not workspace_dir.exists()
    assert remaining_workspaces == []
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

    remaining_workspaces, removed_count = WorkspaceCleaner._remove_expired_workspaces(
        [workspace]
    )

    assert workspace_dir.exists()
    assert remaining_workspaces == [workspace]
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

    remaining_workspaces, removed_count = WorkspaceCleaner._remove_expired_workspaces(
        [workspace]
    )

    assert not workspace_dir.exists()
    assert remaining_workspaces == []
    assert removed_count == 1


def test_remove_workspaces_over_storage_limit_keeps_workspace_at_limit(
    isolated_workspace_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    storage_limit = 100

    monkeypatch.setattr(cleaner_module, "WORKSPACE_STORAGE_MAX_SIZE", storage_limit)

    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    workspace = cleaner_module.WorkspaceSnapshot(
        path=workspace_dir, modified_at=0, size=100
    )

    removed_workspaces_count = WorkspaceCleaner._remove_workspaces_over_storage_limit(
        [workspace]
    )

    assert removed_workspaces_count == 0
    assert workspace_dir.exists()


def test_remove_workspaces_over_storage_limit_removes_workspace_above_limit(
    isolated_workspace_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    storage_limit = 100

    monkeypatch.setattr(cleaner_module, "WORKSPACE_STORAGE_MAX_SIZE", storage_limit)

    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    workspace = cleaner_module.WorkspaceSnapshot(
        path=workspace_dir, modified_at=0, size=101
    )

    removed_workspaces_count = WorkspaceCleaner._remove_workspaces_over_storage_limit(
        [workspace]
    )

    assert removed_workspaces_count == 1
    assert not workspace_dir.exists()


def test_remove_workspaces_over_storage_limit_removes_oldest_workspace_first(
    isolated_workspace_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    storage_limit = 100
    workspace_size = 50

    monkeypatch.setattr(cleaner_module, "WORKSPACE_STORAGE_MAX_SIZE", storage_limit)

    oldest_workspace_dir = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )

    middle_workspace_dir = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )

    newest_workspace_dir = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )

    workspaces = [
        cleaner_module.WorkspaceSnapshot(
            path=oldest_workspace_dir, modified_at=10.0, size=workspace_size
        ),
        cleaner_module.WorkspaceSnapshot(
            path=middle_workspace_dir, modified_at=20.0, size=workspace_size
        ),
        cleaner_module.WorkspaceSnapshot(
            path=newest_workspace_dir, modified_at=30.0, size=workspace_size
        ),
    ]
    removed_count = WorkspaceCleaner._remove_workspaces_over_storage_limit(workspaces)

    assert removed_count == 1
    assert not oldest_workspace_dir.exists()
    assert middle_workspace_dir.exists()
    assert newest_workspace_dir.exists()


def test_remove_workspaces_over_storage_limit_handles_concurrently_removed_workspace(
    isolated_workspace_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        cleaner_module,
        "WORKSPACE_STORAGE_MAX_SIZE",
        0,
    )

    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    workspace = cleaner_module.WorkspaceSnapshot(
        path=workspace_dir,
        modified_at=0,
        size=1,
    )

    WorkspaceManager.cleanup_workspace(workspace_id)  # race condition

    removed_count = WorkspaceCleaner._remove_workspaces_over_storage_limit([workspace])

    assert not workspace_dir.exists()
    assert removed_count == 0


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


def test_remove_workspaces_over_storage_limit_logs_oserror_and_continues(
    isolated_workspace_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        cleaner_module,
        "WORKSPACE_STORAGE_MAX_SIZE",
        1,
    )

    failing_workspace_dir = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )
    removable_workspace_dir = WorkspaceManager.setup_workspace_dir(
        WorkspaceManager.create_workspace_id()
    )

    workspaces = [
        cleaner_module.WorkspaceSnapshot(
            path=failing_workspace_dir,
            modified_at=10.0,
            size=1,
        ),
        cleaner_module.WorkspaceSnapshot(
            path=removable_workspace_dir,
            modified_at=20.0,
            size=1,
        ),
    ]

    original_rmtree = cleaner_module.shutil.rmtree

    def mocked_rmtree(path: Path) -> None:
        if path == failing_workspace_dir:
            raise OSError("permission denied")

        original_rmtree(path)

    monkeypatch.setattr(
        cleaner_module.shutil,
        "rmtree",
        mocked_rmtree,
    )

    caplog.set_level(
        logging.WARNING,
        logger=cleaner_module.__name__,
    )

    removed_count = WorkspaceCleaner._remove_workspaces_over_storage_limit(workspaces)

    assert failing_workspace_dir.exists()
    assert not removable_workspace_dir.exists()
    assert removed_count == 1
    assert "Could not remove workspace" in caplog.text
    assert "permission denied" in caplog.text
