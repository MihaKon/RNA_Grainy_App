import pathlib
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import app

TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def empty_file() -> BytesIO:
    f = b"Hello World"
    byte_stream_file = BytesIO(f)
    byte_stream_file.name = "TestFileName.TestExtension"
    return byte_stream_file


@pytest.fixture
def pdb_file() -> BytesIO:
    with open(TEST_DATA_DIR / "1GCT.pdb", "rb") as f:
        data = BytesIO(f.read())
    data.name = "1GCT.pdb"
    return data


@pytest.fixture
def cif_file() -> BytesIO:
    with open(TEST_DATA_DIR / "1GCT.cif", "rb") as f:
        data = BytesIO(f.read())
    data.name = "1GCT.cif"
    return data
