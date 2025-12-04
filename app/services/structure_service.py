from collections import defaultdict
from typing import Any, DefaultDict

from Bio.PDB.Structure import Structure
from Bio.PDB.StructureBuilder import StructureBuilder

from app.coarse_grain.parser import CoarseGrainModels, transform_to_coarse_grain
from app.models import SupportedFormats
from app.validators import count_structure_entities, get_format_parser

import  gemmi
class StructureProcessor:
    @staticmethod
    def parse_structure(
        content: str, filename: str, file_format: SupportedFormats
    ) -> Structure:
        if file_format == SupportedFormats.CIF.value:
            cif = gemmi.cif.read_string(content)
            structure = gemmi.make_structure_from_block(cif.sole_block())
        else:
            structure = gemmi.read_pdb_string(content)
        return structure

    @staticmethod
    def apply_coarse_graining(structure: gemmi.Structure, model: CoarseGrainModels) -> str: #fix: move to parser
        """TEST METHOD"""
        config = model.model()
        atom_subset = config["atoms"]
        residues_subset = config["residues"] # fix: idk if we need this

        subset=[]
        if atom_subset:
            subset.append(f"{','.join(atom_subset)}")

        selection_str = ",".join(atom_subset) if subset else "*"
        selection = gemmi.Selection(f"//*//{selection_str}") 
        coarse_structure = selection.copy_structure_selection(structure)
        cif_doc = coarse_structure.make_mmcif_document()

        return cif_doc.as_string()

    @staticmethod
    def build_comparison_context(
        filename: str,
        original_content: str,
        coarse_content: str,
        file_format: str,
        selected_model: str,
        original_structure: Structure,
        coarse_structure: Structure,
    ) -> DefaultDict[str, Any]:
        display_format = "mmcif" if file_format == SupportedFormats.CIF else file_format

        initial_data = {
            "filename": filename,
            "file_format": [display_format, SupportedFormats.PDB.value],
            "file_data": [original_content, coarse_content],
            "selected_model": selected_model,
        }

        context: DefaultDict[str, Any] = defaultdict(list, initial_data)

        for structure in [original_structure, coarse_structure]:
            counts = count_structure_entities(structure)
            for key, count in counts.items():
                context[key].append(count)

        return context
