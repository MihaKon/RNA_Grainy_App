from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.exceptions import FileProcessingError
from app.services.workspaces import WorkspaceManager
from app.services.workspaces.paths import CONSUMED_MARKER

pytestmark = pytest.mark.usefixtures("isolated_workspace_storage")


def test_metadata_is_unavailable_for_a_workspace_created_before_metadata_support(
    client: TestClient,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace = WorkspaceManager.setup_workspace_dir(workspace_id)
    (workspace / "coarse.mmcif").write_text("old result")

    response = client.get(f"/api/results/{workspace_id}")

    assert response.status_code == 404
    assert (
        client.get(f"/api/results/{workspace_id}/coarse?file_format=mmcif").status_code
        == 200
    )


@pytest.mark.parametrize(
    ("workspace_id", "status"),
    [
        ("not-a-uuid", 422),
        ("594887c0-d7cf-4f93-98c1-9458d58a0cea", 404),
    ],
)
def test_missing_or_invalid_metadata_returns_a_json_error(
    client: TestClient,
    workspace_id: str,
    status: int,
) -> None:
    response = client.get(f"/api/results/{workspace_id}")

    assert response.status_code == status
    assert response.json()["detail"]


def test_metadata_reads_do_not_consume_or_extend_a_result(
    client: TestClient,
    isolated_workspace_storage: Path,
) -> None:
    original = client.post(
        "/api/coarse-grain/preset",
        data={
            "preset_id": "1EHZ",
            "selected_model": "SimModel",
            "chains": "A",
            "models": "1",
        },
    )
    assert original.status_code == 200
    result = original.json()
    workspace = isolated_workspace_storage / result["workspace_id"]
    modified_at = workspace.stat().st_mtime_ns

    for _ in range(2):
        response = client.get(f"/api/results/{result['workspace_id']}")
        assert response.status_code == 200
        assert response.json() == result
        assert response.headers["content-type"] == "application/json"
        assert response.headers["cache-control"] == "no-store"

    assert not (workspace / CONSUMED_MARKER).exists()
    assert workspace.stat().st_mtime_ns == modified_at


def test_metadata_write_failure_removes_the_incomplete_workspace(
    client: TestClient,
    isolated_workspace_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_file = WorkspaceManager.create_file

    async def fail_metadata(workspace_id: str, content: str, filename: str) -> Path:
        if filename == "result.json":
            raise FileProcessingError("Could not save result metadata.")
        return await create_file(workspace_id, content, filename)

    monkeypatch.setattr(WorkspaceManager, "create_file", fail_metadata)

    response = client.post(
        "/api/coarse-grain/preset",
        data={"preset_id": "1EHZ", "selected_model": "SimModel"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Could not save result metadata."
    assert list(isolated_workspace_storage.iterdir()) == []
