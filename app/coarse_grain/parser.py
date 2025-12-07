from dataclasses import dataclass
from app.models import CoarseGrainModels

from gemmi import Structure, Selection

@dataclass
class StructureSelector:
    atoms_subset: list[str] | None = None
    models_subset: list[int] | None = None
    chains_subset: list[str] | None = None

    def _build_selection_query(self) -> str:
        atoms = ",".join(self.atoms_subset) if self.atoms_subset else "*"
        models = ",".join(map(str, self.models_subset)) if self.models_subset else "*"
        chains = ",".join(self.chains_subset) if self.chains_subset else "*"

        query = f"/{models}/{chains}//{atoms}" # query = f"/{models}/{chains}/{residues}/{atoms}
        return query
    
    def select(self, structure: Structure) -> Structure:
        query = self._build_selection_query()
        selection = Selection(query) 
        return selection.copy_structure_selection(structure)

def transform_structure(
    structure: Structure, 
    model_ids: list[int] | None = None, 
    chain_ids: list[str] | None = None, 
    coarse_grain_model: CoarseGrainModels | None = None 
    ) -> Structure:
    atoms_subset = None

    if coarse_grain_model:
        atoms_subset = coarse_grain_model.model()["atoms"]

    selector = StructureSelector(atoms_subset=atoms_subset, models_subset=model_ids, chains_subset=chain_ids)
    return selector.select(structure)
