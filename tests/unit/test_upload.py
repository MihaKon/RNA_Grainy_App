from pytest_httpx import HTTPXMock 
from fastapi.testclient import TestClient
from app.coarse_modeler import CoarseGrainModels

class TestRCSBUpload:
    def test_fetch_rcsb_server_error_returns_502(
        self, client: TestClient, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(
            url="https://files.rcsb.org/download/9XYZ.cif",
            method="GET",
            status_code=502,
        )

        response = client.post(
            "/upload/rcsb",
            data={"rcsb_id": "9XYZ", "selected_model": CoarseGrainModels.DUMMY.name},
        )
        
        assert response.status_code == 502


class TestFileUpload:
    def test_unsupported_format_file_upload_returns_code_415(
        client: TestClient, empty_file: io.BytesIO
    ) -> None:
        response = client.post(
            "/upload-file/",
            files={"file": (empty_file.name, empty_file, "text/plain")},
            data={"selected_model": "option1"},
        )
        assert response.status_code == 415
