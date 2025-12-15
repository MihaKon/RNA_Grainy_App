from gemmi import Structure

from app.coarse_grain.models import CoarseGrainModelRegistry


def process_structure_with_coarse_grain_model(
    original_structure: Structure, model_id: str
) -> Structure:
    model_class = CoarseGrainModelRegistry.get_model(model_id)
    cg_model = model_class()
    coarse_structure = cg_model.get_coarse_grain_structure(original_structure)

    return coarse_structure
