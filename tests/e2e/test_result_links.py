import os
import time

import pytest
from playwright.sync_api import Page, expect

from app.services.workspaces import WorkspaceCleaner, WorkspaceManager


@pytest.mark.parametrize("preset_id", ["1EHZ", "1MNX"])
def test_api_result_opens_in_another_tab_and_survives_reload(
    page: Page, preset_id: str
) -> None:
    base_url = page.url.rstrip("/")
    response = page.request.post(
        f"{base_url}/api/coarse-grain/preset",
        multipart={"preset_id": preset_id, "selected_model": "SimModel"},
    )
    assert response.status == 200
    result = response.json()
    workspace_id = result["workspace_id"]
    link = f"{base_url}/results/{workspace_id}/"
    shared = page.context.new_page()
    methods: list[str] = []
    shared.on(
        "request",
        lambda request: (
            methods.append(request.method) if "/api/results/" in request.url else None
        ),
    )

    try:
        shared.goto(link)
        for _ in range(2):
            expect(
                shared.get_by_role("region", name="Conversion summary")
            ).to_be_visible()
            expect(
                shared.get_by_role("heading", name=preset_id, exact=True)
            ).to_be_visible()
            expect(shared.get_by_role("combobox", name="Representation")).to_be_enabled(
                timeout=60000
            )
            expect(
                shared.get_by_role("button", name="mmCIF", exact=True)
            ).to_be_enabled()
            with shared.expect_download() as download:
                shared.get_by_role("button", name="mmCIF", exact=True).click()
            assert download.value.suggested_filename == f"{preset_id}_SimRNA.cif"
            if _ == 0:
                shared.reload()
        if preset_id == "1MNX":
            indicator = shared.locator(".rnagrainy-model-indicator")
            expect(indicator).to_have_text("Model 1 / 13")
            shared.get_by_role("button", name="Next Model", exact=True).click()
            expect(indicator).to_have_text("Model 2 / 13")
        assert methods and set(methods) == {"GET"}
        metadata = WorkspaceManager.get_file_path(workspace_id, "result.json")
        for age, available in [(2 * 3600, True), (25 * 3600, False)]:
            timestamp = time.time() - age
            os.utime(metadata, (timestamp, timestamp))
            own_workspaces = [
                w
                for w in WorkspaceCleaner._scan_workspaces()
                if w.path.name == workspace_id
            ]
            WorkspaceCleaner._remove_expired_workspaces(own_workspaces)
            shared.reload()
            if available:
                expect(
                    shared.get_by_role("region", name="Conversion summary")
                ).to_be_visible()
                expect(
                    shared.get_by_role("button", name="mmCIF", exact=True)
                ).to_be_enabled()
            else:
                expect(
                    shared.get_by_role("heading", name="Result not available")
                ).to_be_visible()
    finally:
        shared.close()
        WorkspaceManager.cleanup_workspace(workspace_id)
