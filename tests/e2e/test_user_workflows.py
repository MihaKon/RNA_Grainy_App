from fastapi.testclient import TestClient


def test_full_file_upload_workflow(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    test_file_content = b"This is a test document for E2E testing"
    test_file = {"file": ("test_document.txt", test_file_content, "text/plain")}

    upload_response = client.post("/uploadfile/", files=test_file)
    assert upload_response.status_code == 200
    assert upload_response.json() == {"filename": "test_document.txt"}


def test_api_endpoints_integration(client: TestClient) -> None:
    home_response = client.get("/")
    assert home_response.status_code == 200

    test_content = b"Integration test content"
    files = {"file": ("integration_test.txt", test_content, "text/plain")}
    upload_response = client.post("/uploadfile/", files=files)
    assert upload_response.status_code == 200

    response_data = upload_response.json()
    assert "filename" in response_data
    assert response_data["filename"] == "integration_test.txt"
