import gemmi

from app.coarse_grain.models import CoarseGrainModelRegistry


def test_coarse_grain_models_from_registry_execution(structure) -> None:  # type: ignore
    models = CoarseGrainModelRegistry.get_dropdown_options()
    failed_models = []

    for model_name, _ in models:
        try:
            cls = CoarseGrainModelRegistry.get_model(model_name)
            model_instance = cls()

            json_config = model_instance.read_json_model()
            if not json_config:
                failed_models.append(f"{model_name} (JSON Config returned empty)")
                continue

            input_struct = structure.clone()
            cg_structure = model_instance.get_coarse_grain_structure(input_struct)

            if cg_structure is None:
                failed_models.append(f"{model_name} (Returned None)")
            elif not isinstance(cg_structure, gemmi.Structure):
                failed_models.append(
                    f"{model_name} (Returned {type(cg_structure)}, expected gemmi.Structure)"
                )

        except Exception as e:
            failed_models.append(f"{model_name} (Exception: {str(e)})")

    if failed_models:
        for failure in failed_models:
            print(f"FAILED: {failure}")
        assert not failed_models, (
            f"{len(failed_models)} models failed to execute coarse graining."
        )
