from dataclasses import dataclass
from app.models import CoarseGrainModels

from gemmi import Structure, Selection

@dataclass
class CoarseGrainSelector:
    atoms_subset: list[str]

    def _build_selection_query(self) -> str:
        atoms = ",".join(self.atoms_subset) if self.atoms_subset else "*"
        # models = ...
        # chains = ...
        query = f"//*//{atoms}" # query = f"/{models}/{chains}/{residues}/{atoms}
        return query
    
    def select(self, original_structure: Structure) -> Structure:
        query = self._build_selection_query()
        selection = Selection(query) 
        coarse_structure = selection.copy_structure_selection(original_structure)
        return coarse_structure


def transform_to_coarse_grain(
    original_structure: Structure, coarse_grain_model: CoarseGrainModels
) -> Structure:
    model = coarse_grain_model.model()
    selector = CoarseGrainSelector(atoms_subset=model["atoms"])
    return selector.select(original_structure)
