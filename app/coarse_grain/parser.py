from dataclasses import dataclass
from app.models import CoarseGrainModels

import gemmi

@dataclass
class CoarseGrainSelector:
    atoms_subset: list[str]

    def _build_selection_query(self) -> str:
        atoms = ",".join(self.atoms_subset) if self.atoms_subset else "*"
        # models = ...
        # chains = ...
        query = f"//*//{atoms}" # query = f"/{models}/{chains}/{residues}/{atoms}
        return query
    
    def select(self, original_structure: gemmi.Structure) -> gemmi.Structure:
        query = self._build_selection_query()
        selection = gemmi.Selection(query) 
        coarse_structure = selection.copy_structure_selection(original_structure)
        return coarse_structure


def transform_to_coarse_grain(
    original_structure: gemmi.Structure, coarse_grain_model: CoarseGrainModels
) -> gemmi.Structure:
    model = coarse_grain_model.model()
    selector = CoarseGrainSelector(atoms_subset=model["atoms"])
    return selector.select(original_structure)
