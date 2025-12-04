from collections import defaultdict
from typing import Any, DefaultDict

from app.coarse_grain.parser import CoarseGrainModels, transform_to_coarse_grain
from app.models import SupportedFormats
from app.validators import count_structure_entities
from app.settings import COARSE_FILE_FORMAT

from gemmi import Structure, cif, make_structure_from_block, read_pdb_string

class StructureProcessor:
    @staticmethod
    def parse_structure(
        content: str, filename: str, file_format: SupportedFormats
    ) -> Structure:
        if file_format == SupportedFormats.CIF.value:
            dcif = cif.read_string(content)
            structure = make_structure_from_block(dcif.sole_block())
        else:
            structure = read_pdb_string(content)
        return structure

    @staticmethod
    def apply_coarse_graining(structure: Structure, model: CoarseGrainModels) -> str:
        coarse_structure = transform_to_coarse_grain(structure, model)

        if COARSE_FILE_FORMAT == "pdb":
            return coarse_structure.make_pdb_string() 
        
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

        initial_data = {
            "filename": filename,
            "file_format": [file_format, COARSE_FILE_FORMAT],
            "file_data": [original_content, coarse_content],
            "selected_model": selected_model,
        }

        context: DefaultDict[str, Any] = defaultdict(list, initial_data)

        for structure in [original_structure, coarse_structure]:
            counts = count_structure_entities(structure)
            for key, count in counts.items():
                context[key].append(count)

        return context
