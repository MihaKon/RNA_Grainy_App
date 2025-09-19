import pytest
from io import BytesIO


@pytest.fixture
def file() -> BytesIO:
    f = b"Hello World"
    f = BytesIO(f)
    f.name = "TestFileName.TestExtension"
    return f
