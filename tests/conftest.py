import pathlib
import subprocess
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from gemmi import Structure, cif, make_structure_from_block
from playwright.sync_api import Page

from app.main import app

TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"
PORT = 8000
BASE_URL = f"http://localhost:{PORT}"


@pytest.fixture(scope="session", autouse=True)
def start_local_server():
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--port", str(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    yield

    process.terminate()
    process.wait()


@pytest.fixture
def page(page: Page):
    page.goto(BASE_URL)
    yield page


@pytest.fixture
def test_data_dir() -> pathlib.Path:
    return TEST_DATA_DIR


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
    with open(TEST_DATA_DIR / "4GXY.pdb", "rb") as f:
        data = BytesIO(f.read())
    data.name = "1GCT.pdb"
    return data


@pytest.fixture
def cif_file() -> BytesIO:
    with open(TEST_DATA_DIR / "4GXY.cif", "rb") as f:
        data = BytesIO(f.read())
    data.name = "1GCT.cif"
    return data


@pytest.fixture
def structure(cif_file: BytesIO) -> Structure:
    cif_file.seek(0)
    cif_content = cif_file.getvalue().decode("utf-8")
    cif_doc = cif.read_string(cif_content)
    block = cif_doc.sole_block()
    return make_structure_from_block(block)
