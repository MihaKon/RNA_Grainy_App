from collections.abc import Iterable

from gemmi import Residue

PHOSPHATE_ATOMS = {"P", "OP1", "OP2"}

BACKBONE_ATOMS = {
    "C1'",
    "C2'",
    "C3'",
    "C4'",
    "C5'",
    "O2'",
    "O3'",
    "O4'",
    "O5'",
}

BASE_ATOMS = {
    "A": {"N1", "C2", "N3", "C4", "C5", "C6", "N6", "N7", "C8", "N9"},
    "C": {"N1", "C2", "O2", "N3", "C4", "N4", "C5", "C6"},
    "G": {"N1", "C2", "N2", "N3", "C4", "C5", "C6", "O6", "N7", "C8", "N9"},
    "U": {"N1", "C2", "O2", "N3", "C4", "O4", "C5", "C6"},
}

ATOM_NAME_ALIASES = {
    "O1P": "OP1",
    "O2P": "OP2",
}


def normalize_atom_name(atom_name: str) -> str:
    return ATOM_NAME_ALIASES.get(atom_name, atom_name)


def get_atoms(residue_name: str) -> set[str]:
    return BACKBONE_ATOMS | PHOSPHATE_ATOMS | BASE_ATOMS[residue_name]


def get_required_atoms(residue_name: str, atom_groups: Iterable[list[str]]) -> set[str]:
    configured_atoms = {
        normalize_atom_name(atom_name) for atoms in atom_groups for atom_name in atoms
    }
    return configured_atoms & get_atoms(residue_name)


def check_residue_completeness(
    residue: Residue,
    required_atoms: set[str],
    is_first_residue: bool = False,
) -> set[str]:
    present_atoms = {normalize_atom_name(atom.name) for atom in residue}
    missing_atoms = required_atoms - present_atoms

    if is_first_residue and PHOSPHATE_ATOMS.isdisjoint(present_atoms):
        missing_atoms -= PHOSPHATE_ATOMS

    return missing_atoms
