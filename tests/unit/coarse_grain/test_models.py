from app.coarse_grain.models import CoarseGrainModelRegistry


def test_coarse_grain_models_from_registry_can_be_created():
    models = CoarseGrainModelRegistry.get_dropdown_options()
    failed_models = []

    for model_name, _ in models:
        try:
            cls = CoarseGrainModelRegistry.get_model(model_name)
            obj = cls().read_json_model()

            if not obj:
                failed_models.append(f"{model_name} (Returned None/Empty)")

        except Exception as e:
            failed_models.append(f"{model_name} (Error: {str(e)})")

    if failed_models:
        print("\n--- Failed Coarse Grain Models ---")
        for failure in failed_models:
            print(f"FAILED: {failure}")

        assert not failed_models, f"{len(failed_models)} models failed to load."
    else:
        print("All models created successfully!")
