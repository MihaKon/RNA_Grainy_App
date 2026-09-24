import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

from app.coarse_grain.models import CoarseGrainModelRegistry

pytestmark = pytest.mark.usefixtures("isolated_workspace_storage")


def test_get_app_config(client: TestClient) -> None:
    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json() == {
        "supported_file_formats": ["pdb", "cif", "mmcif"],
        "preset_ids": ["1EHZ", "1MNX", "2F8S"],
        "max_file_upload_size": 100 * 1024**2,
        "custom_model_json_max_chars": 5000,
        "custom_model_json_max_size": 8 * 1024,
    }


class TestListModels:
    def test_returns_every_registered_model(self, client: TestClient) -> None:
        response = client.get("/api/models")

        assert response.status_code == 200
        model_ids = {model["id"] for model in response.json()}
        assert model_ids == set(CoarseGrainModelRegistry._registry)

    def test_models_are_sorted_by_bead_count(self, client: TestClient) -> None:
        models = client.get("/api/models").json()

        bead_counts = [model["beads_per_residue"] for model in models]
        assert bead_counts == sorted(bead_counts)

    def test_description_is_plain_text_with_citation_markers(
        self, client: TestClient
    ) -> None:
        models = client.get("/api/models").json()
        sim_model = next(model for model in models if model["id"] == "SimModel")

        assert "<a" not in sim_model["description"]
        assert "[1]" in sim_model["description"]
        assert sim_model["citations"][0]["number"] == 1
        assert sim_model["citations"][0]["url"].startswith("https://doi.org/")

    def test_mapping_lists_every_residue_separately(self, client: TestClient) -> None:
        models = client.get("/api/models").json()
        sim_model = next(model for model in models if model["id"] == "SimModel")

        residues = {
            mapping["residue"]: mapping["residue_type"]
            for mapping in sim_model["mapping"]
        }
        assert residues == {
            "A": "Purine",
            "G": "Purine",
            "C": "Pyrimidine",
            "U": "Pyrimidine",
        }
        for mapping in sim_model["mapping"]:
            assert [bead["bead_id"] for bead in mapping["beads"]] == [
                "A1",
                "A2",
                "A3",
                "A4",
                "A5",
            ]


class TestCoarseGrainPreset:
    def test_returns_result_with_downloadable_files(
        self, client: TestClient, isolated_workspace_storage: Path
    ) -> None:
        response = client.post(
            "/api/coarse-grain/preset",
            data={"preset_id": "1ehz", "selected_model": "SimModel"},
        )

        assert response.status_code == 200
        result = response.json()
        workspace_id = result["workspace_id"]

        assert result["filename"] == "1EHZ"
        assert result["reference_format"] == "mmcif"
        assert result["coarse_format"] == "mmcif"
        assert result["model"]["id"] == "SimModel"
        assert result["selected_models"] == []
        assert result["selected_chains"] == []
        assert 0 < result["atom_counts"]["coarse"] < result["atom_counts"]["original"]
        assert 0 < result["atom_counts"]["reduction"] < 1
        assert (isolated_workspace_storage / workspace_id).is_dir()

        files = result["files"]
        assert files["consumed_url"] == f"/api/results/{workspace_id}/consumed"
        for url in (
            files["reference_url"],
            files["coarse_mmcif_url"],
            files["coarse_pdb_url"],
        ):
            assert url.startswith(f"/api/results/{workspace_id}/")
            download = client.get(url)
            assert download.status_code == 200
            assert download.content

    def test_filters_models_and_chains(self, client: TestClient) -> None:
        response = client.post(
            "/api/coarse-grain/preset",
            data={
                "preset_id": "1EHZ",
                "selected_model": "SimModel",
                "models": "1",
                "chains": "A",
            },
        )

        assert response.status_code == 200
        assert response.json()["selected_models"] == [1]
        assert response.json()["selected_chains"] == ["A"]

    def test_unknown_preset_returns_json_error(self, client: TestClient) -> None:
        response = client.post(
            "/api/coarse-grain/preset",
            data={"preset_id": "XXXX", "selected_model": "SimModel"},
        )

        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid example ID."}

    def test_missing_field_returns_json_error(self, client: TestClient) -> None:
        response = client.post("/api/coarse-grain/preset", data={"preset_id": "1EHZ"})

        assert response.status_code == 422
        assert response.json() == {"detail": "Required: selected_model"}

    def test_custom_model_description_is_returned_verbatim(
        self, client: TestClient, test_data_dir: Path
    ) -> None:
        custom_model = (test_data_dir / "html_inject_custom_model.json").read_text()

        response = client.post(
            "/api/coarse-grain/preset",
            data={
                "preset_id": "1EHZ",
                "selected_model": "custom",
                "custom_model_data": custom_model,
            },
        )

        assert response.status_code == 200
        model = response.json()["model"]
        assert model["id"] == "custom"
        assert model["description"] == json.loads(custom_model)["description"]
        assert model["image_url"] is None


class TestCoarseGrainFile:
    @pytest.mark.parametrize(
        ("fixture_name", "reference_format"),
        [("pdb_file", "pdb"), ("cif_file", "mmcif")],
    )
    def test_supported_file_returns_result(
        self,
        client: TestClient,
        request: pytest.FixtureRequest,
        fixture_name: str,
        reference_format: str,
    ) -> None:
        structure_file: io.BytesIO = request.getfixturevalue(fixture_name)

        response = client.post(
            "/api/coarse-grain/file",
            files={"file": (structure_file.name, structure_file, "text/plain")},
            data={"selected_model": "SimModel"},
        )

        assert response.status_code == 200
        assert response.json()["filename"] == "1GCT"
        assert response.json()["reference_format"] == reference_format

    def test_unsupported_format_returns_json_error(
        self, client: TestClient, empty_file: io.BytesIO
    ) -> None:
        response = client.post(
            "/api/coarse-grain/file",
            files={"file": (empty_file.name, empty_file, "text/plain")},
            data={"selected_model": "SimModel"},
        )

        assert response.status_code == 422
        assert response.json() == {"detail": "Unsupported file format."}


class TestCoarseGrainRCSB:
    def test_unknown_id_returns_json_error(
        self, client: TestClient, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(
            url="https://files.rcsb.org/download/9XYZ.cif", status_code=404
        )

        response = client.post(
            "/api/coarse-grain/rcsb",
            data={"rcsb_id": "9xyz", "selected_model": "SimModel"},
        )

        assert response.status_code == 422
        assert response.json() == {"detail": "Could not fetch file for RCSB ID: 9XYZ"}

    def test_valid_id_returns_result(
        self, client: TestClient, httpx_mock: HTTPXMock, cif_file: io.BytesIO
    ) -> None:
        httpx_mock.add_response(
            url="https://files.rcsb.org/download/4GXY.cif",
            text=cif_file.read().decode("utf-8"),
        )

        response = client.post(
            "/api/coarse-grain/rcsb",
            data={"rcsb_id": "4gxy", "selected_model": "SimModel"},
        )

        assert response.status_code == 200
        assert response.json()["filename"] == "4GXY"
