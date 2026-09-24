import json
import pathlib
import re

from playwright.sync_api import Page, expect

INJECTION_MARKER = "TEST HALTED BY INJECTION"


def test_custom_model_html_is_shown_as_text(
    page: Page, test_data_dir: pathlib.Path
) -> None:
    custom_model_path = test_data_dir / "html_inject_custom_model.json"
    injected_description = json.loads(custom_model_path.read_text())["description"]

    page.get_by_label(re.compile("Choose a file")).set_input_files(
        test_data_dir / "4GXY.cif"
    )
    page.get_by_label("Coarse-grained model").select_option("custom")
    page.get_by_label("Custom model JSON file").set_input_files(custom_model_path)
    expect(page.get_by_text("Custom model loaded")).to_be_visible()

    page.get_by_role("button", name="Coarse-grain structure").click()
    expect(page.get_by_role("region", name="Model report")).to_be_visible()

    page.get_by_text("Model description").click()
    expect(
        page.get_by_role("paragraph").filter(has_text=injected_description)
    ).to_be_visible()
    expect(page.locator('img[src="x"]')).to_have_count(0)
    expect(page.get_by_role("heading", name=INJECTION_MARKER)).to_have_count(0)
