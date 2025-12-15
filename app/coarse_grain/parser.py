from dataclasses import dataclass

from gemmi import Selection, Structure

from app.coarse_grain.models import CoarseGrainModelRegistry


@dataclass
class CoarseGrainSelector:
    atoms_subset: list[str]

    def _build_selection_query(self) -> str:
        atoms = ",".join(self.atoms_subset) if self.atoms_subset else "*"
        # models = ...
        # chains = ...
        query = f"//*//{atoms}"  # query = f"/{models}/{chains}/{residues}/{atoms}
        return query

    def select(self, original_structure: Structure) -> Structure:
        query = self._build_selection_query()
        selection = Selection(query)
        coarse_structure = selection.copy_structure_selection(original_structure)
        return coarse_structure


def process_structure_with_coarse_grain_model(
    original_structure: Structure, model_id: str
) -> Structure:
    ModelClass = CoarseGrainModelRegistry.get_model(model_id)

    if not ModelClass:
        raise ValueError(f"Model '{model_id}' not found in registry.")
    cg_model = ModelClass()
    return cg_model
