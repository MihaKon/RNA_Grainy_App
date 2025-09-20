"""
E2E-specific test configuration.

This conftest.py is specifically for end-to-end tests and can include:
- Browser setup (if using Selenium/Playwright)
- Database setup/teardown
- External service mocks
- Test data fixtures specific to E2E scenarios
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def e2e_client():
    """Session-scoped client for E2E tests to maintain state across tests."""
    return TestClient(app)


@pytest.fixture
def large_test_file():
    """Fixture for testing large file uploads in E2E scenarios."""
    # Create a larger file for E2E testing
    content = b"Large file content for E2E testing. " * 1000  # ~37KB
    return content


@pytest.fixture
def multiple_test_files():
    """Fixture providing multiple files for batch upload testing."""
    files = {
        "document1.txt": b"First document content",
        "document2.txt": b"Second document content",
        "document3.txt": b"Third document content",
    }
    return files
