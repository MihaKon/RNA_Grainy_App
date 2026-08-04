import re
from pathlib import Path

from fastapi.testclient import TestClient


def extract_data_attribute(html: str, attribute: str) -> str:
    match = re.search(
        rf'{attribute}="([^"]+)"',
        html,
    )

    if match is None:
        raise AssertionError(f"Missing HTML attribute: {attribute}")

    return match.group(1)


def test_results_lifecycle(
    client: TestClient, isolated_workspace_storage: Path
) -> None:
    upload_response = client.post(
        "/upload/preset/",
        data={"preset_id": "1EHZ", "selected_model": "SimModel"},
    )

    assert upload_response.status_code == 200
    assert "text/html" in upload_response.headers["content-type"]
    assert 'id="comparison-view"' in upload_response.text

    match = re.search(r"results/([^/]+)/", upload_response.text)

    assert match is not None

    result_urls = {
        "reference_url": extract_data_attribute(
            upload_response.text, "data-reference-url"
        ),
        "coarse_cif_url": extract_data_attribute(
            upload_response.text, "data-coarse-cif-url"
        ),
        "coarse_pdb_url": extract_data_attribute(
            upload_response.text, "data-coarse-pdb-url"
        ),
        "consumed_url": extract_data_attribute(
            upload_response.text, "data-consumed-url"
        ),
    }

    assert all(result_urls.values())

    workspace_id = match.group(1)

    for url in result_urls.values():
        assert f"/api/results/{workspace_id}/" in url

    download_urls = {
        "reference_url": result_urls["reference_url"],
        "coarse_cif_url": result_urls["coarse_cif_url"],
        "coarse_pdb_url": result_urls["coarse_pdb_url"],
    }

    downloaded_contents: dict[str, bytes] = {}

    for result_name, url in download_urls.items():
        response = client.get(url)
        assert response.status_code == 200
        assert response.content
        assert response.headers["content-type"] == "application/octet-stream"
        downloaded_contents[result_name] = response.content

    workspace_dir = isolated_workspace_storage / workspace_id
    assert workspace_dir.is_dir()

    expected_files = {
        "reference": workspace_dir / "reference.mmcif",
        "coarse_cif": workspace_dir / "coarse.mmcif",
        "coarse_pdb": workspace_dir / "coarse.pdb",
    }

    for file_path in expected_files.values():
        assert file_path.is_file()

    consumed_response = client.post(result_urls["consumed_url"])
    assert consumed_response.status_code == 204
    assert consumed_response.content == b""
    assert not workspace_dir.exists()

    assert all(downloaded_contents.values())

    second_download_response = client.get(result_urls["reference_url"])

    assert second_download_response.status_code == 422
