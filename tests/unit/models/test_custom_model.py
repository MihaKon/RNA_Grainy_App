import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.models.custom_model import CustomModelDefinition
from app.models.form import describe_custom_model_error


@pytest.fixture
def definition(test_data_dir: Path) -> dict[str, Any]:
    return json.loads((test_data_dir / "custom_model.json").read_text())


def error_message(data: dict[str, Any]) -> str:
    with pytest.raises(ValidationError) as error:
        CustomModelDefinition.model_validate(data)
    return describe_custom_model_error(error.value)


def test_accepts_a_complete_definition(definition: dict[str, Any]) -> None:
    CustomModelDefinition.model_validate(definition)


@pytest.mark.parametrize("field", ["default_mapping", "connectivity"])
def test_requires_the_sections_used_for_coarse_graining(
    definition: dict[str, Any], field: str
) -> None:
    del definition[field]

    assert error_message(definition) == f"Invalid custom model: {field}: Field required"


def test_rejects_a_definition_with_only_a_name() -> None:
    assert error_message({"model_name": "Example"}).startswith(
        "Invalid custom model: default_mapping: Field required"
    )


def test_rejects_unknown_fields(definition: dict[str, Any]) -> None:
    definition["unexpected_field"] = True

    assert error_message(definition) == (
        "Invalid custom model: unexpected_field: Extra inputs are not permitted"
    )


def test_rejects_wrong_field_types(definition: dict[str, Any]) -> None:
    definition["default_mapping"]["residues"] = "ACGU"

    assert error_message(definition) == (
        "Invalid custom model: default_mapping.residues: Input should be a valid list"
    )


def test_rejects_an_empty_residue_list(definition: dict[str, Any]) -> None:
    definition["default_mapping"]["residues"] = []

    assert error_message(definition).startswith(
        "Invalid custom model: default_mapping.residues: List should have at least 1 item"
    )


def test_rejects_mappings_for_residues_outside_the_default(
    definition: dict[str, Any],
) -> None:
    definition["mapping"][0]["residues"].append("T")

    assert error_message(definition) == (
        "Invalid custom model: Residue T has a mapping but is not listed in "
        "default_mapping residues."
    )


def test_rejects_a_definition_without_beads(definition: dict[str, Any]) -> None:
    empty_config = {
        "bead_names": {},
        "atom_centers": {},
        "description": {},
        "strategies": {},
    }
    definition["default_mapping"]["config"] = copy.deepcopy(empty_config)
    definition["mapping"] = []
    definition["connectivity"] = {"intra_residue": [], "inter_residue": []}

    assert (
        error_message(definition) == "Invalid custom model: The model defines no beads."
    )


def test_rejects_beads_without_atoms(definition: dict[str, Any]) -> None:
    definition["default_mapping"]["config"]["atom_centers"]["A2"] = []

    assert (
        error_message(definition) == "Invalid custom model: Bead A2 of A has no atoms."
    )


def test_rejects_unknown_strategies(definition: dict[str, Any]) -> None:
    definition["default_mapping"]["config"]["strategies"]["A1"] = "closest"

    assert error_message(definition) == (
        "Invalid custom model: Bead A1 of A has an unknown strategy 'closest'. "
        "Use one of: direct, geometric_center, center_of_mass."
    )


def test_rejects_connections_to_beads_missing_in_some_residues(
    definition: dict[str, Any],
) -> None:
    purine_config = definition["mapping"][0]["config"]
    purine_config["bead_names"]["A6"] = "N7"
    purine_config["atom_centers"]["A6"] = ["N7"]
    definition["connectivity"]["intra_residue"].append(["A1", "A6"])

    assert error_message(definition) == (
        "Invalid custom model: Connection A1–A6: bead A6 is not defined for C, U."
    )


def test_rejects_inter_residue_links_to_unknown_beads(
    definition: dict[str, Any],
) -> None:
    definition["connectivity"]["inter_residue"] = [{"source": "A2", "target": "X9"}]

    assert error_message(definition) == (
        "Invalid custom model: Inter-residue connection A2 → X9: "
        "bead X9 is not defined for A, G, C, U."
    )
