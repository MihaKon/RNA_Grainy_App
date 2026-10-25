import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.services.workspaces.cleaner as cleaner_module
from app.services.workspaces import WorkspaceCleaner
from app.services.workspaces.paths import CONSUMED_MARKER
from app.settings import WORKSPACE_CONSUMED_LIFETIME


def test_results_lifecycle(
    client: TestClient,
    isolated_workspace_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload_response = client.post(
        "/api/coarse-grain/preset",
        data={"preset_id": "1EHZ", "selected_model": "SimModel"},
    )

    assert upload_response.status_code == 200
    result = upload_response.json()
    workspace_id = result["workspace_id"]
    files = result["files"]
    metadata_url = f"/api/results/{workspace_id}"
    assert client.get(metadata_url).json() == result

    download_urls = {
        "reference": files["reference_url"],
        "coarse_cif": files["coarse_mmcif_url"],
        "coarse_pdb": files["coarse_pdb_url"],
    }

    for url in [*download_urls.values(), files["consumed_url"]]:
        assert url.startswith(f"/api/results/{workspace_id}/")

    downloaded_contents: dict[str, bytes] = {}

    for result_name, url in download_urls.items():
        response = client.get(url)
        assert response.status_code == 200
        assert response.content
        assert response.headers["content-type"] == "application/octet-stream"
        downloaded_contents[result_name] = response.content

    workspace_dir = isolated_workspace_storage / workspace_id
    assert workspace_dir.is_dir()

    expected_files = {
        "reference": workspace_dir / "reference.mmcif",
        "coarse_cif": workspace_dir / "coarse.mmcif",
        "coarse_pdb": workspace_dir / "coarse.pdb",
        "metadata": workspace_dir / "result.json",
    }

    for file_path in expected_files.values():
        assert file_path.is_file()

    consumed_response = client.post(files["consumed_url"])
    assert consumed_response.status_code == 204
    assert consumed_response.content == b""
    assert (workspace_dir / CONSUMED_MARKER).is_file()

    assert all(downloaded_contents.values())

    second_download_response = client.get(download_urls["reference"])
    assert second_download_response.status_code == 200
    assert second_download_response.content == downloaded_contents["reference"]

    WorkspaceCleaner.cleanup_workspaces()
    assert workspace_dir.is_dir()

    after_grace_period = time.time() + WORKSPACE_CONSUMED_LIFETIME
    monkeypatch.setattr(cleaner_module.time, "time", lambda: after_grace_period)
    WorkspaceCleaner.cleanup_workspaces()
    assert not workspace_dir.exists()

    expired_download_response = client.get(download_urls["reference"])
    assert expired_download_response.status_code == 404
    assert client.get(metadata_url).status_code == 404
