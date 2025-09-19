import io
from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_file_upload(file: io.BytesIO):
    response = client.post(
        "/uploadfile/", files={"file": (file.name, file, "text/plain")}
    )
    assert response.status_code == 200
    assert response.json() == {"filename": "TestFileName.TestExtension"}


def test_file_upload_without_file():
    response = client.post("/uploadfile/")
    assert response.status_code == 422


def test_file_upload_empty_file():
    empty_file = io.BytesIO(b"")
    empty_file.name = "empty.txt"

    response = client.post(
        "/uploadfile/", files={"file": ("empty.txt", empty_file, "text/plain")}
    )

    assert response.status_code == 200
    assert response.json() == {"filename": "empty.txt"}


def test_file_upload_large_filename(file: io.BytesIO):
    file.name = "a" * 100 + ".txt"

    response = client.post(
        "/uploadfile/", files={"file": (file.name, file, "text/plain")}
    )

    assert response.status_code == 200
    assert response.json() == {"filename": file.name}
