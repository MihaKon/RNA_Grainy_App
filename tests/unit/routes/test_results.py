from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.services.workspaces import WorkspaceManager


@dataclass(frozen=True)
class ResultWorkspace:
    workspace_id: str
    directory: Path
    contents: dict[str, bytes]


@pytest.fixture
def result_workspace(isolated_workspace_storage: Path) -> ResultWorkspace:
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    contents = {
        "reference.pdb": b"reference PDB file",
        "reference.mmcif": b"reference mmCIF file",
        "coarse.mmcif": b"coarse mmCIF file",
        "coarse.pdb": b"coarse PDB file",
    }

    for filename, content in contents.items():
        file_path = workspace_dir / filename
        file_path.write_bytes(content)

    return ResultWorkspace(
        workspace_id=workspace_id, directory=workspace_dir, contents=contents
    )


@pytest.mark.parametrize(
    ("file_type", "file_format", "filename"),
    [
        ("reference", "pdb", "reference.pdb"),
        ("reference", "mmcif", "reference.mmcif"),
        ("coarse", "mmcif", "coarse.mmcif"),
        ("coarse", "pdb", "coarse.pdb"),
    ],
)
def test_get_result_file_returns_requested_file(
    client: TestClient,
    result_workspace: ResultWorkspace,
    file_type: str,
    file_format: str,
    filename: str,
) -> None:
    response = client.get(
        (f"/api/results/{result_workspace.workspace_id}/{file_type}"),
        params={"file_format": file_format},
    )

    assert response.status_code == 200
    assert response.content == result_workspace.contents[filename]
    assert response.headers["content-type"] == "application/octet-stream"


@pytest.mark.parametrize(
    ("file_type", "file_format", "filename"),
    [
        ("reference", "pdb", "reference.pdb"),
        ("reference", "mmcif", "reference.mmcif"),
        ("coarse", "mmcif", "coarse.mmcif"),
        ("coarse", "pdb", "coarse.pdb"),
    ],
)
def test_get_result_file_returns_requested_file_multiple_times(
    client: TestClient,
    result_workspace: ResultWorkspace,
    file_type: str,
    file_format: str,
    filename: str,
) -> None:
    first_response = client.get(
        (f"/api/results/{result_workspace.workspace_id}/{file_type}"),
        params={"file_format": file_format},
    )

    second_response = client.get(
        (f"/api/results/{result_workspace.workspace_id}/{file_type}"),
        params={"file_format": file_format},
    )

    for response in (first_response, second_response):
        assert response.status_code == 200
        assert response.content == result_workspace.contents[filename]
        assert response.headers["content-type"] == "application/octet-stream"

    assert result_workspace.directory.exists()


def test_get_result_file_fails_when_file_type_is_unknown(
    client: TestClient,
    result_workspace: ResultWorkspace,
) -> None:
    response = client.get(
        (f"/api/results/{result_workspace.workspace_id}/some_file"),
        params={"file_format": "pdb"},
    )

    assert response.status_code == 422
    assert "Invalid file type requested." in response.text


def test_get_result_file_fails_when_file_format_is_unknown(
    client: TestClient,
    result_workspace: ResultWorkspace,
) -> None:
    response = client.get(
        (f"/api/results/{result_workspace.workspace_id}/reference"),
        params={"file_format": "txt"},
    )

    assert response.status_code == 422
    assert "Invalid file format requested." in response.text


def test_get_result_file_fails_when_file_format_is_missing(
    client: TestClient,
    result_workspace: ResultWorkspace,
) -> None:
    response = client.get(
        (f"/api/results/{result_workspace.workspace_id}/reference"),
    )

    assert response.status_code == 422


def test_get_result_file_fails_when_workspace_id_is_invalid(
    client: TestClient,
) -> None:
    response = client.get(
        ("/api/results/uuid/reference"),
        params={"file_format": "mmcif"},
    )

    assert response.status_code == 422
    assert "Invalid workspace ID format" in response.text


@pytest.mark.parametrize(
    ("file_type", "file_format"),
    [
        ("reference", "pdb"),
        ("reference", "mmcif"),
        ("coarse", "mmcif"),
        ("coarse", "pdb"),
    ],
)
def test_get_result_file_fails_when_requested_file_is_missing(
    isolated_workspace_storage: Path,
    client: TestClient,
    file_type: str,
    file_format: str,
) -> None:
    workspace_id = WorkspaceManager.create_workspace_id()
    workspace_dir = WorkspaceManager.setup_workspace_dir(workspace_id)

    result_workspace = ResultWorkspace(
        workspace_id=workspace_id, directory=workspace_dir, contents={}
    )

    response = client.get(
        (f"/api/results/{result_workspace.workspace_id}/{file_type}"),
        params={"file_format": file_format},
    )
    assert response.status_code == 422
    assert "does not exist" in response.text
    assert workspace_dir.exists()


def test_consumed_removes_workspace(
    client: TestClient,
    result_workspace: ResultWorkspace,
) -> None:
    response = client.post((f"/api/results/{result_workspace.workspace_id}/consumed"))

    assert response.status_code == 204
    assert len(response.content) == 0
    assert not result_workspace.directory.exists()


def test_consumed_is_idempotent(
    client: TestClient,
    result_workspace: ResultWorkspace,
) -> None:
    first_response = client.post(
        (f"/api/results/{result_workspace.workspace_id}/consumed")
    )
    second_response = client.post(
        (f"/api/results/{result_workspace.workspace_id}/consumed")
    )

    assert first_response.status_code == 204
    assert second_response.status_code == 204
    assert not result_workspace.directory.exists()


@pytest.mark.parametrize(
    ("file_type", "file_format", "filename"),
    [
        ("reference", "pdb", "reference.pdb"),
        ("reference", "mmcif", "reference.mmcif"),
        ("coarse", "mmcif", "coarse.mmcif"),
        ("coarse", "pdb", "coarse.pdb"),
    ],
)
def test_consumed_makes_download_unavailable(
    client: TestClient,
    result_workspace: ResultWorkspace,
    file_type: str,
    file_format: str,
    filename: str,
) -> None:
    first_response = client.post(
        (f"/api/results/{result_workspace.workspace_id}/consumed")
    )
    assert first_response.status_code == 204

    second_response = client.get(
        (f"/api/results/{result_workspace.workspace_id}/{file_type}"),
        params={"file_format": file_format},
    )

    assert second_response.status_code == 422
    assert not result_workspace.directory.exists()


def test_consumed_fails_when_workspace_id_is_invalid(
    client: TestClient,
) -> None:
    response = client.post("/api/results/uuid/consumed")
    assert response.status_code == 422
    assert "Invalid workspace ID format" in response.text
