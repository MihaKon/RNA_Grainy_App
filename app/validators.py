from typing import Dict

from Bio.PDB.Structure import Structure
from Bio.PDB.StructureBuilder import StructureBuilder

from app.models import FORMAT_PARSERS, SupportedFormats


def count_structure_entities(structure: Structure) -> Dict[str, int]:
    """Count atoms, chains, models, and residues in a structure."""
    return {
        "atoms": sum(1 for _ in structure.get_atoms()),
        "chains": sum(1 for _ in structure.get_chains()),
        "models": sum(1 for _ in structure.get_models()),
        "residues": sum(1 for _ in structure.get_residues()),
    }


def get_format_parser(file_format: SupportedFormats) -> StructureBuilder:
    parser_class = FORMAT_PARSERS.get(file_format)
    if not parser_class:
        raise ValueError(f"Unsupported format: {file_format}")

    return parser_class(QUIET=True)
