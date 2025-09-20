import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def e2e_client():
    return TestClient(app)


@pytest.fixture
def large_test_file():
    content = b"Large file content for E2E testing. " * 1000  # ~37KB
    return content


@pytest.fixture
def multiple_test_files():
    files = {
        "document1.txt": b"First document content",
        "document2.txt": b"Second document content",
        "document3.txt": b"Third document content",
    }
    return files
