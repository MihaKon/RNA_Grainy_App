from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_file() -> BytesIO:
    f = b"Hello World"
    byte_stream_file = BytesIO(f)
    byte_stream_file.name = "TestFileName.TestExtension"
    return byte_stream_file
