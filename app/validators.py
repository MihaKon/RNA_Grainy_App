from typing import Dict

from gemmi import Structure


def count_structure_entities(structure: Structure) -> Dict[str, int]:
    """Count atoms, chains, models, and residues in a structure."""
    return {
        "atoms": sum(1 for _ in structure.get_atoms()),
        "chains": sum(1 for _ in structure.get_chains()),
        "models": sum(1 for _ in structure.get_models()),
        "residues": sum(1 for _ in structure.get_residues()),
    }
