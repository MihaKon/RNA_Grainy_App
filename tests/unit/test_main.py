from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.routes.frontend

INDEX_HTML = '<!doctype html><div id="root"></div>'


@pytest.fixture
def frontend_dist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text(INDEX_HTML)
    (tmp_path / "favicon.svg").write_text("<svg/>")
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log('app');")
    monkeypatch.setattr(app.routes.frontend, "FRONTEND_DIST_DIR", tmp_path)
    return tmp_path


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.usefixtures("frontend_dist")
@pytest.mark.parametrize("path", ["/", "/documentation", "/results/some-workspace"])
def test_frontend_routes_serve_the_app(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert response.text == INDEX_HTML
    assert response.headers["cache-control"] == "no-cache"


@pytest.mark.usefixtures("frontend_dist")
def test_fingerprinted_assets_are_cached_for_good(client: TestClient) -> None:
    response = client.get("/assets/index-abc123.js")

    assert response.status_code == 200
    assert response.text == "console.log('app');"
    assert "immutable" in response.headers["cache-control"]


@pytest.mark.usefixtures("frontend_dist")
def test_root_files_are_served(client: TestClient) -> None:
    response = client.get("/favicon.svg")

    assert response.status_code == 200
    assert response.text == "<svg/>"
    assert "cache-control" not in response.headers


@pytest.mark.usefixtures("frontend_dist")
def test_unknown_api_paths_are_not_swallowed_by_the_app(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


@pytest.mark.usefixtures("frontend_dist")
def test_files_outside_the_build_are_not_served(client: TestClient) -> None:
    response = client.get("/..%2F..%2Fpyproject.toml")

    assert response.status_code == 200
    assert response.text == INDEX_HTML


def test_missing_build_is_reported(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(app.routes.frontend, "FRONTEND_DIST_DIR", tmp_path)

    response = client.get("/")

    assert response.status_code == 404
    assert "Frontend build not found" in response.json()["detail"]


def test_model_images_are_still_served_as_static_files(client: TestClient) -> None:
    response = client.get("/static/images/simmodel.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
