from playwright.sync_api import Page, expect

from app.services.workspaces import WorkspaceManager


def test_api_result_opens_in_another_tab_and_survives_reload(page: Page) -> None:
    base_url = page.url.rstrip("/")
    response = page.request.post(
        f"{base_url}/api/coarse-grain/preset",
        multipart={"preset_id": "1EHZ", "selected_model": "SimModel"},
    )
    assert response.status == 200
    result = response.json()
    workspace_id = result["workspace_id"]
    link = f"{base_url}/results/{workspace_id}/"
    shared = page.context.new_page()

    try:
        shared.goto(link)
        for _ in range(2):
            expect(
                shared.get_by_role("region", name="Conversion summary")
            ).to_be_visible()
            expect(
                shared.get_by_role("heading", name="1EHZ", exact=True)
            ).to_be_visible()
            expect(shared.get_by_role("combobox", name="Representation")).to_be_enabled(
                timeout=60000
            )
            expect(
                shared.get_by_role("button", name="mmCIF", exact=True)
            ).to_be_enabled()
            with shared.expect_download() as download:
                shared.get_by_role("button", name="mmCIF", exact=True).click()
            assert download.value.suggested_filename == "1EHZ_SimRNA.cif"
            if _ == 0:
                shared.reload()
    finally:
        shared.close()
        WorkspaceManager.cleanup_workspace(workspace_id)
