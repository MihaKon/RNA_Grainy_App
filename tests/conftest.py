import pathlib

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from gemmi import Structure, cif, make_structure_from_block

from app.main import app as fastapi_app
import app.services.workspaces.manager
import app.services.workspaces.cleaner
import app.services.workspaces.paths
import app.settings


TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


@pytest.fixture
def test_data_dir() -> pathlib.Path:
    return TEST_DATA_DIR


@pytest.fixture
def client() -> TestClient:
    return TestClient(fastapi_app)


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


@pytest.fixture
def isolated_workspace_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Provide an isolated workspace storage directory for each test.
    """

    monkeypatch.setattr(
        app.settings,
        "WORKSPACE_STORAGE_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        app.services.workspaces.paths,
        "WORKSPACE_STORAGE_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        app.services.workspaces.manager,
        "WORKSPACE_STORAGE_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        app.services.workspaces.cleaner,
        "WORKSPACE_STORAGE_DIR",
        tmp_path,
    )

    return tmp_path
