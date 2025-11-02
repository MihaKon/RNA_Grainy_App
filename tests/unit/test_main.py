import io

from fastapi.testclient import TestClient

from app.coarse_modeler import CoarseGrainModels


def test_unsupported_format_file_upload_returns_code_415(
    client: TestClient, empty_file: io.BytesIO
) -> None:
    response = client.post(
        "/uploadfile/",
        files={"file": (empty_file.name, empty_file, "text/plain")},
        data={"selected_model": "option1"},
    )
    assert response.status_code == 415


def test_file_upload_without_file_returns_code_422(client: TestClient) -> None:
    response = client.post("/uploadfile/")
    assert response.status_code == 422


def test_file_upload_empty_file_returns_415_code(client: TestClient) -> None:
    empty_file = io.BytesIO(b"")
    empty_file.name = "empty.txt"

    response = client.post(
        "/uploadfile/",
        files={"file": ("empty.txt", empty_file, "text/plain")},
        data={"selected_model": CoarseGrainModels.DUMMY.name},
    )

    assert response.status_code == 415


def test_correct_pdb_file_upload_returns_200(
    client: TestClient, pdb_file: io.BytesIO
) -> None:
    response = client.post(
        "/uploadfile/",
        files={"file": (pdb_file.name, pdb_file, "text/plain")},
        data={"selected_model": CoarseGrainModels.DUMMY.name},
    )
    assert response.status_code == 200


def test_correct_cif_file_upload_returns_200(
    client: TestClient, cif_file: io.BytesIO
) -> None:
    response = client.post(
        "/uploadfile/",
        files={"file": (cif_file.name, cif_file, "text/plain")},
        data={"selected_model": CoarseGrainModels.DUMMY.name},
    )
    assert response.status_code == 200


def test_file_upload_without_model_selection_returns_422(
    client: TestClient, pdb_file: io.BytesIO
) -> None:
    response = client.post(
        "/uploadfile/", files={"file": (pdb_file.name, pdb_file, "text/plain")}
    )
    assert response.status_code == 422


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
