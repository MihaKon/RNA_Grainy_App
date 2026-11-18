import json
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from app.services.workspaces import WorkspaceManager


@pytest.mark.parametrize("width", [390, 1920])
def test_shared_custom_result_downloads_definition_and_report(
    page: Page, test_data_dir: Path, width: int
) -> None:
    page.set_viewport_size({"width": width, "height": 900})
    base_url = page.url.rstrip("/")
    definition = json.loads((test_data_dir / "custom_model.json").read_text())
    response = page.request.post(
        f"{base_url}/api/coarse-grain/preset",
        multipart={
            "preset_id": "1EHZ",
            "selected_model": "custom",
            "custom_model_data": json.dumps(definition),
        },
    )
    assert response.status == 200
    result = response.json()
    try:
        page.goto(f"{base_url}/results/{result['workspace_id']}/")
        report = page.get_by_role("region", name="Conversion report", exact=True)
        expect(report).to_be_visible()
        expect(report).to_contain_text("Modified nucleotide mapped")
        with page.expect_download() as custom_download:
            page.get_by_role("button", name="Download custom model (JSON)").click()
        custom_path = custom_download.value.path()
        assert custom_path is not None
        assert json.loads(custom_path.read_text()) == definition
        with page.expect_download() as report_download:
            report.get_by_role("button", name="Download report").click()
        report_path = report_download.value.path()
        assert report_path is not None
        assert json.loads(report_path.read_text()) == result["report"]
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        page.reload()
        expect(report).to_be_visible()
        expect(
            page.get_by_role("button", name="Download custom model (JSON)")
        ).to_be_visible()
    finally:
        WorkspaceManager.cleanup_workspace(result["workspace_id"])
