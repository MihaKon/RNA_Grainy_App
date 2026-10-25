from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.services.workspaces.cleaner as cleaner_module
from app.services.workspaces import WorkspaceCleaner
from app.settings import SECONDS_PER_HOUR, WORKSPACE_MAX_LIFETIME


def test_results_remain_available_for_24_hours_regardless_of_downloads(
    client: TestClient,
    isolated_workspace_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = client.post(
        "/api/coarse-grain/preset",
        data={"preset_id": "1EHZ", "selected_model": "SimModel"},
    )
    assert response.status_code == 200
    result = response.json()
    workspace_id = result["workspace_id"]
    workspace = isolated_workspace_storage / workspace_id
    metadata_file = workspace / "result.json"
    created_at = metadata_file.stat().st_mtime
    urls = [
        f"/api/results/{workspace_id}",
        result["files"]["reference_url"],
        result["files"]["coarse_mmcif_url"],
        result["files"]["coarse_pdb_url"],
    ]
    initial = {url: client.get(url).content for url in urls}
    assert all(initial.values())
    assert "consumed_url" not in result["files"]

    for age in [0, SECONDS_PER_HOUR + 1, WORKSPACE_MAX_LIFETIME - 1]:
        monkeypatch.setattr(cleaner_module.time, "time", lambda: created_at + age)
        assert WorkspaceCleaner.cleanup_workspaces() == 0
        for url in urls:
            download = client.get(url)
            assert download.status_code == 200
            assert download.content == initial[url]
        assert metadata_file.stat().st_mtime == created_at

    monkeypatch.setattr(
        cleaner_module.time, "time", lambda: created_at + WORKSPACE_MAX_LIFETIME
    )
    assert WorkspaceCleaner.cleanup_workspaces() == 1
    assert not workspace.exists()
    for url in urls:
        assert client.get(url).status_code == 404
