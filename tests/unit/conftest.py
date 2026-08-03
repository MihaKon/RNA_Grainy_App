from pathlib import Path

import pytest

import app.services.workspaces.manager
import app.services.workspaces.cleaner
import app.services.workspaces.paths
import app.settings


@pytest.fixture
def isolated_workspace_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Provide an isolated workspace storage directory for each test.
    """

    monkeypatch.setattr(
        app.settings,
        "WORKSPACE_STORAGE_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        app.services.workspaces.paths,
        "WORKSPACE_STORAGE_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        app.services.workspaces.manager,
        "WORKSPACE_STORAGE_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        app.services.workspaces.cleaner,
        "WORKSPACE_STORAGE_DIR",
        tmp_path,
    )

    return tmp_path
