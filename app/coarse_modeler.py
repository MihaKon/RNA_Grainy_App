import enum
import json
from dataclasses import dataclass
from io import StringIO
from typing import Any

from Bio.PDB import Atom
from Bio.PDB.PDBIO import PDBIO, Select
from Bio.PDB.Structure import Structure

from app.settings import BASE_DIR

COARSE_GRAIN_MODELS_DIR = BASE_DIR / "coarse_grain_models"


class CoarseGrainModels(enum.Enum):
    DUMMY = "simrna.json"

    def model(self) -> dict[str, Any]:
        with open(COARSE_GRAIN_MODELS_DIR / self.value) as f:
            result = json.load(f)
        return result


@dataclass
class CoarseGrainSelect(Select):
    atoms_subset: list[str]
    residues: list[str]

    def accept_atom(self, atom: Atom.Atom) -> int:
        if (
            atom.get_name() in self.atoms_subset
            or atom.get_parent().get_resname() in self.residues
        ):
            return 1
        return 0


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
