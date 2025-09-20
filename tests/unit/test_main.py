from fastapi.testclient import TestClient
import io


def test_file_upload(client: TestClient, sample_file: io.BytesIO) -> None:
    """Test successful file upload."""
    response = client.post(
        "/uploadfile/", files={"file": (sample_file.name, sample_file, "text/plain")}
    )
    assert response.status_code == 200
    assert response.json() == {"filename": "TestFileName.TestExtension"}


def test_file_upload_without_file(client: TestClient) -> None:
    """Test file upload endpoint without providing a file."""
    response = client.post("/uploadfile/")
    assert response.status_code == 422


def test_file_upload_empty_file(client: TestClient) -> None:
    """Test uploading an empty file."""
    empty_file = io.BytesIO(b"")
    empty_file.name = "empty.txt"

    response = client.post(
        "/uploadfile/", files={"file": ("empty.txt", empty_file, "text/plain")}
    )

    assert response.status_code == 200
    assert response.json() == {"filename": "empty.txt"}


def test_file_upload_large_filename(
    client: TestClient, sample_file: io.BytesIO
) -> None:
    """Test uploading a file with a very long filename."""
    sample_file.name = "a" * 100 + ".txt"

    response = client.post(
        "/uploadfile/", files={"file": (sample_file.name, sample_file, "text/plain")}
    )

    assert response.status_code == 200
    assert response.json() == {"filename": sample_file.name}


def test_root_endpoint(client: TestClient) -> None:
    """Test the root endpoint returns HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
