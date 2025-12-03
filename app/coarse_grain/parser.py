from dataclasses import dataclass
from io import StringIO

from Bio.PDB import Atom, Model, Chain
from Bio.PDB.PDBIO import PDBIO, Select
from Bio.PDB.mmcifio import MMCIFIO
from Bio.PDB.Structure import Structure
from app.models import CoarseGrainModels, SupportedFormats


@dataclass
class CoarseGrainSelect(Select):
    atoms_subset: list[str]
    residues: list[str]

    def accept_atom(self, atom: Atom.Atom) -> int:
        if (
            atom.get_name() in self.atoms_subset
            or atom.get_parent().get_resname() in self.residues  # type: ignore
        ):
            return 1
        return 0

@dataclass
class ModelAndChainSelect(Select):
    model_ids: list[str] | None = None
    chain_ids: list[str] | None = None

    def accept_model(self, model: Model.Model) -> int:
        if not self.model_ids:
            return 1
        if str(model.get_id()) in self.model_ids:
            return 1
        return 0

    def accept_chain(self, chain: Chain.Chain) -> int:
        if not self.chain_ids:
            return 1
        if chain.get_id() in self.chain_ids:
            return 1
        return 0

    def accept_atom(self, atom: Atom.Atom) -> int:
        return 1
    
def transform_to_coarse_grain(
    original_structure: Structure, coarse_grain_model: CoarseGrainModels
) -> StringIO:
    model = coarse_grain_model.model()
    selector = CoarseGrainSelect(
        atoms_subset=model["atoms"], residues=model["residues"]
    )
    io = PDBIO()
    io.set_structure(original_structure)
    file = StringIO()
    io.save(file=file, select=selector)
    return file

def extract_structure_subset(
    original_structure: Structure, file_format: SupportedFormats, model_ids: list[str] | None = None, chain_ids: list[str] | None = None
) -> StringIO:
    selector = ModelAndChainSelect(model_ids = model_ids, chain_ids = chain_ids)
    file = StringIO()
    if file_format == SupportedFormats.CIF:
        io = MMCIFIO()
        io.set_structure(original_structure)
        io.save(file, select=selector)
    else:
        io = PDBIO()
        io.set_structure(original_structure)
        io.save(file=file, select=selector)

    return file

