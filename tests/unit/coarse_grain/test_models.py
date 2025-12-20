from app.coarse_grain.models import CoarseGrainModelRegistry


def test_coarse_grain_models_from_registry_can_be_created():
    models = CoarseGrainModelRegistry.get_dropdown_options()

    for model, _ in models:
        cls = CoarseGrainModelRegistry.get_model(model)
        obj = cls().read_json_model()
        assert obj
