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


class TestValidateCustomModel:
    def test_accepts_a_valid_definition(
        self, client: TestClient, test_data_dir: Path
    ) -> None:
        response = client.post(
            "/api/models/custom/validate",
            data={
                "custom_model_data": (test_data_dir / "custom_model.json").read_text()
            },
        )

        assert response.status_code == 204

    @pytest.mark.parametrize(
        ("custom_model_data", "detail"),
        [
            ("{", "Invalid JSON format."),
            (
                json.dumps({"unexpected_field": True}),
                "Invalid custom model: default_mapping: Field required",
            ),
            ("x" * 10_000, "Custom model JSON upload size is too large."),
        ],
    )
    def test_rejects_an_invalid_definition(
        self, client: TestClient, custom_model_data: str, detail: str
    ) -> None:
        response = client.post(
            "/api/models/custom/validate",
            data={"custom_model_data": custom_model_data},
        )

        assert response.status_code == 422
        assert response.json() == {"detail": detail}


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

    @pytest.mark.parametrize(
        ("models", "detail"),
        [
            ("0", "Model numbers start at 1."),
            ("1, 0", "Model numbers start at 1."),
            ("1, 2, 1", "Model 1 is listed more than once."),
            (
                "-1",
                "Incorrect symbols in the model selector or provided model ID is negative.",
            ),
            (
                "1;2",
                "Incorrect symbols in the model selector or provided model ID is negative.",
            ),
        ],
    )
    def test_invalid_model_numbers_return_json_error(
        self, client: TestClient, models: str, detail: str
    ) -> None:
        response = client.post(
            "/api/coarse-grain/preset",
            data={"preset_id": "1EHZ", "selected_model": "SimModel", "models": models},
        )

        assert response.status_code == 422
        assert response.json() == {"detail": detail}

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

    def test_unknown_model_returns_json_error(self, client: TestClient) -> None:
        response = client.post(
            "/api/coarse-grain/preset",
            data={"preset_id": "1EHZ", "selected_model": "NonExistentModel"},
        )

        assert response.status_code == 422
        assert response.json() == {
            "detail": "Unknown coarse-grained model: NonExistentModel."
        }

    def test_custom_model_without_definition_returns_json_error(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/coarse-grain/preset",
            data={"preset_id": "1EHZ", "selected_model": "custom"},
        )

        assert response.status_code == 422
        assert response.json() == {
            "detail": "Custom model selected but no definition was provided."
        }

    @pytest.mark.parametrize(
        ("definition", "detail"),
        [
            (
                {"model_name": "Example"},
                "Invalid custom model: default_mapping: Field required",
            ),
            (
                {"unexpected_field": True},
                "Invalid custom model: default_mapping: Field required",
            ),
            (
                [],
                "Invalid custom model: Input should be a valid dictionary or instance of CustomModelDefinition",
            ),
        ],
    )
    def test_incomplete_custom_model_returns_json_error(
        self, client: TestClient, definition: object, detail: str
    ) -> None:
        response = client.post(
            "/api/coarse-grain/preset",
            data={
                "preset_id": "1EHZ",
                "selected_model": "custom",
                "custom_model_data": json.dumps(definition),
            },
        )

        assert response.status_code == 422
        assert response.json() == {"detail": detail}

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


class TestAtomCounts:
    def test_input_atoms_leave_out_water_and_ions(
        self, client: TestClient, test_data_dir: Path
    ) -> None:
        structure = test_data_dir / "1EHZ.pdb"

        response = client.post(
            "/api/coarse-grain/file",
            files={"file": (structure.name, structure.read_bytes(), "text/plain")},
            data={"selected_model": "SimModel"},
        )

        assert response.status_code == 200
        # 1,821 atom sites: 1,652 RNA atoms, 160 waters and 9 magnesium ions.
        assert response.json()["atom_counts"]["original"] == 1652


class TestEmptyResult:
    def test_structure_without_nucleotides_returns_json_error(
        self, client: TestClient, isolated_workspace_storage: Path
    ) -> None:
        protein = (
            "ATOM      1  N   ALA A   1      11.104   6.134  -6.504  1.00  0.00           N\n"
            "ATOM      2  CA  ALA A   1      11.639   6.071  -5.147  1.00  0.00           C\n"
            "END\n"
        )

        response = client.post(
            "/api/coarse-grain/file",
            files={"file": ("protein.pdb", protein.encode(), "text/plain")},
            data={"selected_model": "SimModel"},
        )

        assert response.status_code == 422
        assert "found no nucleotides" in response.json()["detail"]
        assert list(isolated_workspace_storage.iterdir()) == []


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

    @pytest.mark.parametrize(
        ("filename", "is_cif"),
        [("1EHZ.pdb", False), ("1EHZ.cif", True)],
    )
    def test_reference_keeps_the_uploaded_format(
        self, client: TestClient, test_data_dir: Path, filename: str, is_cif: bool
    ) -> None:
        structure = test_data_dir / filename

        response = client.post(
            "/api/coarse-grain/file",
            files={"file": (filename, structure.read_bytes(), "text/plain")},
            data={"selected_model": "SimModel"},
        )

        assert response.status_code == 200
        reference = client.get(response.json()["files"]["reference_url"]).text
        assert reference.startswith("data_") is is_cif
        assert ("\nATOM  " in reference) is not is_cif

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
