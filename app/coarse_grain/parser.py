from dataclasses import dataclass
from app.models import CoarseGrainModels

from gemmi import Structure, Selection

@dataclass
class StructureSelector:
    atoms_subset: list[str] | None = None
    models_subset: list[int] | None = None
    chains_subset: list[str] | None = None

    def _filter_models(self, structure: Structure) -> None:
        if self.models_subset is None:
            return 
        
        for i in range(len(structure) - 1, -1, -1):
            model = structure[i]
            model_num = int(model.num)

            if model_num not in self.models_subset:
                del structure[i]
                
    def _build_selection_query(self) -> str:
        atoms = ",".join(self.atoms_subset) if self.atoms_subset else "*"
        chains = ",".join(self.chains_subset) if self.chains_subset else "*"

        query = f"/*/{chains}//{atoms}"
        return query
    
    def select(self, structure: Structure) -> Structure:
        query = self._build_selection_query()
        selection = Selection(query) 
        new_structure =  selection.copy_structure_selection(structure)
        if self.models_subset is not None:
            self._filter_models(new_structure)
        return new_structure

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
