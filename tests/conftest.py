import pytest
from io import BytesIO
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_file() -> BytesIO:
    """Sample file fixture for upload tests."""
    f = b"Hello World"
    byte_stream_file = BytesIO(f)
    byte_stream_file.name = "TestFileName.TestExtension"
    return byte_stream_file
