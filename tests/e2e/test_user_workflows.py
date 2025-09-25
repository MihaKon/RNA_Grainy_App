import io

from fastapi.testclient import TestClient


# Dummy placeholder for e2e tests
# TODO: After adding visualization configure real life e2e tests
def test_pdb_file_upload_workflow(client: TestClient, pdb_file: io.BytesIO) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    test_file = {"file": (pdb_file.name, pdb_file, "text/plain")}

    upload_response = client.post("/uploadfile/", files=test_file)
    assert upload_response.status_code == 200
