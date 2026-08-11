import io

import pytest
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock


class TestRCSBUpload:
    def test_fetch_rcsb_server_error_returns_400(
        self, client: TestClient, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(
            url="https://files.rcsb.org/download/9XYZ.cif",
            method="GET",
            status_code=502,
        )

        response = client.post(
            "/upload/rcsb",
            data={"rcsb_id": "9XYZ", "selected_model": "SimModel"},
        )

        assert response.status_code == 422

    @pytest.mark.parametrize("rcsb_id", ["4GXY", "4gxy"])
    @pytest.mark.usefixtures("isolated_workspace_storage")
    def test_fetch_rcsb_valid_id_returns_200(
        self,
        client: TestClient,
        httpx_mock: HTTPXMock,
        rcsb_id: str,
        cif_file: io.BytesIO,
    ) -> None:
        valid_cif_text = cif_file.read().decode("utf-8")

        httpx_mock.add_response(
            url=f"https://files.rcsb.org/download/{rcsb_id.upper()}.cif",
            method="GET",
            status_code=200,
            text=valid_cif_text,
        )

        response = client.post(
            "/upload/rcsb",
            data={"rcsb_id": rcsb_id, "selected_model": "SimModel"},
        )

        assert response.status_code == 200

    def test_fetch_rcsb_invalid_id_returns_400(
        self, client: TestClient, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(
            url="https://files.rcsb.org/download/9XYZ.cif",
            method="GET",
            status_code=404,
        )

        response = client.post(
            "/upload/rcsb",
            data={"rcsb_id": "9XYZ", "selected_model": "SimModel"},
        )

        assert response.status_code == 422

    def test_fetch_rcsb_without_id_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/upload/rcsb",
            data={"selected_model": "SimModel"},
        )

        assert response.status_code == 422

    def test_fetch_rcsb_without_model_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/upload/rcsb",
            data={"rcsb_id": "4GXY"},
        )

        assert response.status_code == 422


class TestFileUpload:
    def test_unsupported_format_file_upload_returns_code_400(
        self, client: TestClient, empty_file: io.BytesIO
    ) -> None:
        response = client.post(
            "/upload/file/",
            files={"file": (empty_file.name, empty_file, "text/plain")},
            data={"selected_model": "SimModel"},
        )
        assert response.status_code == 422

    def test_file_upload_without_file_returns_code_422(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/upload/file/",
            data={"selected_model": "SimModel"},
        )
        assert response.status_code == 422

    def test_file_upload_empty_file_returns_415_code(self, client: TestClient) -> None:
        empty_file = io.BytesIO(b"")
        empty_file.name = "empty.txt"

        response = client.post(
            "/upload/file/",
            files={"file": ("empty.txt", empty_file, "text/plain")},
            data={"selected_model": "SimModel"},
        )

        assert response.status_code == 422

    @pytest.mark.usefixtures("isolated_workspace_storage")
    def test_correct_pdb_file_upload_returns_200(
        self,
        client: TestClient,
        pdb_file: io.BytesIO,
    ) -> None:
        response = client.post(
            "/upload/file/",
            files={"file": (pdb_file.name, pdb_file, "text/plain")},
            data={"selected_model": "SimModel"},
        )
        assert response.status_code == 200

    @pytest.mark.usefixtures("isolated_workspace_storage")
    def test_correct_cif_file_upload_returns_200(
        self, client: TestClient, cif_file: io.BytesIO
    ) -> None:
        response = client.post(
            "/upload/file/",
            files={"file": (cif_file.name, cif_file, "text/plain")},
            data={"selected_model": "SimModel"},
        )

        assert response.status_code == 200

    def test_file_upload_without_model_selection_returns_422(
        self, client: TestClient, pdb_file: io.BytesIO
    ) -> None:
        response = client.post(
            "/upload/file/", files={"file": (pdb_file.name, pdb_file, "text/plain")}
        )
        assert response.status_code == 422
