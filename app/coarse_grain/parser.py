from gemmi import Structure

from app.coarse_grain.models import CoarseGrainModelRegistry, DynamicCoarseGrainModel


def process_structure_with_coarse_grain_model(
    original_structure: Structure, 
    model_id: str,
    custom_model_data: dict | None = None
) -> Structure:
    
    if model_id == "custom":
        if not custom_model_data:
            raise ValueError("Custom model selected but no configuration data provided.")
        cg_model = DynamicCoarseGrainModel(custom_model_data) # type: ignore
    else:
        model_class = CoarseGrainModelRegistry.get_model(model_id)
        cg_model = model_class() # type: ignore

    coarse_structure = cg_model.get_coarse_grain_structure(original_structure)
    return coarse_structure