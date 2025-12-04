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
        job_id: str,
        filename: str,
        file_format: SupportedFormats,
        selected_model: CoarseGrainModels
    ) -> DefaultDict[str, Any]:

        initial_data = {
            "job_id": job_id,
            "reference_url": f"/api/jobs/{job_id}/reference?file_format={file_format}", 
            "coarse_url": f"/api/jobs/{job_id}/coarse?file_format={COARSE_FILE_FORMAT}",
            "filename": filename,
            "file_format": [file_format, COARSE_FILE_FORMAT],
            "selected_model": selected_model,
        }

        context: DefaultDict[str, Any] = defaultdict(list, initial_data)

        # fix: move to calculations in other issue
        """
        for structure in [original_structure, coarse_structure]:
            counts = count_structure_entities(structure)
            for key, count in counts.items():
                context[key].append(count)
        """
        return context
