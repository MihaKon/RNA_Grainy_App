import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.mark.usefixtures("isolated_workspace_storage")
@pytest.mark.parametrize("selected_model", ["SimModel", "custom"])
def test_report_and_custom_definition_survive_result_reload(
    client: TestClient, test_data_dir: Path, selected_model: str
) -> None:
    definition = json.loads((test_data_dir / "custom_model.json").read_text())
    data = {"preset_id": "1EHZ", "selected_model": selected_model}
    if selected_model == "custom":
        data["custom_model_data"] = json.dumps(definition)
    response = client.post("/api/coarse-grain/preset", data=data)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["report"]["created_beads"] == result["atom_counts"]["coarse"]
    assert result["report"]["modified_residues"] > 0
    assert result["report"]["residues"]
    assert result["custom_model"] == (
        definition if selected_model == "custom" else None
    )
    reloaded = client.get(f"/api/results/{result['workspace_id']}")
    assert reloaded.status_code == 200
    assert reloaded.json() == result
