import subprocess
import sys
import time
from collections.abc import Generator

import httpx
import pytest
from playwright.sync_api import Page


PORT = 8000
BASE_URL = f"http://127.0.0.1:{PORT}"


@pytest.fixture(scope="session", autouse=True)
def start_local_server() -> Generator[None, None, None]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
        ],
    )

    try:
        for _ in range(50):
            if process.poll() is not None:
                raise RuntimeError(f"Uvicorn exited with code {process.returncode}.")

            try:
                response = httpx.get(
                    f"{BASE_URL}/healthz",
                    timeout=1,
                )

                if response.status_code == 200:
                    break
            except httpx.RequestError:
                pass

            time.sleep(0.2)
        else:
            raise RuntimeError("Uvicorn did not become ready within 10 seconds.")

        yield
    finally:
        if process.poll() is None:
            process.terminate()

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


@pytest.fixture
def page(page: Page) -> Generator[Page, None, None]:
    page.goto(BASE_URL)
    yield page
