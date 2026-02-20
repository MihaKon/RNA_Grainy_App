import pathlib

from playwright.sync_api import Page, expect


def test_html_injection_in_custom_models(
    page: Page, test_data_dir: pathlib.Path
) -> None:
    file_path = test_data_dir / "4GXY.cif"
    with page.expect_file_chooser() as fc_info:
        page.get_by_text("Click to upload").click()

    file_chooser = fc_info.value
    file_chooser.set_files(file_path)
    page.locator('[class="block truncate text-sm text-primary/50"]').click()

    hidden_item = page.locator('[x-show="dropdownOpen"]').get_by_text("Custom Model")
    hidden_item.click()

    file_path = test_data_dir / "html_inject_custom_model.json"
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="Upload JSON").click()

    file_chooser = fc_info.value
    file_chooser.set_files(file_path)
    page.get_by_text("Process Structure").click()

    model_btn = page.get_by_role("button", name="Model description")
    expect(model_btn).to_be_visible()
    model_btn.click()
